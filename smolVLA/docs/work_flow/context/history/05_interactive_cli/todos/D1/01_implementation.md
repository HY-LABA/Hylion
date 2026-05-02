# TODO-D1 — Implementation

> 작성: 2026-05-01 | task-executor | cycle: 1

## 목표

datacollector 측 flow 2~7 단계 구체 동작 정의 + 5단계 학습 종류 옵션 ≤5개 후보 제안 (awaits_user-A 발송)

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `docs/storage/15_datacollector_cli_flow.md` | 신규 | datacollector flow 2~7 전체 동작 정의 (§1~§5) |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 — 레퍼런스는 Read 전용 ✓
- Category B·C 해당 없음 — `docs/storage/` 신규 파일만 생성 ✓
- 레퍼런스 직접 Read + 인용:
  - `docs/reference/lerobot/src/lerobot/scripts/lerobot_record.py` — `DatasetRecordConfig` (line 161~211), `RecordConfig` (line 217~258), CLI 예시 (line 22~41) 인용
  - `datacollector/scripts/run_teleoperate.sh` line 19~20, 29, 35, 70~74 — 포트·타입·커맨드 인용
  - `datacollector/scripts/push_dataset_hub.sh` line 6, 90~94, 104~117 — 실행 위치·validation·인증 인용
  - `scripts/sync_dataset_collector_to_dgx.sh` line 6, 67~77, 117~136 — 실행 위치 (devPC 전용) 인용
  - `docs/lerobot_study/04_lerobot_dataset_structure.md §3` — 카메라 키 명명 규칙 인용
  - `docs/lerobot_study/06_smolvla_finetune_feasibility.md §6.1` — 에피소드 수·batch_size 권장값 인용
  - `docs/lerobot_study/07b_smolvla_pretrain_dataset_structure.md §1-5` — 사전학습 태스크 instruction 실측값 인용
  - `docs/lerobot_study/03b_smolvla_milestone_config_guide.md §2 05` — 첫 사이클 기본값 유지 근거 인용
- lerobot-reference-usage 스킬: 레퍼런스 직접 Read + 핵심 인터페이스 인용 ✓
- Coupled File Rules: `orin/`, `dgx/`, `pyproject.toml`, `setup_env.sh` 미변경 — 해당 없음 ✓

## 변경 내용 요약

`docs/storage/15_datacollector_cli_flow.md` 신규 작성. 5개 절로 구성:

**§1 flow 2 (환경 체크)**: 04 G1 `check_hardware.sh` 5단계 패턴을 datacollector 맞춤으로 미러. venv (.hylion_collector) + USB 포트 (/dev/ttyACM0·1) + 카메라 인덱스 + lerobot import + 데이터 저장 경로 5항목. D2 의 `env_check.py` 구현 기준.

**§2 flow 3·4 (텔레오퍼레이션 + 사용자 확인)**: `run_teleoperate.sh all` 을 subprocess 로 호출하는 패턴 정의. flow 4 에서 재시도('r') / 진행(Enter) 분기 포함.

**§3 flow 5 (학습 종류 옵션)**: `docs/lerobot_study/` 전체 Read 후 5개 후보 도출. 단순 pick-place / push / stack / drawer / handover. `svla_so100_pickplace` 사전학습 분포 최근접인 후보 1 (단순 pick-place) 권장. **awaits_user-A 발송 명세 포함.**

**§4 flow 6 (lerobot-record draccus 인자 매핑)**: `lerobot_record.py` `DatasetRecordConfig` 시그니처 직접 인용. 고정 인자 (robot.type·port·id, teleop.type·port·id, push_to_hub=false, streaming_encoding=true 등) + 사용자 입력 필수 인자 (repo_id, num_episodes) + 5단계 답 → single_task 매핑 표. D2 validation 4항목 명시.

**§5 flow 7 (전송 방식 선택)**: HF Hub 분기 (`push_dataset_hub.sh` 직접 호출) / rsync 분기 (devPC 에서 실행 안내 — 직접 호출 X) / 안함 분기 (로컬 저장 유지). `sync_dataset_collector_to_dgx.sh` 가 devPC 전용이므로 datacollector 에서 직접 호출 금지 — 안내 메시지 출력으로 대체.

## code-tester 입장에서 검증 권장 사항

- 단위 테스트: 없음 (study todo — 코드 구현 없음)
- 문서 정합성:
  - `lerobot_record.py` `DatasetRecordConfig.repo_id` / `single_task` 인용이 실제 파일과 일치하는지 확인 (line 163, 165)
  - `run_teleoperate.sh` 포트·타입 상수값 (line 19~20, 29, 35) 이 인용과 일치하는지 확인
  - `sync_dataset_collector_to_dgx.sh` 실행 위치 (line 6 "devPC") 안내가 §5 에 반영되어 있는지 확인
  - `push_dataset_hub.sh` HF 인증 체크 로직 (line 104~117) 이 §5 분기 1 에 반영되어 있는지 확인
