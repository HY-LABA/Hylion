# TODO-P5 — Code Test

> 작성: 2026-05-03 | code-tester | cycle: 1

## Verdict

**`MINOR_REVISIONS`**

Critical 이슈 0건. Recommended 2건.

---

## 단위 테스트 결과

P5 변경 대상 (orin/interactive_cli/, dgx/interactive_cli/, dgx/config/) 에 대한 전용 pytest 없음.
변경 성격이 docstring·주석·텍스트 정리이므로 별도 유닛 테스트 미존재는 정상.

```
pytest 해당 없음 (orin/tests/ 는 hardware/smoke 테스트 — 본 변경과 무관)
```

---

## Lint·Type 결과

```
bash -n orin/interactive_cli/main.sh
→ PASS

python3 -m py_compile orin/interactive_cli/flows/entry.py
→ PASS

python3 -m py_compile dgx/interactive_cli/flows/entry.py
→ PASS

python3 -m json.tool dgx/config/dataset_repos.json
→ PASS (valid JSON)

ruff check orin/interactive_cli/flows/entry.py dgx/interactive_cli/flows/entry.py
→ All checks passed!
```

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. orin/ 활성 잔재 0건 | ✅ | main.sh L16, entry.py 4건 모두 처리. 나머지는 확인된 이력 주석 |
| 2. dgx/ 활성 잔재 0건 | ⚠️ | entry.py 3건 + dataset_repos.json + config/README.md 처리 완료. **dgx/README.md 4건 미처리 (R#1).** training.py L284 borderline (R#2) |
| 3. scripts/ 잔재 0건 | ✅ | P1 이 dev-connect.sh 처리. scripts/ 내 다른 파일 grep 0건 확인 |
| 4. docs/lerobot_study/ 잔재 0건 | ✅ | grep 0건 확인 |
| 5. pyproject.toml / Makefile 잔재 0건 | ✅ | grep 0건 확인 |
| 6. bash -n / py_compile / json.tool PASS | ✅ | 전 파일 통과 |
| 7. P1·P2·P3·P4 영역과 겹침 없음 | ✅ | P5 변경 파일 6건이 P1(dev-connect.sh)·P2(.gitignore)·P3(arm_2week_plan.md)·P4(specs/README.md) 와 완전 분리됨 |
| 8. 제외 영역(legacy, history, docs/reference/) 미변경 | ✅ | git diff 확인 — 해당 영역 0건 |
| 9. docs/storage/ bash 명령 예시 미추가 | ✅ | 13_orin_cli_flow.md 에 bash 예시 신규 추가 없음 (스크립트명 정정 + HTML 주석만) |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| R#1 | `dgx/README.md` L16, L44, L184~189 | "DataCollector ↔ DGX 인터페이스" 섹션 및 L16/L44 DataCollector 언급이 P5 그렙 결과에 포함됨에도 01_implementation.md 에서 분류 누락 (활성 잔재도 의도된 이력도 아닌 상태). DOD "발견 시 모두 제거 또는 history 참조 명시" 미충족. 다음 수정 주기에서 섹션 제목 정정 + L16·L44 최신화 권장 |
| R#2 | `dgx/interactive_cli/flows/training.py` L284 | `print("로컬 데이터셋이 없습니다. 먼저 DataCollector 에서 rsync 를 실행하세요.")` — task-executor 는 이 파일을 "의도된 history 참조"로 분류했으나 L284는 실제 실행 시 사용자에게 노출되는 print 문. DataCollector 노드가 폐기된 상황에서 "DGX 에서 rsync" 또는 "HF Hub 사용" 등으로 안내 문구 교체 권장 (현재는 기능 오동작 없이 단순 혼란 가능성) |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경. `.claude/` 미변경. git diff 확인 0건 |
| B (자동 재시도 X) | ✅ | `orin/lerobot/`, `dgx/lerobot/`, `pyproject.toml`, `setup_env.sh`, `deploy_*.sh`, `.gitignore` 미변경 (P5 변경 파일 6건 모두 Category B 외) |
| Coupled File Rules | ✅ | orin/lerobot/ 미변경 → 03_orin_lerobot_diff.md 갱신 불요. orin/pyproject.toml 미변경 → 02_orin_pyproject_diff.md·setup_env.sh 갱신 불요 |
| D (절대 금지 명령) | ✅ | 해당 명령 사용 없음 |
| 옛 룰 (docs/storage/ bash 예시 X) | ✅ | 13_orin_cli_flow.md 수정이 스크립트명 정정 + HTML 주석 추가에 한정. 신규 bash 명령 예시 없음 |

---

## 분류 적정성 spot-check

task-executor 의 분류 (활성/의도됨/모호) 에 대한 spot-check:

| 항목 | task-executor 분류 | 실제 | 평가 |
|---|---|---|---|
| orin/entry.py L21~23, L48, L121 | 의도된 이력 주석 | 갱신 이력 주석 (datacollector 제거 기록) | ✅ 적정 |
| dgx/entry.py L17~18, L37, L110 | 의도된 이력 주석 | 동일 패턴 | ✅ 적정 |
| dgx/scripts/push_dataset_hub.sh, run_teleoperate.sh | 이식 이력 주석 | "원본: legacy/...", "이식: 06_dgx_absorbs_datacollector" | ✅ 적정 |
| dgx/interactive_cli/flows/training.py | 의도된 이력 주석 | L17~64 는 주석/docstring 이력. **L284 는 실행 print()** — 분류 불완전 | ⚠️ R#2 |
| dgx/README.md | 분류 없음 (언급 자체 없음) | 4건의 활성 DataCollector 참조 존재 | ⚠️ R#1 (누락) |
| docs/storage/02_hardware.md §5 | 의도된 이력 (실측 기록) | smallgaint 호스트명 실측 기록 — DataCollector 실측 | ✅ 적정 |
| docs/storage/12_interactive_cli_framework.md | 의도된 이력 (3-노드 boilerplate 역사적 보존) | 05 시점 boilerplate 코드 — 정정 주석 동반 | ✅ 적정 |

---

## 배포 권장

MINOR_REVISIONS — prod-test-runner 진입 권장.

R#1 (dgx/README.md)·R#2 (training.py L284) 는 기능 오동작 없는 문서/안내 텍스트 문제.
task-executor 1회 추가 수정 후 재검증 없이 prod-test 진행.

수정 지침:
- `dgx/README.md` L184 섹션 제목 "DataCollector ↔ DGX 인터페이스" → "DGX 데이터 수집 인터페이스" 또는 이전 구조 역사 참조 주석 추가 + L16, L44 최신화.
- `dgx/interactive_cli/flows/training.py` L284 print 문 → "로컬 데이터셋이 없습니다. DGX 에서 데이터 수집 후 학습을 진행하세요." 등으로 교체.
