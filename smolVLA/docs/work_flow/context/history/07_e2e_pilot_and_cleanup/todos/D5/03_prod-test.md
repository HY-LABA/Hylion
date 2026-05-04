# TODO-D5 — Prod Test

> 작성: 2026-05-03 | prod-test-runner | cycle: 1

## Verdict

**`NEEDS_USER_VERIFICATION`**

자동 정적 검증 5항목 전체 PASS. DOD 항목 자동 충족 가능한 것 모두 PASS. 단 "새 환경에서 setup_train_env.sh 재실행 후 lerobot-find-port 정상 동작" 은 실 DGX 재설치 없이 검증 불가 — verification_queue 에 PHYS_REQUIRED 류 항목 추가.

---

## 배포 대상

- DGX / AUTO_LOCAL (배포 스크립트 불실행 — 변경 파일이 스크립트 + 문서 파일이며 실 환경 재실행 의도 없음)
- Category B (`dgx/scripts/setup_train_env.sh`) — 사용자 동의 (결정 C 옵션) 수령 완료

---

## 배포 결과

- 명령: `deploy_dgx.sh` 미실행 (AUTO_LOCAL 정적 검증 범위 — 실 DGX venv 재설치는 사용자 Phase 3 대상)
- 결과: N/A (정적 검증으로 대체)

---

## 자동 비대화형 검증 결과

| # | 검증 항목 | 명령 | 결과 |
|---|---|---|---|
| A-1 | bash 구문 검증 | `bash -n dgx/scripts/setup_train_env.sh` | PASS (exit_code=0) |
| A-2 | extras 갱신 라인 존재 | `grep -En "smolvla.*training.*hardware.*feetech" dgx/scripts/setup_train_env.sh` | 1건 발견 (L77) |
| B-1 | lerobot upstream `hardware` 키 spot-check | `sed -n '108,118p' docs/reference/lerobot/pyproject.toml` | `hardware = ["lerobot[pynput-dep]", "lerobot[pyserial-dep]", "lerobot[deepdiff-dep]"]` L110 확인 |
| B-2 | lerobot upstream `feetech` 키 spot-check | `sed -n '143,147p' docs/reference/lerobot/pyproject.toml` | `feetech = ["feetech-servo-sdk>=1.0.0,<2.0.0", "lerobot[pyserial-dep]", "lerobot[deepdiff-dep]"]` L145 확인 |
| C-1 | Coupled File — 04_dgx_lerobot_diff.md 항목 | `grep -n "2026-05-03"` | L131 `[2026-05-03] dgx/scripts/setup_train_env.sh — lerobot extras hardware,feetech 추가` 확인 |
| C-2 | before/after 표 정합 | Read L137-140 | `[smolvla,training]` → `[smolvla,training,hardware,feetech]` 정합 |
| D-1 | BACKLOG 07 #3 항목 | `grep -n "§3-c\|D5"` | L145 `§3-c 정리 — D5 extras 통합 후 중복 라인 제거` 항목 확인 |
| E-1 | pyserial 충돌 분석 | 정적 분석 (실행 X) | pyserial-dep `>=3.5,<4.0` — DGX 즉석 설치 pyserial 3.5 범위 내 → pip no-op 보장 (code-tester L90 교차 확인 일치) |
| F-1 | dgx/lerobot/ 변경 없음 | `git diff HEAD -- dgx/lerobot/` | 출력 없음 (변경 0건) |
| F-2 | dgx/pyproject.toml 변경 없음 | `git diff HEAD -- dgx/pyproject.toml` | 출력 없음 (파일 미존재 — Option B 유지) |
| F-3 | docs/reference/ 변경 없음 | `git diff HEAD -- docs/reference/` | 출력 없음 (변경 0건) |
| F-4 | .claude/ 변경 없음 | `git diff HEAD -- .claude/` | settings.json 만 변경 (D5 외 별도 변경 — D5 산출물 X) |

---

## DOD 자동 부합

| DOD 항목 | 자동 검증 | 결과 |
|---|---|---|
| 1. §3 extras `[smolvla,training,hardware,feetech]` 로 갱신 | yes (grep) | ✅ L77 확인 |
| 2. extras 키 이름이 lerobot upstream pyproject.toml 과 일치 | yes (sed spot-check) | ✅ hardware L110, feetech L145 직접 확인 |
| 3. §3-c 주석 갱신 — §3 extras 통합 완료 명시 | yes (git diff Read) | ✅ L81-82 "07 TODO-D5 이후: hardware·feetech extras 는 §3 의 editable install extras 로 통합 완료" |
| 4. §3-c 기존 패키지 미삭제 (pip no-op 보장) | yes (git diff Read) | ✅ pynput·pyserial·deepdiff·feetech-servo-sdk 라인 유지 확인 |
| 5. 04_dgx_lerobot_diff.md 변경 이력 항목 추가 | yes (grep) | ✅ L131 2026-05-03 항목, before/after 표·이유·upstream 인용·Option B 선언 포함 |
| 6. BACKLOG 07 #3 항목 추가 | yes (grep) | ✅ L145 §3-c 정리 후보 항목 확인 |
| 7. dgx/lerobot/ 변경 X (Option B) | yes (git diff) | ✅ 변경 0건 |
| 8. dgx/pyproject.toml 변경 X (06 X4 결정) | yes (git diff) | ✅ 파일 미존재 유지 확인 |
| 9. docs/reference/lerobot/ 변경 X (Category A) | yes (git diff) | ✅ 변경 0건 |
| 10. 새 환경에서 setup_train_env.sh 재실행 후 lerobot-find-port 정상 동작 | no (실 재실행 필요) | → verification_queue (PHYS_REQUIRED 류) |

---

## 사용자 실물 검증 필요 사항 (verification_queue 추가됨)

1. 새 DGX venv 셋업 또는 setup_train_env.sh 재실행 시 `lerobot-find-port` 정상 동작 확인 — pyserial ImportError 미발생, entrypoint 실행 성공

   (현 DGX 환경은 07 D4 즉석 설치로 pyserial 3.5 이미 설치됨. 재실행 시 lerobot[hardware,feetech] extras 가 pyserial 범위 내 버전 no-op 처리 예상 — 실 확인은 시연장 셋업 시 자연 수행 기회 있음)

---

## CLAUDE.md 준수

| 항목 | 결과 |
|---|---|
| Category B (`setup_train_env.sh`) 변경 — 사용자 동의 | ✅ 결정 C 옵션 수령 후 진행 |
| Category A (`docs/reference/`, `.claude/agents/`, `.claude/skills/`) 변경 X | ✅ 확인 |
| 자율 영역만 실행 (AUTO_LOCAL 정적 검증) | ✅ bash -n·grep·git diff·Read only |
| 실 DGX venv 재실행 (환경 재구성) — 동의 영역 → 미실행 | ✅ verification_queue 위임 |
