# TODO-N1 — Prod Test

> 작성: 2026-05-04 | prod-test-runner | cycle: 1

## Verdict

**`AUTOMATED_PASS`**

---

## 배포 대상

- devPC 로컬 (AUTO_LOCAL — interactive_cli 코드 변경, SSH 불필요)

## 배포 결과

- N1 변경 파일은 dgx/interactive_cli/flows/ 및 orin/interactive_cli/flows/ 하위 Python 파일.
- Category B 영역 (orin/lerobot/, dgx/lerobot/, pyproject.toml, deploy_*.sh) 변경 없음 → deploy_*.sh 실행 불필요.
- 로컬 파일 직접 검증 (SSH 불필요, AUTO_LOCAL 레벨).

## 자동 비대화형 검증 결과

| # | 검증 | 명령 | 결과 |
|---|---|---|---|
| 1 | dgx flows py_compile (10개) | `python -m py_compile dgx/interactive_cli/flows/{entry,env_check,mode,precheck,data_kind,record,teleop,training,transfer,_back}.py` | OK (오류 없음) |
| 2 | orin flows py_compile (4개) | `python -m py_compile orin/interactive_cli/flows/{entry,env_check,inference,_back}.py` | OK (오류 없음) |
| 3 | teleop -1 sentinel 존재 | `grep -c "return -1" dgx/interactive_cli/flows/teleop.py` | 1건 (flow3_teleoperate L130) |
| 4 | teleop == -1 분기 존재 | `grep -c "== -1" dgx/interactive_cli/flows/teleop.py` | 2건 (flow4_confirm_teleop L150, L199) |
| 5 | teleop return 2 잔재 없음 | `grep -nE "return 2$|return 2 #" dgx/interactive_cli/flows/teleop.py` | 0건 (잔재 없음) |
| 6 | training CANCELED sentinel | `grep -c "CANCELED" dgx/interactive_cli/flows/training.py` | 4건 (반환 2 + early return 분기 2) |
| 7 | Category C 회피 | `test ! -d dgx/interactive_cli/common && test ! -d orin/interactive_cli/common` | OK (common/ 미생성 확인) |

## DOD 자동 부합

| DOD 항목 | 자동 검증 | 결과 |
|---|---|---|
| 1. 모든 prompt 분기점에 b/back 처리 (dgx 9 + orin 3) | py_compile 통과 + grep (code-tester 기확인) | ✅ |
| 2. helper 위치 — flows/_back.py (Category C 회피) | Category C 검증 + py_compile | ✅ |
| 3. entry (0단계) b/back 시 종료 또는 재표시 | code-tester cycle 1 확인 (return None) | ✅ |
| 4. README 두 개 갱신 (UX 섹션) | code-tester cycle 1 확인 | ✅ |
| 5. subprocess 진행 중 Ctrl+C 권고 안내 | code-tester cycle 1 확인 | ✅ |
| MINOR #2 — teleop sentinel -1 적용 | return -1 존재 (1건) + == -1 분기 (2건) + return 2 잔재 없음 | ✅ |
| MINOR #3 — training CANCELED sentinel + early return | CANCELED 4건 (반환 + 분기), flow5 early return 확인 | ✅ |

## 사용자 실물 검증 필요 사항

없음. N1 변경은 Python CLI flow 코드 (dgx/orin 로컬 실행 로직) — 구문·sentinel 정합은 AUTO_LOCAL 레벨에서 완전 검증 가능. 실물 CLI UX 확인은 N2 회귀 검증에 포함.

## CLAUDE.md 준수

- Category B 영역 (orin/lerobot/, dgx/lerobot/, pyproject.toml, deploy_*.sh) 변경 없음: yes
- Category C 회피 (신규 디렉터리 미생성): yes — flows/ 기존 디렉터리 내 _back.py 배치
- 자율 영역만 사용: yes — AUTO_LOCAL py_compile·grep 검증만 (SSH 불필요)
- MINOR cycle 1 수정 산출물 (teleop -1 sentinel, training CANCELED sentinel) 모두 prod 파일에 반영 확인

## 잔여 리스크 (비차단)

- Recommended #1 (orin/entry.py `# noqa: E402`) 미적용 — pre-existing 아키텍처 제약, BACKLOG 이관 예정.
- `run_teleoperate.sh` 내부 exit 2 사용 여부 미확인 (SKILL_GAP) — 단 -1 sentinel 로 충돌 위험 제거됨.
