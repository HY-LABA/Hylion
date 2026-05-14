# 14_dgx_cli_flow.md

> 작성: 2026-05-01 | task-executor | TODO-X1 study cycle 1 (05 spec 학습 flow 원안)
> 갱신: 2026-05-02 | task-executor | TODO-X1 study cycle 1 (06 spec — 학습+수집 통합)
> 목적: dgx/interactive_cli/ 의 통합 flow 설계 입력.
>       X2 task 는 본 문서의 §1~§5 결정(사용자 결정 G·H 후)대로 구현한다.

---

## §1 flow 2 환경 체크 — 학습·수집 통합

### 1-1) 위치

flow 0·1 (entry.py boilerplate) 이후 `env_check.py` 가 담당.
DGX 가 학습 + 수집 두 책임을 모두 흡수하므로 flow 2 는 두 환경을 통합 체크.

### 1-2) 학습 환경 체크 (기존 — 05 TODO-X1 확정)

`dgx/scripts/preflight_check.sh` 기반 5단계:

| # | 체크 | FAIL 조건 |
|---|---|---|
| 1 | venv / 환경변수 격리 | VIRTUAL_ENV 미일치 또는 HF_HOME 미설정 또는 CUDA_VISIBLE_DEVICES != "0" |
| 2 | 메모리 가용성 | MemAvailable < REQUIRED_GB + 10 GiB 안전 마진 |
| 3 | Walking RL 프로세스 | 관찰만, kill 절대 금지 (FAIL 아님 — INFO 출력) |
| 4 | Ollama GPU 점유 | nvidia-smi 에 ollama 프로세스 있으면 FAIL |
| 5 | 디스크 가용량 | /home/laba 가용 < 50 GiB |

`preflight_check.sh` 인용 (line 22~32):
```bash
# 사용:
#   bash preflight_check.sh smoke   # 1 step 검증용 (필요 메모리 20 GB)
#   bash preflight_check.sh s1      # 04 / 06 1차 학습 (35 GB)
#   bash preflight_check.sh s3      # 06 2차 학습 — VLM 까지 풀 학습 (65 GB)
#   bash preflight_check.sh lora    # LoRA fallback (28 GB)
```

### 1-3) 수집 환경 체크 (신규 — 06 TODO-X1 추가)

수집 mode 진입 전 추가로 확인할 항목:

| # | 체크 | 대응 |
|---|---|---|
| 6 | USB 포트 존재 | `/dev/ttyACM0` (leader), `/dev/ttyACM1` (follower) 존재 확인 |
| 7 | dialout 그룹 | `groups` 명령으로 현재 사용자의 dialout 멤버십 확인 |
| 8 | v4l2 카메라 | `/dev/video*` 디바이스 존재 + OpenCV 인덱스 probe |
| 9 | SO-ARM 포트 응답 | `lerobot-find-port` 비대화형 호출 또는 pyserial serial.Serial 임시 open 검증 |

비고:
- 체크 항목 6~9는 수집 mode 선택 후 진입 시에만 실행 (학습 mode 선택 시 skip).
- env_check.py 는 mode 인자 (`"collect"` / `"train"`) 를 받아 해당 체크만 실행.
- 패턴 기반: `docs/storage/legacy/02_datacollector_separate_node/docs_storage_15_datacollector_cli_flow.md §1` 의 datacollector env_check 5단계 미러 (venv→항목1·2 대신 6~9로 대체).

### 1-4) env_check.py 구현 패턴 (X2 입력)

