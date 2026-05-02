# TODO-X1 — Implementation

> 작성: 2026-05-02 14:00 | task-executor | cycle: 1

## 목표

dgx/interactive_cli/ 통합 flow 재설계 study — 옵션 α mode 분기 구체화 + 사용자 결정 G·H 후보 제안 + awaits_user 발송 명세 작성.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `docs/storage/14_dgx_cli_flow.md` | M | 학습+수집 통합 flow 설계 — §1~§7 갱신 (G·H 후보 + X2 인계) |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경. 코드 변경 X (study 타입). Category B 영역 미변경.
- Coupled File Rule: `orin/lerobot/` 미변경 → `03_orin_lerobot_diff.md` 갱신 불필요.
- 레퍼런스 직접 Read 목록:
  - `docs/storage/legacy/02_datacollector_separate_node/docs_storage_15_datacollector_cli_flow.md` — flow 5 학습 종류 옵션 5개 + flow 6 draccus 인자 + flow 7 전송 분기 원본
  - `docs/storage/legacy/02_datacollector_separate_node/datacollector/interactive_cli/flows/teleop.py` — `flow3_teleoperate()`, `flow4_confirm_teleop()` 함수 시그니처
  - `docs/storage/legacy/02_datacollector_separate_node/datacollector/interactive_cli/flows/data_kind.py` — `DATA_KIND_OPTIONS` 딕셔너리 (5개 옵션)
  - `docs/storage/legacy/02_datacollector_separate_node/datacollector/interactive_cli/flows/record.py` — `build_record_args()` (line 157~216), 고정 인자 상수
  - `docs/storage/legacy/02_datacollector_separate_node/datacollector/interactive_cli/flows/transfer.py` — `flow7_select_transfer()` (D1 §5 패턴)
  - `docs/storage/14_dgx_cli_flow.md` (기존 학습 flow 원안) — §2~§5 옵션 C 구조, `training.py` 설계
  - `docs/storage/12_interactive_cli_framework.md` — `VALID_NODES`, `flow1_select_node()`, entry.py 구조
  - `dgx/interactive_cli/flows/entry.py` — 현재 `VALID_NODES = ("orin", "dgx", "datacollector")` 확인
  - `dgx/interactive_cli/flows/training.py` — 기존 학습 flow 구현체 확인

## 변경 내용 요약

`docs/storage/14_dgx_cli_flow.md` 를 05 spec 의 학습 전용 설계 문서에서 **학습+수집 통합 설계 문서**로 갱신했다. 기존 §1~§6 (학습 flow 원안) 을 보존하면서 06 spec 의 수집 흡수 결정을 반영한 §1~§7 구조로 재편했다.

§1 에서는 기존 학습 환경 체크 (preflight_check.sh 5단계) 에 수집 환경 체크 항목 (USB 포트·dialout·v4l2·SO-ARM, 총 4항목) 을 추가했다. §2 에서는 flow 3 mode 분기 후보 G-1·G-2·G-3 세 가지를 mode.py 코드 구조 비교표와 함께 제시했다. §3 에서는 datacollector 원본 4 파일 (teleop/data_kind/record/transfer.py) 을 직접 Read 하여 dgx 이식 시 변경 필요 항목을 파일별로 명세했다. §4 는 기존 학습 flow (옵션 C 3단계) 를 그대로 보존했다. §5 에서는 flow 7 전송 분기 재정의 후보 H-1·H-2·H-3 을 transfer.py 코드 구조 비교표와 함께 제시했다. §6 은 orchestrator 가 사용자에게 발송할 G·H 결정 요청 전문을 완성했다. §7 은 X2 이식 대상 4 파일 + entry.py·node.yaml 수정 사항을 인계했다.

## §1 갱신한 14_dgx_cli_flow.md 핵심 변경

| 섹션 | 변경 내용 |
|---|---|
| §1 flow 2 체크 | 학습 5단계 (preflight) + 수집 4단계 (USB·dialout·v4l2·SO-ARM) 통합 |
| §2 flow 3 mode 분기 | G-1 (단발) / G-2 (루프) / G-3 (직렬 옵션) 3 후보 + mode.py 구조 비교 |
| §3 수집 mode | datacollector 4 파일 이식 변경 사항 명세 (draccus 인자 dgx 경로 맞춤) |
| §4 학습 mode | 기존 §2~§5 (학습 flow) 그대로 보존 + 학습 mode 진입 흐름 명시 |
| §5 flow 7 전송 | H-1 (보존) / H-2 (재정의·spec 권고) / H-3 (단순화) 3 후보 + transfer.py 구조 비교 |
| §6 awaits_user | G·H 결정 요청 전문 완성 |
| §7 X2 인계 | 4 파일 이식 대상 + entry.py·node.yaml 수정 사항 |

