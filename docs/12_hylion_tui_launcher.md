# Hylion 통합 런처 (`scripts/hylion-tui.py`) — 사용 가이드

기준: 2026-05-23

노트북에서 SSH 로 Jetson + NUC 를 같이 띄우는 3단계 TUI 런처.
부팅 자동 실행 대신 사람이 한 줄로 시작/중단하는 시나리오용.

```
┌─ Hylion Launcher ────────────────────────── Jetson=jetson  NUC=nuc ─┐
│ ✓  Stage 1 · 초기 셋팅                                              │
│        ✓  Jetson preflight 점검                — 모든 항목 PASS     │
│        ✓  NUC: CAN 인터페이스 up               — CAN up (sudo)      │
│        ✓  NUC: 관절 캘리브레이션 (사람 필요)    — 갱신: 2026-..      │
│                                                                      │
│ ▶  Stage 2 · Cold Start                                             │
│        ✓  Jetson: Ollama / MeloTTS 데몬 점검   — Ollama ✓ · Melo ✓  │
│        ✓  NUC: hylion-bhl-bridge               — :9000 listen 확인  │
│        ▶  NUC: bhl-lowlevel (C++ make run)                          │
│        ·  NUC: bhl-policy (ONNX rl_controller)                      │
│                                                                      │
│ ·  Stage 3 · 전체 프로그램 실행                                     │
│        ·  Jetson: run_coordinator.sh                                │
├─ Live log ─────────────────── 진행: Stage step — bhl-lowlevel ─────┤
│   $ ssh nuc: tmux new -d -s hylion-bhl-lowlevel "cd ~/Berke..."     │
│     C++ control_loop 기동 대기 (5초)…                                │
│     $ ssh nuc: tmux has-session -t hylion-bhl-lowlevel              │
│       ALIVE                                                          │
│   ✓ NUC: bhl-lowlevel                                                │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 0. 한 줄 요약

- **노트북 한 곳에서** `python3 scripts/hylion-tui.py` 한 줄로 1→2→3 단계 진행.
- 각 단계 사이에 진행 확인 프롬프트 1번. 중단은 항상 `Ctrl+C`.
- 캘리브와 coordinator 본체는 자동화 못 하니 SSH 가 잠시 terminal 을 인계 →
  끝나면 TUI 복귀.

---

## 1. 3 단계 구조

| 단계 | 무엇? | 사람 손 필요? | 시간 |
|---|---|---|---|
| **Stage 1 · 초기 셋팅** | preflight · CAN up · 관절 캘리브 | **캘리브 시에만** (로봇 옆) | ~3분 |
| **Stage 2 · Cold Start** | Jetson 데몬 점검 + NUC bridge / bhl-lowlevel / bhl-policy 기동 | 없음 (노트북에서) | ~15초 |
| **Stage 3 · 전체 프로그램 실행** | Jetson coordinator (`run_coordinator.sh`) foreground | 음성 인터랙션 | 시연 끝까지 |

각 단계의 step 정의는 [scripts/hylion-tui.py](../scripts/hylion-tui.py) 의
`build_stages()` 참고.

---

## 2. 사전 준비 (1회)

### 2.1 노트북

```bash
pip install rich            # 유일한 의존성
```

`~/.ssh/config` 에 두 호스트 등록 — **NUC 는 Jetson 경유**가 깔끔:

```ssh-config
Host jetson
  HostName <jetson-wifi-ip>
  User laba

Host nuc
  HostName 10.42.0.221
  User <nuc-user>
  ProxyJump jetson
