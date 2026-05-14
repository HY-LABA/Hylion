# TODO-O3 — Implementation

> 작성: 2026-05-03 | task-executor | cycle: 1

## 목표

`orin/scripts/setup_env.sh` 에 dpkg 사전 체크 (BACKLOG #8) + torchvision wheel 자동 설치 (BACKLOG #7) 추가

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `orin/scripts/setup_env.sh` | M | Pre-flight dpkg 체크 + 3-b torchvision 자동 설치 로직 추가 |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경. `orin/lerobot/` 미변경.
- Coupled File Rule: `orin/pyproject.toml` 변경 없음 — wheel 설치는 `setup_env.sh` 직접 처리 (torch/torchvision 은 pyproject.toml 이 아닌 setup_env.sh 에서 관리 — SKILL.md §1.a 명시).
- `docs/storage/lerobot_upstream_check/02_orin_pyproject_diff.md` 갱신 불요 (pyproject 미변경).
- Category B: spec 합의 (결정 C) — 사용자 동의 완료.
- lerobot-reference-usage: setup_env.sh 는 레퍼런스 파일이 아닌 운영 스크립트. SKILL_GAP 해당 없음.

## 변경 내용 요약

### 변경 1 — Pre-flight dpkg 체크 (BACKLOG #8)

`set -e` 직후, `SMOLVLA_DIR` 정의 이전에 dpkg 중단 상태 체크 블록 추가.

```bash
if dpkg --audit 2>&1 | grep -q .; then
    echo "[setup] ERROR: dpkg 중단 상태가 감지되었습니다."
    echo "[setup]   아래 명령을 먼저 실행하여 복구한 후 재시도하세요:"
    echo "[setup]     sudo dpkg --configure -a"
    echo "[setup]   복구 후: bash $(realpath "$0")"
    exit 1
fi
```

BACKLOG #8 지침 패턴과 일치:
- `dpkg --audit 2>&1 | grep -q .` — 중단 상태 발견 시 출력이 있으므로 `grep -q .` 로 유무 판별
- 사용자에게 `sudo dpkg --configure -a` 를 안내하고 exit 1. 자동 실행 X (Category B 범주 — sudo 자동 실행 금지)

### 변경 2 — torchvision wheel 자동 설치 (BACKLOG #7)

기존 섹션 3-b 에서 "수동 안내만 출력" → "로컬 wheel 파일이 있으면 자동 설치" 로 변경.

```
TORCHVISION_WHL="${SMOLVLA_DIR}/docs/storage/others/torchvision-0.20.0a0+afc54f7-cp310-cp310-linux_aarch64.whl"
```

- `SMOLVLA_DIR` 은 `orin/scripts/setup_env.sh` 기준 `orin/` → `orin/../docs/storage/others/` = `smolVLA/docs/storage/others/` 로 올바르게 해석됨
- wheel 파일 존재 시: `pip install "$TORCHVISION_WHL" --no-deps --force-reinstall --quiet` 자동 실행
- wheel 파일 미존재 시 (Orin 에 docs/storage 미동기): scp 전송 안내 + 재실행 안내 출력 (graceful fallback)
- `import torchvision` 이미 성공 시: 버전만 출력하고 스킵 (재실행 안전)

wheel 파일은 devPC 에 `docs/storage/others/torchvision-0.20.0a0+afc54f7-cp310-cp310-linux_aarch64.whl` 로 존재 확인됨 (`ls` 명시 확인).

## code-tester 입장에서 검증 권장 사항

- 문법: `bash -n orin/scripts/setup_env.sh` — PASS 확인됨
- dpkg 체크 존재 확인: `grep -n "dpkg --audit" orin/scripts/setup_env.sh` — Pre-flight 블록
- torchvision 자동 설치 존재 확인: `grep -n "TORCHVISION_WHL\|pip install.*TORCHVISION" orin/scripts/setup_env.sh`
- BACKLOG #7 DOD: wheel 경로 변수 `TORCHVISION_WHL` + `pip install "$TORCHVISION_WHL"` 존재
- BACKLOG #8 DOD: `dpkg --audit` + `sudo dpkg --configure -a` 안내 + `exit 1` 존재
- pyproject 영향 X 확인: `orin/pyproject.toml` 미변경 (Coupled File Rule 충족)
- shellcheck 불가 (미설치) — `bash -n` 으로 대체

---

## Cycle 2 (MAJOR Critical 2건 처리)

> 작성: 2026-05-03 | task-executor | cycle: 2 (Category B MAJOR — spec 결정 C 안에서 진행)

### 직전 피드백 반영

| Critical 이슈 | 수정 |
|---|---|
| C1: TORCHVISION_WHL 경로 버그 — `SMOLVLA_DIR`(=orin/) 기반 경로가 잘못 계산되어 wheel 항상 미발견 | `SMOLVLA_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"` 신규 추가 + `TORCHVISION_WHL="${SMOLVLA_ROOT}/docs/storage/others/..."` 로 정정 |
| C2: BACKLOG.md 02섹션 #7·#8 마킹 누락 | `docs/work_flow/specs/BACKLOG.md` #7·#8 상태 "완료 (07 O3, ...)" 로 갱신 |
| R1: 헤더 주석 경로 오기 (Recommended) | L3 `~/smolvla/scripts/setup_env.sh` → `~/smolvla/orin/scripts/setup_env.sh` 정정 |

### Cycle 2 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `orin/scripts/setup_env.sh` | M | SMOLVLA_ROOT 변수 추가 + TORCHVISION_WHL 경로 SMOLVLA_ROOT 기반으로 정정 + 헤더 주석 경로 오기 정정 |
| `docs/work_flow/specs/BACKLOG.md` | M | 02_dgx_setting #7·#8 상태 "미완" → "완료 (07 O3, 2026-05-03)" 마킹 |

### Cycle 2 변경 내용

**C1 — TORCHVISION_WHL 경로 정정**

`SMOLVLA_DIR`은 `orin/scripts/` 기준 `..` = `orin/` 디렉터리. 따라서 기존 `${SMOLVLA_DIR}/docs/storage/others/` = `~/smolvla/orin/docs/storage/others/` (존재 X). 실제 wheel 위치는 `~/smolvla/docs/storage/others/` (smolVLA 루트). 수정: `SMOLVLA_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"` (smolVLA 루트 계산) 를 SMOLVLA_DIR 다음 줄에 추가하고 TORCHVISION_WHL 경로를 `${SMOLVLA_ROOT}/docs/storage/others/...` 로 교체.

경로 시뮬레이션 검증 (devPC):
- `SMOLVLA_DIR` = `~/smolvla/orin` (정상, lerobot install 등 기존 사용처 그대로)
- `SMOLVLA_ROOT` = `~/smolvla` (신규, smolVLA 루트)
- `[ -f "$TORCHVISION_WHL" ]` = true (wheel 파일 존재 확인됨)

**C2 — BACKLOG 마킹**

`docs/work_flow/specs/BACKLOG.md` 02_dgx_setting 섹션:
- #7: 상태 "미완" → "완료 (07 O3, setup_env.sh SMOLVLA_ROOT 기반 wheel 자동 설치 경로 정정, 2026-05-03)"
- #8: 상태 "미완" → "완료 (07 O3, setup_env.sh pre-flight dpkg 사전 체크 + 안내 추가, 2026-05-03)"

**R1 — 헤더 주석 경로 오기**

L3 `~/smolvla/scripts/setup_env.sh` → `~/smolvla/orin/scripts/setup_env.sh` (실제 경로와 일치하도록 정정)

### Cycle 2 검증 결과

```
bash -n orin/scripts/setup_env.sh → EXIT: 0 (SYNTAX OK)
SMOLVLA_ROOT 경로 시뮬레이션 → wheel 존재 확인: [ -f "$TORCHVISION_WHL" ] = true
grep -n "SMOLVLA_ROOT" → L28: 존재
grep -n "TORCHVISION_WHL" → L108: SMOLVLA_ROOT 기반 경로 확인
BACKLOG.md #7·#8 → "완료 (07 O3, ...)" 마킹 확인
```

### prod-test-runner 진입 가능 여부

Critical 2건 정정 완료. bash -n PASS. DOD 전 항목 충족:
- DOD #1: torchvision wheel 자동 설치 — SMOLVLA_ROOT 기반 경로 정정으로 `[ -f "$TORCHVISION_WHL" ]` true → 자동 설치 분기 실행 가능
- DOD #2: dpkg 사전 체크 — cycle 1 구현 그대로 유지 (변경 없음)
- DOD #3: BACKLOG #7·#8 마킹 — 완료

메인 판단에 따라 code-tester 재검증 또는 prod-test-runner 직진 가능.