## §2 awaits_user G 발송 명세 (flow 3 mode 분기)

dgx interactive_cli 의 flow 3 mode 분기 구조를 선택해주세요.

**(G-1) 단발 종료**
- 메뉴: `(1) 데이터 수집 / (2) 학습 / (3) 종료`
- 한 mode 실행 후 CLI 종료. 수집→학습 연속은 CLI 재시작 필요.
- trade-off: 구현 가장 단순. DataCollector 단독 운영 시 패턴과 동일. 시연장에서 수집→학습 연속 세션 불가.

**(G-2) 재진입 루프**
- 메뉴: `(1) 데이터 수집 / (2) 학습 / (3) 종료`
- mode 완료 후 다시 flow 3 메뉴로 돌아옴. (3) 종료 선택 시 CLI 종료.
- trade-off: 한 세션에서 수집→학습 전환 가능. 루프 상태 관리·오류 시 재진입 보장 구현 필요.

**(G-3) 수집→학습 직렬 옵션 추가**
- 메뉴: `(1) 수집→학습 직렬 실행 / (2) 수집만 / (3) 학습만 / (4) 종료`
- 수집 완료 직후 학습 flow 자동 진입 옵션.
- trade-off: 수집→학습 원클릭. 옵션 4개로 증가. 수집 데이터셋 → 학습 dataset 자동 전달 로직 필요.

**결정 전 X2 dispatch X**: G 결정 없이 X2 는 `mode.py` 구조를 확정할 수 없음.

## §3 awaits_user H 발송 명세 (flow 7 전송 분기)

dgx interactive_cli flow 7 데이터 전송 옵션 재정의 방향을 선택해주세요.

datacollector 원본의 `(2) rsync → DGX` 옵션이 DGX 흡수 후 자기 자신으로의 전송이 되어 무의미해집니다.

**(H-1) 기존 그대로 보존**
- 메뉴: `(1) HF Hub / (2) rsync DGX (무의미 경고 추가) / (3) 안함`
- trade-off: 코드 변경 최소. 무의미 옵션 노출로 UX 혼란 발생.

**(H-2) 옵션 재정의** (spec 권고)
- 메뉴: `(1) HF Hub 업로드 / (2) 로컬 DGX 보관 / (3) Orin rsync 안내`
- Orin rsync 는 `sync_dataset_dgx_to_orin.sh` 안내 메시지 출력 (스크립트 미존재 — 07 이후 구현).
- trade-off: spec 정합 최고. Orin rsync 스크립트 미존재 → 안내만.

**(H-3) 단순화**
- 메뉴: `(1) HF Hub 업로드 / (2) 로컬 DGX 보관`
- Orin rsync 는 학습 mode ckpt 관리 단계(flow 5 학습)로 분리.
- trade-off: 가장 단순·명확. 데이터셋 전송과 ckpt 전송 역할이 명확히 분리.

**결정 전 X2 dispatch X**: H 결정 없이 X2 는 `transfer.py` 옵션을 확정할 수 없음.

## §4 X2 인계 항목

### 이식 대상 코드 4 파일

| 원본 (legacy) | 대상 (dgx) | 수정 필요 라인 |
|---|---|---|
| `datacollector/interactive_cli/flows/teleop.py` | `dgx/interactive_cli/flows/teleop.py` | `script_dir.parent.parent / "scripts" / "run_teleoperate.sh"` — 경로 해석은 동일, flow 번호 표기 갱신 |
| `datacollector/interactive_cli/flows/data_kind.py` | `dgx/interactive_cli/flows/data_kind.py` | 변경 없음 (`DATA_KIND_OPTIONS` 독립적) |
| `datacollector/interactive_cli/flows/record.py` | `dgx/interactive_cli/flows/record.py` | line 194: `~/smolvla/datacollector/data/` → `~/smolvla/dgx/data/` (1 라인 변경) |
| `datacollector/interactive_cli/flows/transfer.py` | `dgx/interactive_cli/flows/transfer.py` | H 결정에 따른 분기 옵션 재정의 (H-1 최소변경 / H-2 중간 / H-3 옵션제거) |

