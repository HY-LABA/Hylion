# TODO-O3 — Code Test

> 작성: 2026-05-03 14:30 | code-tester | cycle: 1

## Verdict

**`MAJOR_REVISIONS`** — Critical 1건 (TORCHVISION_WHL 경로 논리 버그 + DOD 미충족)

---

## 단위 테스트 결과

```
bash -n orin/scripts/setup_env.sh
EXIT: 0  (문법 오류 없음)
```

pytest 해당 없음 (shell script — bash -n 으로 대체).

---

## Lint·Type 결과

```
ruff check: 해당 없음 (bash script)
shellcheck: 미설치 — bash -n 으로 대체 (task-executor 명시)

추가 grep 검증:
  grep -n "dpkg --audit"          → L19: 정상 존재
  grep -n "sudo dpkg --configure" → L22: echo 안내만, 자동 실행 X
  grep -n "exit 1"                → L24: 정상 존재
  grep -n "TORCHVISION_WHL"       → L107: 존재
  grep -n "pip install.*WHL"      → L111: 존재
```

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. BACKLOG #7: torchvision wheel 자동 설치 step 추가 | ❌ | wheel 경로 변수 존재 + pip install 로직 존재하나 **TORCHVISION_WHL 경로가 잘못 계산됨** → 항상 wheel 미발견(fallback) 분기 진입. 실질적 자동 설치 불가. |
| 2. BACKLOG #8: dpkg 체크 + 안내 (`sudo dpkg --configure -a` 권고 출력) | ✅ | L19 dpkg --audit + L22 echo 안내 + L24 exit 1. sudo 자동 실행 X (Category D 준수). |
| 3. BACKLOG #7·#8 → BACKLOG.md "완료 (07 O3, 2026-05-XX)" 마킹 | ❌ | BACKLOG.md 02섹션 #7·#8 모두 상태 "미완" 그대로. task-executor 변경 파일 목록에 BACKLOG.md 없음. |

---

## Critical 이슈

### 1. TORCHVISION_WHL 경로 논리 버그 — wheel 파일을 항상 "미발견" 으로 판단

- 위치: `orin/scripts/setup_env.sh:107`
- 코드:
  ```bash
  SMOLVLA_DIR="$(cd "$(dirname "$0")/.." && pwd)"
  # ...
  TORCHVISION_WHL="${SMOLVLA_DIR}/docs/storage/others/torchvision-...whl"
  ```
- 사유:
  - `orin/scripts/setup_env.sh` 기준 `dirname "$0"` = `orin/scripts/`
  - `$(dirname "$0")/..` = `orin/scripts/../` = `orin/`
  - 따라서 `SMOLVLA_DIR` = `~/smolvla/orin` (orin 서브디렉터리)
  - `TORCHVISION_WHL` = `~/smolvla/orin/docs/storage/others/...` → **존재 X**
  - 실제 wheel 위치: `~/smolvla/docs/storage/others/...` (smolVLA 루트 기준)
  - `[ -f "$TORCHVISION_WHL" ]` 항상 false → graceful fallback 분기만 실행
  - DOD #1 "자동 설치 step 추가" 가 기능적으로 미충족
- 검증:
  ```bash
  # 실제 실행 경로 시뮬레이션
  SMOLVLA_DIR="$(cd orin/scripts/../ && pwd)"
  # = /home/.../smolVLA/orin  ← orin 폴더 (smolVLA 루트 아님)
  ls "${SMOLVLA_DIR}/docs/storage/others/"  # No such file or directory
  ```
- 수정 요청:
  - 옵션 A: `TORCHVISION_WHL="${SMOLVLA_DIR}/../docs/storage/others/torchvision-...whl"`
  - 옵션 B: smolVLA 루트를 별도 변수로 분리
    ```bash
    SMOLVLA_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
    TORCHVISION_WHL="${SMOLVLA_ROOT}/docs/storage/others/torchvision-...whl"
    ```
  - fallback scp 안내 (L116) 는 올바른 경로(`orin:~/smolvla/docs/storage/others/`) 를 이미 사용 중 — 변수 수정 후 일관성 확인 필요

### 2. DOD #3 미충족 — BACKLOG.md 02 섹션 #7·#8 마킹 누락

- 위치: `docs/work_flow/specs/BACKLOG.md` (미변경)
- 사유: spec DOD 에 "두 BACKLOG 항목 → 완료 (07 O3, 2026-05-XX) 마킹" 명시. task-executor 변경 파일 목록에 BACKLOG.md 없음. 현재 #7·#8 상태 "미완" 그대로.
- 수정 요청: BACKLOG.md 02_dgx_setting 섹션 #7·#8 의 상태 셀을 "완료 (07 O3, setup_env.sh 자동 설치 로직 추가, 2026-05-03)" 로 갱신.
- 주의: Critical 1 (경로 버그) 수정 후 기능이 올바르게 동작하는 것을 전제로 마킹.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `orin/scripts/setup_env.sh:3` | 헤더 주석 "실행 위치: Orin (`~/smolvla/scripts/setup_env.sh`)" → `~/smolvla/orin/scripts/setup_env.sh` 로 정정 (오기) |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경, `.claude/agents/*.md`·`.claude/skills/` 미변경 |
| B (자동 재시도 X) | ✅ | `setup_env.sh` 변경 — spec 결정 C (사용자 동의 완료). MAJOR_REVISIONS 발급 시 자동 재시도 X — orchestrator 가 사용자에게 보고 후 결정. |
| B — sudo 자동 실행 X | ✅ | 신규 추가 블록에서 `sudo dpkg --configure -a` 는 echo 안내만, 자동 실행 X. (기존 L44 `sudo apt-get install` 은 변경 전부터 존재) |
| Coupled File Rule 1 (`orin/pyproject.toml`) | ✅ | pyproject.toml 미변경 — wheel 설치는 setup_env.sh 직접 관리 (SKILL.md §1.a 패턴). 02_orin_pyproject_diff.md 갱신 불요. |
| Coupled File Rule 3 (`orin/lerobot/`) | ✅ | orin/lerobot/ 미변경 |
| Category D (금지 명령) | ✅ | 신규 블록: sudo 자동 실행 X. dpkg --audit 는 일반 사용자 read-only 실행 가능. |
| 옛 룰 (docs/storage/ bash 예시 추가 X) | ✅ | docs/storage/ 미변경 |

---

## 배포 권장

**no — task-executor 재호출 필요** (단, Category B 영역이므로 자동 재시도 X)

orchestrator 판단 필요:
- Critical 이슈 2건 (경로 버그 + BACKLOG 마킹 누락) 수정 범위가 제한적 (1줄 경로 수정 + BACKLOG.md 1~2줄 갱신)
- Category B 영역 (`setup_env.sh`) MAJOR — CLAUDE.md 정책상 **자동 재시도 X, 사용자 보고 게이트**
- 수정 내용 명확하므로 사용자 확인 후 task-executor 1회 추가 dispatch (수동 승인) 권장
