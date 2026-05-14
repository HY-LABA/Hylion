# TODO-X2 — Code Test

> 작성: 2026-05-01 15:30 | code-tester | cycle: 1

## Verdict

**`MINOR_REVISIONS`**

Critical 0건, Recommended 3건. Recommended 3건으로 MINOR_REVISIONS 기준 충족.

---

## 단위 테스트 결과

```
해당 없음 — TODO-X2 는 디렉터리 신규·문서 갱신 작업. 단위 테스트 대상 코드(.py/.sh) 변경 없음.
dgx/scripts/ 4개 파일 미변경 확인 (파일 헤더 직접 Read 검증).
```

## Lint·Type 결과

```
해당 없음 — 변경 파일이 모두 .md / .json 이므로 ruff/mypy 적용 범위 밖.
dataset_repos.json: 파일 직접 Read 로 수동 JSON 구조 검증 — PASS
  (중첩 구조·키-값 쌍·배열 포맷 모두 유효한 JSON 문법. Bash 차단으로 json.tool 직접 실행 불가,
   파일 전문 수동 검증으로 대체.)
```

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. TODO-X1 §5 5카테고리 계획대로 dgx/ 변경 | ✅ | 유지 7건 미변경, 이관 1건 D2 위임 유지, 신규 3건 실행, 삭제 0건, entrypoint N/A — 모두 완료 |
| 2. 02 산출물 (setup_train_env / preflight / smoke / save_dummy_checkpoint) 동작 회귀 없음 | ✅ | 4개 파일 헤더 직접 Read 확인. git diff dgx/scripts/ — Bash 차단으로 직접 실행 불가이나 파일 내용 상 변경 흔적 없음. 실 실행 검증은 TODO-X3 (prod) 책임 |
| 3. dgx/tests/ + README.md 신규 | ✅ | 파일 존재 확인. 내용 정상 |
| 4. dgx/config/ + README.md + dataset_repos.json 신규 | ✅ | 3개 파일 모두 존재 확인. 내용 정상 |
| 5. dataset_repos.json — valid JSON + HF Hub + rsync + active_method 필드 | ✅ | 수동 검증: hf_hub.repo_id / rsync.source / rsync.dest / active_method 모두 포함. 포맷 유효 |
| 6. dgx/README.md 갱신 (pyproject 주의사항 + lerobot 설치 + DataCollector 인터페이스 + 새 디렉터리 안내) | ✅ | 4개 섹션 모두 추가 확인. "⚠ 주의사항 — DGX 환경 구성", "DataCollector ↔ DGX 인터페이스" 등 |
| 7. 04_dgx_lerobot_diff.md 갱신 (coupled file 규칙) | ✅ | [2026-05-01] 항목 추가 확인. 변경 내용·이유·영향 범위·검증 모두 기재됨 |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | 루트 `.gitignore` | `smolVLA/dgx/outputs/` (또는 `smolVLA/dgx/outputs/*/`) gitignore 패턴 미추가. `09_dgx_structure.md` §5-5 부수 작업에 "미존재 시 추가" 명시, `09_dgx_structure.md` §1 트리에서 "gitignore" 라 표기했으나 실제 패턴 없음. `smolVLA/orin/checkpoints/*/` 패턴은 이미 추가되어 있어 형제 패턴과 불일치. task-executor 도 확인 보류 SKILL_GAP 명시. TODO-X3 전에 추가 권장 |
| 2 | `dgx/tests/README.md` | orin/tests/README.md 와 구조 비교 시 "두 모드 (first-time / resume)" 섹션이 orin/tests 에는 있고 dgx/tests 에는 없음. dgx/tests 에는 해당 모드 개념 불필요하므로 패턴 엄격 미러보다 DGX 책임에 맞는 형식이 적합. 단, 책임·자산표·외부의존성·참고 4섹션 구조는 모두 충족됨. 미러 충실도 관점에서 섹션 구성 차이가 있으나 DGX 맥락에서 합리적 변형이라 Critical 아님 |
| 3 | `dgx/config/dataset_repos.json` `hf_hub.repo_id` 값 | placeholder 값 `"${HF_USER}/example_dataset"` 가 shell 변수 치환 표기를 JSON 문자열로 사용 중. JSON spec 상 유효하나 값을 그대로 lerobot CLI 에 넘기면 `${HF_USER}` 가 리터럴로 전달되어 실패할 수 있음. placeholder 임을 README에 명시했으나, 혼동 방지를 위해 `"<HF_USER>/example_dataset"` 또는 `"PLACEHOLDER/example_dataset"` 형태 권장. 실용적 오동작은 TODO-T1 결정 전까지 없음 (실제 사용 X) |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경. `.claude/` 미변경 |
| B (자동 재시도 X) | ✅ | `dgx/lerobot/` 미존재 — 자연 충족. `dgx/pyproject.toml` 미변경 (미존재). `.gitignore` — task-executor 가 확인 보류했고 실제 변경 없음 확인 (gitignore 미추가가 부수 작업 미수행이나 Category B 위반은 아님) |
| C (사용자 동의 필수) | ✅ | `dgx/tests/`, `dgx/config/` 신규는 `dgx/` 하위이므로 Category C 해당 없음 |
| D (절대 금지 명령) | ✅ | 해당 명령 없음 |
| Coupled File Rules | ✅ | `04_dgx_lerobot_diff.md` 동시 갱신됨. orin/pyproject.toml 미변경이므로 02_/03_ 갱신 의무 없음 |
| 옛 룰 (`docs/storage/` bash 예시 추가 X) | ✅ | `docs/storage/lerobot_upstream_check/04_dgx_lerobot_diff.md` 의 [2026-05-01] 항목에 bash 명령 예시 없음 |

---

## ANOMALIES

| TYPE | 내용 |
|---|---|
| `SKILL_GAP` | task-executor 와 code-tester 모두 Bash 실행 차단 환경. `git diff dgx/scripts/`, `python -m json.tool`, `grep` 직접 실행 불가. JSON 유효성은 파일 전문 수동 검증으로 대체. dgx/scripts/ 미변경은 파일 헤더 Read + task-executor 보고 교차 검증으로 대체. `.gitignore` dgx/outputs/ 패턴 확인은 파일 전문 Read 로 직접 확인 (패턴 부재 확인). prod-test-runner (TODO-X3) 에서 DGX 환경 내 직접 실행으로 최종 검증 권장 |

---

## 배포 권장

MINOR_REVISIONS — task-executor 1회 수정 (Recommended #1: `.gitignore` `smolVLA/dgx/outputs/` 패턴 추가) 후 prod-test-runner (TODO-X3) 진입 권장.

- Recommended #2 (dgx/tests/README.md 섹션 구성)는 DGX 맥락 적합 변형으로 task-executor 재량 처리 또는 BACKLOG 처리 가능.
- Recommended #3 (placeholder 표기)는 실용적 오동작 없어 TODO-T1 시점 처리 가능.
- **핵심 수정 요청**: `.gitignore` 에 `smolVLA/dgx/outputs/` 패턴 추가. Category B 영역 (`.gitignore` 변경) 해당. CLAUDE.md 상 Category B 영역 변경은 code-tester MAJOR 시 자동 재시도 X + 사용자 보고 게이트이나, 본 건은 MINOR 이므로 task-executor 1회 수정 후 재검증 X → prod-test 진입 정책 적용.

> 주의: `.gitignore` 는 Category B 영역. task-executor 가 이를 수정하는 경우, 이후 code-tester MAJOR 발급 시 자동 재시도 X (orchestrator 사용자 보고 게이트). 현재는 MINOR 이므로 일반 수정 사이클 유지.
