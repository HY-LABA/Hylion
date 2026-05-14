# Jetson(Orin) 측 Gesture Replay 구현 가이드 + AI 프롬프트

> **본 문서의 두 가지 용도**:
> 1. **사람 독자**: Jetson 에서 gesture replay 시스템을 직접 만들 때 고려·주의 사항 + 구현 지침
> 2. **AI 에이전트**: §10 의 프롬프트 블록을 Jetson 측 Claude Code 세션에 복붙 → 본 문서 + [dgx/docs/gestures.md](gestures.md) 를 읽고 자동 구현
>
> **작성**: 2026-05-13
> **선행 조건 (DGX 측 완료 사항)**: [gestures.md](gestures.md) 의 record → sync 흐름이 1회 이상 성공해야 함. 즉 Jetson 의 `${ORIN_GESTURES_ROOT}/<name>/meta/info.json` 과 `${HF_HOME}/lerobot/calibration/robots/so_follower/<id>.json` 이 존재.

---

## 1) 목표 / Goal

DGX 에서 녹화·전송된 trajectory 데이터를 받아, **Jetson 에서 트리거 신호 1회 = gesture 동작 1회 실행** 의 단순 인터페이스를 제공하는 wrapper 시스템 구축.

```
trigger system  →  play_gesture.sh wave_hello  →  lerobot-replay  →  SO-ARM 우측 follower
```

