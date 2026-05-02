# 15_datacollector_cli_flow.md

> 작성: 2026-05-01 | task-executor | TODO-D1 study cycle 1
> 목적: datacollector 노드 interactive_cli 의 flow 2~7 단계 구체 동작 정의.
>       D2 task 가 이 문서의 §1~§5 를 기반으로 env_check.py / teleop.py / data_kind.py /
>       record.py / transfer.py 를 구현한다.

---

## §1 flow 2 — 환경 체크 (datacollector 맞춤)

### 역할 및 책임 흡수

spec 라인 52, CLAUDE.md 04 BACKLOG #8 정리:
- 04 G3 (DataCollector check_hardware.sh 이식) 를 D2 의 `env_check.py` 가 흡수
- 04 G4 (DataCollector check_hardware prod) 를 D3 prod 가 흡수
- flow 2 는 `datacollector/interactive_cli/flows/env_check.py` 로 구현 (D2 담당)

### 체크 항목 (datacollector 환경 맞춤)

04 G1 `orin/tests/check_hardware.sh` 의 5단계 패턴을 datacollector 환경에 미러:

| 단계 | orin 원본 | datacollector 적용 |
|---|---|---|
| 1. venv | `.hylion_arm` venv 활성화 확인 | `.hylion_collector` venv 활성화 확인 |
| 2. USB/포트 | SO-ARM follower/leader 포트 체크 | SO-ARM follower (`/dev/ttyACM1`) + leader (`/dev/ttyACM0`) 포트 존재 확인 (run_teleoperate.sh 기본값) |
| 3. 카메라 | OpenCV 카메라 인덱스 확인 | OpenCV 카메라 인덱스 확인 (`lerobot-find-cameras` 패턴) |
| 4. lerobot 설치 | `lerobot` import 확인 | `lerobot` import 확인 (동일) |
| 5. 데이터 저장 경로 | cache yaml 체크 | `~/smolvla/datacollector/data/` 디렉터리 존재 + 쓰기 가능 확인 |

### env_check.py 동작 흐름

```
flow 2 시작
    ↓
venv 활성화 확인 (.hylion_collector)
    ↓
USB 포트 존재 확인 (/dev/ttyACM0, /dev/ttyACM1)
    ↓
카메라 인덱스 확인 (lerobot-find-cameras 또는 OpenCV index probe)
    ↓
lerobot import 확인
    ↓
데이터 저장 경로 확인 (~/smolvla/datacollector/data/)
    ↓
모두 통과 → flow 3 으로
체크 실패 → 실패 항목 출력 + 해결 방법 안내 + exit 1
```

### 레퍼런스 인용

- 04 G1 `orin/tests/check_hardware.sh` — venv 체크, 포트 체크, lerobot import 체크 패턴
- `datacollector/scripts/run_teleoperate.sh` line 19~20 — 기본 포트값 (`/dev/ttyACM1`, `/dev/ttyACM0`)
- `docs/storage/09_datacollector_setup.md §1-1` — DataCollector 의 책임 범위 (SO-ARM 직접 연결 + lerobot-record 실행)

---

## §2 flow 3·4 — 텔레오퍼레이션 + 사용자 확인

### flow 3 — 텔레오퍼레이션 진행

spec 라인 53: "텔레오퍼레이션을 진행하겠습니다 (이 작업이 끝나면 학습 준비가 완료됩니다)" 출력 + enter 시 실행

구현 파일: `datacollector/interactive_cli/flows/teleop.py`

동작:
1. 메시지 출력:
   ```
   [flow 3] 텔레오퍼레이션을 진행하겠습니다.
            이 작업이 끝나면 학습 준비가 완료됩니다.
   
   Enter 를 누르면 run_teleoperate.sh 가 실행됩니다.
   (종료하려면 Ctrl+C)
   ```
