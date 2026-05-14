# Gesture 시스템 가이드 (record → sync → replay)

> **목적**: SmolVLA / ACT 학습 모델과 별개로, 트리거 기반 고정 동작 (인사·절·포인팅 등) 을 lerobot 내장 record/replay 메커니즘으로 구현.
> **작성**: 2026-05-13
> **자매 문서**:
> - [status.md](status.md) — 전체 현황
> - [data_collection.md](data_collection.md) — 학습 dataset 수집 (대비)
> - [gestures_jetson_setup_prompt.md](gestures_jetson_setup_prompt.md) — Jetson 측 replay 구현용 AI 프롬프트
> **스크립트**: [record_gesture.sh](../scripts/record_gesture.sh), [sync_gesture_to_orin.sh](../scripts/sync_gesture_to_orin.sh)
> **lerobot 참조**: [lerobot_replay.py](../../docs/reference/lerobot/src/lerobot/scripts/lerobot_replay.py) (`replay()` 함수가 핵심 — episode 의 `action` 컬럼을 fps 맞춰 `robot.send_action()` 호출)

---

## 0) 한 줄 요약

녹화 (DGX, 1회) → 동기화 (rsync, 1회/gesture) → 재생 (Jetson, 트리거마다). VLA / ACT 추론 없이 lerobot 의 record/replay CLI 만 사용.

```text
                                                        ┌─ 트리거 1 ──> play_gesture.sh wave_hello
DGX                              [rsync]                │
  record_gesture.sh wave_hello  ────────>   Jetson  ────┼─ 트리거 2 ──> play_gesture.sh bow
  (lerobot-record, 5s, motors only)        replay env   │
                                                        └─ ...
```

---

## 0-1) 본 시스템 적용 현황 / 양팔 배치 (2026-05-13 기준)

본 프로젝트는 SO-101 **양팔** 환경입니다. 좌·우 팔 각각 follower + leader 1쌍 (총 4 devices) 물리 배치 완료.

### 팔별 역할 분담

| 팔 | 역할 | 캘리브레이션 상태 | 데이터셋 / 시스템 |
|---|---|---|---|
| **좌측** | SmolVLA 학습·추론 전담 | ✅ 완료 (2026-05-11, `leftarm_test_follower` + `leftarm_test_leader`) | `BaboGaeguri/leftarm_v1` (40 ep) → SmolVLA fine-tune |
| **우측** | **Gesture 전담 (본 시스템)** | ⬜ **미수행** — 녹화 전 1회 필요 | `dgx/gestures/<name>` (record_gesture.sh 산출물) |

### 결정 사항 / 운영 효과

- **좌측은 절대 건드리지 않음**. 좌측 캘리브레이션 JSON 은 `leftarm_v1` 데이터셋과 SmolVLA 학습 좌표계와 묶여 있어 재캘리브 시 모든 학습 자산 무효화
- **우측은 신규 robot.id 부여로 좌측과 격리**. 캘리브레이션 파일도 별도 — leftarm 측에 영향 0
- **USB 포트 mutex 영향 X (양팔 분담 효과)**: 좌측 follower 가 SmolVLA inference 로 점유 중이어도 우측 follower 는 다른 USB 포트 → gesture replay **동시 실행 가능**. 이전 단일팔 시나리오의 mutex 우려가 양팔 환경에서는 자동 해소
- **Jetson 추론도 동일 구조** — 좌측 SmolVLA inference + 우측 gesture replay 동시 운영 가능

### 우측 팔 robot.id / 캘리브레이션 규약

| 항목 | 값 |
|---|---|
| follower id | `rightarm_test_follower` |
| leader id | `rightarm_test_leader` |
| follower 캘리브 파일 | `${HF_HOME}/lerobot/calibration/robots/so_follower/rightarm_test_follower.json` |
| leader 캘리브 파일 | `${HF_HOME}/lerobot/calibration/teleoperators/so_leader/rightarm_test_leader.json` |
| `FOLLOWER_PORT` / `LEADER_PORT` | **미확인** — `lerobot-find-port` 로 4-device 환경 enumeration 1회 확인 후 env export |

> **명명 일관성**: 좌측의 `leftarm_test_*` 형식을 그대로 미러링 (`rightarm_test_*`). "_test_" infix 가 어색하면 향후 좌·우 동시에 정리 가능 (현재 단계에서는 좌측 dataset 호환성 우선이라 그대로 유지).

### 다음 단계 체크리스트 (사용자 가용 시 1회 수행)

