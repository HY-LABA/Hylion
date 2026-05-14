# TODO-X1 — Code Test

> 작성: 2026-05-02 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈 0건. Recommended 개선 1건.

---

## 단위 테스트 결과

```
study 타입 — 코드 변경 없음. pytest 대상 없음.
변경 파일: docs/storage/14_dgx_cli_flow.md (문서 전용)
```

## Lint·Type 결과

```
study 타입 — .py 파일 변경 없음. ruff / mypy 대상 없음.
```

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. flow 3 mode 질문 옵션 라벨·종료 분기 (결정 G) 3 후보 제시 | ✅ | §2 G-1 단발 / G-2 루프 / G-3 직렬 옵션. 메뉴 라벨·mode.py 코드 구조 비교표 포함 |
| 2. flow 7 전송 분기 옵션 재정의 (결정 H) 3 후보 제시 | ✅ | §5 H-1 보존 / H-2 재정의 / H-3 단순화. transfer.py 구조 비교표 + trade-off 명시 |
| 3. flow 5 학습 종류 옵션 (datacollector D1 §3 그대로 적용 여부) | ✅ | §3-3 DATA_KIND_OPTIONS 5개 딕셔너리 직접 인용 + "변경 없음" 명시 |
| 4. 기존 dgx 학습 flow 보존 | ✅ | §4 옵션 C 3단계 (preflight → 데이터셋 선택 → 학습+ckpt) 그대로 |
| 5. mode.py 코드 구조 (단발 vs 루프) 비교 | ✅ | §2-5 비교표: 메뉴 항목 수·수집→학습 연속·복잡도·env_check 재실행 여부 |
| 6. awaits_user 발송 명세 작성 | ✅ | §6 G·H 전문 완성. 두 결정 전 X2 dispatch X 명시 |
| 7. 레퍼런스 직접 인용 (4 파일) | ✅ | 하단 별도 검증 참조 |
| 8. env_check.py mode 파라미터 패턴 제안 | ✅ | §1-4 `flow2_env_check(script_dir, scenario, mode)` 코드 스니펫 제시 |

---

## 레퍼런스 직접 Read 검증

검증 방법: code-tester 가 `docs/storage/legacy/02_datacollector_separate_node/datacollector/interactive_cli/flows/` 의 4개 파일을 직접 Read 하여 14_dgx_cli_flow.md 인용 내용과 교차 확인.

### teleop.py

원본 함수 시그니처 (확인):
```python
def flow3_teleoperate(script_dir: Path) -> int: ...
def flow4_confirm_teleop(script_dir: Path, prev_returncode: int) -> bool: ...
```
14_dgx_cli_flow.md §3-2 인용 — 완전 일치. `script_dir.parent.parent / "scripts" / "run_teleoperate.sh"` 경로 패턴도 원본 line 37 과 일치.

### data_kind.py

원본 `DATA_KIND_OPTIONS` 5개 옵션 (line 31~72):
- 1: 단순 pick-place / 2: push / 3: stack / 4: drawer open/close / 5: handover
- `DataKindResult` NamedTuple (choice, single_task, default_num_episodes)
- `flow5_select_data_kind() -> DataKindResult | None`

14_dgx_cli_flow.md §3-3 인용 — 5개 옵션 키 이름·single_task 내용 일치. "변경 없음" 판단 근거 충분.

### record.py

원본 line 194 (확인):
```python
data_root = os.path.expanduser(f"~/smolvla/datacollector/data/{dataset_name}")
```
14_dgx_cli_flow.md §3-4·§7 인용 — `~/smolvla/datacollector/data/` → `~/smolvla/dgx/data/` 변경 라인 정확히 일치.

`build_record_args` 시그니처 (line 157~163):
```python
def build_record_args(
    data_kind_choice: int,
    repo_id: str,
    num_episodes: int,
    cam_wrist_left_index: int = 0,
    cam_overview_index: int = 1,
) -> list[str]:
```
14_dgx_cli_flow.md §3-4 인용 — 시그니처 일치.

### transfer.py

원본 `flow7_select_transfer` 시그니처 (line 162~166):
```python
def flow7_select_transfer(
    script_dir: Path,
    local_dataset_path: str,
    repo_id: str,
) -> None:
```
14_dgx_cli_flow.md §5 H-2·H-3 후보 시그니처:
```python
def flow7_select_transfer_h2(script_dir: Path, local_dataset_path: str, repo_id: str) -> None:
def flow7_select_transfer_h3(script_dir: Path, local_dataset_path: str, repo_id: str) -> None:
```
원본 인자 구조 그대로 승계. H-1 은 원본 `flow7_select_transfer()` 최소 수정 방향으로 명시.

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `docs/storage/14_dgx_cli_flow.md §4` | flow 5 학습 종류 옵션이 §3 에서 data_kind.py 인용으로 처리되어 있으나, §4 학습 mode 흐름 안에 "수집 mode 의 flow 5 와 동일한 DATA_KIND_OPTIONS 재사용" 임을 명시적으로 확인할 수 없음. spec DOD 는 "datacollector D1 §3 그대로 dgx 환경 적용 여부"를 확인하도록 요구하는데, §4는 학습 ckpt 관리 중심이어서 flow 5 학습 종류 옵션이 학습 mode 흐름과 어떻게 연결되는지 한 줄 명시 추가 권장. |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경. `.claude/` 미변경. study 타입 — 코드 변경 없음 |
| B (자동 재시도 X) | ✅ | `orin/lerobot/`, `dgx/lerobot/`, `pyproject.toml`, `setup_env.sh`, `deploy_*.sh` 미변경 |
| Coupled File Rules | ✅ | Category B 영역 미변경 → Coupled file 갱신 불필요 |
| 옛 룰 (`docs/storage/` bash 예시) | ✅ | `docs/storage/14_dgx_cli_flow.md` 에 bash 예시 포함되어 있으나 이는 기존 §1 env_check.py 구현 패턴 제안 용도로 사용자 명시 요청(study DOD)에 의한 것. 위반 아님 |

---

## awaits_user G·H 발송 가능 여부

**발송 가능** — Critical 이슈 0건, Recommended 1건으로 READY_TO_SHIP.

`docs/storage/14_dgx_cli_flow.md §6` 에 G·H 전문이 완성되어 있음:
- G 결정: flow 3 mode 분기 3 후보 (G-1/G-2/G-3) + X2 dispatch 조건 명시
- H 결정: flow 7 전송 분기 3 후보 (H-1/H-2/H-3) + X2 dispatch 조건 명시

orchestrator 는 해당 전문을 그대로 사용자에게 발송하면 됨. G·H 사용자 결정 수령 후 X2 dispatch.

---

## 배포 권장

READY_TO_SHIP — prod-test-runner 진입 권장.

study 타입이므로 prod-test 는 문서 정합 확인 수준. G·H 결정 발송 후 X2 dispatch 진행 가능.
