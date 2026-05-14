# 데이터 수집 가이드 (DGX, SO-ARM 100/101)

> **대상 데이터셋**: `${HF_USER}/leftarm_v1` — "Pick up the doll and place it right next to its original position"
> **노드**: DGX Spark (단일 노드, 데이터 수집 + 학습)
> **작성**: 2026-05-11
> **참조**: `~/smolvla/docs/reference/lerobot/src/lerobot/scripts/lerobot_record.py`, 본 repo `dgx/scripts/run_teleoperate.sh`

---

## 0) 전제 조건

### 0-1. 환경 요건

- DGX Spark, venv `~/smolvla/dgx/.arm_finetune` 활성화
- SO-ARM follower + leader 2대, USB 카메라 2대 (top + wrist)
- HuggingFace 계정 로그인 (`hf auth login`) + `HF_USER` 환경변수
- (Walking RL 동시 가동 시) **GPU 가속 코덱 사용 X** — 본 가이드는 `libsvtav1` (CPU) 기본

### 0-2. venv 활성화 + HF_USER export

```bash
source ~/smolvla/dgx/.arm_finetune/bin/activate
export HF_USER=<your_hf_username>   # 예: BaboGaeguri

# HF 로그인 확인 (push_to_hub=true 사용 시 필수)
hf auth whoami
# → "✓ Logged in" + user 이름 표시되어야 함. 미로그인 시:
# hf auth login
```

### 0-3. Rerun 의존성 설치 (시각화용, 최초 1회)

`--display_data=true` 사용 시 필요. lerobot `[viz]` extra 또는 직접 설치:

```bash
pip install 'rerun-sdk>=0.24.0,<0.27.0'
# 대안 (lerobot extra 통째로):
# pip install -e ~/smolvla/docs/reference/lerobot[viz]
```

### 0-4. 하드웨어 점검

```bash
bash ~/smolvla/dgx/scripts/check_hardware.sh
```

→ dialout 그룹 / SO-ARM 포트 / v4l2 장치 / OpenCV 카메라 발견 검증.

---

## 1) lerobot-find-port — SO-ARM 포트 확인

USB enumeration 순서가 시연장 / 부팅마다 변동되므로 매 세션 재확인.

### 1-1. follower 포트 확인

```bash
lerobot-find-port
```

→ 프롬프트 따라 follower USB 케이블 분리 → Enter → 변경된 포트가 표시됨. 재연결 후:

```bash
export FOLLOWER_PORT=/dev/ttyACM1   # 출력값으로 교체
```

### 1-2. leader 포트 확인

```bash
lerobot-find-port
```

→ leader USB 분리 → Enter → 표시된 포트를 export:

```bash
export LEADER_PORT=/dev/ttyACM0     # 출력값으로 교체
```

> **직전 확인 (2026-04-27)**: follower=`/dev/ttyACM1` (serial 5B42138563), leader=`/dev/ttyACM0` (serial 5B42138566). 시연장 이동 시 무효 가능.

---

## 2) lerobot-find-cameras — 카메라 인덱스 확인

```bash
lerobot-find-cameras opencv
```

→ 발견된 카메라마다 `id`, `default_stream_profile` (width/height/fps), 미리보기 이미지 출력.

```bash
export CAMERA_TOP_INDEX=0     # 출력의 top 카메라 id
export CAMERA_WRIST_INDEX=1   # 출력의 wrist 카메라 id
```

### 2-1. fourcc / color_mode 결정

시연장 USB 토폴로지 (USB 3.0 포트 + 디바이스 USB 2.0 only) 에서는 **MJPG** 강제 필요. raw 포맷 (YUYV 등) 은 USB 2.0 대역폭 제한으로 30fps 미달.

| 인자 | 값 | 이유 |
|---|---|---|
| `color_mode` | `rgb` | lerobot 표준. policy 학습 / 추론 모두 RGB 가정 |
| `fourcc` | `MJPG` | USB 2.0 path 30fps 안정 |

---

## 3) lerobot-calibrate — 캐리브레이션