2. 사용자 Enter 확인
3. subprocess 로 `datacollector/scripts/run_teleoperate.sh all` 호출:
   ```python
   # teleop.py 의 subprocess 호출 패턴
   import subprocess
   from pathlib import Path
   
   def run_teleop(script_dir: Path) -> int:
       teleop_script = script_dir.parent.parent / "scripts" / "run_teleoperate.sh"
       result = subprocess.run(
           ["bash", str(teleop_script), "all"],
           check=False
       )
       return result.returncode
   ```
4. 스크립트 종료 후 flow 4 로 넘어감

### 레퍼런스 인용

`datacollector/scripts/run_teleoperate.sh` 의 `main()` 함수:
- `all` 커맨드: `calibrate_follower → calibrate_leader → teleoperate` 순서 (line 70~74)
- 포트 상수: `FOLLOWER_PORT="/dev/ttyACM1"`, `LEADER_PORT="/dev/ttyACM0"` (line 19~20)
- 선행 조건: `.hylion_collector` venv 활성화 상태 (line 9~11)

### flow 4 — 사용자 확인

spec 라인 54: "잘 작동하면 enter를 눌러주세요" 출력 + enter 입력

동작:
1. 텔레오퍼레이션이 정상 종료된 경우 (returncode == 0):
   ```
   [flow 4] 텔레오퍼레이션이 완료되었습니다.
   
   잘 작동했다면 Enter 를 눌러 데이터 수집 단계로 진행하세요.
   다시 실행하려면 'r' 을 입력하세요.
   ```
2. `r` 입력 시 flow 3 재실행
3. Enter 입력 시 flow 5 로 이동
4. 텔레오퍼레이션이 비정상 종료된 경우 (returncode != 0):
   - 에러 메시지 출력 + 재시도 옵션 안내 → flow 3 재실행 또는 종료 분기

---

## §3 flow 5 — 학습 종류 옵션 후보

### docs/lerobot_study/ 전체 Read 결과 요약

후보 도출을 위해 다음 파일들을 직접 Read:
- `04_lerobot_dataset_structure.md` — 카메라 키·state/action 차원·task instruction 형식
- `06_smolvla_finetune_feasibility.md` — 마일스톤별 학습 사이클 (`05_leftarmVLA` / `07_biarm_VLA`)
- `03b_smolvla_milestone_config_guide.md` — 마일스톤별 Config 분기 (S1/S3, 카메라 구성)
- `07b_smolvla_pretrain_dataset_structure.md` — 사전학습 데이터셋 (`svla_so100_pickplace`) 태스크 instruction 실측값
- `05_hf_model_selection.md` — 모델 선택 (smolvla_base 고정)

### 후보 도출 기준

1. `tokenizer_max_length=48` (configuration_smolvla.py:60 인용) — 48 토큰 이내 영문 자연어
2. 06_smolvla_finetune_feasibility.md §6.1 — 05_leftarmVLA 기준 단일팔 6 DOF 수집
3. `svla_so100_pickplace` 사전학습 태스크 — "Pick up the cube and place it in the box." (07b §1-5 실측값)
4. 03b §2 05 — 첫 사이클은 기본값 유지, 변수 최소화 권장

### 학습 종류 옵션 후보 (≤5개)

| # | 이름 | 설명 | task instruction (lerobot-record `--dataset.single_task`) | 에피소드 목표 |
|---|---|---|---|---|
| 1 | **단순 pick-place** | 책상 위 물체를 집어 지정 위치에 놓기 — SmolVLA 사전학습 분포에 가장 가까움 | `"Pick up the object and place it in the target area."` | 50 에피소드 |
| 2 | **push (밀기)** | 물체를 한 위치에서 다른 위치로 밀기 — 그리퍼 클로즈 없이 팔 움직임 위주 | `"Push the object to the target position."` | 30~50 에피소드 |
| 3 | **stack (쌓기)** | 블록을 다른 블록 위에 쌓기 — pick-place 보다 정밀도 요구 | `"Pick up the block and stack it on top of the other block."` | 50~100 에피소드 |
| 4 | **drawer open/close** | 서랍 열고 닫기 — 지속적 힘 인가 동작 | `"Open the drawer."` / `"Close the drawer."` | 30~50 에피소드 |
| 5 | **handover (물건 전달)** | 한 위치에서 집어 사람 손 방향으로 가져다 주기 | `"Pick up the object and hand it over."` | 30~50 에피소드 |