```
[ ] (DGX) 우측 follower + leader USB 연결 확인 — 케이블 + dialout 권한
[ ] (DGX) lerobot-find-port 2회 — 우측 follower 포트, 우측 leader 포트 확인
[ ] (DGX) 우측 follower 캘리브레이션
        FOLLOWER_PORT=/dev/ttyACMx FOLLOWER_ID=rightarm_test_follower \
          bash dgx/scripts/run_teleoperate.sh calibrate-follower
[ ] (DGX) 우측 leader 캘리브레이션
        LEADER_PORT=/dev/ttyACMy LEADER_ID=rightarm_test_leader \
          bash dgx/scripts/run_teleoperate.sh calibrate-leader
[ ] (DGX) 사전 검증 — 우측 텔레오퍼레이션 짧게 (run_teleoperate.sh teleoperate 인자 env override)
[ ] (DGX) record_gesture.sh <gesture_name> 으로 첫 gesture 녹화
[ ] (DGX) (선택) 빈 공간 lerobot-replay 로 trajectory 검증
[ ] (DGX) sync_gesture_to_orin.sh <gesture_name> — Jetson 으로 데이터 + 캘리브 전송
[ ] (Jetson) gestures_jetson_setup_prompt.md §10 프롬프트로 wrapper 구현
[ ] (Jetson) 빈 공간 / 사용자 입회 하 첫 실 재생 검증
```

---

## 1) 아키텍처 / 결정 사항

### 왜 lerobot-record/replay 를 그대로 쓰나

