#!/usr/bin/env python3
"""
bridge.py - Hylion Coordinator(JSON) -> BHL lowlevel(UDP 13-byte) 브리지

실행 위치: NUC (BHL onboard)
역할:
  - Jetson coordinator 가 TCP/NDJSON 으로 보내는 행동 결정을
  - BHL C 컨트롤러가 기대하는 13-byte little-endian UDP 패킷("<Bfff")으로 변환
  - watchdog / safety / cold-start 보장
  - duration_sec 기반 시간 타이머: 동작 종료 시점에 자동 STOP + Jetson 에 DONE 회신

자세한 사양: nuc/bhl/Jetson_NUC_연결_가이드.md
"""

import json
import logging
import os
import signal
import socket
import struct
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


# =============================================================================
# 설정 (CLI/env 로 override 가능. 우선순위: CLI > env > default)
# =============================================================================
# ↓↓↓ TUNE: BHL 학습 명령 범위 안에서 보수적으로 잡은 값 ↓↓↓
# gamepad.py 는 raw_stick/32768 로 정규화 → [-1.0, 1.0] 범위가 학습된 범위로 추정.
# 처음엔 full stick 의 절반(0.5)에서 시작해서 실험 후 조정.
VEL_FORWARD_MPS = 0.5        # TUNE: walk_forward 시 velocity_x (m/s, +가 전진)
VEL_TURN_LEFT_RPS = 0.5      # TUNE: turn_left 시 velocity_yaw (rad/s, +가 좌회전 추정 — 검증 필요)
VEL_LATERAL_MPS = 0.0        # TUNE: 좌우(strafe) 미사용. 필요 시 별도 gait_cmd 추가하고 매핑.

# ↓↓↓ TUNE: 통신 설정 ↓↓↓
TCP_LISTEN_HOST = "0.0.0.0"  # 모든 인터페이스. 보안 강화 시 "192.168.10.2" 같은 특정 IP 로.
TCP_LISTEN_PORT = 9000       # coordinator 와 합의된 포트
UDP_TARGET_HOST = "127.0.0.1"  # bridge 가 NUC 에서 실행되므로 localhost. C 컨트롤러도 같은 머신.
UDP_TARGET_PORT = 10011      # BHL consts.h JOYSTICK_PORT 와 일치. 절대 수정 금지.

# ↓↓↓ TUNE: 타이밍/안전 ↓↓↓
WATCHDOG_TIMEOUT_S = 0.2     # 마지막 RX 이후 이 시간 넘으면 STOP. 200ms = 네트워크 지터 여유분.
SEND_RATE_HZ = 20.0          # C joystick_loop polling 주기와 매칭(real_humanoid.cpp).
COLD_START_INIT_WAIT_S = 1.5 # RL_INIT 진입 후 init_percentage 1.0 도달 보장 시간(1.0초 + 여유).
COLD_START_RUNNING_SETTLE_S = 0.1  # RL_RUNNING 진입 후 안정화 짧은 대기.
DEFAULT_DURATION_SEC = 3.0   # action_json 에 duration_sec 가 없거나 0 일 때 사용.
MAX_DURATION_SEC = 30.0      # 안전 상한. 이보다 큰 값은 clamp.

# ↓↓↓ TUNE: 로깅 ↓↓↓
LOG_LEVEL = "INFO"           # DEBUG 로 바꾸면 매 패킷 송신 로그까지 나옴
LOG_FILE: Optional[str] = None  # None 이면 stdout (systemd 가 journald 로 캡쳐). 파일 경로 주면 거기로.


# =============================================================================
# UDP 패킷 (수정 금지 — BHL 호환 인터페이스)
# =============================================================================
# 13 byte: uint8_t mode + float32 vx + float32 vy + float32 vyaw (little-endian)
# 참조: csrc/real_humanoid.cpp joystick_loop() (offset 0,1,5,9 / total 13 bytes)
PACKET_FMT = "<Bfff"
PACKET_SIZE = 13

MODE_KEEP = 0       # 상태 변화 없음 (정상 운용 중 권장)
MODE_IDLE = 1       # -> STATE_IDLE (정지)
MODE_RL_INIT = 2    # -> STATE_RL_INIT (1초간 default pose 진입)
MODE_RL_RUNNING = 3 # -> STATE_RL_RUNNING (정책 명령 따름)