각 디바이스 첫 사용 시 또는 기구학 변경 후 1회. `robot.id` / `teleop.id` 가 캐리브레이션 파일명이며 record / teleoperate 시 정합 필요.

### 3-1. follower

```bash
export FOLLOWER_ID=my_awesome_follower_arm

lerobot-calibrate \
  --robot.type=so101_follower \
  --robot.port="${FOLLOWER_PORT}" \
  --robot.id="${FOLLOWER_ID}"
```

### 3-2. leader

```bash
export LEADER_ID=my_awesome_leader_arm

lerobot-calibrate \
  --teleop.type=so101_leader \
  --teleop.port="${LEADER_PORT}" \
  --teleop.id="${LEADER_ID}"
```

캐리브레이션 파일 위치: `~/.cache/huggingface/lerobot/calibration/<robot|teleop>/<id>.json`

---

## 4) (선택) lerobot-teleoperate — 동작 확인

수집 시작 전 30초 정도 텔레오퍼레이션으로 모터·통신·캐리브레이션 정합 확인:

```bash
lerobot-teleoperate \
  --robot.type=so101_follower \
  --robot.port="${FOLLOWER_PORT}" \
  --robot.id="${FOLLOWER_ID}" \
  --teleop.type=so101_leader \
  --teleop.port="${LEADER_PORT}" \
  --teleop.id="${LEADER_ID}"
```

또는 헬퍼:

```bash
bash ~/smolvla/dgx/scripts/run_teleoperate.sh teleoperate
```

---

## 5) lerobot-record — 데이터 수집 (총 100 episodes, 20 × 5 resume)

### 5-1. 1 차 — 신규 수집 (episodes 1~20)

```bash
lerobot-record \
  --robot.type=so101_follower \
  --robot.port="${FOLLOWER_PORT}" \
  --robot.id="${FOLLOWER_ID}" \
  --robot.cameras="{
    top: {type: opencv, index_or_path: ${CAMERA_TOP_INDEX}, width: 640, height: 480, fps: 30, color_mode: rgb, fourcc: MJPG},
    wrist: {type: opencv, index_or_path: ${CAMERA_WRIST_INDEX}, width: 640, height: 480, fps: 30, color_mode: rgb, fourcc: MJPG}
  }" \
  --teleop.type=so101_leader \
  --teleop.port="${LEADER_PORT}" \
  --teleop.id="${LEADER_ID}" \
  --dataset.repo_id="${HF_USER}/leftarm_v1" \
  --dataset.single_task="Pick up the doll and place it right next to its original position" \
  --dataset.num_episodes=20 \
  --dataset.fps=30 \
  --dataset.episode_time_s=60 \
  --dataset.reset_time_s=60 \
  --dataset.video=true \
  --dataset.vcodec=libsvtav1 \
  --dataset.streaming_encoding=true \
  --dataset.push_to_hub=true \
  --dataset.private=false \
  --dataset.tags='[smolvla, so101, leftarm, doll, hylion]' \
  --display_data=true \
  --play_sounds=true
```

### 5-2. 2~5 차 — resume (episodes 21~40, 41~60, 61~80, 81~100)

위 명령에 `--resume=true` 추가하고 `dataset.num_episodes` 를 **누적 목표값** 으로 증가:

| 차수 | `dataset.num_episodes` | 추가 인자 |
|---|---|---|
| 1차 | `20`  | (resume 없음) |
| 2차 | `40`  | `--resume=true` |
| 3차 | `60`  | `--resume=true` |
| 4차 | `80`  | `--resume=true` |
| 5차 | `100` | `--resume=true` |

예 (3차):

```bash
lerobot-record \
  ... (1차 인자 동일) ... \
  --dataset.num_episodes=60 \
  --resume=true
```

> **주의**: `num_episodes` 는 "총 목표값". 기존 dataset episode 수보다 작으면 실패.

### 5-3. 수집 중 키 조작

| 키 | 동작 |
|---|---|
| `→` | 현재 episode 종료, 다음 episode reset 단계 진입 |
| `←` | 현재 episode 폐기 후 재시도 |
| `Esc` | 전체 수집 안전 종료 |

### 5-4. 결과 위치

