# TODO-O1 — Implementation cycle 2

> 작성: 2026-05-01 | task-executor | cycle: 2

## 목표

cycle 1 code-tester MAJOR_REVISIONS Critical 2건 수정:
1. `orin/inference/hil_inference.py` Category B 오분류 정정
2. `check_hardware.sh` 에 `--gate-json` 전달 — 동작 불가 오류 정정
3. (cascade) `12_interactive_cli_framework.md §5` 동일 패턴 cascade 정정

---

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `docs/storage/13_orin_cli_flow.md` | M | §1 --gate-json 제거 + §3 Category B 오분류 정정 + §6 흐름도 + §7 테이블 정정 |
| `docs/storage/12_interactive_cli_framework.md` | M | §5 run_env_check() --gate-json 제거 (cascade 정정) |
| `docs/work_flow/context/todos/O1/01_implementation.md` | M | awaits_user-B 명세에서 Category B 항목 + 03_orin_lerobot_diff.md 갱신 요청 제거 |

---

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경. `docs/storage/` + `context/todos/` 변경만.
- Coupled File Rule: `orin/lerobot/` 미변경 → `03_orin_lerobot_diff.md` 갱신 불필요 (이번 cycle 정정의 핵심 내용이기도 함).
- `check_hardware.sh` line 68~83 직접 Read 후 인자 파싱 확인 (`--mode`, `--config`, `--quiet`, `--output-json` 만 지원, `--gate-json` 미지원 확인).

---

## 변경 내용 요약

### Critical #1 수정 — Category B 오분류 정정

`orin/inference/hil_inference.py` 는 `orin/inference/` 하위 파일로, CLAUDE.md Category B 정의 (`orin/lerobot/`, `dgx/lerobot/`, `pyproject.toml`, `setup_env.sh`, `deploy_*.sh`, `.gitignore`) 에 해당하지 않는다. cycle 1 에서 이를 Category B 로 잘못 분류하여 awaits_user-B 명세에 불필요한 "Category B 수정 동의" 게이트와 `03_orin_lerobot_diff.md` 갱신 요청이 포함되었다. cycle 2 에서 다음을 정정했다:

- `13_orin_cli_flow.md §3`: "**Category B** (자동 재시도 X 영역, 사용자 보고 게이트 대상)" → "일반 코드 수정 (사용자 보고 게이트 없음)"
- `13_orin_cli_flow.md §7`: "Category B 해당 여부" 행 → "수정 분류: 일반 코드 수정 (orin/inference/ — Category B 비해당)" 행으로 교체
- `01_implementation.md` awaits_user-B 추가 결정 사항: "Category B 수정 동의" 안내 제거 → "일반 코드 수정, O2 에서 자동 처리" 로 교체
- `01_implementation.md` 다음 단계 권고 섹션: 3번 항목 "hil_inference.py 수정 동의 (Category B)" 제거, `03_orin_lerobot_diff.md` 갱신 요청 제거 → 3가지 결정 사항으로 정리
- `01_implementation.md` 잔여 리스크: "Category B — 사용자 명시 동의 필요" → "일반 코드 수정, O2 에서 자동 처리 가능"

### Critical #2 수정 — check_hardware.sh --gate-json 오류 정정

`check_hardware.sh` (orin/tests/check_hardware.sh) 의 인자 파싱은 line 68~83 에서 `--mode`, `--config`, `--quiet`, `--output-json` 만 지원한다. 알 수 없는 인자 수신 시 `[ERROR] 알 수 없는 인자: --gate-json` + `usage()` (exit 2) 를 호출한다. cycle 1 에서 `12_interactive_cli_framework.md §5` 의 동일 오류 패턴을 그대로 복사한 결과, `run_env_check()` 가 항상 exit 2 로 실패하는 구조가 되었다. 정정 내용:

- `13_orin_cli_flow.md §1` run_env_check() 예시: `"--gate-json", str(config_dir)` 줄 제거, 올바른 호출 `["bash", str(check_script), "--mode", "resume"]` 로 수정, 주석에 "check_hardware.sh 지원 인자 (line 68~83)" 명기
- `13_orin_cli_flow.md §6` 흐름도: `check_hardware.sh --mode resume --gate-json orin/config/` → `check_hardware.sh --mode resume`

### Cascade 정정 — 12_interactive_cli_framework.md §5

Critical #2 의 근본 원인 파일. cycle 1 task-executor 가 이 예시를 그대로 복사했으므로 동일 오류를 cascade 정정했다:

- `12_interactive_cli_framework.md §5` run_env_check() 예시: `--gate-json` 인자 제거, 올바른 호출로 수정, 주석에 미지원 이유 명기
- `12_interactive_cli_framework.md §5` 표: orin flow 2 셀에서 `+ --gate-json 적용` 문구 제거

---

## Critical 이슈 수정 결과 (파일 라인 인용)

### Critical #1 수정 결과

