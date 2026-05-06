# TODO-N1 — Implementation

> 작성: 2026-05-04 | task-executor | cycle: 1

## 목표

dgx + orin interactive_cli 모든 prompt 분기점에 `b` 또는 `back` 입력 시 직전 분기점으로 복귀하는 뒤로가기 UX 일괄 적용.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `dgx/interactive_cli/flows/_back.py` | 신규 | is_back() helper — flows/ 내부 모듈 (Category C 회피) |
| `orin/interactive_cli/flows/_back.py` | 신규 | 동일 (orin 측 독립 설치) |
| `dgx/interactive_cli/flows/entry.py` | M | flow1 장치 선택 + detect_display_mode 에 b/back 추가 |
| `dgx/interactive_cli/flows/mode.py` | M | flow3 mode 선택에 b/back 추가 |
| `dgx/interactive_cli/flows/precheck.py` | M | teleop_precheck 에 b/back 추가 |
| `dgx/interactive_cli/flows/data_kind.py` | M | flow5 학습 종류 선택에 b/back 추가 |
| `dgx/interactive_cli/flows/record.py` | M | task 텍스트·repo_id·num_episodes·실행 전 prompt 에 b/back 추가 |
| `dgx/interactive_cli/flows/teleop.py` | M | flow3 teleop 시작 전 + flow4 confirm 에 b/back 추가 |
| `dgx/interactive_cli/flows/training.py` | M | 시나리오·데이터셋·ckpt·ckpt 관리 선택에 b/back 추가 |
| `dgx/interactive_cli/flows/transfer.py` | M | flow7 전송 방식 선택에 b/back 추가 |
| `orin/interactive_cli/flows/entry.py` | M | flow1 장치 선택에 b/back 추가 |
| `orin/interactive_cli/flows/inference.py` | M | flow3 ckpt 선택·모드 선택에 b/back 추가 |
| `dgx/interactive_cli/README.md` | M | UX 뒤로가기 섹션 + 후행 todo 갱신 |
| `orin/interactive_cli/README.md` | M | UX 뒤로가기 섹션 + 후행 todo 갱신 |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 ✓
- Category C 회피: `flows/` 기존 디렉터리 내 `_back.py` 배치 (신규 디렉터리 생성 X) ✓
- Coupled File Rule: `orin/lerobot/` 미변경 → 03_orin_lerobot_diff.md 갱신 불필요 ✓
- 레퍼런스 활용: interactive_cli 는 자체 코드 (lerobot upstream 에 동일 구현 없음) — 기존 flow 패턴 (input() + while True 분기) 직접 확장. SKILL_GAP 해당 없음 (b/back UX 는 CLI 고유 기능).

## helper 위치 결정 사유

**`flows/_back.py` 선택** (인라인 대비):

- `is_back()` 는 단일 함수 3 줄 — 12개 파일에 중복 정의하면 유지보수 부담
- `flows/` 는 기존 디렉터리이므로 Category C (신규 디렉터리 생성) 에 해당 X
- `_back` prefix 로 내부 모듈 컨벤션 명시 (공개 API X)
- dgx·orin 는 독립 설치 구조이므로 양쪽 별도 파일 (공유 상위 common/ 없음 — Category C 회피 일관)

## 변경 내용 요약

각 flow 파일에 `from flows._back import is_back` import 를 추가하고, 모든 `input()` prompt 표시 문자열에 `(b: 뒤로)` 또는 `(b: 건너뜀)` 힌트를 삽입했다. 입력 후 `if is_back(raw):` 분기로 직전 단계 복귀 동작을 구현했다.

**분기점별 복귀 동작 패턴**:

| 분기점 유형 | b/back 동작 |
|---|---|
| 최상위 entry (flow 1, flow 3 최상위) | 종료 (`return None` 또는 `sys.exit(0)`) |
| 서브메뉴 → 상위 메뉴 | `return None` (호출 측이 None 을 복귀 신호로 처리) |
| teleop 시작 전 | `return 2` (특수 코드 — flow4_confirm_teleop 에서 처리) |
| ckpt 선택 서브 입력 | `return flow3_select_ckpt()` (재귀 복귀) |
| training _select_start_ckpt | `return "back", None, None` (호출 측에서 분기) |
| lerobot-record/train 실행 전 | 실행 취소 후 `return False, "", ""` |
| transfer/ckpt 관리 | 로컬 저장 유지 후 반환 (건너뜀 의미) |

**subprocess 실행 중 뒤로가기 불가** 명시:
- `lerobot-record` (flow 6), `run_teleoperate.sh` (flow 3 teleop), `lerobot-train` (flow 5 실 학습), `hil_inference.py` (orin flow 4) — 각 실행 직전 안내 문구 추가.

## MINOR cycle 1 수정 (2026-05-04)

> code-tester MINOR_REVISIONS → task-executor 재호출 (재검증 X, 직접 prod-test 진입)

### 적용된 수정

| # | 대상 | 이전 | 이후 |
|---|---|---|---|
| Recommended #2 | `teleop.py` — `flow3_teleoperate` b/back sentinel | `return 2` | `return -1` |
| Recommended #2 | `teleop.py` — `flow4_confirm_teleop` 분기 (2곳) | `== 2` | `== -1` |
| Recommended #3 | `training.py` — `_run_real_training` b/back 반환 | `return False, None` | `return "CANCELED", None` |
| Recommended #3 | `training.py` — `_run_real_training` 반환 타입 | `tuple[bool, str\|None]` | `tuple[bool\|str, str\|None]` |
| Recommended #3 | `training.py` — `flow5_train_and_manage_ckpt` 분기 | `(False, None)` 수신 → ckpt UI 호출 | `"CANCELED"` 감지 → early return, ckpt UI skip |

### sentinel 선택 이유

- **teleop `-1`**: bash returncode 범위 0~255 초과 → `run_teleoperate.sh` 의 임의 `exit N` 과 충돌 불가. Python 측 전용 값.
- **training `"CANCELED"`**: `bool(result)` 호출 없이 타입으로 취소 vs 실패를 명확히 구분. `flow5` 에서 `result == "CANCELED"` 분기 후 early return → `_show_ckpt_management` 미호출.

### 잔여 리스크

- Recommended #1 (entry.py `# noqa: E402`) 미적용 — pre-existing 아키텍처 제약, 별도 BACKLOG 이관.
- `run_teleoperate.sh` 내부 exit code 정적 미확인 (SKILL_GAP 유지) — 그러나 `-1` sentinel 로 충돌 위험 제거.

---

## code-tester 입장에서 검증 권장 사항

- **구문 검사**: `python3 -m py_compile` 전 파일 — 이미 통과 확인 (12개 파일 모두 OK)
- **is_back 존재 검증**: `grep -rn "is_back" dgx/interactive_cli/flows/ orin/interactive_cli/flows/` — 9개 flow 파일 + 2개 _back.py 확인
- **prompt 힌트 일관성**: `grep -rn "b: 뒤로\|b: 건너뜀" dgx/interactive_cli/flows/ orin/interactive_cli/flows/`
- **subprocess 뒤로가기 불가 명시**: `grep -rn "뒤로가기 불가" dgx/interactive_cli/flows/ orin/interactive_cli/flows/`
- **Category C 위반 없음**: 신규 디렉터리 생성 없음 — `ls dgx/interactive_cli/` 로 `flows/` 하위 `_back.py` 확인
- **DOD 충족**: 9+3 = 12개 flow 파일 (dgx 9 + orin 3) 모두 b/back 분기 존재
