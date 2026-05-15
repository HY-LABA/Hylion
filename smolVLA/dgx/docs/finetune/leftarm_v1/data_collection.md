# 데이터 수집 가이드 (DGX, SO-ARM 100/101)

> **대상 데이터셋**: `${HF_USER}/leftarm_v1` — "Pick up the doll and reach forward"
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
export HF_USER=BaboGaeguri

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
export LEADER_PORT=/dev/ttyACM1
export FOLLOWER_PORT=/dev/ttyACM0     # 출력값으로 교체
```

> **직전 확인 (2026-05-11)**: follower=`/dev/ttyACM0` (serial 5B42138563), leader=`/dev/ttyACM1` (serial 5B42138566). 시연장 이동 시 무효 가능.

---

## 2) lerobot-find-cameras — 카메라 인덱스 확인

```bash
lerobot-find-cameras opencv
```

→ 발견된 카메라마다 `id`, `default_stream_profile` (width/height/fps), 미리보기 이미지 출력.

`index_or_path` 값은 **`/dev/videoN` 의 정수 N** 입니다 (lerobot 출력의 "Camera #" 순번이 아님). USB 카메라 1대는 보통 `/dev/videoN`, `/dev/video(N+1)` 2개 노드를 차지하며, **앞쪽 짝수 번호만 캡처 노드**입니다. `v4l2-ctl --list-devices` 로 카메라 ↔ 노드 매핑을 확인하세요.

직전 확인 (2026-05-11, `v4l2-ctl --list-devices` 출력):

```
YJX-C5                    : /dev/video0, /dev/video1   ← top 캡처 노드는 video0
Innomaker-U20CAM-720P     : /dev/video2, /dev/video3   ← wrist 캡처 노드는 video2
```

```bash
export CAMERA_TOP_INDEX=0     # /dev/video0 — YJX-C5 (top 마운트)
export CAMERA_WRIST_INDEX=2   # /dev/video2 — Innomaker U20CAM-720P (wrist 마운트)
```

> **검증**: `ffplay -f v4l2 -input_format mjpeg -video_size 640x480 -framerate 30 /dev/videoN` 로 각 노드의 실제 영상을 미리 확인 가능. `q` 로 종료. `top` 회전 확인은 `-vf "transpose=2"` (반시계 90°) 추가.

### 2-1. fourcc / color_mode / rotation 결정

시연장 USB 토폴로지 (USB 3.0 포트 + 디바이스 USB 2.0 only) 에서는 **MJPG** 강제 필요. raw 포맷 (YUYV 등) 은 USB 2.0 대역폭 제한으로 30fps 미달.

| 인자 | 값 | 적용 카메라 | 이유 |
|---|---|---|---|
| `color_mode` | `rgb` | top, wrist | lerobot 표준. policy 학습 / 추론 모두 RGB 가정 |
| `fourcc` | `MJPG` | top, wrist | USB 2.0 path 30fps 안정 |
| `rotation` | `-90` (= `ROTATE_270`, 반시계 90°) | **top 만** | top 카메라가 옆으로 장착되어 있어 frame 을 왼쪽 90° 회전시켜 정립 방향 확보. wrist 는 정방향이므로 미적용 |
| `width` × `height` | top: **480 × 640** / wrist: 640 × 480 | 각각 | **회전 후 최종 출력 크기**. top 은 회전 (-90) 후 480x640 세로 정립이 목표 |

> `rotation` 매핑 (`Cv2Rotation`): `0` = 회전 없음, `90` = 시계 90°, `180` = 180°, `-90` = 반시계 90° (= 왼쪽 90°).
>
> ⚠️ **중요 — `width` / `height` 시맨틱**: lerobot OpenCV camera 의 `width` / `height` 는 **회전 후 출력 크기** ([camera_opencv.py:123-126](../../docs/reference/lerobot/src/lerobot/cameras/opencv/camera_opencv.py#L123-L126)). rotation 이 90°/270° 면 하드웨어에는 자동으로 transpose 해서 (height × width) 로 캡처 요청. 따라서 top 카메라는 `width=480, height=640, rotation=-90` 로 지정 → 하드웨어 640x480 캡처 → CCW 90° 회전 → 480x640 portrait 출력. `width=640, height=480, rotation=-90` 로 주면 하드웨어가 480x640 캡처를 지원해야 하므로 (대부분 미지원) `RuntimeError: failed to set capture_width=480 (actual_width=640)` 발생.
>
> 출력 해상도 (top 480x640 portrait, wrist 640x480 landscape) 가 서로 달라도 lerobot 은 카메라별 독립 처리하므로 OK. 학습 / 추론 / eval 모두 동일 rotation + width/height 유지 필수.

---

## 3) lerobot-calibrate — 캐리브레이션

각 디바이스 첫 사용 시 또는 기구학 변경 후 1회. `robot.id` / `teleop.id` 가 캐리브레이션 파일명이며 record / teleoperate 시 정합 필요.

### 3-1. follower

```bash
export FOLLOWER_ID=leftarm_test_follower

