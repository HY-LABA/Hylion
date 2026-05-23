# Hylion

Non-ROS2 (UDP/TCP 기반) 파이프라인. 표준 진입점은 Jetson 의
[scripts/run_coordinator.sh](scripts/run_coordinator.sh) 한 줄.

전체 구조와 흐름은 [docs/09_project_flow_overview.md](docs/09_project_flow_overview.md)
참고.

---

## 가장 빠른 시작 — 노트북에서 한 줄 TUI 런처

NUC 측 캘리브·`make run`·`rl_controller`·bridge 까지 **노트북에서** SSH 로 다
띄우고 싶으면 [scripts/hylion-tui.py](scripts/hylion-tui.py) 를 쓴다. 3 단계
(초기 셋팅 → Cold Start → 전체 프로그램 실행) 진행이 한 화면에 표시되고, 각
step 의 라이브 로그가 같이 보인다.

```bash
# 노트북 (1회): pip install rich
# ~/.ssh/config 에 'jetson' / 'nuc' (ProxyJump=jetson) 등록

python3 scripts/hylion-tui.py              # 1→2→3 순차
python3 scripts/hylion-tui.py --stage 2    # 같은 부팅에서 캘리브 끝났으면
python3 scripts/hylion-tui.py --status     # 지금 떠 있는 NUC 세션 확인
python3 scripts/hylion-tui.py --reset      # NUC tmux 세션 전부 정리
```

자세한 SSH 셋업 · 환경변수 override · 트러블슈팅:
[docs/12_hylion_tui_launcher.md](docs/12_hylion_tui_launcher.md).

아래는 TUI 를 쓰지 않고 직접 하나씩 띄울 때의 절차다.

---

## 운영 흐름 — "환경 설정"과 "작동"을 분리

Hylion 은 **두 단계로 나눠서** 운영한다. 부팅하자마자 코디네이터가 자동으로 뜨지
않는다 — 사람이 점검을 마치고 명시적으로 작동을 시작한다.

1. **1단계 · 환경 설정 / 점검** — 노트북에서 SSH 로 Jetson 에 들어와,
   하드웨어 · venv · 모델 · 네트워크 · NUC 연결이 정상인지 확인. 코디네이터(메인
   루프)는 아직 띄우지 않는다.
2. **2단계 · 작동 시작** — 점검이 모두 통과하면 코디네이터를 띄운다.

> 무인 배치(모니터·키보드·노트북 없이 전원만으로 기동)가 필요한 경우에만
> 아래 "[(옵션) 부팅 시 자동 실행](#옵션-부팅-시-자동-실행--무인-배치용)" 을 쓴다.

### 1단계: 환경 설정 / 점검 (시연 전)

노트북에서 Jetson 으로 SSH 접속:

```bash
ssh <jetson-user>@<jetson-ip>
cd ~/Hylion
```

환경 점검 — **코디네이터를 띄우지 않고** venv/모델/마이크/스피커/NUC 연결/데몬을
한 번에 확인:

```bash
bash scripts/preflight.sh
```

- `[FAIL]` 이 하나라도 있으면 고치기 전에는 2단계로 넘어가지 말 것 (종료코드 1).
- `[WARN]` 은 그 기능만 제한됨 (예: NUC 연결 없으면 다리 동작만 불가, 대화·팔은
  정상) — 시연 범위에 필요한 항목인지 판단해서 진행.

간단 기능 테스트 — 마이크 + wake word 가 실제로 잡히는지 격리 확인:

```bash
bash scripts/test_wakeword.sh checkpoints/wakeword/Hey_Hyleon.tflite
```

### 2단계: 작동 시작

점검이 끝나고 이상 없으면 코디네이터를 띄운다:

```bash
bash scripts/run_coordinator.sh
```

이 스크립트가 venv 활성화 + `LD_LIBRARY_PATH` + 마이크/e-stop env 까지 다 처리.
"Hey Hyleon" 으로 응답을 확인하고, 종료는 `Ctrl+C`.
옵션은 그대로 전달됨. 예: `bash scripts/run_coordinator.sh --whisper-model-size base`.

가동 중 RAM/GPU/프로세스 상태는 다른 터미널(또는 별도 SSH 세션)에서:

```bash
bash scripts/live_monitor.sh
```

> Ollama / MeloTTS / NUC BHL bridge 데몬은 각자의 systemd 로 미리 떠 있어야 함.
> `preflight.sh` 의 §4·§5 가 이를 점검해준다.

---

## (옵션) 부팅 시 자동 실행 — 무인 배치용

평소 시연은 위 2단계 수동 흐름을 쓴다. **모니터·키보드·노트북 없이 전원만으로**
기동해야 하는 무인 배치 상황에서만 systemd user service 를 설치한다.

```bash
bash scripts/install-coordinator-service.sh
sudo loginctl enable-linger $USER       # 로그인 없이도 부팅 시 시작
```

설치하면 부팅 시 코디네이터가 자동으로 뜬다. 단 이 경우 `preflight.sh` 점검을
사람이 거치지 못하므로, 하드웨어/연결이 확실할 때만 쓸 것.

자동 실행 해제 (다시 수동 운영으로 — 권장 기본 상태):

```bash
bash scripts/install-coordinator-service.sh --uninstall
```

설치 후 조작:

```bash
systemctl --user status hylion-coordinator         # 상태
systemctl --user restart hylion-coordinator        # 재시작
systemctl --user stop hylion-coordinator           # 정지
journalctl --user -u hylion-coordinator -f         # 실시간 로그
```

> **주의**: 서비스가 도는 상태에서 `bash scripts/run_coordinator.sh` 를 또 띄우면
> 마이크/포트 충돌. `preflight.sh` §9 가 이 충돌을 잡아준다. 수동 실행 전 먼저
> `systemctl --user stop hylion-coordinator`.

## (옵션) GUI 모드 토글

GUI 를 끄면 GPU/RAM 이 절약된다. SSH 로 운영하므로 **필수는 아니지만**, 시연
안정성을 위해 끄고 싶으면:

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
