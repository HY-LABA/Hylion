"""jetson/core/test_coordinator.py — 하드웨어 순차 검증.

coordinator.py 와 동일한 컴포넌트(STT·TTS·gesture daemon·servo)를 초기화하고
마이크 → 스피커 → 팔 → 서보 순으로 하나씩 테스트한다.
각 테스트 후 사용자가 "완료했어" (또는 "완료", "됐어", "다음") 라고 말하면
다음 항목으로 넘어간다.

실행:
    cd ~/Hylion
    python3 -m jetson.core.test_coordinator
"""
from __future__ import annotations

import os
import socket as _socket
import time
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT    = Path(__file__).resolve().parents[2]
_TEST_AUDIO_DIR = PROJECT_ROOT / "data" / "test_episodes"
_TEST_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

RECORD_SEC       = 4.0
CONFIRM_KEYWORDS = {"완료", "완료했어", "다음", "확인", "됐어", "됐습니다", "ok", "오케이"}
_GESTURE_SOCK    = os.environ.get("HYLION_GESTURE_SOCK", "/tmp/hylion_gesture.sock")


# ── gesture daemon 재사용 핸들 ────────────────────────────────────────────────

def _sock_ping(sock_path: str) -> bool:
    try:
        with _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM) as s:
            s.settimeout(2.0)
            s.connect(sock_path)
            s.sendall(b"ping\n")
            return s.recv(64).decode().strip() == "pong"
    except Exception:
        return False


def _sock_send(sock_path: str, cmd: str) -> str | None:
    try:
        with _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM) as s:
            s.settimeout(5.0)
            s.connect(sock_path)
            s.sendall((cmd.strip() + "\n").encode())
            chunks: list[bytes] = []
            while b"\n" not in b"".join(chunks):
                data = s.recv(1024)
                if not data:
                    break
                chunks.append(data)
            return b"".join(chunks).decode(errors="replace").strip()
    except Exception:
        return None


class _ExternalGestureHandle:
    """stage2_verify.py 가 미리 띄운 gesture daemon 소켓을 재사용하는 핸들.

    proc 을 소유하지 않으므로 stop() 에서 데몬을 종료하지 않는다.
    coordinator 가 이어서 같은 소켓을 쓴다.
    """

    def __init__(self, sock_path: str) -> None:
        self._sock = sock_path

    def wait_ready(self, timeout: float = 30.0) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if _sock_ping(self._sock):
                return True
            time.sleep(1)
        return False

    def play(self, gesture_name: str) -> tuple[bool, str]:
        resp = _sock_send(self._sock, f"play {gesture_name}")
        if resp is None:
            return False, "gesture 소켓 응답 없음"
        return (True, resp) if resp.startswith("accepted") else (False, resp)

    def stop(self) -> None:
        pass  # 외부 관리 — 종료하지 않음


def _get_gesture():
    """소켓이 이미 살아있으면 재사용, 아니면 신규 기동."""
    if _sock_ping(_GESTURE_SOCK):
        print(f"[Gesture] 기존 daemon 소켓 감지 ({_GESTURE_SOCK}) → 재사용")
        return _ExternalGestureHandle(_GESTURE_SOCK)
    print("[Gesture] 소켓 없음 → daemon 신규 기동...")
    from jetson.core.client.gesture_client import start_gesture_daemon
    return start_gesture_daemon()


# ── 헬퍼 ──────────────────────────────────────────────────────────────────────

def _speak(tts, text: str) -> None:
    print(f"[TTS] {text}")
    audio_file = tts.synthesize_reply_audio(text)
    if audio_file:
        tts.play_audio_blocking(audio_file)


def _record(label: str) -> str:
    from jetson.expression.microphone import record_to_wav
    wav_path = str(_TEST_AUDIO_DIR / f"test_{label}_{int(time.time())}.wav")
    print(f"[Mic] {RECORD_SEC:.0f}초 녹음 중...")
    record_to_wav(wav_path, duration_sec=RECORD_SEC, preferred_keyword="P5HD", samplerate=44100)
    return wav_path


def _transcribe(stt, wav_path: str) -> str:
    from jetson.expression.microphone import wav_has_speech
    has_speech, peak_rms = wav_has_speech(wav_path)
    print(f"[Mic] peak_rms={peak_rms}, has_speech={has_speech}")
    if not has_speech:
        return ""
    result = stt.transcribe(wav_path)
    text = result.text.strip() if result else ""
    print(f"[STT] \"{text}\"")
    return text


def _is_confirm(text: str) -> bool:
    normalized = text.lower().strip().rstrip(".!?")
    return any(kw in normalized for kw in CONFIRM_KEYWORDS)


def _wait_confirm(stt, tts, label: str) -> bool:
    for attempt in range(3):
        wav = _record(f"confirm_{label}")
        transcript = _transcribe(stt, wav)
        if _is_confirm(transcript):
            _speak(tts, "확인됐습니다. 다음으로 넘어갑니다.")
            return True
        hint = "완료됐으면 완료했어 라고 말씀해 주세요." if attempt < 2 else "확인이 안 됐지만 다음으로 넘어갑니다."
        _speak(tts, hint)
    return False