```

키 인증이 안 돼 있으면 `ssh-copy-id jetson` / `ssh-copy-id nuc` 한 번씩.
런처는 `BatchMode=yes` 로 SSH 를 호출하므로 **비밀번호 프롬프트는 비대화 단계에서
허용되지 않습니다** — 키 인증 필수.

### 2.2 Jetson

- 이미 있는 그대로. `~/Hylion` 체크아웃 + `jetson/expression/.venv` 구축
  (WORKLOG 2026-05-04 항목 참고).
- Ollama 와 MeloTTS 데몬은 각자의 systemd 로 평소 떠 있는 상태.

### 2.3 NUC

```bash
sudo apt install tmux                 # 장기 실행 세션 detach 용
# ~/Hylion 클론 (bridge.py 가 여기 있음)
git clone <repo> ~/Hylion
# ~/Berkeley-Humanoid-Lite-Lowlevel 빌드 (make)
# CAN 권한: 사용자를 dialout 그룹에 + sudoers NOPASSWD (선택)
```

`start_can_transports.sh` 를 매번 비밀번호 없이 돌리려면 `/etc/sudoers.d/hylion-can`:

```
<nuc-user> ALL=(root) NOPASSWD: /home/<nuc-user>/Berkeley-Humanoid-Lite-Lowlevel/scripts/start_can_transports.sh
```

없으면 그 step 만 인터랙티브로 비밀번호 받습니다 (그 동안 TUI 가 잠시 멈춤).

### 2.4 환경변수 (선택)

기본 경로가 다르면 셸에서 export:

| 변수 | 기본값 | 의미 |
|---|---|---|
| `HYLION_JETSON_HOST` | `jetson` | SSH host alias |
| `HYLION_NUC_HOST` | `nuc` | SSH host alias |
| `HYLION_JETSON_PROJECT` | `~/Hylion` | Jetson 측 Hylion 경로 |
| `HYLION_NUC_PROJECT` | `~/Hylion` | NUC 측 Hylion 경로 (bridge.py 위치) |
| `HYLION_NUC_BHL_REPO` | `~/Berkeley-Humanoid-Lite-Lowlevel` | NUC 측 BHL 리포 |
| `HYLION_NUC_PYTHON` | `python3` | NUC 에서 rl_controller / calibrate 돌릴 Python |

---

## 3. 사용

### 3.1 평소 시연 (전체 흐름)

```bash
# 노트북
python3 scripts/hylion-tui.py
```

- Stage 1 → 캘리브 차례에서 사람이 로봇 옆으로 가서 손으로 관절 12개를
  돌립니다. 끝나면 TUI 가 자동으로 `calibration.yaml` 갱신을 검증.
- "Stage 1 완료. 다음 단계 진행?" 에 Enter.
- Stage 2 가 NUC tmux 세션 3개를 띄움.
- "Stage 2 완료. 다음 단계 진행?" 에 Enter.
- Stage 3 가 Jetson coordinator 를 **노트북 터미널 foreground 로 인계**.
- "Hey Hyleon" 으로 시연. `Ctrl+C` 로 종료하면 TUI 가 다시 돌아옴.

### 3.2 부분 실행 / 재시작

```bash
# 같은 부팅 중에 캘리브는 이미 했음 → Stage 2 부터
python3 scripts/hylion-tui.py --stage 2

# 그냥 coordinator 만 다시 띄우고 싶다 (NUC 세션 다 살아있음)
python3 scripts/hylion-tui.py --stage 3

# 흐름만 보기 (실제 SSH 호출 X)
python3 scripts/hylion-tui.py --dry-run

# 단계 사이 확인 프롬프트 생략 (자동화)
python3 scripts/hylion-tui.py --no-confirm
```

> Stage 1 의 캘리브 step 은 같은 부팅 안에서 `calibration.yaml` 이 이미 신선
> 하면 알아서 SKIP 을 제안합니다. (`/proc/1` mtime 과 비교)

### 3.3 상태 확인 / 정리

```bash
# 지금 NUC tmux 세션·포트·Jetson coordinator 가 어떤 상태인가
python3 scripts/hylion-tui.py --status

