# TODO-W3 — Prod Test

> 작성: 2026-05-03 | prod-test-runner | cycle: 1

## Verdict

**`AUTOMATED_PASS`**

## 배포 대상

없음 — 문서 변경 (docs/storage/, specs/BACKLOG.md). Orin/DGX 배포 불필요.

## 배포 결과

- 명령: 해당 없음 (orin/·dgx/ 코드 변경 없으므로 배포 스크립트 실행 불필요)
- 결과: N/A

## 자동 비대화형 검증 결과 (AUTO_LOCAL)

| 검증 | 명령 | 결과 |
|---|---|---|
| 신규 절차 섹션 존재 | `grep -n "upstream 동기화 시 entrypoint 정리 절차" 02_orin_pyproject_diff.md` | L216 섹션 헤더 확인 |
| 6단계 절차 완전성 | python3 분석 (L216~261) | 단계 1~6 모두 존재 — 6개 확인 |
| 유지 entrypoint 9개 목록 vs orin/pyproject.toml | `grep -n "lerobot-calibrate\|lerobot-find-cameras\|..." orin/pyproject.toml` | 유지 9개 완전 일치 (L51~59) |
| 제거 entrypoint 2개 확인 | `grep -n "lerobot-eval\|lerobot-train" orin/pyproject.toml` | L60 주석 1건만 — 실제 활성 등록 없음 확인 |
| 재확인 항목 cross-ref 보강 | `grep -n "(아래 절차 참조)" 02_orin_pyproject_diff.md` | "(아래 절차 참조)" 존재 확인 |
| BACKLOG 04 #1 완료 마킹 | `grep -n "04.*#1\|entrypoint\|W3" BACKLOG.md` | L87 "완료 (07 W3 명문화 — 02_orin_pyproject_diff.md 에 동기화 절차 섹션 추가, 2026-05-03)" 확인 |
| docs/reference/ 변경 0건 | `git diff -- docs/reference/` | 0줄 |
| .claude/ 변경 0건 (W3 영역) | `git diff -- .claude/` | W3 변경 없음 (settings.json 변경은 P 그룹 산출물) |

## DOD 자동 부합

| DOD 항목 | 자동 검증 | 결과 |
|---|---|---|
| 1. 절차 6단계 실행 가능 안내 | yes (python3 단계 탐색) | ✅ 1=Read 확인, 2=유지 9개 표, 3=제거 2개 표, 4=재추가 시 삭제, 5=신규 entrypoint 판단, 6=후속 이력·Coupled File |
| 2. 유지/제거 entrypoint 표 현 pyproject.toml 일치 | yes (grep 대조) | ✅ 유지 9개·제거 2개 완전 일치 |
| 3. 04 BACKLOG #1 원문 의도 충족 | yes (섹션 존재 + grep) | ✅ "동기화 절차 명문화" → 02_orin_pyproject_diff.md L216 신규 섹션 |
| 4. 재확인 항목 [project.scripts] cross-ref 보강 | yes (grep) | ✅ "(아래 절차 참조)" 추가 확인 |
| 5. BACKLOG 04 #1 마킹 형식·날짜 | yes (grep) | ✅ 형식·날짜 (2026-05-03) 정확 |
| 6. Category A (.claude/) 변경 X | yes (git diff) | ✅ SKILL.md 미변경, storage 문서 경로 선택 준수 |
| 7. Coupled File Rule — pyproject.toml 직접 미변경 → setup_env.sh 갱신 불요 판단 | yes (git diff orin/pyproject.toml 확인) | ✅ pyproject.toml 미변경 — Rule 1 트리거 없음 |

DOD 전 항목 자동 검증으로 충족.

## 사용자 실물 검증 필요 사항

없음. 문서 절차 명문화 — 하드웨어·환경 의존 없음.

## CLAUDE.md 준수

- Category A 영역 변경: 없음 (`docs/reference/`·`.claude/` 미변경)
- Category B 영역 변경된 배포: 해당 없음 (`orin/pyproject.toml`·`setup_env.sh`·`deploy_*.sh` 미변경)
- 자율 영역만 사용: yes (로컬 정적 확인)
- Coupled File Rule: pyproject.toml 직접 미변경 → setup_env.sh 갱신 불요 판단 올바름