# ── 하드웨어별 테스트 함수 ────────────────────────────────────────────────────

def test_microphone(stt, tts) -> bool:
    print("\n" + "=" * 60)
    print("[마이크] 테스트 시작")
    _speak(tts, "마이크 테스트입니다. 아무 말이나 해보세요. 소리가 잘 녹음되면 완료했어 라고 말씀해 주세요.")
    from jetson.expression.microphone import wav_has_speech
    wav = _record("mic")
    has_speech, peak_rms = wav_has_speech(wav)
    print(f"[마이크] peak_rms={peak_rms}, has_speech={has_speech}")
    msg = f"마이크 감지됐습니다. 피크 {peak_rms}." if has_speech else "소리가 감지되지 않았습니다."
    _speak(tts, f"{msg} 완료됐으면 완료했어 라고 말씀해 주세요.")
    return _wait_confirm(stt, tts, "mic")


def test_speaker(tts, stt) -> bool:
    print("\n" + "=" * 60)
    print("[스피커] 테스트 시작")
    _speak(tts, "스피커 테스트입니다. 이 음성이 잘 들리면 완료했어 라고 말씀해 주세요.")
    return _wait_confirm(stt, tts, "speaker")


def test_arm(gesture, stt, tts) -> bool:
    print("\n" + "=" * 60)
    print("[팔] 테스트 시작")
    if not gesture.wait_ready(timeout=10.0):
        _speak(tts, "팔 데몬이 준비되지 않았습니다. 팔 테스트를 건너뜁니다.")
        print("[팔] gesture daemon 미준비 — 건너뜀")
        return False
    _speak(tts, "팔 동작 테스트입니다.")
    ok, msg = gesture.play("wave_hello")
    print(f"[팔] play wave_hello → ok={ok}, msg={msg}")
    time.sleep(4)
    status = "팔이 wave hello 동작을 했습니다" if ok else f"팔 동작 실패: {msg}"
    _speak(tts, f"{status}. 확인됐으면 완료했어 라고 말씀해 주세요.")
    return _wait_confirm(stt, tts, "arm")


def test_servo(servo, stt, tts) -> bool:
    print("\n" + "=" * 60)
    print("[서보] 테스트 시작")
    if not servo.is_available:
        _speak(tts, "서보 GPIO를 사용할 수 없습니다. 서보 테스트를 건너뜁니다.")
        print("[서보] GPIO 없음 — 건너뜀")
        return False
    _speak(tts, "입 서보 테스트입니다. 서보가 두 번 움직입니다.")
    servo.initialize()
    for _ in range(2):
        servo.move_to_angle(70)
        time.sleep(0.4)
        servo.move_to_angle(120)
        time.sleep(0.4)
    print("[서보] open/close 2회 완료")
    _speak(tts, "서보 동작이 끝났습니다. 확인됐으면 완료했어 라고 말씀해 주세요.")
    return _wait_confirm(stt, tts, "servo")


# ── 메인 ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("\n" + "=" * 60)
    print("  Hylion 하드웨어 검증 시작")
    print("=" * 60 + "\n")

    print("[Init] STT (Groq) 초기화...")
    from jetson.core.stt import build_stt_backend
    stt = build_stt_backend(online=True, language="ko")

    print("[Init] TTS (Clova) 초기화...")
    from jetson.expression.speaker import build_tts_backend, DEFAULT_CLOVA_SPEAKER
    tts = build_tts_backend(DEFAULT_CLOVA_SPEAKER)

    print("[Init] 입 서보 초기화...")
    from jetson.expression.mouth_servo import MouthServoController, cleanup_gpio
    servo = MouthServoController()

    print("[Init] gesture daemon 확인...")
    gesture = _get_gesture()

    _speak(tts, "하드웨어 검증을 시작합니다. 각 항목 테스트 후 완료했어 라고 말씀해 주세요.")

    results: dict[str, bool] = {}
    results["마이크"] = test_microphone(stt, tts)
    results["스피커"] = test_speaker(tts, stt)
    results["팔"]    = test_arm(gesture, stt, tts)
    results["서보"]  = test_servo(servo, stt, tts)

    print("\n" + "=" * 60)
    print("  하드웨어 검증 결과")
    print("=" * 60)
    for name, ok in results.items():
        print(f"  [{'✓' if ok else '✗'}] {name}")

    passed  = sum(results.values())
    total   = len(results)
    summary = f"하드웨어 검증 완료. {passed}/{total}개 통과."
    print(f"\n{summary}")
    _speak(tts, summary + " Stage 2 대화 검증으로 넘어갑니다.")

    # gesture daemon 은 외부(_ExternalGestureHandle)면 stop() 이 no-op
    gesture.stop()
    cleanup_gpio()
    print("\n[완료] test_coordinator 종료")


if __name__ == "__main__":
    main()