def pack(mode: int, vx: float, vy: float, vyaw: float) -> bytes:
    p = struct.pack(PACKET_FMT, mode, vx, vy, vyaw)
    assert len(p) == PACKET_SIZE, f"packet size {len(p)} != {PACKET_SIZE}"
    return p


STOP_PACKET = pack(MODE_IDLE, 0.0, 0.0, 0.0)
NEUTRAL_PACKET = pack(MODE_KEEP, 0.0, 0.0, 0.0)


# =============================================================================
# 상태
# =============================================================================
@dataclass
class BridgeState:
    current_packet: bytes = STOP_PACKET
    last_rx_time: float = 0.0
    cold_start_done: bool = False
    running: bool = True
    client_connected: bool = False
    # 현재 활성 동작
    active_action_id: Optional[str] = None
    active_deadline: Optional[float] = None  # monotonic 기준
    active_conn: Optional[socket.socket] = None  # DONE 회신용


state = BridgeState()
state_lock = threading.Lock()
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
log = logging.getLogger("bridge")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# =============================================================================
# JSON -> UDP 매핑 (가이드 §6 결정 우선순위)
# =============================================================================
def map_json_to_packet(msg: dict) -> bytes:
    """coordinator 의 action JSON 한 건을 UDP 패킷으로 변환.

    우선순위(위에서 막히면 즉시 STOP):
      1. safety_allowed == false
      2. state_current == EMERGENCY
      3. requires_bhl == false
      4. intent == stop
      5. gait_cmd 매핑
    """
    if not msg.get("safety_allowed", False):
        return STOP_PACKET
    if msg.get("state_current") == "EMERGENCY":
        return STOP_PACKET
    if not msg.get("requires_bhl", False):
        return STOP_PACKET
    if msg.get("intent") == "stop":
        return STOP_PACKET

    gait = msg.get("gait_cmd", "none")

    # ↓↓↓ TUNE: gait_cmd -> velocity 매핑 테이블. 새 gait 추가 시 여기 ↓↓↓
    if gait == "walk_forward":
        return pack(MODE_KEEP, VEL_FORWARD_MPS, 0.0, 0.0)
    if gait == "turn_left":
        return pack(MODE_KEEP, 0.0, VEL_LATERAL_MPS, VEL_TURN_LEFT_RPS)
    if gait == "stop":
        return STOP_PACKET
    # "none" 또는 미지의 값 → 안전하게 속도 0, mode 유지
    return NEUTRAL_PACKET


def clamp_duration(value) -> float:
    """LLM/스키마 외부에서 들어오는 duration_sec 을 안전 범위로 보정."""
    try:
        d = float(value)
    except (TypeError, ValueError):
        return DEFAULT_DURATION_SEC
    if d <= 0:
        return DEFAULT_DURATION_SEC
    return min(d, MAX_DURATION_SEC)


# =============================================================================
# Cold start: IDLE -> RL_INIT -> RL_RUNNING
# =============================================================================
def cold_start() -> None:
    """첫 유효 명령 수신 시 자동 실행. 재연결 시에도 재실행.

    중요: 모드 전환 패킷을 단 1번만 보내면 UDP sender 가 즉시 다른 mode 로 덮어써서
    C 컨트롤러의 next_state 가 즉시 원상복구됨 (real_humanoid.cpp:259 — 매 패킷마다
    command_mode 가 0 이 아니면 next_state 를 갱신). 따라서 sender 가 정확히 그
    모드를 계속 broadcast 하도록 current_packet 자체를 바꾸고 1.5s 대기.
    """
    log.info("cold start: -> RL_INIT (broadcasting mode=2 for %.1fs)", COLD_START_INIT_WAIT_S)
    with state_lock:
        state.current_packet = pack(MODE_RL_INIT, 0.0, 0.0, 0.0)
    time.sleep(COLD_START_INIT_WAIT_S)

    log.info("cold start: -> RL_RUNNING (broadcasting mode=3 for %.1fs)", COLD_START_RUNNING_SETTLE_S)
    with state_lock:
        state.current_packet = pack(MODE_RL_RUNNING, 0.0, 0.0, 0.0)
    time.sleep(COLD_START_RUNNING_SETTLE_S)

    # 이후엔 mode=0(keep) + vel=0 로 두고, handle_client 가 실제 명령으로 갱신.
    with state_lock:
        state.current_packet = NEUTRAL_PACKET
        state.cold_start_done = True
    log.info("cold start: done")