### 후보 선택 시 고려사항

- **후보 1 (단순 pick-place) 권장**: `svla_so100_pickplace` 사전학습 태스크와 동일 도메인 → 파인튜닝 효율 최대
- 카메라 수 (1~2대): `04_lerobot_dataset_structure.md §3` 의 `observation.images.wrist_left` + `observation.images.overview` 키 결정과 연동
- 에피소드 수: `smolvla.mdx` 공식 권장 ~50 에피소드 / variation (06_smolvla_finetune_feasibility.md §6.1 인용)

### awaits_user-A 발송 내용

```
datacollector interactive_cli 의 5단계 "어떤 학습 데이터를 모을건가요?" 옵션을 선택해주세요.

docs/lerobot_study/ 전체 Read 결과 다음 5개 후보를 도출했습니다:

(1) 단순 pick-place
    설명: 책상 위 물체를 집어 지정 위치에 놓기 (SmolVLA 사전학습 분포에 가장 가까움)
    task instruction: "Pick up the object and place it in the target area."
    lerobot-record 인자: --dataset.single_task="Pick up the object and place it in the target area."
    권장 에피소드: 50

(2) push (밀기)
    설명: 물체를 한 위치에서 다른 위치로 밀기 (그리퍼 클로즈 없이 팔 움직임 위주)
    task instruction: "Push the object to the target position."
    lerobot-record 인자: --dataset.single_task="Push the object to the target position."
    권장 에피소드: 30~50

(3) stack (쌓기)
    설명: 블록을 다른 블록 위에 쌓기 (정밀도 요구)
    task instruction: "Pick up the block and stack it on top of the other block."
    lerobot-record 인자: --dataset.single_task="Pick up the block and stack it on top of the other block."
    권장 에피소드: 50~100

(4) drawer open/close
    설명: 서랍 열고 닫기 (지속적 힘 인가 동작)
    task instruction: "Open the drawer." (또는 "Close the drawer.")
    lerobot-record 인자: --dataset.single_task="Open the drawer."
    권장 에피소드: 30~50

(5) handover (물건 전달)
    설명: 물체를 집어 사람 손 방향으로 가져다 주기
    task instruction: "Pick up the object and hand it over."
    lerobot-record 인자: --dataset.single_task="Pick up the object and hand it over."
    권장 에피소드: 30~50

사용자 결정 사항: 위 중 어떤 옵션을 채택? (복수 선택 또는 다른 후보 제안 가능)

영향: D2 의 data_kind.py 분기 + record.py 의 draccus 인자 동적 생성 로직 결정
```

---

## §4 flow 6 — lerobot-record draccus 인자 매핑

### lerobot_record.py 인자 시그니처 직접 인용

`docs/reference/lerobot/src/lerobot/scripts/lerobot_record.py` 에서 직접 Read 한 dataclass 시그니처:

**DatasetRecordConfig** (line 161~211):
```python
@dataclass
class DatasetRecordConfig:
    repo_id: str                           # line 163 — 필수 (예: "myuser/my_dataset")
    single_task: str                       # line 165 — 필수 (자연어 태스크 설명)
    root: str | Path | None = None         # line 167 — 로컬 저장 경로 (None → $HF_LEROBOT_HOME/repo_id)
    fps: int = 30                          # line 169 — 기본 30fps
    episode_time_s: int | float = 60       # line 171 — 에피소드 당 녹화 시간 (초)
    reset_time_s: int | float = 60         # line 173 — 에피소드 간 리셋 시간 (초)
    num_episodes: int = 50                 # line 175 — 수집할 에피소드 수
    video: bool = True                     # line 177 — 비디오 인코딩
    push_to_hub: bool = True               # line 179 — HF Hub 자동 업로드 (interactive_cli 에서는 False 권장)
    private: bool = False                  # line 181 — private repo 여부
    streaming_encoding: bool = False       # line 202
    encoder_threads: int | None = None     # line 208
    vcodec: str = "libsvtav1"              # line 199
```