- DOD 항목 충족 확인:
  - [x] flow 2~7 단계 구체 동작 정의 (§1~§5)
  - [x] 5단계 옵션 후보 ≤5개 — 5개 도출 ✓
  - [x] flow 6 lerobot-record draccus 인자 매핑 결정 (§4)
- awaits_user-A 발송 명세가 §3 에 완전히 작성되었는지 확인

## awaits_user-A 발송 내용

아래 내용을 사용자에게 발송 (orchestrator 가 spec 및 plan 갱신 후 D2 dispatch 결정):

---

**datacollector interactive_cli 의 5단계 "어떤 학습 데이터를 모을건가요?" 옵션을 선택해주세요.**

`docs/lerobot_study/` 전체 Read 결과 다음 5개 후보를 도출했습니다:

**(1) 단순 pick-place** (권장)
- 설명: 책상 위 물체를 집어 지정 위치에 놓기 — SmolVLA 사전학습 데이터셋 (`svla_so100_pickplace`) 와 동일 도메인
- task instruction: `"Pick up the object and place it in the target area."`
- 권장 에피소드: 50

**(2) push (밀기)**
- 설명: 물체를 한 위치에서 다른 위치로 밀기 — 그리퍼 클로즈 없이 팔 움직임 위주
- task instruction: `"Push the object to the target position."`
- 권장 에피소드: 30~50

**(3) stack (쌓기)**
- 설명: 블록을 다른 블록 위에 쌓기 — pick-place 보다 정밀도 요구
- task instruction: `"Pick up the block and stack it on top of the other block."`
- 권장 에피소드: 50~100

**(4) drawer open/close**
- 설명: 서랍 열고 닫기 — 지속적 힘 인가 동작
- task instruction: `"Open the drawer."`
- 권장 에피소드: 30~50

**(5) handover (물건 전달)**
- 설명: 물체를 집어 사람 손 방향으로 가져다 주기
- task instruction: `"Pick up the object and hand it over."`
- 권장 에피소드: 30~50

**사용자 결정 사항**: 위 중 어떤 옵션을 채택하시겠습니까? (복수 선택 또는 다른 후보 제안 가능)

**영향**: D2 의 `data_kind.py` 분기 + `record.py` 의 draccus 인자 동적 생성 로직 (`--dataset.single_task` 값) 결정

---

## 다음 단계 권고 — D2 task 가 받을 입력

5단계 옵션 확정 후 D2 가 받아야 할 입력 명세:

### D2 입력: 인자 매핑 표 (사용자 답 확정 후 채워질 항목)

| 항목 | 값 (사용자 답 전 미확정) | 확정 후 D2 입력 |
|---|---|---|
| 선택 옵션 번호 | 미확정 (1~5 중) | `data_kind_choice: int` |
| `--dataset.single_task` | 미확정 | §4 매핑 표에서 자동 결정 |
| 복수 선택 여부 | 미확정 | 복수 시 data_kind.py 에 메뉴 항목 추가 필요 |

### D2 가 구현할 파일 (15_datacollector_cli_flow.md 기반)

| 파일 | 기반 절 | 핵심 구현 사항 |
|---|---|---|
| `datacollector/interactive_cli/flows/env_check.py` | §1 | 5단계 체크 (venv/포트/카메라/lerobot/저장경로) |
| `datacollector/interactive_cli/flows/teleop.py` | §2 | `run_teleoperate.sh all` subprocess 호출 + flow 4 재시도 |
| `datacollector/interactive_cli/flows/data_kind.py` | §3 | 5개 옵션 메뉴 + 사용자 답 반환 |
| `datacollector/interactive_cli/flows/record.py` | §4 | `build_record_args()` + validation 4항목 + subprocess 호출 |
| `datacollector/interactive_cli/flows/transfer.py` | §5 | 3분기 (HF Hub / rsync 안내 / 안함) |

### D2 validation 4항목 (§4 명시)

1. `repo_id` 형식 확인 — `<user>/<name>` 형식
2. `num_episodes` 양수 정수 확인
3. `data_kind_choice` 유효 범위 (1~N, N은 옵션 수)
4. 카메라 인덱스가 flow 2 env_check 결과와 일치하는지 확인

### 잔여 리스크 (spec 라인 237 + §4 명시)

- 5단계 답 동적 매핑 검증 — D2 에서 validation 4항목 필수
- flow 7 rsync 는 datacollector 직접 호출 불가 (devPC 전용) — 안내 메시지로만 처리
- HF Token 미설정 시 flow 7 HF Hub 분기 실패 — flow 7 진입 전 Token 유무 확인 후 안내 추가 권고