- lerobot upstream 에 이미 `lerobot-replay` 존재 ([lerobot_replay.py:100-132](../../docs/reference/lerobot/src/lerobot/scripts/lerobot_replay.py#L100-L132)). 자체 trajectory 포맷·재생기를 만들 이유 X
- 학습 dataset 과 동일한 LeRobotDataset 포맷 → 캘리브레이션 / robot.id 일관성 자동 보장
- 비디오·카메라 제외 옵션 (`--dataset.video=false` + `--robot.cameras` 미지정) 으로 모터-only dataset 생성 가능

### 학습 dataset 과의 차이 (요약)

| 항목 | `leftarm_v1` (학습용) | `gestures/<name>` (replay 용) |
|---|---|---|
| 위치 | `${HF_HOME}/lerobot/${HF_USER}/leftarm_v1/` | `dgx/gestures/<name>/` |
| Episodes | 40~100 | **1** |
| 카메라 / 비디오 | 2대 + libsvtav1 | **없음** |
| HF Hub push | true | **false** |
| `episode_time_s` | 60 | 5 (기본) |
| `reset_time_s` | 15 | **0** |
| 용도 | SmolVLA fine-tune | `lerobot-replay` 로 그대로 재생 |

### Stage 분담

| 단계 | 노드 | 도구 | 빈도 |
|---|---|---|---|
| 캘리브레이션 | DGX | `lerobot-calibrate` (run_teleoperate.sh) | 1회 / 본체 |
| 녹화 | **DGX** | `record_gesture.sh` (lerobot-record wrapper) | 1회 / gesture |
| 동기화 | DGX → Jetson | `sync_gesture_to_orin.sh` (rsync) | 1회 / gesture |
| 재생 | **Jetson** | `lerobot-replay` (Jetson 측 wrapper — [Jetson prompt 참조](gestures_jetson_setup_prompt.md)) | 트리거마다 |

---

## 2) 사전 조건 (DGX 측, 녹화 1회 시)

1. **venv + 환경변수**: `source ~/smolvla/dgx/.arm_finetune/bin/activate`
2. **lerobot-record / lerobot-replay 명령 확인**: `which lerobot-record`
3. **SO-ARM follower + leader 연결**: USB 케이블 + dialout 그룹
4. **포트 확인**: `lerobot-find-port` → `FOLLOWER_PORT`, `LEADER_PORT` 확인
5. **캘리브레이션 파일 존재**: `${HF_HOME}/lerobot/calibration/robots/so_follower/${FOLLOWER_ID}.json` 있어야 함. 없으면:
   ```bash
   bash ~/smolvla/dgx/scripts/run_teleoperate.sh calibrate-follower
   bash ~/smolvla/dgx/scripts/run_teleoperate.sh calibrate-leader
   ```
6. **카메라 / Rerun 등 학습 dataset 측 의존성은 불필요** — gesture 녹화는 motors only

---

## 3) 녹화 절차

### 3-1. 한 번에

```bash
source ~/smolvla/dgx/.arm_finetune/bin/activate

# (USB 변동 시) lerobot-find-port 로 포트 재확인 후 export
# export FOLLOWER_PORT=/dev/ttyACM0
# export LEADER_PORT=/dev/ttyACM1

bash ~/smolvla/dgx/scripts/record_gesture.sh wave_hello
# 또는 길이 지정 (기본 5s):
# bash ~/smolvla/dgx/scripts/record_gesture.sh wave_hello 3
```

### 3-2. 녹화 중 권장 절차

1. follower 를 자연스러운 **home pose** 로 두기 (replay 시점도 같은 자세로 시작 — 첫 프레임 점프 방지)
2. 비프 / "Recording" 안내 → leader 로 동작 시연
3. 동작 끝나면 `→` (오른쪽 화살표) 키로 episode 종료
4. 만족스러우면 그대로 종료. 재시도는 `←` 또는 `Esc` → 디렉터리 삭제 후 본 스크립트 재실행

### 3-3. 결과 검증

```bash
# meta 한 줄 요약
jq '{total_episodes, total_frames, fps}' \
  ~/smolvla/dgx/gestures/wave_hello/meta/info.json
# → {"total_episodes": 1, "total_frames": 90~150, "fps": 30}

# 파일 구조 (비디오 없음 — motors only)
find ~/smolvla/dgx/gestures/wave_hello -type f
# data/chunk-000/file-000.parquet
# meta/info.json, stats.json, tasks.parquet, episodes/...
```

### 3-4. (선택) DGX 에서 trajectory 검증 재생

사람 / 물체 없는 빈 공간에서:

```bash
lerobot-replay \
  --robot.type=so101_follower \
  --robot.port=${FOLLOWER_PORT} \
  --robot.id=${FOLLOWER_ID:-rightarm_test_follower} \
  --dataset.repo_id=local/wave_hello \
  --dataset.root=~/smolvla/dgx/gestures/wave_hello \
  --dataset.episode=0
```

진동 / 그리퍼 부하 / 첫 프레임 jerk 가 없으면 OK. 문제 시 §5 안전 원칙 참조 후 재녹화.

---

## 4) 안전 원칙

### 4-1. 첫 프레임 jerk (가장 중요)

`lerobot-replay` 는 첫 프레임의 `action` 을 곧바로 `send_action()` 호출. follower 현재 자세가 trajectory[0] 과 멀면 모든 모터가 동시에 빠른 속도로 이동 → 모터 부하 / 사람·물체 충돌 위험.

**완화 방법**:
- 녹화 시 trajectory[0] = "home pose" 로 시작 (예: 모든 관절 0 근처, 그리퍼 살짝 열림)
- 트리거 시점에도 follower 가 같은 home pose 에 있도록 운영 (이전 gesture 가 home 으로 끝나거나, idle 시 home 유지)
- 트리거 사이에 사람이 follower 자세 변경하는 경우 → 트리거 호출 전 "현재 자세 ↔ trajectory[0] 거리" 임계치 체크 추가 (Jetson 측 wrapper 책임 — [Jetson prompt](gestures_jetson_setup_prompt.md) §6 참조)

### 4-2. 그리퍼 (motor id=6) overload

leftarm_v1 수집 때 이미 발생한 이슈 ([backlog.md](backlog.md) ⚙ "그리퍼 overload"). gesture 도 같은 모터.

**완화**:
- gesture 길이 짧게 (5s 이하)
- 그리퍼 닫힘 지속 X → 인사 동작은 그리퍼 열림 / 살짝 열림으로
- 동작 끝 자세도 그리퍼 가벼운 상태로

### 4-3. 캘리브레이션 일관성

- 녹화 시점 캘리브레이션 ↔ replay 시점 캘리브레이션 **동일 파일** 이어야 함
- DGX 에서 녹화 → Jetson 으로 sync 시 `sync_gesture_to_orin.sh` 가 calibration JSON 함께 전송
- **재캘리브레이션 금지** — 한 번 하면 모든 기존 gesture trajectory 및 leftarm_v1 dataset 무효화

### 4-4. USB 포트 mutex

같은 follower 포트 (`/dev/ttyACM*`) 를 두 프로세스가 동시에 잡지 못함. 즉:
- SmolVLA inference 와 gesture replay 동시 실행 불가
- 트리거 시스템은 "명령 1개 → 동작 1개 → 종료 → 다음 명령" 순차 처리 (사용자 설계 의도와 일치)

### 4-5. 처음 한 번은 느린 fps 로 검증

`DatasetReplayConfig.fps` 기본값은 데이터셋 fps (30). 첫 검증 시 사람·물체 없는 빈 공간에서 30fps 로 1회 재생, 진동·jerk 없는지 확인. 의심스러우면 trajectory 재녹화 (lerobot-replay 가 fps override 지원하지만 본 가이드에서는 재녹화 권장 — replay 명령 인터페이스 단순 유지).

---

## 5) 디렉터리 / 파일 컨벤션

```text
~/smolvla/dgx/
├── gestures/
│   ├── README.md                       # 디렉토리 책임 + 컨벤션
│   ├── wave_hello/                     # ★ 녹화 산출물 (record_gesture.sh 생성)
│   │   ├── meta/info.json              # total_episodes=1, fps=30
│   │   ├── meta/stats.json
│   │   ├── meta/tasks.parquet
│   │   ├── meta/episodes/...
│   │   └── data/chunk-000/file-000.parquet   # action / observation.state 만
│   └── <other_gesture>/...
├── scripts/
│   ├── record_gesture.sh               # ★ 녹화 wrapper
│   └── sync_gesture_to_orin.sh         # ★ DGX→Jetson rsync wrapper
└── docs/
    ├── gestures.md                     # ★ 본 문서
    └── gestures_jetson_setup_prompt.md # ★ Jetson 측 AI 프롬프트
```

**naming 규약**: gesture name 은 `^[a-z][a-z0-9_]*$` (snake_case, 영문/숫자/언더스코어).

---

## 6) Jetson 동기화 절차

DGX 에서 1회 (또는 gesture 추가/수정마다):

```bash
# 사전 (Jetson 환경 확인 후) — 본 export 는 ~/.bashrc 에 영구 저장 권장
export ORIN_HOST=orin                                           # ~/.ssh/config 의 Host alias
export ORIN_HF_HOME=/home/laba/smolvla/.hf_cache                # Jetson 측 HF_HOME (사용자 환경 따라 조정)
export ORIN_GESTURES_ROOT=/home/laba/smolvla/orin/gestures      # Jetson 측 gesture 루트

bash ~/smolvla/dgx/scripts/sync_gesture_to_orin.sh wave_hello
```

전송 항목:
1. `dgx/gestures/wave_hello/` → `${ORIN_GESTURES_ROOT}/wave_hello/`
2. `${HF_HOME}/lerobot/calibration/robots/so_follower/${FOLLOWER_ID}.json` → 동일 경로

Jetson 측 환경 구축 (venv / lerobot 설치 / 트리거 wrapper) 은 **[gestures_jetson_setup_prompt.md](gestures_jetson_setup_prompt.md) 의 AI 프롬프트** 로 처리.

---

## 7) 향후 확장 고려

| 확장 | 접근 |
|---|---|
| 여러 gesture 등록 (wave, bow, point, …) | 각각 `record_gesture.sh <name>` 1회 + sync 1회. dispatcher 는 `play_gesture.sh <name>` 호출만 변경 |
| Trajectory 길이 trimming | `lerobot-edit-dataset` 사용. 또는 재녹화 권장 (단순함) |
| Hybrid (SmolVLA inference 중 트리거 받으면 gesture 로 전환) | USB mutex 때문에 통합 controller 필요. 본 가이드 범위 외. 현 단계는 "한 명령 → 한 동작" shell 레벨 mutex |
| 양팔 / 멀티 robot | lerobot-record/replay 가 `bi_so_follower` 지원. 본 가이드 단일팔 가정. 양팔 시 record_gesture.sh 인자 확장 필요 |

---

## 8) 트러블슈팅

| 증상 | 원인 / 해결 |
|---|---|
| `record_gesture.sh` 실행 시 `lerobot-record: command not found` | venv 미활성 → `source ~/smolvla/dgx/.arm_finetune/bin/activate` |
| `${GESTURE_DIR} 이미 존재` | 이전 시도 잔존 → 만족스러우면 그대로 사용, 재녹화 원하면 `rm -rf` |
| 캘리브레이션 파일 없음 WARN | `bash scripts/run_teleoperate.sh calibrate-follower` (+ calibrate-leader) 선행 |
| `Permission denied: /dev/ttyACM*` | dialout 그룹 미포함 → `sudo usermod -aG dialout $(id -un)` + 재로그인 |
| lerobot-record 가 카메라 요구 에러 | (현 lerobot SHA 에선 미발생 예상) `--robot.cameras='{}'` 명시 추가 필요 시 record_gesture.sh §lerobot-record 호출부에 추가 |
| Jetson sync 후 replay 가 `dataset features mismatch` | DGX 와 Jetson 의 lerobot 버전 차이 가능성. 양쪽 동일한 [docs/reference/lerobot/](../../docs/reference/lerobot/) SHA 인지 확인 |
| 첫 replay 시 follower 가 격렬히 jerk | trajectory[0] ↔ 현재 자세 거리 큼 → §4-1 home pose 보장 / 재녹화 |

---

## 9) 참조

- [lerobot_replay.py](../../docs/reference/lerobot/src/lerobot/scripts/lerobot_replay.py) — 본 시스템의 핵심 (LeRobotDataset 의 action 컬럼을 fps 맞춰 send_action)
- [lerobot_record.py](../../docs/reference/lerobot/src/lerobot/scripts/lerobot_record.py) — DatasetRecordConfig 의 `video: bool` (177행) 등
- [data_collection.md](data_collection.md) — 학습 dataset 수집 가이드 (대비점 비교용)
- [status.md](status.md) — gesture 시스템 등록 시 §8 갱신
- 본 repo CLAUDE.md — Walking RL 보호 원칙 (gesture 녹화는 motors only 라 부담 X 이지만 USB 점유는 발생)
