# TODO-M3 — Code Test

> 작성: 2026-05-02 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 0건, Recommended 2건.

---

## 단위 테스트 결과

```
해당 없음 — 본 todo 는 문서(docs/storage/, docs/work_flow/, orin/interactive_cli/README.md, dgx/interactive_cli/README.md) 수정 전용.
pytest 실행 대상 없음.
```

## Lint·Type 결과

```
해당 없음 — .py 파일 변경 없음. ruff / mypy 불필요.
```

실제 검증 항목 (grep + git diff):

```
1. grep -n "07_datacollector|10_datacollector|15_datacollector" docs/storage/README.md
   → L17·L20·L25 에서 legacy 이관 표기 3건 확인 ✓

2. grep -n "06_dgx_absorbs|leftarmVLA|biarm" docs/work_flow/specs/README.md
   → L109·L119·L120·L121·L122·L124 — spec 번호 현황 표 + 시프트 주석 확인 ✓

3. grep -n "datacollector" orin/interactive_cli/README.md
   → L7·L8·L11·L37·L39·L40·L53·L58 전부 HTML 주석 또는 취소선/정정 표기. 활성 참조 없음 ✓

4. grep -n "datacollector" dgx/interactive_cli/README.md
   → L7·L8·L11·L37·L39·L40·L53·L58 전부 주석 또는 정정 표기. 활성 참조 없음 ✓

5. ls docs/storage/13_orin_cli_flow.md → EXISTS ✓ (README 신규 추가 행 유효)

6. Category A 파일 (.claude/, docs/reference/) 수정 없음 ✓
```

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. `docs/storage/README.md` — 07·10·15 datacollector 행 legacy 이관 표기 | ✅ | L17·L20·L25 — 취소선 + legacy 경로 안내 완료 |
| 2. `docs/work_flow/specs/README.md` — 본 spec 추가 + 06~09 → 07~10 시프트 반영 | ✅ | "활성 spec 번호 현황" 절 신규 추가. 07~10 시프트 + 배경 주석 포함 |
| 3. `docs/storage/lerobot_upstream_check/README.md` — `05_datacollector_lerobot_diff.md` 행 제거 | ✅ | 해당 파일은 실존하지만(91줄), 색인(`docs/storage/README.md`의 `lerobot_upstream_check/` 서브섹션)에는 이전 커밋부터 원래 없었음 — 제거할 행 자체가 없어 DOD 실질 충족. (관련 Recommended #1 별도 기재) |
| 4. L2 grep 인계 8 파일 처리 정합 | ✅ | 12·08·09·02·03·11·ckpt_transfer 7건 모두 HTML 주석 + 인라인 정정 — 역사적 결정 보존 + 정경 경위 표기 완료 |
| 5. `orin/interactive_cli/README.md` 정정 | ✅ | 3-노드→2-노드 전환, datacollector 열 제거, deploy 절차 2-노드로 갱신 |
| 6. `dgx/interactive_cli/README.md` 정정 | ✅ | 개요·노드별 차이점·deploy 절차·후행 todo 갱신. "학습 + 데이터 수집 책임" 명시 |
| 7. Category A 영역 미수정 | ✅ | `.claude/skills/` 미변경. L111 경로 불일치는 발견만 보고·reflection 인계 |
| 8. M3 인계 항목 보고서 명시 | ✅ | §2 X2 인계 (training.py L15·L54·L70·L72 등), §3 reflection 인계 (SKILL.md L111) 명시 |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `docs/storage/lerobot_upstream_check/05_datacollector_lerobot_diff.md` | 파일이 91줄 실존함에도 task-executor 보고서 §4 및 DOD 체크에서 "파일 미존재" 로 오기재. 파일 자체는 datacollector legacy 이관 완료 후에도 `lerobot_upstream_check/` 에 잔존. 색인에서 행 제거(DOD)는 원래 없어서 충족이지만, 파일 자체의 legacy 이관·보존 여부는 reflection 시점 검토 권장 |
| 2 | `docs/storage/README.md` `lerobot_upstream_check/` 서브섹션 | `04_dgx_lerobot_diff.md` 파일이 실존하나 색인에 없음 (기존 누락 — M3 범위 외). 색인 완전성 차원에서 차기 doc 정합 todo 에서 추가 권장 |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경. `.claude/agents/`, `.claude/skills/` 미변경. SKILL.md L111 경로 불일치는 발견 보고만, 수정 X |
| B (자동 재시도 X) | ✅ | `orin/lerobot/`, `dgx/lerobot/`, `pyproject.toml` 등 미변경 |
| Coupled File Rules | ✅ | lerobot/ 코드 미변경 → `03_orin_lerobot_diff.md` 갱신 불필요. pyproject.toml 미변경 → `02_orin_pyproject_diff.md` 갱신 불필요 |
| 역사적 결정 보존 원칙 | ✅ | 본문 완전 삭제 없이 HTML 주석 + 취소선 + "정정" 안내로 처리 — 11건 모두 준수 |
| 옛 룰 (docs/storage/ bash 예시 추가 X) | ✅ | bash 명령 예시 추가 없음 |

---

## 배포 권장

READY_TO_SHIP — prod-test-runner 진입 권장.

본 todo 는 순수 문서 정합 작업이므로 prod-test-runner 는 파일 존재·링크 유효성·grep 검증으로 AUTOMATED_PASS 처리 가능.