lerobot-calibrate \
  --robot.type=so101_follower \
  --robot.port="${FOLLOWER_PORT}" \
  --robot.id="${FOLLOWER_ID}"
```

### 3-2. leader

```bash
export LEADER_ID=leftarm_test_leader

lerobot-calibrate \
  --teleop.type=so101_leader \
  --teleop.port="${LEADER_PORT}" \
  --teleop.id="${LEADER_ID}"
```

캐리브레이션 파일 위치: `${HF_HOME}/lerobot/calibration/<robots|teleoperators>/<type>/<id>.json`

- 본 환경 (`HF_HOME=/home/laba/smolvla/.hf_cache`, [setup_finetune_env.sh](../scripts/setup_finetune_env.sh) 에서 Walking RL 캐시와 격리):
  - follower: `/home/laba/smolvla/.hf_cache/lerobot/calibration/robots/so_follower/${FOLLOWER_ID}.json`
  - leader:   `/home/laba/smolvla/.hf_cache/lerobot/calibration/teleoperators/so_leader/${LEADER_ID}.json`

> 시스템 디폴트 (`HF_HOME` unset) 라면 `~/.cache/huggingface/lerobot/...` 로 들어가지만, 본 가이드는 setup_finetune_env.sh 적용 전제이므로 위 경로가 정답.

---

## 4) lerobot-teleoperate — record 직전 최종 검증

수집 시작 직전 30초~1분 정도 텔레오퍼레이션으로 **카메라 (회전 / 해상도 / 포맷) + 모터·통신·캐리브레이션 정합** 을 한 번에 검증. record 명령 (§5) 과 동일한 `--robot.cameras` 인자를 사용해 record 시점 영상과 픽셀 단위로 일치하는지 확인하는 단계입니다.

### 4-1. 카메라 포함 (권장)

```bash
lerobot-teleoperate \
  --robot.type=so101_follower \
  --robot.port="${FOLLOWER_PORT}" \
  --robot.id="${FOLLOWER_ID}" \
  --robot.cameras="{
    top: {type: opencv, index_or_path: ${CAMERA_TOP_INDEX}, width: 480, height: 640, fps: 30, color_mode: rgb, fourcc: MJPG, rotation: -90},
    wrist: {type: opencv, index_or_path: ${CAMERA_WRIST_INDEX}, width: 640, height: 480, fps: 30, color_mode: rgb, fourcc: MJPG}
  }" \
  --teleop.type=so101_leader \
  --teleop.port="${LEADER_PORT}" \
  --teleop.id="${LEADER_ID}" \
  --display_data=true
```

→ Rerun viewer 윈도우에 `observation.images.top` (480x640, 반시계 90° 회전) / `observation.images.wrist` (640x480, 회전 없음) / 관절 state·action 그래프 표시. 리더 팔로 follower 추종 동작 + 카메라 영상 정합 둘 다 정상이어야 §5 진입.

체크포인트:

- [ ] top 영상이 **세로 방향**으로 정립되어 보임 (480x640)
- [ ] wrist 영상이 좌우 반전 / 상하 반전 없이 정상
- [ ] 두 카메라 모두 끊김 없이 30fps 유지 (Rerun 의 fps 카운터 또는 영상 부드러움)
- [ ] 리더 모든 관절이 follower 에 즉시 반영, 진동 / 폭주 없음

> ffplay 가 카메라를 잡고 있으면 lerobot 이 못 여니까 사전 정리: `pkill ffplay 2>/dev/null || true`

### 4-2. 빠른 모터·통신 점검 (카메라 미포함)

캐리브레이션 직후 또는 카메라 분리 상태에서 모터 / 시리얼 통신만 빠르게 확인하고 싶을 때:

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

> 이 단계는 **§5 record 진입 자격을 부여하지 않습니다** — 카메라 검증은 4-1 또는 record 첫 episode 의 Rerun 화면으로 별도 확인 필요.

---

## 5) lerobot-record — 데이터 수집 (총 100 episodes, 20 × 5 resume)

### 5-1. 1 차 — 테스트 수집 (episodes 1~10)

```bash
lerobot-record \
  --robot.type=so101_follower \
  --robot.port="${FOLLOWER_PORT}" \
  --robot.id="${FOLLOWER_ID}" \
  --robot.cameras="{
    top: {type: opencv, index_or_path: ${CAMERA_TOP_INDEX}, width: 480, height: 640, fps: 30, color_mode: rgb, fourcc: MJPG, rotation: -90},
    wrist: {type: opencv, index_or_path: ${CAMERA_WRIST_INDEX}, width: 640, height: 480, fps: 30, color_mode: rgb, fourcc: MJPG}
  }" \
  --teleop.type=so101_leader \
  --teleop.port="${LEADER_PORT}" \
  --teleop.id="${LEADER_ID}" \
  --dataset.repo_id="${HF_USER}/leftarm_v1" \
  --dataset.single_task="Pick up the doll and reach forward" \
  --dataset.num_episodes=10 \
  --dataset.fps=30 \
  --dataset.episode_time_s=60 \
  --dataset.reset_time_s=15 \
  --dataset.video=true \
  --dataset.vcodec=libsvtav1 \
  --dataset.streaming_encoding=true \
  --dataset.push_to_hub=true \
  --dataset.private=false \
  --dataset.tags='[smolvla, so101, leftarm, doll, hylion]' \
  --display_data=true \
  --play_sounds=true