**RecordConfig** (line 217~258):
```python
@dataclass
class RecordConfig:
    robot: RobotConfig                     # line 219 — 필수 (--robot.type 등)
    dataset: DatasetRecordConfig           # line 220 — 필수
    teleop: TeleoperatorConfig | None = None   # line 222
    display_data: bool = False             # line 226
    resume: bool = False                   # line 234
```

### lerobot-record CLI 예시 (lerobot_record.py line 22~41)

```bash
lerobot-record \
    --robot.type=so100_follower \
    --robot.port=/dev/tty.usbmodem58760431541 \
    --robot.cameras="{laptop: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}}" \
    --robot.id=black \
    --dataset.repo_id=<my_username>/<my_dataset_name> \
    --dataset.num_episodes=2 \
    --dataset.single_task="Grab the cube" \
    --dataset.streaming_encoding=true \
    --dataset.encoder_threads=2 \
    --display_data=true
```

### 5단계 답 → 동적 인자 생성 매핑

사용자 미응답 시 **후보 1 (단순 pick-place)** 가정.

#### 고정 인자 (모든 옵션 공통)

| 인자 | 값 | 결정 근거 |
|---|---|---|
| `--robot.type` | `so101_follower` | `run_teleoperate.sh` line 29 (`so101_follower`) |
| `--robot.port` | `/dev/ttyACM1` | `run_teleoperate.sh` line 19 (`FOLLOWER_PORT`) |
| `--robot.id` | `my_awesome_follower_arm` | `run_teleoperate.sh` line 21 (`FOLLOWER_ID`) |
| `--teleop.type` | `so101_leader` | `run_teleoperate.sh` line 35 (`so101_leader`) |
| `--teleop.port` | `/dev/ttyACM0` | `run_teleoperate.sh` line 20 (`LEADER_PORT`) |
| `--teleop.id` | `my_awesome_leader_arm` | `run_teleoperate.sh` line 22 (`LEADER_ID`) |
| `--dataset.push_to_hub` | `false` | interactive_cli 에서 전송은 flow 7 에서 별도 처리 |
| `--dataset.root` | `~/smolvla/datacollector/data/<repo_id>/` | `09_datacollector_setup.md` 의 DataCollector 데이터 경로 |
| `--dataset.streaming_encoding` | `true` | 실시간 인코딩 (저장 시간 단축) |
| `--dataset.encoder_threads` | `2` | `lerobot_record.py` line 33 기본 예시 |
| `--dataset.fps` | `30` | `DatasetRecordConfig.fps` 기본값 + `07b §1-2` fps=30 실측 |

#### 카메라 인자 (datacollector 환경 맞춤)

`04_lerobot_dataset_structure.md §3` 의 카메라 키 명명 규칙:
- `observation.images.<camera_name>` — prefix 고정, 이름 자유
- 본 프로젝트 권장 (05_leftarmVLA 기준): `wrist_left` + `overview` (2대)

```
--robot.cameras="{wrist_left: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}, overview: {type: opencv, index_or_path: 1, width: 640, height: 480, fps: 30}}"
```

#### 사용자 입력 필수 인자

| 인자 | 사용자 입력 단계 | 설명 |
|---|---|---|
| `--dataset.repo_id` | flow 6 진입 시 질문 | HF Hub ID (예: `myuser/my_dataset_name`). 로컬 저장 경로에도 사용 |
| `--dataset.num_episodes` | flow 6 진입 시 질문 | 수집할 에피소드 수 (기본 50, 후보별 권장값 안내) |
| `--dataset.single_task` | flow 5 답 기반 자동 설정 | 5단계에서 선택한 옵션의 task instruction 자동 매핑 |