# =============================================================================
# Jetson 에 DONE 회신
# =============================================================================
def send_done(conn: Optional[socket.socket], action_id: Optional[str], reason: str) -> None:
    """Jetson coordinator 에 동작 종료 알림. 같은 TCP 연결 위에 NDJSON 한 줄로.

    실패해도 예외 전파 안 함 (브리지 본체가 죽지 않게).
    """
    if conn is None or action_id is None:
        return
    msg = {
        "event": "done",
        "action_id": action_id,
        "reason": reason,
        "timestamp": utc_now_iso(),
    }
    try:
        line = (json.dumps(msg) + "\n").encode("utf-8")
        conn.sendall(line)
        log.info("TX DONE action_id=%s reason=%s", action_id, reason)
    except OSError as e:
        log.warning("send DONE failed: %s", e)


def finish_active_action(reason: str) -> None:
    """현재 활성 동작을 종료시키고 Jetson 에 DONE 회신.

    호출 시점:
      - 시간 타이머 만료 (timer_loop)
      - 명시적 stop intent 수신 (handle_client)
      - 안전 게이트 발동 시 (safety_allowed=False, EMERGENCY)
    """
    with state_lock:
        action_id = state.active_action_id
        conn = state.active_conn
        had_active = action_id is not None
        # 활성 클리어 + UDP 는 다음 사이클부터 STOP
        state.active_action_id = None
        state.active_deadline = None
        state.current_packet = STOP_PACKET

    if had_active:
        log.info("FINISH action_id=%s reason=%s", action_id, reason)
        send_done(conn, action_id, reason)


