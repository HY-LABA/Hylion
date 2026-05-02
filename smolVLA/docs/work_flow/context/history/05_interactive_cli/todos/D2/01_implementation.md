# TODO-D2 — Implementation

> 작성: 2026-05-01 14:00 | task-executor | cycle: 1

## 목표

datacollector/interactive_cli/ 의 flow 2~7 단계 구현 (env_check, teleop, data_kind, record, transfer) + entry.py 통합 연결.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `datacollector/interactive_cli/flows/env_check.py` | 신규 | flow 2 환경 체크 5단계 (venv/USB/카메라/lerobot/data 경로) |
| `datacollector/interactive_cli/flows/teleop.py` | 신규 | flow 3·4 run_teleoperate.sh all subprocess 호출 + 재시도 분기 |
| `datacollector/interactive_cli/flows/data_kind.py` | 신규 | flow 5 학습 종류 5개 옵션 메뉴 (옵션 1 단순 pick-place 권장) |
| `datacollector/interactive_cli/flows/record.py` | 신규 | flow 6 lerobot-record draccus 인자 동적 생성 + subprocess 호출 + validation 4항목 |
| `datacollector/interactive_cli/flows/transfer.py` | 신규 | flow 7 HF Hub / rsync 안내 / 안함 3분기 |
| `datacollector/interactive_cli/flows/entry.py` | M | flow 2~7 순차 호출 `_run_datacollector_flows()` 추가 |

## 적용 룰

### lerobot-reference-usage 직접 Read + 인용

1. `docs/reference/lerobot/src/lerobot/scripts/lerobot_record.py` (line 161~258) 직접 Read:
   - `DatasetRecordConfig` 전체 필드 인용:
     ```
     repo_id: str                         (line 163)
     single_task: str                     (line 165)
     root: str | Path | None = None       (line 167)
     fps: int = 30                        (line 169)
     num_episodes: int = 50               (line 175)
     push_to_hub: bool = True             (line 179)
     streaming_encoding: bool = False     (line 202)
     encoder_threads: int | None = None   (line 208)
     vcodec: str = "libsvtav1"            (line 199)
     __post_init__: raises ValueError if single_task is None  (line 212~214)
     ```
   - CLI 예시 (line 22~41) — `--dataset.streaming_encoding=true`, `--dataset.encoder_threads=2` 인용
   - `RecordConfig.teleop`, `.display_data` 인용

2. `datacollector/scripts/run_teleoperate.sh` 직접 Read:
   - line 19~22: `FOLLOWER_PORT="/dev/ttyACM1"`, `LEADER_PORT="/dev/ttyACM0"`, `FOLLOWER_ID="my_awesome_follower_arm"`, `LEADER_ID="my_awesome_leader_arm"` → record.py 고정 인자로 사용
   - line 27~35: `so101_follower`, `so101_leader` → `--robot.type`, `--teleop.type` 고정값
   - line 70~74: `all` 커맨드 = calibrate_follower → calibrate_leader → teleoperate → teleop.py subprocess 인자로 사용

3. `datacollector/scripts/push_dataset_hub.sh` 직접 Read:
   - line 104~117: HF_TOKEN 환경변수 / huggingface-cli cached token 확인 패턴 → transfer.py `_check_hf_token()` 미러
   - line 90~94: `grep -qE "^[^/]+/[^/]+$"` → record.py `_validate_repo_id()` 정규식 패턴 재사용
   - line 6~14: `--dataset` + `--repo-id` + `--private` 인자 형식 → transfer.py `_transfer_to_hub()` cmd 구성에 사용

4. `scripts/sync_dataset_collector_to_dgx.sh` 직접 Read:
   - line 6: "실행 위치: devPC (어디서든)" → datacollector 직접 호출 금지 근거
   - line 67~77: SSH alias `Host datacollector`, `Host dgx` 등록 요구 → 안내 메시지에 반영

5. `orin/tests/check_hardware.sh` 직접 Read:
   - step_venv (line 152~173): VIRTUAL_ENV + sys.prefix 체크 패턴 → env_check.py `_check_venv()` 미러
   - step_soarm_port (line 220~328): ttyACM* 스캔 패턴 → env_check.py `_check_usb_ports()` 미러
   - step_cameras (line 336~486): OpenCV probe + ImportError 처리 → env_check.py `_check_cameras()` 미러

6. `datacollector/interactive_cli/flows/entry.py` (F2 산출물) 직접 Read:
   - flow 1 완료 후 `flow 2+` TODO 플레이스홀더 (line 249~253) → `_run_datacollector_flows()` 로 교체

### CLAUDE.md Hard Constraints

- Category A: `docs/reference/` 수정 X (레퍼런스 Read 전용) ✓
- Category B: `orin/lerobot/`, `pyproject.toml`, `setup_env.sh` 미변경 ✓
  - `datacollector/interactive_cli/` 는 신규 Python 파일 — Category B 비해당
- Category D: `rm -rf`, `sudo` 등 금지 명령 미사용 ✓
- Coupled File Rule: `orin/lerobot/` 미변경 → `03_orin_lerobot_diff.md` 갱신 불필요 ✓

### lerobot-upstream-check

- `orin/lerobot/` 미변경 (옵션 B 준수) ✓
- `pyproject.toml` 미변경 (`bash main.sh` 직접 호출 — entrypoint 추가 X) ✓

## 사용자 결정 옵션 (1) 단순 pick-place 적용 결과

```
awaits_user-A 답 (2026-05-02): 옵션 (1) 단순 pick-place
  task instruction: "Pick up the object and place it in the target area."
  권장 에피소드: 50
```

