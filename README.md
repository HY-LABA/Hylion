# Hylion

Non-ROS2 (UDP/TCP 기반) 파이프라인. 표준 진입점은 Jetson 의
[scripts/run_coordinator.sh](scripts/run_coordinator.sh) 한 줄.

전체 구조와 흐름은 [docs/09_project_flow_overview.md](docs/09_project_flow_overview.md)
참고.

---

## 빠른 사용법

### 1) 평소 실행 (수동)

수동으로 한 번 띄울 때:

```bash
bash scripts/run_coordinator.sh
```

이 스크립트가 venv 활성화 + `LD_LIBRARY_PATH` + 마이크/e-stop env 까지 다 처리.
옵션은 그대로 전달됨. 예: `bash scripts/run_coordinator.sh --whisper-model-size base`.

가동 중 RAM/GPU/프로세스 상태는 다른 터미널에서:

```bash
bash scripts/live_monitor.sh
```

(Ollama / MeloTTS / NUC BHL bridge 데몬은 각자의 systemd 로 띄워둔 상태여야 함.)

### 2) 자동 실행 (systemd user service, 권장)

부팅 시 자동으로 띄우려면 한 번만 설치:

```bash
bash scripts/install-coordinator-service.sh
sudo loginctl enable-linger $USER       # 로그인 없이도 부팅 시 시작
```

설치 후 조작:

```bash
systemctl --user status hylion-coordinator         # 상태
systemctl --user restart hylion-coordinator        # 재시작
systemctl --user stop hylion-coordinator           # 정지 (다음 부팅 때 다시 뜸)
journalctl --user -u hylion-coordinator -f         # 실시간 로그
```

제거:

```bash
bash scripts/install-coordinator-service.sh --uninstall
```

> **주의**: 서비스가 도는 상태에서 `bash scripts/run_coordinator.sh` 를 또 띄우면
> 마이크/포트 충돌. 수동 실행할 때는 먼저 `systemctl --user stop hylion-coordinator`.

### 3) GUI 모드 토글 (현장 배치 ↔ 개발)

GUI 와 자동 실행은 서로 독립. 현장에 올릴 때만 GUI 끄고, 디버깅할 때만 다시 켜면 됨.

```bash
bash scripts/headless-on.sh  && sudo reboot       # GUI 끄기 (multi-user.target)
bash scripts/headless-off.sh && sudo reboot       # GUI 다시 켜기 (graphical.target)
```

재부팅 없이 즉시 바꾸려면 (현재 X 세션 끊김 주의):

```bash
sudo systemctl isolate multi-user.target           # 즉시 GUI 끔
sudo systemctl isolate graphical.target            # 즉시 GUI 켬
```

---

## 현장 배치 체크리스트

로봇에 Jetson 올리고 모니터/키보드 떼는 시나리오:

```bash
# 1. systemd 서비스 설치 (한 번만)
bash scripts/install-coordinator-service.sh
sudo loginctl enable-linger $USER

# 2. 수동 실행으로 동작 확인
systemctl --user stop hylion-coordinator
bash scripts/run_coordinator.sh           # Hey Hyleon → 응답 확인
# Ctrl+C 종료
systemctl --user start hylion-coordinator

# 3. GUI 끄기
bash scripts/headless-on.sh

# 4. 재부팅 — 이때부터 모니터/키보드 없이 전원만 켜면 자동 진입
sudo reboot
```

GUI 다시 보고 싶으면 SSH 로 들어와서:

```bash
bash scripts/headless-off.sh && sudo reboot
```

---

## 기본 실행 흐름 (요약)

1. USB 마이크에서 wake word ("Hey Hyleon") 감지
2. Whisper STT 로 텍스트 변환
3. LLM (online: Groq · offline: Ollama) 이 action JSON 생성
4. intent 분기:
   - `chat` → TTS + 입 서보 lipsync + 우측 SO-ARM gesture (옵션)
   - `pick_place / move / stop` → NUC BHL bridge 로 송신, 동작 중 "stop" 발화
     모니터링, 완료/비상정지 DONE 대기
   - `standby` → 다시 wake word 대기 모드

자세한 다이어그램·파일 구조·E-stop 흐름은
[docs/09_project_flow_overview.md](docs/09_project_flow_overview.md).

---

## 원칙

- 신규 구현은 ROS2 의존을 추가하지 않는다.
- ROS2 관련 파일은 삭제 대신 [legacy/ros2/](legacy/ros2/) 에 이관.
- 모든 메시지는 [configs/schemas/](configs/schemas/) 의 JSON Schema 로 검증.
- 푸시 전 [WORKLOG.md](WORKLOG.md) 에 변경 사항 기록 (같은 커밋에 포함).