- **로컬**: `${HF_LEROBOT_HOME:-$HF_HOME/lerobot}/${HF_USER}/leftarm_v1/`
  → 본 환경: `/home/laba/smolvla/.hf_cache/lerobot/${HF_USER}/leftarm_v1/`
- **HF Hub**: `https://huggingface.co/datasets/${HF_USER}/leftarm_v1`

---

## 6) 인자 결정 근거 (DGX Spark 환경 특화)

| 인자 | 값 | 근거 |
|---|---|---|
| `vcodec=libsvtav1` | CPU SVT-AV1 | DGX Walking RL 트랙이 GPU 점유 가능 → NVENC 회피. Grace 20-core CPU 충분. lerobot 기본값 |
| `streaming_encoding=true` | 실시간 인코딩 | PNG 중간 저장 X → 디스크 IO·용량 절감. `save_episode()` near-instant. 30fps × 2 cam 640x480 부담 적음 |
| `encoder_threads` 미지정 | auto | libsvtav1 기본 (svtav1-params lp 자동 결정) |
| `num_image_writer_processes=0` | 기본 | `streaming_encoding=true` 면 미사용. 폴백 시에도 0 권장 (메인 스레드 경합 ↓) |
| `display_data=true` | Rerun on | DGX 모니터 직접 연결. `rerun-sdk` 설치 전제 |
| `play_sounds=true` | 음성 알림 | episode 시작·종료·reset 시점 청각 피드백 |
| `tags=[smolvla, so101, leftarm, doll, hylion]` | HF Hub 분류 | 프로젝트 / 하드웨어 / 태스크 / 조직 식별 |

### Walking RL 미가동 시 (대안)

GPU 여유 시 NVENC 가속:

```bash
--dataset.vcodec=h264_nvenc
```

→ CPU 부담 ↓, 인코딩 속도 ↑, 용량 약간 ↑. **Walking RL 가동 중에는 사용 금지** (CLAUDE.md Walking RL 보호 원칙).

---

## 7) 트러블슈팅

| 증상 | 원인 / 해결 |
|---|---|
| `lerobot-record` import 실패 | venv 미활성 또는 lerobot[hardware] 미설치 → `bash ~/smolvla/dgx/scripts/setup_train_env.sh` 재실행 |
| `Permission denied: /dev/ttyACM*` | dialout 그룹 미포함 → `sudo usermod -aG dialout $(id -un)` + 재로그인 |
| `Record loop is running slower than target FPS` | USB 대역폭 부족 → `fourcc=MJPG` 사용 / 해상도 ↓ / 카메라 분리 USB 컨트롤러 |
| Rerun 뷰어 미표시 | `pip install 'rerun-sdk>=0.24.0,<0.27.0'` |
| `push_to_hub` 실패 | `hf auth login` 또는 `export HF_TOKEN=hf_...` |
| 캐리브레이션 정합 오류 | `robot.id` / `teleop.id` 와 `~/.cache/huggingface/lerobot/calibration/` 파일명 불일치 → 재캐리브레이션 |
| Resume 시 `num_episodes too small` | `dataset.num_episodes` 가 기존 episode 수보다 작음 → 누적 목표값으로 지정 (5-2 표 참조) |
| 카메라 미발견 | `lerobot-find-cameras opencv` 재실행. v4l2 검출은 `check_hardware.sh` |

---

## 8) 참조

- `~/smolvla/dgx/scripts/run_teleoperate.sh` — 캐리브레이션·텔레오퍼레이션 헬퍼
- `~/smolvla/dgx/scripts/check_hardware.sh` — 수집 환경 점검
- `~/smolvla/docs/reference/lerobot/src/lerobot/scripts/lerobot_record.py` — `RecordConfig` / `DatasetRecordConfig` 정의
- `~/smolvla/docs/reference/lerobot/src/lerobot/cameras/opencv/configuration_opencv.py` — `OpenCVCameraConfig` (color_mode / fourcc)
- `~/smolvla/dgx/config/dataset_repos.json` — 데이터셋 메타 캐시
- 본 repo CLAUDE.md — Walking RL 보호 원칙