```python
# dgx/interactive_cli/flows/env_check.py — X2 구현 시 참고
import subprocess, sys
from pathlib import Path

def flow2_env_check(script_dir: Path, scenario: str = "smoke", mode: str = "train") -> bool:
    """preflight_check.sh 호출 (학습 공통) + 수집 추가 체크 (mode="collect" 시).

    Args:
        script_dir: interactive_cli/ 디렉터리 경로
        scenario:   "smoke"|"s1"|"s3"|"lora" (학습 시나리오)
        mode:       "train"|"collect" — 수집 mode 시 USB·카메라·SO-ARM 추가 체크

    Returns:
        True: PASS / False: FAIL
    """
    preflight = script_dir.parent / "scripts" / "preflight_check.sh"
    result = subprocess.run(["bash", str(preflight), scenario], check=False)
    if result.returncode != 0:
        return False

    if mode == "collect":
        return _check_hardware_collect()
    return True


def _check_hardware_collect() -> bool:
    """수집 환경 하드웨어 체크 (항목 6~9).
    datacollector env_check.py §1 미러 (dgx 경로 맞춤).
    """
    ...  # X2 구현 — USB 포트, dialout, v4l2, SO-ARM 포트 체크
```

---

## §2 flow 3 mode 분기 — 사용자 결정 G 대상

### 2-1) 배경

06 spec 결정 C: 단일 진입점 `bash dgx/interactive_cli/main.sh` + flow 3 단계에서
*수집 / 학습 / 종료* mode 질문 분기 (옵션 α).

flow 2 (env_check) 완료 후 사용자에게 mode 선택 메뉴를 제시.

### 2-2) 후보 G-1 — 단발 종료 (한 mode 진행 후 CLI 종료)

```
[flow 3] 무엇을 하겠습니까?
  (1) 데이터 수집 → flow 4~7 (teleop → record → transfer)
  (2) 학습        → flow 3~5 (시나리오 선택 → 데이터셋 → 학습+ckpt)
  (3) 종료
```

mode.py 구조 (단발):
```python
def flow3_select_mode() -> str | None:
    """단발 종료 — 한 mode 실행 후 리턴."""
    # 선택 → mode 실행 → return
    # 재진입 루프 없음
    ...
```

특징:
- 구현 단순. 수집 후 학습하려면 CLI 재시작 필요.
- UX: 초보자에게 명확 (한 번에 한 가지 일)
- 제약: 수집→학습 연속 흐름을 한 세션에서 달성 불가

### 2-3) 후보 G-2 — 재진입 루프 (mode 완료 후 메뉴 재출력)

```
[flow 3] 무엇을 하겠습니까?
  (1) 데이터 수집
  (2) 학습
  (3) 종료
```

mode 완료 후 다시 flow 3 메뉴로 돌아옴. `(3) 종료` 선택 시 CLI 종료.

mode.py 구조 (루프):
```python
def flow3_mode_loop(script_dir: Path) -> int:
    """재진입 루프 — mode 완료 후 메뉴 재출력."""
    while True:
        mode = _ask_mode()          # (1)/(2)/(3)
        if mode is None or mode == "exit":
            return 0
        if mode == "collect":
            _run_collect_flow(script_dir)   # flow 4~7
        elif mode == "train":
            _run_train_flow(script_dir)     # flow 3~5 (기존 training.py 흐름)
        # 완료 후 루프 재진입
```

특징:
- 수집 후 학습, 학습 후 다시 수집 — 한 세션에서 가능
- UX: 세션 유지 편리. 단, 각 mode 진입 시 env_check 재실행 여부 결정 필요
- 구현 복잡도: 중간 (루프 상태 관리 + 오류 시 재진입 보장)

### 2-4) 후보 G-3 — 수집→학습 직렬 옵션 추가

```
[flow 3] 무엇을 하겠습니까?
  (1) 데이터 수집 후 바로 학습 (수집→학습 직렬 실행)
  (2) 데이터 수집만
  (3) 학습만
  (4) 종료
```

mode.py 구조:
```python
def flow3_select_mode() -> str | None:
    """4 옵션 단발 — (1) collect_then_train, (2) collect, (3) train, (4) exit."""
    ...

def run_collect_then_train(script_dir: Path) -> int:
    """수집 완료 후 자동으로 학습 flow 진입."""
    rc = run_collect_flow(script_dir)
    if rc == 0:
        print("[mode] 수집 완료 → 학습 flow 자동 진입")
        return run_train_flow(script_dir)
    return rc
```