```

### 5-2. 2~N 차 — resume (episodes 추가)

위 명령에 `--resume=true` + `--dataset.root` + `dataset.num_episodes` (**이번 세션에서 추가 기록할 새 episode 수**) 추가.

⚠️ **`--dataset.num_episodes` 의미** ([lerobot_record.py:597](../../docs/reference/lerobot/src/lerobot/scripts/lerobot_record.py#L597)): 누적 목표값 X, **이번 세션에서 새로 기록할 개수** O. 코드에서 `recorded_episodes = 0` 으로 매 세션 0부터 카운트하기 때문. 예: 기존 10개 + `num_episodes=30` 으로 resume → 30개 새로 기록 → **총 40개**. 매 차수마다 "이번 차수에 몇 개 추가" 만 적으면 됨 — 누적값 계산 불필요.

⚠️ **`--resume=true` 면 `--dataset.root` 명시 필수** ([lerobot_dataset.py:767-772](../../docs/reference/lerobot/src/lerobot/datasets/lerobot_dataset.py#L767-L772)). 신규 (create) 와 달리 resume 은 root 를 자동 추론하지 않음 — Hub snapshot cache 손상 방지 목적. 누락 시:

```
ValueError: resume() requires an explicit 'root' directory ...
```

| 차수 | `dataset.num_episodes` (추가 개수) | 끝나면 누적 | 추가 인자 |
|---|---|---|---|
| 1차 | `10` (테스트, fresh) | 10 | (resume 없음) |
| 2차 | `20` | 30 | `--resume=true --dataset.root="${HF_HOME}/lerobot/${HF_USER}/leftarm_v1"` |
| 3차 | `20` | 50 | `--resume=true --dataset.root=...` |
| 4차 | `20` | 70 | `--resume=true --dataset.root=...` |
| 5차 | `20` | 90 | `--resume=true --dataset.root=...` |
| 6차 | `10` | 100 | `--resume=true --dataset.root=...` (목표 도달) |

전체 명령 (resume 포함, 차수 진행 시 `--dataset.num_episodes` 값만 표대로 갱신):

```bash
lerobot-record \
  --robot.type=so101_follower \
  --robot.port="${FOLLOWER_PORT}" \
  --robot.id="${FOLLOWER_ID}" \
  --robot.cameras="{
    top: {type: opencv, index_or_path: ${CAMERA_TOP_INDEX}, width: 480, height: 640, fps: 30, color_mode: rgb, fourcc: MJPG, rotation: -90},
    wrist: {type: opencv, index_or_path: ${CAMERA_WRIST_INDEX}, width: 640, height: 480, fps: 30, color_mode: rgb, fourcc: MJPG}
  }" \
  --teleop.type=so101_leader \
  --teleop.port="${LEADER_PORT}" \
  --teleop.id="${LEADER_ID}" \
  --dataset.repo_id="${HF_USER}/leftarm_v1" \
  --dataset.single_task="Pick up the doll and reach forward" \
  --dataset.num_episodes=20 \
  --dataset.fps=30 \
  --dataset.episode_time_s=60 \
  --dataset.reset_time_s=15 \
  --dataset.video=true \
  --dataset.vcodec=libsvtav1 \
  --dataset.streaming_encoding=true \
  --dataset.push_to_hub=true \
  --dataset.private=false \
  --dataset.tags='[smolvla, so101, leftarm, doll, hylion]' \
  --display_data=true \
  --play_sounds=true \
  --resume=true \
  --dataset.root="${HF_HOME}/lerobot/${HF_USER}/leftarm_v1"