#### 5단계 답 → `--dataset.single_task` 매핑 표

| 선택 # | 옵션 이름 | `--dataset.single_task` 값 |
|---|---|---|
| 1 | 단순 pick-place | `"Pick up the object and place it in the target area."` |
| 2 | push (밀기) | `"Push the object to the target position."` |
| 3 | stack (쌓기) | `"Pick up the block and stack it on top of the other block."` |
| 4 | drawer open/close | `"Open the drawer."` |
| 5 | handover (물건 전달) | `"Pick up the object and hand it over."` |

#### record.py 동적 생성 전체 인자 조합 예시 (후보 1 기준)

```python
# record.py 의 lerobot-record 인자 동적 생성 (후보 1 가정)
def build_record_args(
    data_kind_choice: int,          # flow 5 선택 번호 (1~5)
    repo_id: str,                   # 사용자 입력 (예: "myuser/leftarm_pickplace_v1")
    num_episodes: int,              # 사용자 입력 (기본 50)
    cam_wrist_left_index: int = 0,  # flow 2 env_check 결과로 확정
    cam_overview_index: int = 1,    # flow 2 env_check 결과로 확정
) -> list[str]:
    SINGLE_TASK_MAP = {
        1: "Pick up the object and place it in the target area.",
        2: "Push the object to the target position.",
        3: "Pick up the block and stack it on top of the other block.",
        4: "Open the drawer.",
        5: "Pick up the object and hand it over.",
    }
    cameras_str = (
        f"{{wrist_left: {{type: opencv, index_or_path: {cam_wrist_left_index},"
        f" width: 640, height: 480, fps: 30}},"
        f" overview: {{type: opencv, index_or_path: {cam_overview_index},"
        f" width: 640, height: 480, fps: 30}}}}"
    )
    data_root = os.path.expanduser(f"~/smolvla/datacollector/data/{repo_id.split('/')[-1]}")

    return [
        "lerobot-record",
        "--robot.type=so101_follower",
        "--robot.port=/dev/ttyACM1",
        "--robot.id=my_awesome_follower_arm",
        f"--robot.cameras={cameras_str}",
        "--teleop.type=so101_leader",
        "--teleop.port=/dev/ttyACM0",
        "--teleop.id=my_awesome_leader_arm",
        f"--dataset.repo_id={repo_id}",
        f"--dataset.root={data_root}",
        f"--dataset.num_episodes={num_episodes}",
        f"--dataset.single_task={SINGLE_TASK_MAP[data_kind_choice]}",
        "--dataset.push_to_hub=false",
        "--dataset.streaming_encoding=true",
        "--dataset.encoder_threads=2",
        "--dataset.fps=30",
        "--display_data=false",
    ]
```

### validation 항목 (D2 구현 시 필수)

`lerobot_record.py` line 212~214:
```python
def __post_init__(self):
    if self.single_task is None:
        raise ValueError("You need to provide a task as argument in `single_task`.")
```

D2 의 `record.py` 는 subprocess 호출 전 다음 validation 을 추가해야 함:
1. `repo_id` 형식 확인 — `<user>/<name>` 형식 (`push_dataset_hub.sh` line 90~94 의 grep 패턴 재사용)
2. `num_episodes` 양수 정수 확인
3. `data_kind_choice` 유효 범위 확인 (1~5)
4. 카메라 인덱스가 flow 2 env_check 결과와 일치하는지 확인

---

## §5 flow 7 — 전송 방식 선택 분기

### spec 라인 60~63

