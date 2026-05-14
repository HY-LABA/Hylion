# TODO-O3 — Prod Test

> 작성: 2026-05-03 | prod-test-runner | cycle: 2

## Verdict

**`AUTOMATED_PASS`**

## 배포 대상

- 없음 (AUTO_LOCAL — devPC 정적 검증 + 경로 시뮬만. SSH 배포 불요)

## 배포 결과

- 대상: `orin/scripts/setup_env.sh` (Category B — spec 결정 C 사용자 동의 완료)
- 배포 명령: 해당 없음 (AUTO_LOCAL 환경 레벨 — SSH 배포 불요)
- 결과: 해당 없음

## 자동 비대화형 검증 결과

| 검증 | 명령 | 결과 |
|---|---|---|
| A1. bash -n 문법 | `bash -n orin/scripts/setup_env.sh` | EXIT: 0 (PASS) |
| A2. SMOLVLA_ROOT 정의 | `grep -n "SMOLVLA_ROOT" setup_env.sh` | L28: 정의 (`$(dirname "$0")/../..`) + L108: 사용 (TORCHVISION_WHL) |
| A3. TORCHVISION_WHL 경로 | `grep -n "TORCHVISION_WHL=" setup_env.sh` | L108: `"${SMOLVLA_ROOT}/docs/storage/others/torchvision-..."` — SMOLVLA_ROOT 기반 ✓ |
| B1. wheel 파일 실존 | `ls docs/storage/others/torchvision-0.20.0a0+afc54f7-...whl` | EXISTS ✓ |
| B2. 경로 시뮬 | devPC 기준 시뮬레이션 실행 | SMOLVLA_DIR=smolVLA/orin, SMOLVLA_ROOT=smolVLA/, `[ -f "$TORCHVISION_WHL" ]` = true ✓ |
| C1. SMOLVLA_DIR 회귀 | `grep -n "SMOLVLA_DIR"` spot-check | L27(정의), L29(VENV_DIR), L38(echo), L88(echo), L89(pip install -e), L175(예시) — 모두 orin/ 기준 의도와 일치, 회귀 없음 ✓ |
| D1. dpkg --audit 존재 | `grep -n "dpkg --audit"` | L19: `if dpkg --audit 2>&1 | grep -q .` ✓ |
| D2. sudo 안내만 (자동 실행 X) | `grep -n "sudo dpkg --configure"` | L22: echo 안내만, 자동 실행 X ✓ |
| D3. exit 1 존재 | `grep -n "exit 1"` | L24: dpkg 블록 내 exit 1 ✓ |
| E1. BACKLOG #7 마킹 | BACKLOG.md 02 섹션 #7 상태 | "완료 (07 O3, setup_env.sh SMOLVLA_ROOT 기반 wheel 자동 설치 경로 정정, 2026-05-03)" ✓ |
| E2. BACKLOG #8 마킹 | BACKLOG.md 02 섹션 #8 상태 | "완료 (07 O3, setup_env.sh pre-flight dpkg 사전 체크 + 안내 추가, 2026-05-03)" ✓ |
| F1. orin/lerobot 미변경 | `git diff HEAD -- orin/lerobot/` | 0 라인 ✓ |
| F2. orin/pyproject.toml 미변경 | `git diff HEAD -- orin/pyproject.toml` | 0 라인 ✓ |
| F3. 헤더 주석 경로 정정 (R1) | L3 확인 | `~/smolvla/orin/scripts/setup_env.sh` ✓ (cycle 2 R1 정정 완료) |

## DOD 자동 부합

| DOD 항목 | 자동 검증 | 결과 |
|---|---|---|
| 1. 02 BACKLOG #7: torchvision wheel 자동 설치 step 추가 | yes — SMOLVLA_ROOT 경로 정합 + wheel 실존 + pip install 분기 | ✓ PASS (SMOLVLA_ROOT 기반, `[ -f "$TORCHVISION_WHL" ]` = true 시뮬 확인) |
| 2. 02 BACKLOG #8: dpkg 체크 + 안내 (sudo dpkg --configure -a 권고 출력) | yes — grep 확인 | ✓ PASS (L19 dpkg --audit + L22 echo 안내 + L24 exit 1, sudo 자동 실행 X) |
| 3. 두 BACKLOG 항목 → "완료 (07 O3, 2026-05-03)" 마킹 | yes — BACKLOG.md 직접 확인 | ✓ PASS (#7 완료 마킹 + #8 완료 마킹) |

## 사용자 실물 검증 필요 사항

spec DOD 에 "실 셋업 검증은 새 환경에서만 (BACKLOG 유지 가능)" 명시. 정적 + 경로 시뮬 PASS 로 자동 충족 범위 충족. 아래 1건은 Phase 3 BACKLOG 이관:

1. **새 Orin 환경 셋업 시 setup_env.sh 실 동작 확인** — 환경 의존 (새 venv 생성 상황에서만 자연 검증 가능). 현 Orin venv `.hylion_arm` 재생성 시 또는 신규 Orin 셋업 시 자연 검증.

→ spec DOD 는 위 1건을 BACKLOG 유지로 명시 허용. verification_queue 에는 등재하지 않음 (spec 자체에 "BACKLOG 유지 가능" 명시됨).

## CLAUDE.md 준수

| Category | 상태 | 메모 |
|---|---|---|
| Category A (절대 금지 영역) | ✓ | `docs/reference/` 미변경, `.claude/agents/`·`.claude/skills/` 미변경 |
| Category B (`setup_env.sh`) | ✓ | spec 결정 C 사용자 동의 완료 + cycle 2 진행은 orchestrator 결정으로 진행 |
| Category B (자율성) | ✓ | AUTO_LOCAL 검증만 — SSH 배포 없음. deploy_orin.sh 미실행 (불요) |
| Category D | ✓ | rm -rf·sudo 자동 실행 없음 |
| Coupled File Rule | ✓ | orin/pyproject.toml 미변경 → 02_orin_pyproject_diff.md 갱신 불요. orin/lerobot/ 미변경 |
| 옛 룰 (docs/storage/ bash 예시) | ✓ | docs/storage/ 미변경 |

## 비고

- Category B 영역 (`orin/scripts/setup_env.sh`) 변경 — spec 결정 C (Phase 1 사용자 동의 완료) 안에서 진행. orchestrator 가 사용자 동의 확인 후 cycle 2 dispatch 진행.
- AUTO_LOCAL 환경 레벨: devPC 정적 검증 + 경로 시뮬로 모든 DOD 자동 충족. SSH 배포 미실행 (setup_env.sh 는 오리진 실행 스크립트 — devPC 에서 배포해도 Orin 에서 실 실행 필요, 이는 spec DOD 가 BACKLOG 허용).
- 실 새 환경 셋업 검증은 spec 자체에서 BACKLOG 허용으로 명시. AUTOMATED_PASS 판단 근거: DOD 3항 전부 자동 충족 + 사용자 실물 검증 필요 항목 spec 허용 BACKLOG — verification_queue 미등재.