특징:
- 수집→학습 자연 흐름 옵션 추가 (시연장에서 수집 직후 학습까지 원클릭)
- UX: 파워 유저 대상. 초보자에게 복잡할 수 있음
- 제약: 수집 데이터셋이 곧바로 학습 데이터셋으로 연결되는 자동 전달 로직 필요

### 2-5) mode.py 코드 구조 비교

| 항목 | G-1 단발 | G-2 루프 | G-3 직렬 옵션 |
|---|---|---|---|
| 메뉴 항목 수 | 3 | 3 | 4 |
| 수집→학습 연속 | 불가 (재시작) | 가능 (루프) | 가능 (직렬 옵션) |
| mode.py 복잡도 | 낮음 | 중간 | 중간 |
| env_check 재실행 | 불필요 | 필요 고려 | 필요 고려 |
| 권장 사용자 | 초보자 | 일반 | 파워 유저 |
| X2 구현 복잡도 | 낮음 | 중간 | 중간 |

**trade-off 요약**:
- G-1: 가장 단순·명확. 수집→학습 연속은 CLI 재시작. DataCollector 단독 운영 시 패턴과 동일
- G-2: 한 세션에서 mode 전환 가능. 루프 상태 관리 필요. 시연장 운영 시 편리
- G-3: 수집→학습 원클릭 + 분리 옵션 병존. 옵션 수 증가. 직렬 흐름 자동화 경로 확보

---

## §3 수집 mode flow 3·4·5·6·7 — datacollector 이식

### 3-1) 전체 흐름 (datacollector flow 2~7 이식)

mode = "수집" 선택 시 진입. 수집 환경 체크 (§1 항목 6~9) 후:

```
[수집 mode]
flow 3(수집): 텔레오퍼레이션 실행 (teleop.py)
    ↓
flow 4(수집): 텔레오퍼레이션 완료 확인 (teleop.py 내 flow4_confirm_teleop)
    ↓
flow 5(수집): 학습 종류 선택 (data_kind.py)
    ↓
flow 6(수집): lerobot-record 실행 (record.py)
    ↓
flow 7(수집): 전송 방식 선택 (transfer.py — H 결정 적용)
```

### 3-2) teleop.py 이식 변경 사항

원본: `legacy/02_datacollector_separate_node/datacollector/interactive_cli/flows/teleop.py`

이식 시 변경 필요 항목:

| 항목 | datacollector 원본 | dgx 이식 후 |
|---|---|---|
| scripts/ 경로 | `script_dir.parent.parent / "scripts" / "run_teleoperate.sh"` | 동일 패턴 유지 (dgx/scripts/ 로 경로 자동 해석) |
| venv 전제 | `.hylion_collector` | `.arm_finetune` (main.sh 에서 이미 activate) |
| 스크립트 존재 | `datacollector/scripts/run_teleoperate.sh` | `dgx/scripts/run_teleoperate.sh` (X3 이식 대상) |
| flow 번호 표기 | flow 3, flow 4 | mode 분기 후 수집 flow 번호 (G 결정에 따라 재번호 가능) |

`teleop.py` 핵심 함수 시그니처 (그대로 재사용):
```python
def flow3_teleoperate(script_dir: Path) -> int: ...
def flow4_confirm_teleop(script_dir: Path, prev_returncode: int) -> bool: ...
```

### 3-3) data_kind.py 이식 변경 사항

원본: `legacy/02_datacollector_separate_node/datacollector/interactive_cli/flows/data_kind.py`

`DATA_KIND_OPTIONS` 딕셔너리 (5개 옵션) 그대로 재사용 가능:
```python
# data_kind.py line 31~72: DATA_KIND_OPTIONS — 변경 불필요
DATA_KIND_OPTIONS: dict[int, dict] = {
    1: {"name": "단순 pick-place", "single_task": "Pick up the object and place it in the target area.", ...},
    2: {"name": "push (밀기)", ...},
    3: {"name": "stack (쌓기)", ...},
    4: {"name": "drawer open/close", ...},
    5: {"name": "handover (물건 전달)", ...},
}
```

`DataKindResult` NamedTuple 및 `flow5_select_data_kind()` 함수 그대로 재사용.
변경 항목: 없음 (데이터 종류 상수·로직 독립적).