```
7. "[저장경로]에 저장되었습니다" 출력 + 전송 방식 사용자 선택 (HF Hub / rsync DGX / 안함)
   → HF Hub 선택 시 04 T1 datacollector/scripts/push_dataset_hub.sh 호출
   → rsync 선택 시 04 T1 scripts/sync_dataset_collector_to_dgx.sh 호출
   → 안함 선택 시 로컬 저장 (datacollector/data/<dataset>/) 만 유지
```

### transfer.py 동작 흐름

```
flow 6 완료 → 저장 경로 출력
    ↓
[flow 7] 전송 방식을 선택해주세요:
  (1) HF Hub 업로드 (인터넷 필요, --private 옵션 가능)
  (2) rsync → DGX (devPC 경유 2-hop, devPC 에서 실행해야 함)
  (3) 안함 (로컬 저장만 유지)
    ↓
사용자 선택 → 각 분기 실행
```

### 분기 1 — HF Hub 업로드

`datacollector/scripts/push_dataset_hub.sh` 직접 호출.

```python
# transfer.py 의 HF Hub 분기
def transfer_to_hub(
    script_dir: Path,
    local_dataset_path: str,
    repo_id: str,
    private: bool = False,
) -> int:
    push_script = script_dir.parent.parent / "scripts" / "push_dataset_hub.sh"
    cmd = ["bash", str(push_script),
           "--dataset", local_dataset_path,
           "--repo-id", repo_id]
    if private:
        cmd.append("--private")
    result = subprocess.run(cmd, check=False)
    return result.returncode
```

`push_dataset_hub.sh` 필수 조건 (line 104~117):
- `HF_TOKEN` 환경변수 설정 또는 `huggingface-cli login` 사전 완료
- flow 7 진입 전 HF Token 환경변수 유무 확인 후 없으면 안내 메시지 출력

### 분기 2 — rsync DGX

**중요**: `sync_dataset_collector_to_dgx.sh` 는 **devPC 에서 실행** 하는 스크립트 (line 6: "실행 위치: devPC (어디서든)"). datacollector 머신에서 직접 호출 X.

`scripts/sync_dataset_collector_to_dgx.sh` 의 동작:
- DataCollector (시연장) → devPC 임시 디렉터리 rsync (line 117~123)
- devPC → DGX rsync (line 126~136)
- DGX 측 파일 수 검증 (line 139~148)
- SSH alias 필요: `~/.ssh/config` 에 `Host datacollector` + `Host dgx` 등록 (line 67~77)

따라서 flow 7 에서 rsync 선택 시 동작:
1. datacollector 터미널에서는 직접 실행 X
2. 사용자에게 devPC 에서 아래 명령 실행 안내:
   ```
   bash smolVLA/scripts/sync_dataset_collector_to_dgx.sh --dataset <repo_id_suffix>
   ```
3. 안내 출력 후 대기 (선택적) 또는 즉시 종료

```python
# transfer.py 의 rsync 분기 — 직접 실행 X, devPC 명령 안내
def guide_rsync_to_dgx(repo_id: str) -> None:
    dataset_name = repo_id.split("/")[-1]
    print()
    print("[flow 7] rsync DGX 전송 안내")
    print("  sync_dataset_collector_to_dgx.sh 는 devPC 에서 실행해야 합니다.")
    print()
    print("  devPC 터미널에서 아래 명령을 실행하세요:")
    print(f"    bash smolVLA/scripts/sync_dataset_collector_to_dgx.sh --dataset {dataset_name}")
    print()
    print("  필요 조건: ~/.ssh/config 에 'Host datacollector' + 'Host dgx' 등록")
    print("  (docs/storage/04_devnetwork.md §5 (구 09_datacollector_setup.md §5-1, 삭제됨) 참조)")
```

### 분기 3 — 안함 (로컬 저장 유지)

```python
def keep_local(local_dataset_path: str) -> None:
    print()
    print(f"[flow 7] 로컬 저장 유지: {local_dataset_path}")
    print("  나중에 전송하려면:")
    print(f"  HF Hub:  bash datacollector/scripts/push_dataset_hub.sh --dataset {local_dataset_path} --repo-id <USER>/<NAME>")
    print(f"  rsync:   (devPC 에서) bash smolVLA/scripts/sync_dataset_collector_to_dgx.sh --dataset <NAME>")
```