# =============================================================================
# TCP server
# =============================================================================
def tcp_server_loop() -> None:
    """단일 클라이언트(coordinator) 만 받는 단순 구조. 끊기면 다시 accept."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((TCP_LISTEN_HOST, TCP_LISTEN_PORT))
    srv.listen(1)
    srv.settimeout(1.0)  # 종료 시 빠져나올 수 있게
    log.info(f"TCP listening on {TCP_LISTEN_HOST}:{TCP_LISTEN_PORT}")

    while state.running:
        try:
            conn, addr = srv.accept()
        except socket.timeout:
            continue
        except OSError as e:
            log.error(f"accept failed: {e}")
            continue

        log.info(f"client connected from {addr}")
        with state_lock:
            state.client_connected = True
            # 새 연결은 항상 cold start 다시 진행
            state.cold_start_done = False
            state.current_packet = STOP_PACKET
            state.active_conn = conn
            state.active_action_id = None
            state.active_deadline = None

        try:
            handle_client(conn)
        except Exception as e:
            log.exception(f"client handler crashed: {e}")
        finally:
            # 끊김 시 진행 중 동작 종료 처리 (DONE 못 보냄 — 연결 이미 끊김)
            with state_lock:
                state.client_connected = False
                state.current_packet = STOP_PACKET
                state.active_action_id = None
                state.active_deadline = None
                state.active_conn = None
            try:
                conn.close()
            except OSError:
                pass
            log.warning("client disconnected -> STOP, waiting for reconnect")

    srv.close()


def start_active_action(msg: dict, conn: socket.socket) -> None:
    """movement 명령 수신 시 활성 동작 시작 + 타이머 갱신."""
    action_id = msg.get("action_id")
    duration = clamp_duration(msg.get("duration_sec"))
    packet = map_json_to_packet(msg)
    deadline = time.monotonic() + duration

    with state_lock:
        state.current_packet = packet
        state.last_rx_time = time.time()
        state.active_action_id = action_id
        state.active_deadline = deadline
        state.active_conn = conn

    log.info(
        "START action_id=%s gait=%s duration=%.2fs",
        action_id, msg.get("gait_cmd"), duration,
    )


def handle_client(conn: socket.socket) -> None:
    conn.settimeout(1.0)
    buf = b""
    while state.running:
        try:
            data = conn.recv(4096)
        except socket.timeout:
            continue
        except ConnectionError as e:
            log.warning(f"recv: {e}")
            return

        if not data:
            return  # 정상 close

        buf += data
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                log.error(f"parse error: {e} (line={line[:120]!r})")
                continue

            # cold start 는 첫 유효 메시지 수신 시 한 번
            with state_lock:
                need_cold_start = not state.cold_start_done
            if need_cold_start:
                cold_start()

            log.info(
                "RX action_id=%s gait=%s intent=%s state=%s safe=%s bhl=%s dur=%s",
                msg.get("action_id"),
                msg.get("gait_cmd"),
                msg.get("intent"),
                msg.get("state_current"),
                msg.get("safety_allowed"),
                msg.get("requires_bhl"),
                msg.get("duration_sec"),
            )

            # 안전 게이트: 진행 중이던 동작도 즉시 종료
            if (not msg.get("safety_allowed", False)
                    or msg.get("state_current") == "EMERGENCY"):
                finish_active_action("safety_or_emergency")
                continue

            intent = msg.get("intent")
            requires_bhl = bool(msg.get("requires_bhl", False))

            # 명시적 stop: 진행 중이던 동작을 종료
            if intent == "stop":
                finish_active_action("stop_command")
                continue

            # BHL 무관 메시지: 무시 (coordinator 가 chat/standby 를 안 보내야 정상.
            # 보냈더라도 active 동작은 그대로 두고 패킷 변경 없이 keepalive 만 처리)
            if not requires_bhl or intent not in {"move"}:
                with state_lock:
                    state.last_rx_time = time.time()
                continue

            # movement 명령 — 새 동작 시작 (keepalive 도 같은 경로로 들어옴.
            # action_id 가 같으면 deadline 유지하면서 패킷만 갱신, 다르면 새 동작으로 갈음)
            with state_lock:
                same_action = (state.active_action_id == msg.get("action_id"))
            if same_action:
                # keepalive — deadline 은 유지, 패킷/last_rx_time 만 갱신
                with state_lock:
                    state.current_packet = map_json_to_packet(msg)
                    state.last_rx_time = time.time()
            else:
                # 새 동작 시작 (이전 동작이 있다면 그 동작은 자동 폐기, DONE 안 보냄
                # — 같은 coordinator 가 새 명령 보낸 거라 굳이 DONE 줄 필요 없음)
                start_active_action(msg, conn)


# =============================================================================
# 시간 타이머 (active_deadline 만료 감시)
# =============================================================================
def timer_loop() -> None:
    """100ms 주기로 active_deadline 체크. 만료 시 finish_active_action."""
    while state.running:
        time.sleep(0.05)
        with state_lock:
            deadline = state.active_deadline
        if deadline is None:
            continue
        if time.monotonic() >= deadline:
            finish_active_action("duration_elapsed")


# =============================================================================
# UDP sender (20 Hz) + watchdog
# =============================================================================
def udp_sender_loop() -> None:
    period = 1.0 / SEND_RATE_HZ
    target = (UDP_TARGET_HOST, UDP_TARGET_PORT)

    while state.running:
        t0 = time.monotonic()

        with state_lock:
            packet = state.current_packet
            last_rx = state.last_rx_time
            cold_done = state.cold_start_done
            connected = state.client_connected

        # Watchdog: cold start 이후 + 클라이언트 연결됨 + 명령 끊긴 지 timeout 초과
        if cold_done and connected and last_rx > 0 and (time.time() - last_rx) > WATCHDOG_TIMEOUT_S:
            if packet != STOP_PACKET:
                log.warning("watchdog: no RX for >%.0fms -> STOP", WATCHDOG_TIMEOUT_S * 1000)
            packet = STOP_PACKET
            with state_lock:
                state.current_packet = STOP_PACKET

        try:
            udp_sock.sendto(packet, target)
        except OSError as e:
            log.error(f"UDP send failed: {e}")
            # 다음 사이클에 재시도

        if log.isEnabledFor(logging.DEBUG):
            m, vx, vy, vyaw = struct.unpack(PACKET_FMT, packet)
            log.debug(f"TX mode={m} vx={vx:.3f} vy={vy:.3f} vyaw={vyaw:.3f}")

        # 정확한 20 Hz 유지
        elapsed = time.monotonic() - t0
        sleep_for = period - elapsed
        if sleep_for > 0:
            time.sleep(sleep_for)


# =============================================================================
# Shutdown
# =============================================================================
def shutdown(*_args) -> None:
    log.info("shutdown: sending STOP and exiting")
    try:
        udp_sock.sendto(STOP_PACKET, (UDP_TARGET_HOST, UDP_TARGET_PORT))
    except OSError:
        pass
    state.running = False
    time.sleep(0.2)
    sys.exit(0)


# =============================================================================
# CLI / env override
# =============================================================================
def apply_env_overrides() -> None:
    """간단한 env 기반 오버라이드. CLI 인자 안 받고 systemd EnvironmentFile 으로 조절."""
    global TCP_LISTEN_HOST, TCP_LISTEN_PORT, UDP_TARGET_HOST, UDP_TARGET_PORT
    global WATCHDOG_TIMEOUT_S, SEND_RATE_HZ, LOG_LEVEL, LOG_FILE
    global VEL_FORWARD_MPS, VEL_TURN_LEFT_RPS, DEFAULT_DURATION_SEC, MAX_DURATION_SEC

    TCP_LISTEN_HOST = os.environ.get("BRIDGE_TCP_HOST", TCP_LISTEN_HOST)
    TCP_LISTEN_PORT = int(os.environ.get("BRIDGE_TCP_PORT", TCP_LISTEN_PORT))
    UDP_TARGET_HOST = os.environ.get("BRIDGE_UDP_HOST", UDP_TARGET_HOST)
    UDP_TARGET_PORT = int(os.environ.get("BRIDGE_UDP_PORT", UDP_TARGET_PORT))
    WATCHDOG_TIMEOUT_S = float(os.environ.get("BRIDGE_WATCHDOG_S", WATCHDOG_TIMEOUT_S))
    SEND_RATE_HZ = float(os.environ.get("BRIDGE_SEND_HZ", SEND_RATE_HZ))
    VEL_FORWARD_MPS = float(os.environ.get("BRIDGE_VEL_FORWARD", VEL_FORWARD_MPS))
    VEL_TURN_LEFT_RPS = float(os.environ.get("BRIDGE_VEL_TURN_LEFT", VEL_TURN_LEFT_RPS))
    DEFAULT_DURATION_SEC = float(os.environ.get("BRIDGE_DEFAULT_DURATION_S", DEFAULT_DURATION_SEC))
    MAX_DURATION_SEC = float(os.environ.get("BRIDGE_MAX_DURATION_S", MAX_DURATION_SEC))
    LOG_LEVEL = os.environ.get("BRIDGE_LOG_LEVEL", LOG_LEVEL)
    LOG_FILE = os.environ.get("BRIDGE_LOG_FILE") or None


def setup_logging() -> None:
    fmt = "%(asctime)s %(levelname)-5s [%(threadName)s] %(message)s"
    handlers = []
    if LOG_FILE:
        handlers.append(logging.FileHandler(LOG_FILE))
    handlers.append(logging.StreamHandler(sys.stdout))
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format=fmt,
        handlers=handlers,
    )


def main() -> None:
    apply_env_overrides()
    setup_logging()
    log.info(
        "config: tcp=%s:%d udp=%s:%d watchdog=%.3fs send=%.0fHz vF=%.2f vT=%.2f durDef=%.1f durMax=%.1f",
        TCP_LISTEN_HOST, TCP_LISTEN_PORT,
        UDP_TARGET_HOST, UDP_TARGET_PORT,
        WATCHDOG_TIMEOUT_S, SEND_RATE_HZ,
        VEL_FORWARD_MPS, VEL_TURN_LEFT_RPS,
        DEFAULT_DURATION_SEC, MAX_DURATION_SEC,
    )

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    threading.Thread(target=tcp_server_loop, name="tcp", daemon=True).start()
    threading.Thread(target=timer_loop, name="timer", daemon=True).start()

    # UDP sender 를 main 스레드에서 돌려서 시그널 즉시 처리되게.
    udp_sender_loop()


if __name__ == "__main__":
    main()