### 3-4) record.py 이식 변경 사항

원본: `legacy/02_datacollector_separate_node/datacollector/interactive_cli/flows/record.py`

| 항목 | datacollector 원본 | dgx 이식 후 |
|---|---|---|
| `data_root` 경로 | `~/smolvla/datacollector/data/<dataset_name>` (line 194) | `~/smolvla/dgx/data/<dataset_name>` |
| `run_teleoperate.sh` 포트 상수 | `FOLLOWER_PORT="/dev/ttyACM1"`, `LEADER_PORT="/dev/ttyACM0"` (그대로) | 동일 |
| `ROBOT_TYPE` / `TELEOP_TYPE` | `"so101_follower"` / `"so101_leader"` (그대로) | 동일 |
| draccus 인자 | `lerobot_record.py DatasetRecordConfig` 기반 (그대로) | 동일 |

레퍼런스 직접 인용 (record.py line 157~216 `build_record_args` 패턴 그대로):
```python
def build_record_args(
    data_kind_choice: int,
    repo_id: str,
    num_episodes: int,
    cam_wrist_left_index: int = 0,
    cam_overview_index: int = 1,
) -> list[str]:
    ...
    data_root = os.path.expanduser(f"~/smolvla/dgx/data/{dataset_name}")  # 경로 변경
    ...
```

`lerobot-record` draccus 인자 고정 부분 (레퍼런스 인용 — `docs_storage_15_datacollector_cli_flow.md §4` 확정값):

| 인자 | 값 | 근거 |
|---|---|---|
| `--robot.type` | `so101_follower` | run_teleoperate.sh line 29 |
| `--robot.port` | `/dev/ttyACM1` | run_teleoperate.sh line 19 (FOLLOWER_PORT) |
| `--robot.id` | `my_awesome_follower_arm` | run_teleoperate.sh line 21 |
| `--teleop.type` | `so101_leader` | run_teleoperate.sh line 35 |
| `--teleop.port` | `/dev/ttyACM0` | run_teleoperate.sh line 20 (LEADER_PORT) |
| `--teleop.id` | `my_awesome_leader_arm` | run_teleoperate.sh line 22 |
| `--dataset.push_to_hub` | `false` | flow 7 에서 별도 처리 |
| `--dataset.streaming_encoding` | `true` | lerobot_record.py line 33 예시 |
| `--dataset.encoder_threads` | `2` | lerobot_record.py line 33 예시 |
| `--dataset.fps` | `30` | DatasetRecordConfig.fps 기본값 |
| `--robot.cameras` | `{wrist_left: ..., overview: ...}` + `fourcc: MJPG` | USB 2.0 대역 절약 (record.py line 183~189 주석) |

### 3-5) flow 7 전송 분기 (H 결정 대상 — §5 참조)

transfer.py 의 3분기 메뉴가 H 결정에 따라 재정의됨. 상세는 §5.

---

## §4 학습 mode flow 3~ — 기존 training.py 흐름 그대로

### 4-1) 개요

mode = "학습" 선택 시 진입. 05 TODO-X1 에서 결정한 옵션 C 3단계 구조 그대로:

```
[학습 mode]
flow 3(학습): preflight 재확인 + 시나리오 선택 (smoke/s1/s3/lora)
    ↓
flow 4(학습): 데이터셋 선택 (HF Hub repo_id / 로컬 dgx/datasets/ / 기본값)
    ↓
flow 5(학습): 학습 실행 + ckpt 관리 통합
              smoke 선택 시 → smoke_test.sh (동의 게이트 포함)
              실 학습 선택 시 → lerobot-train draccus 인자 동적 생성
              ckpt 전송: 케이스 목록 출력 + 사용자 선택
```

### 4-2) 학습 ckpt 관리 (기존 §5 보존)

`save_dummy_checkpoint.sh` line 25 인용:
```bash
OUTPUT_DIR="${DGX_DIR}/outputs/train/${RUN_NAME}"
# 체크포인트: ${OUTPUT_DIR}/checkpoints/000001/pretrained_model/
#   - config.json, train_config.json, model.safetensors (~900 MB)
```