```

> 차수마다 바뀌는 값은 **`--dataset.num_episodes` 한 줄뿐** (이번 차수에 추가할 개수: `20 → 20 → 20 → 20 → 10`). 나머지 인자는 1차 (§5-1) 와 동일 유지 — instruction / fps / camera config / reset_time 등 일관성 필수.
>
> **주의 1**: `num_episodes` 는 "이번 세션에 새로 기록할 episode 수" (cumulative target 아님). 기존 episodes 가 몇 개든 무관하게 매 차수마다 0 부터 카운트하면서 `num_episodes` 도달 시 종료. `→` 키로 일찍 종료하거나 `←` 로 폐기하면 카운트 안 됨.
>
> **주의 2**: `--dataset.root` 경로는 1차 수집 후 `meta/info.json` 이 있는 경로. 본 환경 기본값은 `${HF_HOME}/lerobot/${HF_USER}/leftarm_v1/`.

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

### 5-5. 수집 결과 검증

수집·업로드 직후 episode 수 / frame 수 / 파일 무결성을 빠르게 확인.

#### 로컬 메타 (`meta/info.json`) 한 줄 요약

```bash
jq '{total_episodes, total_frames, total_tasks, fps, splits}' \
  /home/laba/smolvla/.hf_cache/lerobot/${HF_USER}/leftarm_v1/meta/info.json
```

예시 출력:
```json
{
  "total_episodes": 10,
  "total_frames": 14347,
  "total_tasks": 1,
  "fps": 30,
  "splits": { "train": "0:10" }
}
```

→ `total_frames / total_episodes / fps` 로 평균 episode 길이 계산: `14347 / 10 / 30 ≈ 47.8s`. `episode_time_s=60` 보다 짧으면 수동 종료 (`→` 키) 가 평균보다 빨랐다는 의미.

#### 로컬 파일 구조 확인 (video / parquet 누락 검출)

```bash
find /home/laba/smolvla/.hf_cache/lerobot/${HF_USER}/leftarm_v1/ -type f | \
  awk -F/ '{print $(NF-2)"/"$(NF-1)"/"$NF}' | sort
```

기대 출력 (10 episodes 기준):
```
data/chunk-000/file-000.parquet
meta/episodes/chunk-000/file-000.parquet
.../meta/info.json
.../meta/stats.json
.../meta/tasks.parquet
videos/observation.images.top/chunk-000/file-000.mp4
videos/observation.images.top/chunk-000/file-001.mp4
videos/observation.images.wrist/chunk-000/file-000.mp4
videos/observation.images.wrist/chunk-000/file-001.mp4
```

> chunk 별 mp4 분할 갯수 (`file-000`, `file-001`, …) 는 `video_files_size_in_mb=200` 임계값 도달 시마다 증가. 두 카메라 모두 동일 갯수여야 함.

#### HF Hub 업로드 확인

```bash
# Hub 메타 한 줄 요약 (created_at / last_modified / 파일 목록)
hf datasets info ${HF_USER}/leftarm_v1 2>&1 | \
  python -c "import sys, json; d=json.loads(sys.stdin.read()); \
    print(f\"private: {d['private']}\"); \
    print(f\"created: {d['created_at']}\"); \
    print(f\"modified: {d['last_modified']}\"); \
    print(f\"storage: {d['used_storage']/1024/1024:.1f} MB\"); \
    print(f\"files: {len(d['siblings'])}\"); \
    [print(f'  - {s[\"rfilename\"]}') for s in d['siblings']]"
```

#### 로컬 ↔ Hub 일치 검증 (episode 수)

```bash
# 로컬
echo -n "local : "
jq -r '.total_episodes' /home/laba/smolvla/.hf_cache/lerobot/${HF_USER}/leftarm_v1/meta/info.json

# Hub (info.json 의 일부가 description 안에 포함됨)
echo -n "hub   : "
hf datasets info ${HF_USER}/leftarm_v1 2>&1 | \
  python -c "import sys, json, re; d=json.loads(sys.stdin.read()); \
    m=re.search(r'\"total_episodes\":\s*(\d+)', d['description']); \
    print(m.group(1) if m else 'N/A')"
```

두 값이 같으면 업로드 OK. 다르면 Hub 가 stale (재푸시 필요) 또는 로컬이 손상.

#### Hub 페이지 직접 열기

```bash
xdg-open "https://huggingface.co/datasets/${HF_USER}/leftarm_v1" 2>/dev/null
# 또는 브라우저에 URL 복사:
echo "https://huggingface.co/datasets/${HF_USER}/leftarm_v1"
```

페이지에서 확인할 것:
- **Files and versions** 탭 → mp4 / parquet 다 있나
- **Dataset card** → `total_episodes`, `total_frames` 자동 렌더링
- **Tags** → `smolvla, so101, leftarm, doll, hylion` 포함

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
| `lerobot-record` import 실패 | venv 미활성 또는 lerobot[hardware] 미설치 → `bash ~/smolvla/dgx/scripts/setup_finetune_env.sh` 재실행 |
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
