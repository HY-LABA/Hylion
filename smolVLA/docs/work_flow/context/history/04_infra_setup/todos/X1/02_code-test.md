# TODO-X1 — Code Test

> 작성: 2026-05-01 | code-tester | cycle: 1

---

## Verdict

**`READY_TO_SHIP`**

Critical 이슈 0건. Recommended 개선 사항 2건 (임계값 이하). DOD 5개 항목 전부 충족. CLAUDE.md Hard Constraints 위반 없음.

---

## 단위 테스트 결과

study 타입 (코드 산출물 없음) — 단위 테스트 해당 없음.

---

## Lint·Type 결과

study 타입 — .py / .sh 신규 파일 없음. ruff / mypy 적용 대상 없음.

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| §1 디렉터리 트리 (현재 + 새 구조) | ✅ | 1-1 현재 트리가 실제 `dgx/` 파일시스템과 일치 (scripts/ 4개 + runs/README.md + README.md). 1-2 새 구조에 tests/ + config/ 신규 명시 |
| §2 핵심 컴포넌트 책임 표 | ✅ | 9개 컴포넌트 (기존 7 + 신규 2: tests/, config/) × 책임·04 변경 여부 표 완비 |
| §3 마일스톤별 책임 매트릭스 (00~08) | ✅ | 00~08 9개 마일스톤 × 11개 컴포넌트 행. 08_orin_structure.md 와 동일 행=컴포넌트/열=마일스톤 형식 |
| §4 외부 의존성 | ✅ | devPC sync hub (4-1), HF Hub (4-2), DataCollector↔DGX 인터페이스 (4-3), 시스템 의존성 (4-4), Walking RL 보호 정책 (4-5) 5개 소절 완비 |
| §5 마이그레이션 계획 (TODO-X2 입력) | ✅ | 5개 카테고리 (유지 7건/이관 1건/신규 3건/삭제 0건/entrypoint 정리) + TODO-X2 부수 작업 명시 |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `09_dgx_structure.md` §3, `scripts/smoke_test.sh` 행, `03_smolvla_test_on_orin` 열 | 현재 `-`로 표기됐으나 `04_dgx_lerobot_diff.md`에 "TODO-09b DGX prod 검증에서 smoke_test.sh 단독 실행"이 02 마일스톤 이후 03 시점에 보정·재검증된 이력이 있음. 해당 셀을 `✓`로 표기하면 더 정확한 반영. 단, 02_dgx_setting에서 ✏️이 이미 표기되어 있으므로 경계가 모호하며 Minor 수준 |
| 2 | `09_dgx_structure.md` §5-3 | `dgx/config/dataset_repos.json`의 placeholder 스키마 예시 (키 이름 등)가 문서에 기술되지 않음. TODO-T1 미결이므로 스키마 확정 불가는 이해되나, 08_orin_structure.md §5-3의 ports.json/cameras.json과 달리 08은 스키마 미제시. TODO-T1 결정 후 갱신 계획이 명시되어 있으므로 구조상 문제는 아님 |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/`, `.claude/agents/`, `.claude/skills/`, `.claude/settings.json` 미변경. 변경 파일은 `docs/storage/09_dgx_structure.md`, `context/todos/X1/01_implementation.md`, `context/history/` 3종만 |
| B (자동 재시도 X 영역) | ✅ | `dgx/pyproject.toml` 미존재, `dgx/lerobot/` 미존재. Category B 변경 없음. task-executor 보고와 일치 |
| Coupled File Rules | ✅ | `dgx/pyproject.toml` 변경 없음 → 02_orin_pyproject_diff.md 갱신 의무 없음. `dgx/lerobot/` 코드 변경 없음 → 04_dgx_lerobot_diff.md 갱신 의무 없음 (본 TODO). 04_dgx_lerobot_diff.md 존재 여부 직접 확인 — 파일 실재, 02 마일스톤 산출물 포함 |
| 옛 룰 (`docs/storage/` bash 예시) | ✅ | 09_dgx_structure.md 내 bash 명령 예시 추가 없음 (HF Hub 커맨드 라인 예시는 §4-3 인터페이스 설명 맥락으로 기술됐고 docs/storage/ 저장 bash 예시 패턴에 해당하지 않음) |

---

## 패턴 미러 검증 (08_orin_structure.md 대비)

| 항목 | 07 패턴 | 08 일치 여부 | 메모 |
|---|---|---|---|
| 절 번호·제목 (§0~§6) | §0 본 문서 위치 / §1 트리 / §2 컴포넌트 책임 / §3 마일스톤 매트릭스 / §4 외부 의존성 / §5 마이그레이션 / §6 후속 TODO | ✅ | 08도 동일 §0~§6 구성. §6 제목은 "후속 TODO 트리거 포인트" vs "04 진입 시 활용 포인트" 로 표현 차이 있으나 의미 동일 |
| §0 변경 이력 절 존재 | 맨 끝 "변경 이력" 표 | ✅ | 08에도 동일 위치에 변경 이력 표 있음 |
| §3 매트릭스 형식 | 행=컴포넌트, 열=마일스톤, 기호 ✓/✏️/- | ✅ | 08 동일 형식 |
| §5 마이그레이션 5개 카테고리 | 유지/이관/신규/삭제/entrypoint 정리 | ✅ | 08 동일 5개 카테고리 (§5-1~§5-5) |
| 형제 문서 cross-reference | 07이 08을 형제 문서로 언급 | ✅ | 07의 헤더에 "형제 문서: 09_dgx_structure.md (TODO-X1 산출물 예정)" 으로 예고됨. 08의 헤더에 "형제 문서: 08_orin_structure.md" 명시 |

---

## 사실 정확성 검증

| 검증 항목 | 결과 | 근거 |
|---|---|---|
| 현재 dgx/ 트리 실제 파일시스템 일치 | ✅ | 실측: `dgx/README.md`, `dgx/runs/README.md`, `dgx/scripts/{preflight_check,save_dummy_checkpoint,setup_train_env,smoke_test}.sh` — 08 §1-1과 정확히 일치 |
| 02 산출물 4개 위치 (`dgx/scripts/`) | ✅ | 실측 확인 |
| `dgx/pyproject.toml` 미존재 | ✅ | 실측 확인. 08 §0 및 §5-5에 명시 |
| `dgx/lerobot/` curated 디렉터리 미존재 | ✅ | 실측 확인. 08 §0에 "dgx/lerobot/ curated 디렉터리를 두지 않는다" 명시 |
| 06_dgx_venv_setting.md 핵심 사실 활용 | ✅ | Python 3.12.3, torch 2.10.0+cu130, lerobot editable v0.5.1-52-g05a52238, HF_HOME, smoke test 실측 (5.97초/step, RAM peak 48 GiB), GB10 CUDA capability 12.1 UserWarning — §1-1 비고 + §4-4에 반영 |
| `04_dgx_lerobot_diff.md` 존재 여부 | ✅ | 파일 직접 Read 확인 — `docs/storage/lerobot_upstream_check/04_dgx_lerobot_diff.md` 실재. 02 마일스톤 smoke_test.sh 보정 이력 포함. task-executor 보고 "이미 존재" 와 일치 |
| `run_teleoperate.sh.archive` 임시 보관 위치 | ✅ | `docs/storage/others/run_teleoperate.sh.archive` 실재 확인. TODO-O2 임시 보관 사실과 일치 |

---

## 핵심 결정 합리성 검증

| 결정 | 합리성 | 근거 |
|---|---|---|
| run_teleoperate.sh 최종 위치: DataCollector (후보 a) | ✅ | "DGX 는 SO-ARM 직접 연결 없음" 사실 기반. 08 §5-2에 후보 (a)/(b)/(c) 비교 + 채택 이유 명시. 08_orin_structure.md §5-2 이관 항목과 일관 |
| DataCollector ↔ DGX 인터페이스: TODO-T1 미결 명시 | ✅ | §4-3에 "DataCollector ↔ DGX 인터페이스 미결 사항: TODO-T1 awaits_user" 명시. 현재 사용자 답 (HF Hub + rsync 둘 다) 기준으로 §5-3 갱신 필요 여부도 명시됨 |
| TODO-X2 마이그레이션 5개 카테고리 | ✅ | 08_orin_structure.md §5 의 5개 카테고리 패턴 그대로 미러. 내용은 DGX 실정 반영 (삭제 0건, entrypoint 정리 = pyproject.toml 미존재이므로 N/A) |
| 04_dgx_lerobot_diff.md 갱신 의무 판단 | ✅ | study 타입 (코드 변경 없음) → 갱신 불필요. TODO-X2 시점 이력 추가 권장으로 명시. CLAUDE.md Coupled File Rules 준수 |

---

## SKILL_GAP / Anomaly

task-executor 보고: SKILL_GAP 없음, CONSTRAINT_AMBIGUITY 없음. 검증 과정에서도 동일 — 추가 ANOMALIES 누적 없음.

---

## 배포 권장

READY_TO_SHIP — prod-test-runner 진입 권장.

단 본 TODO 는 study 타입이므로 prod-test-runner 단계 의미 없음. **X2 진입 게이트로 사용**: 본 verdict READY_TO_SHIP 을 확인한 orchestrator 는 TODO-X2 dispatch 가능.