ckpt 전송 케이스 안내 (training.py 의 CKPT_CASES 그대로):
- 케이스 1·2: Orin 과 동일 네트워크 / devPC 2-hop → `sync_ckpt_dgx_to_orin.sh`
- 케이스 3: 시연장 Orin 인터넷 격리 → `sync_ckpt_dgx_to_datacollector.sh` (DataCollector 경유)
- 케이스 4: USB 드라이브

interactive_cli (DGX 프로세스) 는 rsync 직접 실행 X → devPC 에서 실행할 명령 안내만.

---

## §5 flow 7 전송 분기 — 사용자 결정 H 대상

### 5-1) 배경

datacollector 원본 transfer.py 의 3분기:
```
(1) HF Hub 업로드
(2) rsync → DGX  ← DGX 가 자기 자신 → 무의미
(3) 안함 (로컬 저장)
```

DGX 가 DataCollector 역할을 흡수하면 "(2) rsync → DGX" 는 자기 자신에게 전송하는 옵션이 되어 무의미. 옵션 재정의 필요.

### 5-2) 후보 H-1 — 기존 그대로 보존

```
(1) HF Hub 업로드
(2) rsync DGX (자기 자신 → 무의미하나 삭제 X 보존)
(3) 안함 (로컬 저장 유지)
```

transfer.py 구조: `transfer.py` 원본 그대로. `_guide_rsync_to_dgx()` 함수를 경고 메시지만 변경:
```python
def _guide_rsync_to_dgx_self(repo_id: str) -> None:
    """H-1: 자기 자신 rsync → 무의미 경고 안내."""
    print("[flow 7] 참고: DGX 가 수집 노드이므로 'rsync DGX' 는 현재 머신에 이미 저장됨.")
    print("  로컬 저장 경로를 확인하세요.")
```

trade-off: 코드 변경 최소. 단, UX 혼란 (무의미 옵션 노출).

### 5-3) 후보 H-2 — 옵션 재정의 (spec 권고)

06 spec `사용자 결정 H` 항목 직접 인용:
> "기존 (HF Hub / rsync DGX / 안함) → 신규 (HF Hub / 로컬 dgx 보관 / Orin rsync)"

```
(1) HF Hub 업로드
(2) 로컬 DGX 보관 (dgx/data/<dataset>/ 에 저장 확인)
(3) Orin rsync (devPC 에서 실행할 명령 안내)
```

transfer.py 구조:
```python
def flow7_select_transfer_h2(script_dir: Path, local_dataset_path: str, repo_id: str) -> None:
    """H-2: 3 옵션 재정의."""
    # (1) → _transfer_to_hub(...)          # 그대로
    # (2) → _keep_local_dgx(...)           # 로컬 보관 안내 (경로 확인)
    # (3) → _guide_rsync_to_orin(...)      # Orin rsync 명령 안내
```

`_guide_rsync_to_orin()` 내용:
```python
def _guide_rsync_to_orin(repo_id: str) -> None:
    dataset_name = repo_id.split("/")[-1]
    print("[flow 7] Orin rsync 전송 안내")
    print("  devPC 에서 실행하세요:")
    print(f"  bash smolVLA/scripts/sync_dataset_dgx_to_orin.sh --dataset {dataset_name}")
    print("  (스크립트 신규 작성 필요 — 07_leftarmVLA 사이클 X 할당 예정)")
```

trade-off: spec 의 권고안. Orin rsync 는 현재 `sync_dataset_dgx_to_orin.sh` 미존재 (07 이후 신규). 안내 메시지로만 처리.

### 5-4) 후보 H-3 — 단순화 (HF Hub + 로컬 dgx 보관)

```
(1) HF Hub 업로드
(2) 로컬 DGX 보관 (dgx/data/<dataset>/)
```

Orin rsync 옵션은 별도 ckpt sync 단계로 분리. transfer.py 는 2 옵션만 관리.