### 추가 수정 대상 (X2 담당)

- `dgx/interactive_cli/flows/entry.py`: `VALID_NODES` 에서 `"datacollector"` 제거 (06 결정 C), 관련 `NODE_DESCRIPTIONS`·`NODE_GUIDE` 행 제거, `main()` 분기에 `mode.py` 호출 추가
- `dgx/interactive_cli/flows/mode.py`: 신규 — G 결정 적용 (G-1/G-2/G-3)
- `dgx/interactive_cli/configs/node.yaml`: `responsibilities` 에 `data_collection` 추가
- `dgx/interactive_cli/flows/env_check.py`: `mode` 파라미터 추가 + 수집 환경 체크 항목 6~9 통합
- `orin/interactive_cli/flows/entry.py`: `VALID_NODES` 에서 `"datacollector"` 제거 (X2 와 함께 처리)

### record.py 경로 변경 확인 (flow 6 draccus 인자)

`docs_storage_15_datacollector_cli_flow.md §4` 에서 확정한 draccus 인자 고정 부분은 **dgx 환경에서 그대로 사용 가능**:
- `--robot.type=so101_follower` / `--robot.port=/dev/ttyACM1` — SO-ARM 포트 동일
- `--dataset.push_to_hub=false` — flow 7 별도 처리 동일
- `--dataset.streaming_encoding=true` + `--dataset.encoder_threads=2` — DGX 는 x86_64 + Python 3.12.3 → lerobot upstream 완전 호환. libsvtav1 vcodec 사용 가능 (DataCollector CPU-only 환경과 달리 DGX GPU 있어서 더 유리)

단 `data_root` 경로 1 라인만 변경:
```python
# record.py line 194 변경 전 (datacollector)
data_root = os.path.expanduser(f"~/smolvla/datacollector/data/{dataset_name}")

# 변경 후 (dgx)
data_root = os.path.expanduser(f"~/smolvla/dgx/data/{dataset_name}")
```

## §5 SKILL_GAP

본 todo (study 타입) 범위 내 SKILL_GAP 없음.

- flow 3 mode 분기: datacollector boilerplate (entry.py) + 05 TODO-X1 training.py 설계 기반 → 레퍼런스 있음
- flow 5 학습 종류 옵션: `docs_storage_15_datacollector_cli_flow.md §3` 5개 후보 → dgx 환경 그대로 적용 가능 (task instruction 독립적)
- flow 6 draccus 인자: datacollector record.py `build_record_args()` 직접 Read + `lerobot_record.py DatasetRecordConfig` 레퍼런스 확인
- flow 7 전송 분기: transfer.py 직접 Read + spec H 결정 후보 도출

후행 X2 에서 SKILL_GAP 발생 가능 영역:
- `env_check.py` 수집 체크 항목 6~9 구현 시: `lerobot-find-port` 비대화형 호출 방법 (레퍼런스 `docs/reference/lerobot/src/lerobot/scripts/lerobot_find_port.py` 직접 Read 필요)
- `sync_dataset_dgx_to_orin.sh` 스크립트 미존재 — H-2 채택 시 안내 메시지 참조 스크립트 없음. 07 이후 신규 작성 대상.

## code-tester 입장에서 검증 권장 사항

- 정적 검증: 본 todo 는 study (문서 작성) — 코드 변경 없음. lint·pytest 대상 아님.
- 문서 정합성:
  - `14_dgx_cli_flow.md §3` 이식 변경 사항이 `legacy/.../record.py line 194` 실제 코드와 일치하는지 확인
  - `14_dgx_cli_flow.md §2` mode.py 구조 비교표가 spec 06 결정 C (옵션 α) 와 정합하는지 확인
  - `14_dgx_cli_flow.md §5` H 후보 transfer.py 구조가 `legacy/.../transfer.py` 원본 함수 시그니처와 일치하는지 확인
- DOD 충족 확인:
  - flow 3 mode 질문 옵션 라벨·종료 분기 (결정 G) 3 후보 제시 ✓
  - flow 7 전송 분기 옵션 재정의 (결정 H) 3 후보 제시 ✓
  - flow 5 학습 종류 옵션 (datacollector D1 §3 그대로 — dgx 환경 적용 가능 여부 확인) ✓
  - 기존 dgx 학습 flow 보존 ✓
  - mode.py 코드 구조 (단발 vs 루프) 비교 ✓
  - awaits_user 발송 명세 작성 ✓