data_kind.py:
- 옵션 1 에 "★ 권장" 마킹 + 주석 "svla_so100_pickplace 분포에 가장 가까움"
- `DATA_KIND_OPTIONS[1].default_num_episodes = 50`
- `DATA_KIND_OPTIONS[1].single_task = "Pick up the object and place it in the target area."`

record.py:
- `SINGLE_TASK_MAP[1] = "Pick up the object and place it in the target area."` (D1 §4 매핑 표 그대로)

## 변경 내용 요약

D1 §1~§5 에서 정의한 설계를 그대로 코드로 구현했다. 각 flow 는 독립적인 모듈로 분리되어 entry.py 의 `_run_datacollector_flows()` 에서 순차 호출된다.

**flow 2 (env_check.py)**: 04 G1 `check_hardware.sh` 의 step_venv / step_soarm_port / step_cameras 패턴을 datacollector 환경에 미러. venv 확인 시 VIRTUAL_ENV 환경변수 + sys.prefix 이중 체크. USB 포트는 `run_teleoperate.sh` 기본값 `/dev/ttyACM1` (follower) / `/dev/ttyACM0` (leader) 존재 여부 직접 확인. 카메라는 OpenCV VideoCapture(idx) 로 인덱스 0~3 탐색. 결과로 `EnvCheckResult(ok, cam_wrist_left_index, cam_overview_index)` 반환 — record.py 로 인덱스 전달.

**flow 3·4 (teleop.py)**: `run_teleoperate.sh all` subprocess 호출. flow 4 에서 `r` 입력 시 flow 3 재실행 루프, Enter 시 flow 5 진행. returncode != 0 시 경고 출력 후 사용자 선택 위임.

**flow 5 (data_kind.py)**: D1 §3 5개 옵션 메뉴. 사용자 결정 옵션 1 권장 마킹. `DataKindResult(choice, single_task, default_num_episodes)` 반환.

**flow 6 (record.py)**: validation 4항목 (repo_id 형식 / num_episodes 양수 / data_kind_choice 1~5 / 카메라 인덱스) 통과 후 `build_record_args()` 로 lerobot-record 전체 인자 동적 생성. subprocess.run(check=False) + returncode 체크. `(success, local_dataset_path, repo_id)` 3-tuple 반환.

**flow 7 (transfer.py)**: HF Hub 분기는 `_check_hf_token()` 으로 인증 확인 후 `push_dataset_hub.sh` 호출. rsync 분기는 `sync_dataset_collector_to_dgx.sh` 가 devPC 전용임을 명시하고 안내 메시지만 출력. 안함 분기는 나중에 전송할 수 있는 명령 출력.

## code-tester 입장에서 검증 권장 사항

- 정적 검사: `python3 -m py_compile datacollector/interactive_cli/flows/*.py` (이미 통과)
- import 체크: `python3 -c "from datacollector.interactive_cli.flows.env_check import flow2_env_check"`
- lerobot 미설치 환경에서 env_check.py `_check_lerobot_import()` 가 FAIL + 안내 메시지 출력하는지 확인
- record.py validation — `_validate_repo_id("badformat")` → False, `_validate_repo_id("user/name")` → True
- transfer.py HF Token 미설정 환경에서 분기 1 선택 시 안내 메시지 출력 후 재선택 루프 확인
- D2 DOD 항목 확인:
  - flow 2~7 모두 구현 ✓
  - `run_teleoperate.sh` subprocess 호출 ✓ (teleop.py)
  - `push_dataset_hub.sh` subprocess 호출 ✓ (transfer.py)
  - `sync_dataset_collector_to_dgx.sh` 직접 호출 금지 + 안내 메시지 ✓ (transfer.py)
  - lerobot-record draccus 인자 동적 생성 ✓ (record.py build_record_args)
  - G3 DataCollector check_hardware 이식 ✓ (env_check.py — 04 G1 패턴 미러)

## 다음 단계 권고 — D3 prod 검증 시 필요한 사용자 환경 조건

| 조건 | 내용 |
|---|---|
| DataCollector 머신 | DataCollector 에서 `bash datacollector/interactive_cli/main.sh` 실행 가능 환경 |
| venv | `~/smolvla/datacollector/.hylion_collector` 존재 + lerobot 설치 완료 |
| SO-ARM | follower (`/dev/ttyACM1`) + leader (`/dev/ttyACM0`) USB 연결 상태 |
| 카메라 | wrist_left (index 0) + overview (index 1) USB 카메라 연결 상태 |
| HF Token | `export HF_TOKEN=hf_xxxxxxxxxx` (flow 7 HF Hub 분기 검증 시) |
| devPC SSH | `~/.ssh/config` 에 `Host datacollector`, `Host dgx` alias 등록 (flow 7 rsync 안내 검증 시) |
| 데이터 저장 경로 | `~/smolvla/datacollector/data/` 쓰기 가능 |

## 잔여 리스크 및 SKILL_GAP

| 항목 | 내용 |
|---|---|
| 카메라 인덱스 런타임 변동 | USB 재연결 시 인덱스가 바뀔 수 있음. env_check 후 record 실행 전 재확인 권장 (D3 에서 실측) |
| HF Token 미설정 시 flow 7 분기 1 실패 | transfer.py 에서 인증 확인 + 재선택 루프로 보호 |
| lerobot-record `so101_follower` 가용 여부 | datacollector 환경의 lerobot 버전이 `so101_follower` 를 지원하는지 D3 실측 필요 |
| push_dataset_hub.sh `LeRobotDataset(root=)` 로드 | lerobot-record 로 수집된 정규 포맷 가정. 비정규 포맷 시 로드 실패 가능 |
| SKILL_GAP | 없음 — 모든 구현이 D1 §1~§5 + 레퍼런스 직접 Read 기반 |