### transfer.py 통합 흐름 코드 개요

```python
def flow7_select_transfer(
    script_dir: Path,
    local_dataset_path: str,
    repo_id: str,
) -> None:
    """flow 7: 전송 방식 선택."""
    dataset_name = repo_id.split("/")[-1]
    print()
    print(f"[flow 7] 데이터셋이 저장되었습니다: {local_dataset_path}")
    print()
    print("전송 방식을 선택해주세요:")
    print("  (1) HF Hub 업로드 (인터넷 필요)")
    print("  (2) rsync → DGX (devPC 에서 실행 안내)")
    print("  (3) 안함 (로컬 저장 유지)")
    print()

    while True:
        raw = input("번호 선택 [1~3]: ").strip()
        if raw == "1":
            private = input("private repo 로 업로드? [y/N]: ").strip().lower() in ("y", "yes")
            returncode = transfer_to_hub(script_dir, local_dataset_path, repo_id, private)
            if returncode == 0:
                print(f"[flow 7] HF Hub 업로드 완료: https://huggingface.co/datasets/{repo_id}")
            else:
                print(f"[flow 7] HF Hub 업로드 실패 (returncode={returncode}). 나중에 재시도 안내:")
                print(f"  bash datacollector/scripts/push_dataset_hub.sh --dataset {local_dataset_path} --repo-id {repo_id}")
            break
        elif raw == "2":
            guide_rsync_to_dgx(repo_id)
            break
        elif raw == "3":
            keep_local(local_dataset_path)
            break
        else:
            print("  1, 2, 3 중 하나를 입력하세요.")
```

---

## 설계 결정 요약

| 항목 | 결정 | 근거 |
|---|---|---|
| flow 2 체크 항목 | venv + USB 포트 + 카메라 + lerobot + 데이터 저장 경로 | 04 G1 패턴 미러 (datacollector 맞춤 5단계) |
| flow 3 teleop 호출 | `run_teleoperate.sh all` subprocess | `run_teleoperate.sh` line 70~74 |
| flow 4 재시도 | `r` 입력 시 flow 3 재실행 | UX 결정 (텔레오퍼레이션 실패 복구) |
| flow 5 옵션 수 | 5개 이하 강제 | spec 라인 239 (CLI UX 복잡도 제한) |
| flow 5 후보 1 권장 | 단순 pick-place | `svla_so100_pickplace` 사전학습 분포 최근접 |
| flow 6 push_to_hub | `false` | flow 7 에서 별도 선택 (이중 업로드 방지) |
| flow 6 streaming_encoding | `true` | lerobot_record.py line 33 예시 + 저장 시간 단축 |
| flow 6 validation | subprocess 전 4항목 체크 | D2 구현 시 lerobot-record 실패 방지 |
| flow 7 rsync | devPC 명령 안내 (직접 실행 X) | `sync_dataset_collector_to_dgx.sh` line 6 실행 위치 명시 |
| task instruction | 영문 50자 이내 | `tokenizer_max_length=48` (configuration_smolvla.py:60) |

---

## SKILL_GAP 보고

본 todo 범위 내 SKILL_GAP 없음.

- flow 2~4 패턴: 04 G1 `check_hardware.sh` + `run_teleoperate.sh` 레퍼런스 있음
- flow 5 옵션: `lerobot_study/` 전체 Read + `svla_so100_pickplace` 태스크 인용
- flow 6 draccus 인자: `lerobot_record.py` `DatasetRecordConfig` / `RecordConfig` dataclass 직접 Read + 인용
- flow 7 스크립트: `push_dataset_hub.sh` + `sync_dataset_collector_to_dgx.sh` 직접 Read + 인용