transfer.py 구조:
```python
def flow7_select_transfer_h3(script_dir: Path, local_dataset_path: str, repo_id: str) -> None:
    """H-3: 2 옵션 단순화."""
    # (1) → _transfer_to_hub(...)
    # (2) → _keep_local_dgx(...)
    # Orin rsync 는 별도 학습 mode ckpt 관리 (flow 5 학습) 로 위임
```

trade-off: 옵션 단순·명확. Orin rsync 를 수집 완료 직후 제공하지 않음 (학습 mode 의 ckpt 케이스 안내로 통합). 데이터셋(수집 결과)과 ckpt(학습 결과)의 전송 경로가 분리되어 역할이 명확.

### 5-5) 각 후보 transfer.py 구조 비교

| 항목 | H-1 보존 | H-2 재정의 | H-3 단순화 |
|---|---|---|---|
| 옵션 수 | 3 | 3 | 2 |
| Orin rsync | 없음 | 안내 포함 | 없음 (별도 단계) |
| 코드 변경 | 최소 (경고만) | 중간 (옵션 재정의) | 낮음 (옵션 제거) |
| spec 정합 | 낮음 (무의미 옵션) | 높음 (spec 권고) | 중간 |
| UX 명확성 | 낮음 (혼란) | 중간 | 높음 |
| sync 스크립트 의존 | 없음 | `sync_dataset_dgx_to_orin.sh` (미존재) | 없음 |

---

## §6 awaits_user G·H 발송 명세

X1 study 완료 — orchestrator 가 사용자에게 아래 두 결정 요청.

### G 결정 발송 내용

dgx interactive_cli 의 flow 3 mode 분기 구조를 선택해주세요.

`datacollector/interactive_cli/flows/{teleop,data_kind,record,transfer}.py` 직접 Read + `14_dgx_cli_flow.md §1~§5` 분석 결과 다음 3 후보를 도출했습니다:

**(G-1) 단발 종료** — 한 mode (수집 또는 학습) 실행 후 CLI 종료.
- trade-off: 구현 단순. 수집→학습 연속은 CLI 재시작 필요.

**(G-2) 재진입 루프** — mode 완료 후 다시 flow 3 메뉴로 돌아옴. (3) 종료 선택 시 CLI 종료.
- trade-off: 한 세션에서 수집→학습 전환 가능. 루프 상태 관리 구현 필요.

**(G-3) 수집→학습 직렬 옵션 추가** — `(1) 수집→학습 직렬 / (2) 수집만 / (3) 학습만 / (4) 종료`. 수집 직후 학습 자동 진입 옵션 추가.
- trade-off: 원클릭 수집+학습. 옵션 4개로 증가. 직렬 흐름 자동 전달 로직 추가 필요.

**영향**: X2 의 `dgx/interactive_cli/flows/mode.py` 구조 결정.
- G-1: `flow3_select_mode() -> str | None` 단발
- G-2: `flow3_mode_loop(script_dir: Path) -> int` 루프
- G-3: 4 옵션 + `run_collect_then_train()` 직렬 함수

**사용자 결정 전 X2 dispatch X** 안내: G 결정 없이 X2 는 mode.py 구조를 확정할 수 없음.

### H 결정 발송 내용

dgx interactive_cli flow 7 (데이터 전송) 분기 옵션 재정의 방향을 선택해주세요.

datacollector 원본의 `(2) rsync → DGX` 옵션이 DGX 흡수 후 자기 자신으로의 전송이 되어 무의미해집니다. 다음 3 후보를 도출했습니다:

**(H-1) 기존 그대로 보존** — `(1) HF Hub / (2) rsync DGX (무의미 경고 추가) / (3) 안함`.
- trade-off: 코드 변경 최소. 무의미 옵션 노출로 UX 혼란.

**(H-2) 옵션 재정의** — `(1) HF Hub / (2) 로컬 DGX 보관 / (3) Orin rsync 안내`.
- trade-off: spec 권고안. Orin rsync 스크립트 (`sync_dataset_dgx_to_orin.sh`) 는 현재 미존재 → 안내 메시지만 출력 (07 이후 구현).

