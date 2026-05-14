# TODO-X5 — Code Test

> 작성: 2026-05-02 | code-tester | cycle: 1

## Verdict

**`MINOR_REVISIONS`**

Critical 0건. Recommended 3건.

---

## 단위 테스트 결과

```
해당 없음 — setup_train_env.sh 는 shell script (Python 단위 테스트 대상 X).
bash -n 문법 검증으로 대체.

$ bash -n dgx/scripts/setup_train_env.sh
exit code: 0  — PASS
```

## Lint·Type 결과

```
ruff / mypy: 해당 없음 (bash script).
shellcheck: 시스템 미설치 — bash -n 으로 대체 (task-executor 보고서 §3 동일 확인).

수동 패턴 점검:
- set -e 선언 존재 (line 14) ✓
- pip install 다중행 백슬래시 연속 — 마지막 패키지 인수 직후 --quiet 로 종결 ✓
- echo 문자열 인용부호 정합 ✓
- here-doc (§4 activate 스크립트) 올바른 EOF 처리 ✓
- 변수 참조 모두 "${...}" 형식 (공백 안전) ✓
```

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. dgx/scripts/setup_env.sh §3 직후 extras 설치 step 추가 | ✅ | 실제 파일명 setup_train_env.sh — spec 오기재. §3 lerobot editable 설치 직후 §3-c 블록 삽입 (line 68~97) |
| 2. record + hardware + feetech extras 설치 | ✅ | 2단계 pip install — torchcodec cu130 인덱스 + 나머지 9개 PyPI 기본 인덱스 |
| 3. bash -n 정적 검증 통과 | ✅ | exit code 0 직접 실행 확인 |
| 4. X4 Option B 채택 (pyproject.toml 미변경) | ✅ | dgx/pyproject.toml 수정 없음 확인 (git diff 기준) |
| 5. 기존 §1~§5 미손상 | ✅ | git diff 확인 — §3 직후 삽입, §4 이하 원본 그대로 보존 |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `setup_train_env.sh` §3-c, torchcodec 1단계 echo | echo 메시지가 `"torchcodec 0.10.0+cu130 설치 중"` 이나 실제 설치는 범위 `>=0.3.0,<0.11.0` — 메시지가 0.10.0 고정처럼 오해 유발. `"torchcodec (>=0.3.0,<0.11.0, cu130 인덱스) 설치 중..."` 으로 수정 권고 (Minor) |
| 2 | `setup_train_env.sh` §3-c 내 torchcodec 1단계 주석 | `먼저 설치하면 이후 pip install (dataset extras 내 torchcodec 조건) 이 재설치 없이 skip` — Option B 에서는 pyproject.toml extras 조건이 없으므로 이 설명이 맥락상 부정확. "이후 일반 pip install 명령에서 torchcodec 조건 중복 없이 skip" 으로 표현 수정 권고 (Minor, 동작에 무영향) |
| 3 | 변경 이력 보존 | `dgx/scripts/setup_train_env.sh` 는 Category B 영역. CLAUDE.md Coupled File Rule 1 은 `orin/pyproject.toml` 수정 시만 적용 (비활성 — 정확). 그러나 `dgx/scripts/` script 수정에 대한 변경 이력 기록 위치가 명확하지 않음. 본 spec `01_implementation.md` §1 에 이유·날짜가 문서화되어 있으나, 별도 `docs/storage/lerobot_upstream_check/` 또는 `docs/storage/09_dgx_structure.md` 에 §3-c 블록 추가 날짜·사유 한 줄 기재 권고 (향후 스크립트 유지보수 참조점). |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/`, `.claude/agents/*.md`, `.claude/skills/**/*.md`, `.claude/settings.json` 미변경 |
| B (자동 재시도 X) | ✅ | `dgx/scripts/setup_train_env.sh` 는 Category B 영역 (`scripts/deploy_*.sh` 유사 패턴 + spec 본문 §잔여리스크 명시). 사용자 동의 (결정 I, Option B 채택) 이미 확보 후 진행 — 정합 |
| Coupled File Rule 1 | ✅ (비활성) | `orin/pyproject.toml` 미변경, `dgx/pyproject.toml` 미변경 → Rule 1 비해당. 단 Recommended #3 (이력 기록 위치) 참조 |
| 옛 룰 | ✅ | `docs/storage/` 하위 bash 예시 추가 없음 |

---

## 세부 검증 결과

### 1. torchcodec 두 단계 분리 설치

- 1단계 (`line 77-80`): `pip install 'torchcodec>=0.3.0,<0.11.0' --index-url https://download.pytorch.org/whl/cu130 --quiet` — 분리 정확
- 2단계 (`line 87-97`): 9개 패키지 `--index-url` 없이 PyPI 기본 인덱스 설치 — 정확
- 분리 사유 주석 (`line 71-75`): "cu130 인덱스 별도 지정 필요" 설명 존재 — 표현 일부 개선 여지 (Recommended #1, #2)

### 2. 패키지 목록 정합 (레퍼런스 직접 대조)

`docs/storage/legacy/02_datacollector_separate_node/datacollector/pyproject.toml` line 40-61 직접 Read 후 대조:

| 패키지 | pyproject.toml 버전 | setup_train_env.sh 버전 | 일치 |
|---|---|---|---|
| datasets | `>=4.0.0,<5.0.0` | `>=4.0.0,<5.0.0` | ✅ |
| pandas | `>=2.0.0,<3.0.0` | `>=2.0.0,<3.0.0` | ✅ |
| pyarrow | `>=21.0.0,<30.0.0` | `>=21.0.0,<30.0.0` | ✅ |
| av | `>=15.0.0,<16.0.0` | `>=15.0.0,<16.0.0` | ✅ |
| torchcodec | `>=0.3.0,<0.11.0; sys_platform == 'linux' and platform_machine == 'x86_64'` | `>=0.3.0,<0.11.0` (1단계 별도) | ✅ — 플랫폼 조건 생략은 DGX = x86_64 Linux 고정 환경이므로 무해 |
| jsonlines | `>=4.0.0,<5.0.0` | `>=4.0.0,<5.0.0` | ✅ |
| pynput | `>=1.7.8,<1.9.0` | `>=1.7.8,<1.9.0` | ✅ |
| pyserial | `>=3.5,<4.0` | `>=3.5,<4.0` | ✅ |
| deepdiff | `>=7.0.1,<9.0.0` | `>=7.0.1,<9.0.0` | ✅ |
| feetech-servo-sdk | `>=1.0.0,<2.0.0` | `>=1.0.0,<2.0.0` | ✅ |

중복 처리: `pyserial`, `deepdiff` 는 hardware·feetech 양쪽 정의 → 단 한 번씩 나열 (pip skip 동작 정상) ✅

총 10개 고유 패키지 (torchcodec 포함) 모두 버전 범위 정확 인용 확인. 누락 없음.

### 3. 기존 §3 미변경

git diff 확인 결과: `pip install -e "${LEROBOT_SRC}[smolvla,training]" --quiet` (line 66) 원본 그대로. §4~§5 (환경변수·smoke 검증) 미접촉 확인 ✅

### 4. idempotent 정합

pip 기본 동작 (이미 설치된 버전 범위 충족 시 "Requirement already satisfied" skip) 으로 재실행 안전. 추가 flag 불요 — 정합 ✅.
§4 `if ! grep -q "${ENV_MARKER}"` 가드도 환경변수 블록 중복 추가 방지 — 이중 idempotent 확보 ✅

### 5. bash -n 자체 검증

직접 실행 결과: `exit code: 0` — PASS ✅

### 6. 파일명 오기재 인계

보고서 §5 `잔여 리스크` 표 마지막 항목에 `spec/TODO 에 setup_env.sh 로 표기되어 있으나 실제 DGX 파일은 setup_train_env.sh` 명시 — 정합 ✅. (이 불일치는 X5 외부 문제이며 본 검증 범위 밖)

---

## 배포 권장

MINOR_REVISIONS — prod-test-runner 진입 권장.

Critical 이슈 없음. Recommended 3건은 동작에 영향 없는 문서 표현·이력 기재 권고이며, task-executor 1회 추가 수정 후 재검증 없이 prod-test 진입 가능.

**Category B 영역 메모**: `dgx/scripts/setup_train_env.sh` 는 CLAUDE.md Category B 영역. 본 cycle에서 Critical 0건이므로 MAJOR_REVISIONS 미해당 — 사용자 보고 게이트 불발동. prod-test-runner 가 DGX 실물 설치 검증 시 torchcodec cu130 wheel 가용성 (Recommended #1 관련 `>=0.3.0,<0.11.0` 범위 내 실제 wheel 존재 여부) 확인 필요.