**13_orin_cli_flow.md §3 (정정 후)**:
```
현재 구현에서 model ID 또는 로컬 ckpt 경로는 CLI 인자로 받지 않는다. O2 에서
`--model-id` 또는 `--ckpt-path` 인자 추가가 필요하다. `orin/inference/hil_inference.py` 는
`orin/inference/` 하위로 Category B 비해당 — 일반 코드 수정 (사용자 보고 게이트 없음).
```

**13_orin_cli_flow.md §7 테이블 (정정 후)**:
```
| 수정 분류 | 일반 코드 수정 (orin/inference/ — Category B 비해당) | 일반 코드 수정 | 일반 코드 수정 |
```

**01_implementation.md 다음 단계 권고 (정정 후)**:
```
1. 선택된 flow 구조 — 후보 A/B/C 중 하나
2. ckpt 선택 소스 조합 — 지원할 소스 조합 4가지
3. 시연 데모 모드 포함 여부 — 포함 (A·C) 또는 미포함 (B)
```
(Category B 수정 동의 항목 + 03_orin_lerobot_diff.md 갱신 요청 제거 완료)

### Critical #2 수정 결과

**check_hardware.sh line 68~83 확인 결과**:
```bash
while [[ $# -gt 0 ]]; do
    case "$1" in
        --mode)  MODE="$2"; shift 2 ;;
        --config) CONFIG_FILE="$2"; shift 2 ;;
        --quiet) QUIET=true; shift ;;
        --output-json) OUTPUT_JSON="$2"; shift 2 ;;
        -h|--help) usage ;;
        *) echo "[ERROR] 알 수 없는 인자: $1"; usage ;;
    esac
done
```
`--gate-json` 은 지원하지 않음 — 전달 시 exit 2.

**13_orin_cli_flow.md §1 정정 후**:
```python
result = subprocess.run(
    ["bash", str(check_script), "--mode", "resume"],
    check=False
)
```

**13_orin_cli_flow.md §6 흐름도 정정 후**:
```
└─ check_hardware.sh --mode resume
     → exit 0: 계속 / exit 1: 오류 안내 + 종료
```

### F1 §5 cascade 정정 결과

**12_interactive_cli_framework.md §5 run_env_check() 정정 후**:
```python
result = subprocess.run(
    ["bash", str(check_script), "--mode", "resume"],
    check=False
)
```
주석: `# --gate-json 은 hil_inference.py 전용 — check_hardware.sh 에 전달하면 exit 2 로 실패`

**12_interactive_cli_framework.md §5 표 정정 후**:
```
| **orin** | env_check.py — check_hardware.sh --mode resume 호출 | ...
```
(`+ --gate-json 적용` 문구 제거)

---

## awaits_user-B 발송 명세 최종본

사용자에게 전달할 3가지 결정 사항:

1. **flow 구조 선택 (A/B/C)**: 후보 A (3단계 순차), B (2단계 통합), C (4단계 재실행 루프) 중 선택 또는 변형
2. **ckpt 선택 소스 조합**: 지원할 소스 조합 결정
   - (1) HF Hub repo_id 입력 여부
   - (2) 로컬 ckpt 경로 직접 입력 여부
   - (3) orin/checkpoints/ 자동 탐색 제안 여부
   - (4) 기본값 smolvla_base 고정 여부
3. **시연 데모 모드 포함 여부**: 포함 시 "로봇이 움직이고 있습니다" + Ctrl+C 안내 (후보 A·C), 미포함 시 hil_inference stdout 그대로 (후보 B)

`orin/inference/hil_inference.py` 수정은 일반 코드 수정 (Category B 비해당) — 사용자 동의 항목에서 제외, O2 에서 자동 처리.

---

## 직전 피드백 반영

| Critical 이슈 | 수정 |
|---|---|
| `orin/inference/hil_inference.py` 를 Category B 로 잘못 분류 (`13_orin_cli_flow.md §3`, `§7`, `01_implementation.md:45, 119, 139~140`) | `13_orin_cli_flow.md §3`: "Category B" → "일반 코드 수정 (Category B 비해당)". `§7` 테이블 행 교체. `01_implementation.md` awaits_user-B 에서 "Category B 수정 동의" + `03_orin_lerobot_diff.md` 갱신 요청 제거. 3가지 결정 사항으로 정리. |
| `run_env_check()` 에서 `check_hardware.sh` 에 `--gate-json` 전달 — exit 2 실패 (`13_orin_cli_flow.md §1`) | `§1` + `§6` 흐름도에서 `--gate-json` 제거. 올바른 호출 `["bash", str(check_script), "--mode", "resume"]` 적용. 주석에 미지원 이유 명기. |
| (cascade) `12_interactive_cli_framework.md §5` 동일 패턴 | `§5` run_env_check() 예시에서 `--gate-json` 제거. `§5` 표에서 `--gate-json 적용` 문구 제거. |