- VLA / ACT 추론 없음 (DGX→Jetson sync 된 LeRobotDataset 의 `action` 컬럼을 그대로 송출)
- **우측 팔 전용** — 좌측은 SmolVLA inference 가 별도 점유 ([gestures.md §0-1](gestures.md#0-1-본-시스템-적용-현황--양팔-배치-2026-05-13-기준))
- 트리거 시스템과의 인터페이스는 **bash exit code + stdout** 만 (REST·WebSocket·ROS 등은 호출 측 책임)

### 본 시스템이 다루는 팔 (중요)

| 팔 | 본 wrapper 가 다루는가 | 비고 |
|---|---|---|
| **좌측** (follower id=`leftarm_test_follower`) | ❌ X | SmolVLA inference 가 점유. 본 wrapper 와 무관 |
| **우측** (follower id=`rightarm_test_follower`) | ✅ O | 본 wrapper 가 lerobot-replay 로 직접 제어 |

→ 우측·좌측 follower 는 서로 다른 USB 포트라 동시 실행 시 USB mutex 충돌 없음. 다만 본 wrapper 는 **우측만 잡으면 끝**, 좌측 SmolVLA inference 와는 상호작용 X.

---

## 2) 아키텍처 (요약)

자세한 그림은 [gestures.md §1](gestures.md) 참조. Jetson 측 책임 범위만 그리면:

```
              [DGX 에서 rsync 완료된 상태]
              ┌─────────────────────────────────────────────┐
              │ ${ORIN_GESTURES_ROOT}/wave_hello/           │  ← gesture dataset (motors only)
              │ ${HF_HOME}/lerobot/calibration/...          │  ← follower 캘리브레이션 JSON
              └─────────────────────────────────────────────┘
                                  │
                                  │  (Jetson 측 신규 구현 — 본 가이드)
                                  ▼
              ┌─────────────────────────────────────────────┐
              │ orin/scripts/play_gesture.sh <name>         │  ← wrapper. 본 문서가 만들 핵심
              │   └─ lerobot-replay --robot.* --dataset.*   │
              └─────────────────────────────────────────────┘
                                  │
                                  ▼
              ┌─────────────────────────────────────────────┐
              │ SO-ARM follower (/dev/ttyACM*)              │
              └─────────────────────────────────────────────┘
                                  ▲
                                  │
              [트리거 시스템: 음성, ROS, MQTT, GPIO, …]
              호출 인터페이스: bash exit code + stdout
```

---

## 3) Jetson 환경 가정 (구현 전 검증 필요)

Jetson 측에 다음이 이미 갖춰져 있어야 합니다. 없으면 에이전트가 사전 조치 후 진행.

| 항목 | 검증 명령 | 미존재 시 |
|---|---|---|
| `orin/` 디렉터리 (DGX 의 `dgx/` 와 형제) | `ls ~/smolvla/orin/` | 본 repo 가 Jetson 에 rsync / clone 되지 않음. 사용자 안내 후 중단 |
| Jetson 추론 venv (`orin/.hylion_arm` 또는 유사) | `ls ~/smolvla/orin/.hylion_arm/bin/activate` | venv 부재 → `orin/scripts/setup_inference_env.sh` 실행 안내 (Jetson 측 별도) |
| lerobot 설치 (`lerobot-replay` 명령) | `source <venv> && which lerobot-replay` | `pip install -e ~/smolvla/docs/reference/lerobot[smolvla]` |
| **HF_HOME** 환경변수 | `echo "${HF_HOME}"` | venv activate 시 자동 설정되도록 setup 스크립트 검토 |
| **Follower 캘리브레이션 JSON** | `ls ${HF_HOME}/lerobot/calibration/robots/so_follower/rightarm_test_follower.json` | DGX 측에서 `bash dgx/scripts/sync_gesture_to_orin.sh <name>` 실행 안내 |
| **Gesture dataset** | `ls ~/smolvla/orin/gestures/<name>/meta/info.json` | 동상 |
| Follower USB 연결 | `ls /dev/ttyACM*` + `lerobot-find-port` | 케이블 / 권한 점검 안내 |
| dialout 그룹 멤버십 | `id -nG | grep dialout` | `sudo usermod -aG dialout $USER` 후 재로그인 |

**중요**: lerobot 버전 / SHA 는 DGX 와 Jetson 이 일치해야 함. 가능한 한 `docs/reference/lerobot/` submodule 을 양쪽에 같은 commit 으로 rsync 또는 git pull.

---

## 4) 만들어야 할 것 (Jetson 측 신규 파일)

| 파일 | 책임 | 필수 |
|---|---|---|
| `orin/scripts/play_gesture.sh` | `lerobot-replay` wrapper. trigger 가 호출하는 진입점 | ✅ |
| `orin/scripts/check_gesture_ready.sh` | 사전 점검 (venv / 파일 / 포트). dry-run | 권장 |
| `orin/gestures/README.md` | 디렉터리 컨벤션 (DGX 쪽 mirror) | 권장 |
| `orin/docs/gestures.md` | Jetson 측 운영 가이드 (DGX 문서로 cross-link) | 권장 |
| `orin/.hylion_arm` env 에 `FOLLOWER_ID` 등 영구 export | run-time 안정성 | 권장 |

**만들지 말 것**:
- 자체 trajectory 포맷 / 자체 replay 엔진 — lerobot-replay 가 이미 함
- 카메라 / VLA 추론 통합 — 본 시스템 범위 외 ([gestures.md §7](gestures.md#7-향후-확장-고려))
- DGX 의 record_gesture.sh 를 Jetson 으로 이식 — Jetson 은 replay 전담, 녹화는 DGX 책임

---

## 5) 구현 상세 (play_gesture.sh)

### 5-1. 인터페이스

```
Usage: play_gesture.sh <gesture_name>

Args:
  gesture_name   필수. ${ORIN_GESTURES_ROOT}/<gesture_name>/meta/info.json 존재 필요.

Exit code:
  0   재생 성공
  2   인자 / 형식 오류
  3   venv / lerobot 환경 문제
  4   gesture 데이터 / 캘리브레이션 미존재
  5   하드웨어 (포트 / 권한) 문제
  1   기타 (lerobot-replay 내부 실패)

Stdout: 한 줄 요약 (gesture name, frame count, elapsed s)
Stderr: 에러 메시지
```

### 5-2. 핵심 호출 (lerobot-replay)

```bash
lerobot-replay \
  --robot.type=so101_follower \
  --robot.port="${FOLLOWER_PORT}" \
  --robot.id="${FOLLOWER_ID}" \
  --dataset.repo_id="local/${GESTURE_NAME}" \
  --dataset.root="${ORIN_GESTURES_ROOT}/${GESTURE_NAME}" \
  --dataset.episode=0
```

→ [lerobot_replay.py:100-132](../../docs/reference/lerobot/src/lerobot/scripts/lerobot_replay.py#L100-L132) 가 dataset 의 `action` 컬럼을 fps 맞춰 송출. 끝나면 `robot.disconnect()`.

### 5-3. 기본값 / env override

| 변수 | 기본값 | 의미 |
|---|---|---|
| `FOLLOWER_PORT` | `/dev/ttyACM0` | USB 변동 시 override. `lerobot-find-port` 로 재확인 |
| `FOLLOWER_ID` | `rightarm_test_follower` | 캘리브레이션 파일 이름 = robot.id |
| `ORIN_GESTURES_ROOT` | `${HOME}/smolvla/orin/gestures` | sync 받은 gesture 데이터 루트 |
| `JETSON_VENV` | `${HOME}/smolvla/orin/.hylion_arm` | 추론 venv. activate 후 lerobot-replay 사용 가능 |
| `HF_HOME` | `${HOME}/smolvla/.hf_cache` (venv activate 시 자동) | 캘리브레이션 경로의 root |

### 5-4. pre-check 흐름 (script 내부)

```
1. 인자 검증 (gesture_name 형식: ^[a-z][a-z0-9_]*$)
2. venv activate (이미 활성이면 skip)
3. lerobot-replay 명령 존재 확인 → exit 3 if not
4. ${ORIN_GESTURES_ROOT}/${GESTURE_NAME}/meta/info.json 확인 → exit 4 if not
5. ${HF_HOME}/lerobot/calibration/robots/so_follower/${FOLLOWER_ID}.json 확인 → exit 4 if not
6. [ -e "${FOLLOWER_PORT}" ] → exit 5 if not
7. lerobot-replay 호출 (위 5-2)
8. exit code 그대로 전달
```

### 5-5. (선택) home pose 사전 점검

가장 안전한 옵션은 trigger 측에서 "현재 자세 ↔ trajectory[0] 거리" 확인 후 호출하는 것. play_gesture.sh 안에 통합하려면:

```python
# (의사 코드 — 실제 구현 필요 시 Python helper 사용)
from lerobot.datasets import LeRobotDataset
from lerobot.robots.so101_follower import SO101Follower, SO101FollowerConfig

ds = LeRobotDataset("local/wave_hello", root="...", episodes=[0])
target = ds.select_columns("action")[0]["action"]  # trajectory[0]

robot = SO101Follower(SO101FollowerConfig(port=..., id=...))
robot.connect()
current = robot.get_observation()["observation.state"]
diff = (current - target).abs().max()
robot.disconnect()

if diff > THRESHOLD:   # 예: 0.1 (정규화된 좌표계 단위)
    print("ERROR: follower not in home pose", file=sys.stderr)
    sys.exit(5)
```

⚠ 이 점검을 넣으면 lerobot-replay 호출 전에 follower 를 한 번 connect/disconnect 함. lerobot-replay 가 다시 connect 할 때 미세 지연 (~0.5s) 발생. 운영상 부담 없으면 채택 권장. 부담되면 trigger 측 책임으로 두기.

**본 가이드는 우선 5-4 까지만 구현. home pose 점검은 첫 시연에서 jerk 발생 시 추가** (YAGNI 원칙).

---

## 6) 안전 / 주의 사항

[gestures.md §4](gestures.md#4-안전-원칙) 의 모든 항목이 Jetson 에 그대로 적용. 추가로:

### 6-1. 캘리브레이션 일치 검증

DGX 의 캘리브레이션 JSON 과 Jetson 의 JSON 이 **바이트 동일** 해야 함. sync 시 rsync 가 보장하지만, 사용자가 양쪽에서 별도로 캘리브레이션 한 경우 두 파일이 다를 수 있음 → trajectory 좌표계 어긋남. 의심 시:

```bash
# DGX 측
md5sum ${HF_HOME}/lerobot/calibration/robots/so_follower/rightarm_test_follower.json

# Jetson 측 (ssh 해서)
md5sum ${HF_HOME}/lerobot/calibration/robots/so_follower/rightarm_test_follower.json
```

두 md5 값이 같지 않으면 → DGX 의 sync_gesture_to_orin.sh 재실행으로 Jetson 쪽 덮어쓰기.

### 6-2. lerobot 버전 일치

DGX `docs/reference/lerobot/` 의 git SHA 와 Jetson 동일 위치의 SHA 가 일치해야 trajectory action 처리 (특히 `make_default_robot_action_processor()`) 가 동일하게 동작. 의심 시:

```bash
# 양쪽에서
cd ~/smolvla/docs/reference/lerobot && git rev-parse HEAD
```

### 6-3. 첫 replay 는 사람 / 물체 없는 빈 공간에서

DGX 에서 검증했어도 Jetson 의 미세 환경 차이 (PYTHONPATH, CUDA, ldconfig) 가 send_action 결과를 살짝 바꿀 가능성 X 는 아님. 처음에는 빈 공간에서 1회 확인 후 실 사용.

### 6-4. 트리거 시스템과의 동시성

play_gesture.sh 가 실행 중일 때 다른 호출이 들어오면 두 번째 호출은 USB 포트 점유 실패로 종료 (exit 5). 트리거 측에서:
- 단일 큐 (FIFO) 로 직렬화, 또는
- 두 번째 호출 거부 (busy)
- 본 wrapper 안에 lock file 추가 옵션도 있음 (`flock /tmp/play_gesture.lock`) — 필요 시 구현 추가

---

## 7) 검증 프로토콜 (구현 직후 1회)

구현 완료 후 사용자가 수동 수행:

```bash
# (Jetson) 1. 환경 확인
ssh orin
source ~/smolvla/orin/.hylion_arm/bin/activate
echo "HF_HOME=${HF_HOME}"
which lerobot-replay
ls ~/smolvla/orin/gestures/wave_hello/meta/info.json
ls ${HF_HOME}/lerobot/calibration/robots/so_follower/rightarm_test_follower.json

# 2. pre-check 만 (dry-run 같은 모드 있으면)
bash ~/smolvla/orin/scripts/check_gesture_ready.sh wave_hello

# 3. 빈 공간에서 실 재생 — 첫 회는 사람·물체 멀리
bash ~/smolvla/orin/scripts/play_gesture.sh wave_hello
# → exit code 0 확인. 진동 / 그리퍼 부하 / jerk 없는지 관찰

# 4. trigger 시스템 연동 (예: simple shell)
echo "wave_hello" | xargs -I{} bash ~/smolvla/orin/scripts/play_gesture.sh {}
```

---

## 8) 컨벤션 (본 프로젝트 기존 규약 준수)

- **lerobot upstream 무수정**: `docs/reference/lerobot/` 는 editable install. Jetson 측도 동일. 패치 필요 시 wrapper 에서 처리
- **Korean 주석 / English 코드**: `dgx/scripts/run_teleoperate.sh`, `dgx/scripts/record_gesture.sh` 스타일 그대로
- **헤더 블록**: 파일 첫 머리에 용도 / 자매 파일 / 의존성 / 결정 근거 명시 (run_teleoperate.sh 참조)
- **`set -euo pipefail`**: bash 스크립트 표준
- **exit code 의미**: 위 §5-1 매핑 따르기. 트리거 시스템이 의존
- **env override 우선**: hardcoded 값은 기본값으로만, env 우선
- **CLAUDE.md 준수**: 본 repo CLAUDE.md (Walking RL 보호) — Jetson 에는 Walking RL 없으나 일관성 위해 인지

---

## 9) 향후 확장 (현 단계 구현 X)

본 단계는 "1 명령 → 1 동작" 의 최소 시스템. 다음은 별도 마일스톤:

- Lock file 기반 동시 호출 방지 (`flock`)
- gesture 큐 / 시퀀스 (wave → bow → idle)
- Home pose 자동 복귀 (gesture 끝마다)
- 안전 영역 (geofence) — joint 한계치 강제
- 트리거 통합 (음성 인식, ROS topic, MQTT) — Jetson 측에서 추가 모듈로 결합

---

## 10) AI 에이전트용 프롬프트 (Jetson 측 Claude Code 세션에 복붙)

> 아래 ``` 블록을 그대로 복사해 Jetson 에서 실행되는 Claude Code 세션의 첫 입력으로 붙여넣으세요.

````
[Jetson Gesture Replay 시스템 구현]

본 프로젝트는 SmolVLA 학습 (DGX) 과 별개로 SO-ARM 에 "인사·절·포인팅" 같은 단일 고정 동작을 트리거 신호로 재생하는 시스템입니다. DGX 측에서 trajectory 녹화 + Jetson 으로 rsync 까지 완료된 상태이고, 본 작업은 Jetson 측에서 그 trajectory 를 재생하는 wrapper 시스템을 만드는 것입니다.

## 먼저 읽을 문서 (이 순서대로)

1. `~/smolvla/dgx/docs/gestures.md` — 전체 아키텍처, 안전 원칙, DGX 측 흐름
2. `~/smolvla/dgx/docs/gestures_jetson_setup_prompt.md` — 본 프롬프트의 출처. §3 ~ §7 가 구현 가이드
3. `~/smolvla/docs/reference/lerobot/src/lerobot/scripts/lerobot_replay.py` — 재사용할 핵심 명령 (lerobot-replay)
4. `~/smolvla/dgx/scripts/record_gesture.sh`, `run_teleoperate.sh` — 컨벤션 참조 (헤더 블록 / pre-check 패턴 / env override)

위 문서가 Jetson 에 없으면, 사용자에게 "DGX → Jetson 으로 본 repo 가 rsync 또는 git pull 되어야 함" 안내 후 중단.

## 작업 목표

다음 파일들을 만들어 트리거 시스템에서 `bash ~/smolvla/orin/scripts/play_gesture.sh wave_hello` 한 줄 호출로 SO-ARM 이 해당 gesture 를 재생하게 합니다.

| 파일 | 책임 |
|---|---|
| `~/smolvla/orin/scripts/play_gesture.sh` | lerobot-replay wrapper. pre-check + 호출 + exit code 매핑 |
| `~/smolvla/orin/scripts/check_gesture_ready.sh` | dry-run 점검 (venv / dataset / 캘리브레이션 / 포트). play_gesture 가 내부 재사용 가능 |
| `~/smolvla/orin/gestures/README.md` | DGX 의 dgx/gestures/README.md mirror — 디렉토리 컨벤션 |
| `~/smolvla/orin/docs/gestures.md` | Jetson 측 운영 가이드. DGX 문서로 cross-link, Jetson-specific 항목만 추가 |

## 작업 절차

1. **환경 검증** — 위 가이드 §3 의 표를 참조해 각 항목 실측. 어느 하나라도 미충족이면 사용자에게 안내 후 중단:
   - `~/smolvla/orin/` 존재 여부
   - Jetson 추론 venv 경로 (`orin/.hylion_arm` 또는 사용자가 알려주는 다른 경로)
   - venv activate 후 `which lerobot-replay`
   - `HF_HOME` 값
   - `${HF_HOME}/lerobot/calibration/robots/so_follower/rightarm_test_follower.json` (DGX 에서 sync 완료된 상태인지)
   - `~/smolvla/orin/gestures/` 디렉토리 (없으면 mkdir 가능)
   - `/dev/ttyACM*` 존재 + dialout 멤버십

2. **play_gesture.sh 구현** — gestures_jetson_setup_prompt.md §5 의 명세 그대로:
   - Header 블록 (DGX 측 record_gesture.sh 스타일)
   - `set -euo pipefail`
   - 인자 검증 (gesture name 형식 ^[a-z][a-z0-9_]*$, 1개 필수)
   - venv activate (이미 활성이면 skip — `${VIRTUAL_ENV}` 체크)
   - pre-check 5단계 (§5-4) → 실패 시 exit code 매핑 (§5-1)
   - lerobot-replay 호출 (§5-2) — 인자 그대로
   - 종료 시 stdout 한 줄 요약 (gesture 이름, 프레임 수, 소요 시간)

3. **check_gesture_ready.sh** — play_gesture.sh 의 pre-check 부분만 재사용. play_gesture.sh 가 내부에서 source 해도 OK 한 구조 권장 (또는 함수 라이브러리 분리). 단순함 우선이면 별도 스크립트로 두고 play_gesture.sh 에서 함수 코드 중복 허용.

4. **gestures/README.md, docs/gestures.md** — DGX 의 dgx/gestures/README.md, dgx/docs/gestures.md 를 mirror. 단:
   - 위치 / 책임 차이 명시 (Jetson 은 replay 전담)
   - DGX 문서로 absolute path 또는 ../ relative path 로 cross-link
   - Jetson-specific 항목 (사용 venv 경로, FOLLOWER_PORT 의 Jetson 측 enumeration) 추가

5. **chmod +x** 모든 .sh 파일

6. **검증** (실 하드웨어 동작 전):
   - `bash check_gesture_ready.sh wave_hello` → 0 exit
   - `bash play_gesture.sh nonexistent_gesture` → exit 4 + 에러 메시지
   - 빈 공간 / 사람 없는 환경 / 사용자 입회 하에 1회 실 재생 → 진동 / jerk / 그리퍼 부하 없는지 사용자 확인

## 컨벤션 (반드시 준수)

- 한국어 주석 + 영문 코드. 헤더 블록에 용도 / 자매 파일 / 의존성 / 결정 근거
- lerobot upstream 무수정 (editable install 그대로 사용)
- env override > hardcoded — `FOLLOWER_PORT`, `FOLLOWER_ID`, `ORIN_GESTURES_ROOT`, `HF_HOME` 모두 env 가 있으면 우선
- 변경 사항을 사용자에게 commit 으로 묶을지는 물어볼 것. 자동 commit 금지

## 주의 사항

- DGX 와 Jetson 의 lerobot SHA 일치 여부 확인 (`cd ~/smolvla/docs/reference/lerobot && git rev-parse HEAD`)
- DGX 의 캘리브레이션 JSON md5 와 Jetson 의 md5 비교 (불일치 시 sync 재실행 요청)
- 첫 replay 는 사용자 입회 + 빈 공간 + 비상 정지 가능 자세 유지
- USB 포트 mutex — 다른 lerobot 프로세스 (record / teleoperate) 가 follower 잡고 있지 않은지 확인
- 본 단계에서는 home pose 자동 점검 / lock file / 큐 시스템은 만들지 말 것 (YAGNI — gestures_jetson_setup_prompt.md §9 별도 마일스톤)
- 음성 / ROS / MQTT 등 트리거 통합은 본 단계 범위 외 — 사용자가 별도로 결합. wrapper 는 인터페이스만 제공

## 완료 후 보고

- 만든 파일 목록 + 각 파일의 용도 한 줄
- 검증 결과 (exit code 케이스별 동작 확인)
- 사용자가 첫 실 재생 전 확인해야 할 항목 체크리스트
- 미해결 의문점 / 후속 작업 제안

작업 시작 전 위 가이드 문서를 읽었음을 확인하고, 환경 검증 표 (§3) 의 결과부터 사용자에게 보고한 뒤 진행하세요. 환경 검증 단계에서 막히면 그 시점에 멈추고 사용자에게 안내.
````

---

## 11) 트리거 시스템 (참고)

본 가이드 범위 외이지만 호출 인터페이스만 정리:

```bash
# 가장 단순 — 단발성 호출
bash ~/smolvla/orin/scripts/play_gesture.sh wave_hello
echo "exit: $?"

# 시퀀스 (직렬)
for g in wave_hello bow_short; do
  bash ~/smolvla/orin/scripts/play_gesture.sh "$g" || break
done

# 트리거 시스템 (의사 코드 — 사용자가 별도로 만들 부분)
on_voice_command("hello") → bash play_gesture.sh wave_hello
on_ros_message(...)       → bash play_gesture.sh <name>
on_mqtt(topic=...)        → bash play_gesture.sh <name>
```

트리거 시스템 자체는 본 문서 범위 외. play_gesture.sh 의 stdout / exit code 만 안정적으로 유지하면 어떤 트리거든 결합 가능.

---

## 12) 변경 이력

| 일자 | 변경 |
|---|---|
| 2026-05-13 | 신규 작성. DGX-side artifacts (gestures.md, record_gesture.sh, sync_gesture_to_orin.sh, gestures/README.md) 완료, Jetson-side 는 본 프롬프트로 후속 |
