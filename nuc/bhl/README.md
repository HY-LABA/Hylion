# Hylion BHL Bridge

Jetson coordinator(JSON) ↔ BHL lowlevel(UDP 13-byte) 변환 브리지.

설계/사양: [BHL_Bridge_Handoff.md](BHL_Bridge_Handoff.md)

## 구성

```
bridge.py                          # 브리지 본체. NUC 에서 실행.
tests/mock_coordinator.py          # Jetson 없이 코디네이터 시뮬레이션
tests/mock_bhl_receiver.py         # C 컨트롤러 없이 UDP 수신 확인
systemd/hylion-bridge.service      # 부팅 시 자동 실행용
systemd/hylion-bridge.env.example  # 튜닝 파라미터 (EnvironmentFile)
```

## 빠른 검증 (NUC 단독)

세 터미널.

```bash
# T1: 가짜 BHL UDP 수신기 (실제 C 컨트롤러가 없을 때만)
python3 tests/mock_bhl_receiver.py

# T2: 브리지
python3 bridge.py

# T3: 코디네이터 흉내 — 시나리오들
python3 tests/mock_coordinator.py walk        # 2s 보행 후 정지
python3 tests/mock_coordinator.py turn        # 2s 좌회전
python3 tests/mock_coordinator.py emergency   # EMERGENCY -> STOP 검증
python3 tests/mock_coordinator.py safety_off  # safety_allowed=false -> STOP
python3 tests/mock_coordinator.py bad_json    # 깨진 JSON 에도 안 죽는지
python3 tests/mock_coordinator.py watchdog    # 1건만 보내고 침묵 -> 200ms 후 STOP
python3 tests/mock_coordinator.py loop        # 10Hz 무한 송신, Ctrl+C 로 끊김 검증
```

T1 출력에서 `CHANGE mode=...` 줄로 상태 전환을 추적할 수 있다.

## 실제 BHL 과의 통합 (NUC)

진짜 C 컨트롤러를 띄울 때는 `mock_bhl_receiver.py`를 같이 돌리면 안 됨(UDP 10011 충돌).

```bash
# T1: C 컨트롤러
cd Berkeley-Humanoid-Lite-Lowlevel-main
make run

# T2: 정책 추론
python3 -m berkeley_humanoid_lite_lowlevel.policy.rl_controller

# T3: 브리지
python3 bridge.py

# 그리고 Jetson 의 coordinator 가 NUC:9000 으로 TCP/NDJSON 송신
```

## 자동 실행 (부팅 시)

```bash
# 1) 코드를 /opt 에 배치 (또는 service 파일의 WorkingDirectory 를 수정)
sudo mkdir -p /opt/hylion
sudo cp -r ~/Hylion /opt/hylion/

# 2) 환경 파일 (튜닝 변수)
sudo cp /opt/hylion/nuc/bhl/systemd/hylion-bridge.env.example /etc/default/hylion-bridge
sudoedit /etc/default/hylion-bridge   # 필요한 값 수정

# 3) 유닛 설치
sudo cp /opt/hylion/nuc/bhl/systemd/hylion-bridge.service /etc/systemd/system/
sudo systemctl daemon-reload

# 4) 활성화 + 시작
sudo systemctl enable hylion-bridge
sudo systemctl start hylion-bridge

# 로그 보기
journalctl -u hylion-bridge -f
```

## 매핑 파라미터 (TUNE: 표시된 곳)

`bridge.py` 상단의 `VEL_FORWARD_MPS`, `VEL_TURN_LEFT_RPS` 등. BHL gamepad.py 의 정규화
(`raw/32768 ∈ [-1, 1]`)에 맞춰 보수적으로 0.5로 시작. 실 보행 시 정책의 학습 범위와
맞춰 조정. systemd 사용 시 `/etc/default/hylion-bridge` 의 env 로 변경.

## 절대 건드리지 말 것

- UDP 패킷 크기 13바이트, `<Bfff` 포맷 (BHL C 컨트롤러 호환 인터페이스)
- 포트 `10011` (`csrc/consts.h` 의 `JOYSTICK_PORT`)
- BHL C 코드 (`csrc/`) — 브리지가 100% 적응