**(H-3) 단순화** — `(1) HF Hub / (2) 로컬 DGX 보관`. Orin rsync 는 학습 mode 의 ckpt 관리 단계로 분리.
- trade-off: 가장 단순·명확. 데이터셋 전송과 ckpt 전송 역할 분리.

**영향**: X2 의 `dgx/interactive_cli/flows/transfer.py` 구조 결정.
- H-1: 원본 `flow7_select_transfer()` 최소 수정
- H-2: 옵션 (2)→로컬보관, (3)→Orin rsync 안내 함수 신규
- H-3: 옵션 (2)→로컬보관, (3) 제거. 2 옵션 구조

**사용자 결정 전 X2 dispatch X** 안내: H 결정 없이 X2 는 transfer.py 옵션을 확정할 수 없음.

---

## §7 X2 인계 항목 (이식 대상 + 수정 필요 사항)

### 이식 대상 4 파일

| 원본 경로 | 대상 경로 | 주요 수정 |
|---|---|---|
| `legacy/.../datacollector/interactive_cli/flows/teleop.py` | `dgx/interactive_cli/flows/teleop.py` | scripts 경로 자동 해석 (부모 경로 구조 동일), flow 번호 표기 갱신 |
| `legacy/.../datacollector/interactive_cli/flows/data_kind.py` | `dgx/interactive_cli/flows/data_kind.py` | 변경 없음 (DATA_KIND_OPTIONS 독립) |
| `legacy/.../datacollector/interactive_cli/flows/record.py` | `dgx/interactive_cli/flows/record.py` | `data_root` 경로: `~/smolvla/datacollector/data/` → `~/smolvla/dgx/data/` (1 라인) |
| `legacy/.../datacollector/interactive_cli/flows/transfer.py` | `dgx/interactive_cli/flows/transfer.py` | H 결정에 따른 옵션 재정의 |

### entry.py 수정 필요 (X2 담당)

현재 `dgx/interactive_cli/flows/entry.py` 의 `VALID_NODES` + `NODE_DESCRIPTIONS` + `NODE_GUIDE`:
- `VALID_NODES = ("orin", "dgx", "datacollector")` → `("orin", "dgx")` 로 변경
- `NODE_DESCRIPTIONS["datacollector"]` 행 제거
- `NODE_GUIDE["datacollector"]` 행 제거
- `flow0_confirm_environment()` 내 `node != "datacollector"` 조건 → 항상 True (orin·dgx 둘 다 확인 단계 없음)

변경 이유: DataCollector 노드 운영 종료 (06 결정 C·F).

변경 후 entry.py `main()` 분기:
```python
if selected == "dgx":
    # flow 2: env_check (mode 인자 없이 — G 결정 후 mode.py 에서 mode 선택)
    if not flow2_env_check(script_dir, scenario="smoke"):
        return 1
    # flow 3: mode 분기 (mode.py — G 결정 적용)
    from flows.mode import flow3_mode_entry
    return flow3_mode_entry(script_dir)
elif selected == "orin":
    # orin: 기존 inference.py 흐름
    ...
```

### configs/node.yaml 수정 (X2 담당)

```yaml
# dgx/interactive_cli/configs/node.yaml 갱신
node: dgx
venv: ~/smolvla/dgx/.arm_finetune
responsibilities:
  - training
  - data_collection   # 신규 추가
```

---

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-01 | 초안 작성 — 05 TODO-X1 study 산출물. preflight·smoke_test·save_dummy_checkpoint·sync_ckpt_dgx_to_datacollector 직접 Read + 인용. 3 후보 (A·B·C) 도출. §6 awaits_user-C 발송 명세 포함. 사용자 옵션 C (3단계) 결정. |
| 2026-05-02 | 06 TODO-X1 study 갱신 — 학습+수집 통합. §1 env_check 수집 항목 추가. §2 mode 분기 G-1·G-2·G-3 후보. §3 datacollector flow 이식 (4 파일 변경 사항 명세). §4 기존 학습 flow 보존. §5 flow 7 전송 분기 H-1·H-2·H-3 후보. §6 G·H awaits_user 발송 명세. §7 X2 인계 항목. |