# NUC 의 hylion-* tmux 세션을 전부 죽이고 처음부터 다시 시작하고 싶다
python3 scripts/hylion-tui.py --reset
```

### 3.4 살아 있는 tmux 세션 직접 들여다보기 (디버그)

```bash
# 라이브 출력 보고 싶으면
ssh -t nuc tmux attach -t hylion-bhl-policy
#   detach: Ctrl+B, d
#   세션 그대로 살려둠 (kill 아님)
```

세션 이름:

| 세션 | 무엇 |
|---|---|
| `hylion-bridge` | `python -m nuc.bhl.bridge` (TCP :9000, UDP :10011) |
| `hylion-bhl-lowlevel` | `make run` (C++ 5스레드, 250Hz control) |
| `hylion-bhl-policy` | `rl_controller.py` (ONNX 25Hz 추론) |

각 세션의 stdout 은 NUC 의 `/tmp/<session>.log` 에도 tee 됩니다.

---

## 4. 단계별 실제 SSH 호출 (참고)

### Stage 1

```
ssh jetson  cd ~/Hylion && bash scripts/preflight.sh
ssh nuc     sudo -n bash ~/Berkeley-Humanoid-Lite-Lowlevel/scripts/start_can_transports.sh
ssh -t nuc  cd ~/Berkeley-Humanoid-Lite-Lowlevel && python3 scripts/calibrate_joints.py
ssh nuc     test -f .../calibration.yaml && stat -c '%y' ...
```

### Stage 2

```
ssh jetson  Ollama/MeloTTS TCP 도달 확인
ssh nuc     systemctl is-active hylion-bhl-bridge.service
            ↳ inactive 면 tmux new -d -s hylion-bridge "python -m nuc.bhl.bridge"
ssh nuc     tmux new -d -s hylion-bhl-lowlevel "make run"
ssh nuc     tmux new -d -s hylion-bhl-policy   "python -m ...rl_controller"
```

각 세션 띄운 직후 헬스 체크 (`tmux has-session` + port listen) 로 즉시 실패 감지.

### Stage 3

```
ssh -t jetson  cd ~/Hylion && bash scripts/run_coordinator.sh
              ↳ foreground 인계. Ctrl+C 로 종료하면 TUI 로 복귀.
```

---

## 5. 문제 해결

| 증상 | 원인 / 조치 |
|---|---|
| `pip install rich` 안 되는 환경 | `pipx install rich` 또는 venv 안에서 설치 |
| `BatchMode=yes` 라 비밀번호 못 받음 | SSH 키 인증 등록 (`ssh-copy-id`) |
| Stage 1 `preflight FAIL` | 메시지 끝의 `[FAIL]` 항목부터 해결. NUC bridge `[WARN]` 은 Stage 2 에서 띄울 거니 OK |
| Stage 2 `tmux 미설치` | `ssh nuc sudo apt install tmux` |
| `bhl-lowlevel` 이 5초 안에 죽음 | `ssh nuc cat /tmp/hylion-bhl-lowlevel.log` 로 원인 확인. CAN up 안 됐거나 권한 문제일 가능성 |
| `bhl-policy` 가 죽음 | ONNX/yaml 파일 경로 확인. `/tmp/hylion-bhl-policy.log` |
| Stage 3 들어가도 다리가 안 움직임 | `--status` 로 세션 셋 다 ALIVE 인지, `:9000`/`:10011` 둘 다 떠 있는지 확인 |
| coordinator 가 NUC 못 찾음 | Jetson 셸에서 `HYLION_BHL_HOST` 확인 — [scripts/run_coordinator.sh](../scripts/run_coordinator.sh) 참고 |

---

## 6. 설계 메모

- **왜 tmux 인가**: 장기 실행 프로세스를 SSH 종료 후에도 살리고, 죽으면 세션이
  사라지므로 헬스체크가 1줄. `ssh -t ... attach` 로 라이브 진단 가능.
- **왜 systemd 가 아닌가**: 사용자가 "자동 실행 말고 노트북으로 직접" 을 명시.
  bridge 만 기존 systemd 가 있으면 그걸 우선 사용 (`systemctl is-active`).
- **왜 coordinator 만 foreground 인가**: 사용자가 직접 말을 걸고 Ctrl+C 로
  끄는 게 자연 흐름이라 tmux 에 가두지 않음. TUI 가 잠시 비켜주고 끝나면 복귀.
- **왜 캘리브 SKIP 휴리스틱이 있나**: 같은 부팅 안에서 두 번 캘리브할 이유가
  없음 (`calibration.yaml` mtime > `/proc/1` mtime 이면 SKIP 제안).
  사용자가 그래도 다시 하고 싶으면 프롬프트에서 Yes.
- **왜 인터랙티브와 비대화를 분리했나**: 비대화는 라이브 로그 스트림(예쁘게),
  인터랙티브는 ssh -t 인계 (rich Live 일시 정지) — 한 화면 안에서 비밀번호
  프롬프트가 깨지지 않게 함.
