# TODO-O1 — Implementation

> 작성: 2026-05-04 | task-executor | cycle: 1

## 목표

orin/interactive_cli/ flow 0~5 정적 검증 + 코드 패치 (ruff F541) + prod-test-runner 인계용 SSH 검증 시퀀스 작성 (05 O3 흡수)

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `orin/interactive_cli/flows/inference.py` | M | ruff F541 4건 수정 — f-string without placeholder 제거 |

변경 없음 (정적 검증 PASS 확인):
- `orin/interactive_cli/flows/entry.py` — 수정 불요
- `orin/interactive_cli/flows/env_check.py` — 수정 불요
- `orin/interactive_cli/flows/__init__.py` — 수정 불요
- `orin/interactive_cli/main.sh` — D1a 패치 이미 적용 (`cd "${SCRIPT_DIR}" && exec python3 -m flows.entry`) + cusparseLt LD_LIBRARY_PATH 처리 포함

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경, `orin/lerobot/` 미변경 (옵션 B 원칙 준수)
- Coupled File Rule: `orin/lerobot/` 미변경이므로 `03_orin_lerobot_diff.md` 갱신 불요
- `orin/pyproject.toml` 미변경이므로 `setup_env.sh`·`02_orin_pyproject_diff.md` 갱신 불요
- 레퍼런스 활용: 본 변경은 ruff 자동 수정 패턴 (f-string 접두사 제거) — lerobot 레퍼런스 해당 없음
- Category B: `orin/lerobot/` 미변경, `pyproject.toml` 미변경, `setup_env.sh` 미변경

## 변경 내용 요약

### Step 1 — 정적 검증 결과

| 검증 항목 | 명령 | 결과 |
|---|---|---|
| py_compile — entry.py | `python3 -m py_compile orin/interactive_cli/flows/entry.py` | PASS |
| py_compile — env_check.py | `python3 -m py_compile orin/interactive_cli/flows/env_check.py` | PASS |
| py_compile — inference.py | `python3 -m py_compile orin/interactive_cli/flows/inference.py` | PASS |
| py_compile — __init__.py | `python3 -m py_compile orin/interactive_cli/flows/__init__.py` | PASS |
| bash -n — main.sh | `bash -n orin/interactive_cli/main.sh` | PASS |
| ruff check (최초) | `python3 -m ruff check orin/interactive_cli/flows/` | 4건 F541 발견 |
| ruff check (패치 후) | `python3 -m ruff check orin/interactive_cli/` | All checks passed! |
| module import (-m) | `cd orin/interactive_cli && python3 -m flows.entry --help` | PASS — argparse 진입 확인 |

### Step 2 — ruff F541 패치 (inference.py)

`inference.py` 의 f-string without placeholder 4건을 일반 string 으로 교체:

- line 61: `f"  1. HF Hub repo_id 입력  ..."` → `"  1. HF Hub repo_id 입력  ..."`
- line 62: `f"  2. 로컬 ckpt 경로 직접 입력"` → `"  2. 로컬 ckpt 경로 직접 입력"`
- line 88: `f"  HF Hub repo_id 를 입력하세요."` → `"  HF Hub repo_id 를 입력하세요."`
- line 89: `f"  (예: lerobot/smolvla_base, <username>/<repo>)"` → `"  (예: ...)"`

단순 표현식 제거 (플레이스홀더 없는 f-string). 동작 변화 없음.

### Step 3 — flow 0~5 분기 정합 검증

| flow | 담당 파일 | 분기 내용 | 정합 여부 |
|---|---|---|---|
| flow 0 | entry.py `flow0_confirm_environment` | orin/dgx 모두 True 즉시 반환 (VSCode remote-ssh 가정) | PASS |
| flow 1 | entry.py `flow1_select_node` | current_node 만 active `[*]`, 나머지는 안내 + 재선택 | PASS |
| flow 2 | env_check.py `run_env_check` | `orin/tests/check_hardware.sh --mode resume` subprocess 실행. exit 0 시 True 반환 | PASS |
| flow 3 | inference.py `flow3_select_ckpt` | 3 소스 (hub / local / default) 메뉴 — 사용자 결정 awaits_user-B 구현 완료 | PASS |
| flow 4 | inference.py `flow4_run_inference` | `--gate-json orin/config/`, `--model-id` / `--ckpt-path` 소스 분기, dry-run 시 `--output-json /tmp/hil_dryrun.json` 자동 추가 | PASS |
| flow 5 | inference.py `flow5_show_result` | returncode 0/130/기타 분기, dry-run 시 JSON 경로 안내 | PASS |

**entry.py dispatch**: `_run_node_flows(node="orin", ...)` → `run_env_check` → `run_inference_flow` 순차 호출 확인.

### Step 4 — hil_inference.py 인자 정합 확인

inference.py 가 참조하는 hil_inference.py 인자 직접 확인:

| inference.py 참조 | hil_inference.py 실제 인자 | 확인 |
|---|---|---|
| `--gate-json` | line 236 `--gate-json` | PASS |
| `--mode` (dry-run/live) | line 186 choices `["dry-run", "live"]` | PASS |
| `--max-steps` | 확인됨 | PASS |
| `--model-id` | line 247 `--model-id`, default=None | PASS |
| `--ckpt-path` | line 257 `--ckpt-path`, default=None | PASS |
| `--output-json` (dry-run 필수) | line 293 `if args.mode == "dry-run" and args.output_json is None: parser.error(...)` | PASS — inference.py 가 dry-run 시 자동 추가 |

### Step 5 — main.sh LD_LIBRARY_PATH 처리 확인

D1a 패치 (이미 적용) 결과 검증:

- `exec python3 "${SCRIPT_DIR}/flows/entry.py" ...` → `cd "${SCRIPT_DIR}" && exec python3 -m flows.entry ...` ✓
- cusparseLt LD_LIBRARY_PATH 처리: main.sh 내 `source "${VENV_ACTIVATE}"` 후 `if [[ -d "${CUSPARSELT_PATH}" ]]; then export LD_LIBRARY_PATH=...` 블록 존재 ✓
- SSH 비대화형에서도 main.sh 직접 실행 시 activate + LD_LIBRARY_PATH 자동 처리됨 (03 BACKLOG #14 패턴 해결)

### Step 6 — 05 BACKLOG #2 마킹 내용

`BACKLOG.md` [05_interactive_cli] 섹션 #2 항목:

```
05 BACKLOG #2 현재 상태: "미완 — 06 V 그룹 통합 처리"
07 O1 에서 흡수: orin flow 0~5 정적 검증 + ruff F541 패치 PASS
→ W5 에서 "완료 (07 O1 흡수, 2026-05-04)" 마킹 예정
```

Note: 실 Orin SSH 검증 (flow 완주 + hil_inference 50-step) 은 prod-test-runner 인계 + PHYS_REQUIRED 부분 BACKLOG 유지.

## prod-test-runner 인계 — SSH 검증 명령 시퀀스

### 전제 조건

1. devPC ↔ Orin SSH 연결 확립: `ssh orin "echo connected"` PASS
2. `bash scripts/deploy_orin.sh` 완료 (interactive_cli/ 포함 전송)
3. Orin 측 `~/smolvla/orin/.hylion_arm` venv 존재

### LD_LIBRARY_PATH 처리 방식

본 TODO 시점에서 O2 (run_python.sh wrapper) 가 아직 완료 전임.
main.sh 가 내부적으로 `source activate` + `export LD_LIBRARY_PATH` 를 처리하므로
SSH 검증은 **main.sh 직접 실행** 방식을 사용한다.

비대화형 SSH 검증에서 main.sh 를 호출하면 venv + LD_LIBRARY_PATH 가 자동 적용된다.

### 검증 명령 시퀀스

#### A. 정적 확인 (SSH read-only)

```bash
# 1. flow 파일 존재 확인
ssh orin "ls ~/smolvla/orin/interactive_cli/flows/"
# 기대: entry.py  env_check.py  inference.py  __init__.py  (+__pycache__/)

# 2. py_compile on orin
ssh orin "source ~/smolvla/orin/.hylion_arm/bin/activate && python3 -m py_compile ~/smolvla/orin/interactive_cli/flows/entry.py ~/smolvla/orin/interactive_cli/flows/env_check.py ~/smolvla/orin/interactive_cli/flows/inference.py && echo py_compile_PASS"
# 기대: py_compile_PASS

# 3. bash -n on orin
ssh orin "bash -n ~/smolvla/orin/interactive_cli/main.sh && echo bash_n_PASS"
# 기대: bash_n_PASS

# 4. venv + cusparseLt 경로 존재 확인
ssh orin "ls ~/smolvla/orin/.hylion_arm/bin/activate && echo venv_PASS"
ssh orin "ls ~/smolvla/orin/.hylion_arm/lib/python3.10/site-packages/nvidia/cusparselt/lib/ 2>/dev/null && echo cusparselt_PASS || echo cusparselt_NOT_FOUND"
# cusparselt: PASS 또는 NOT_FOUND (후자면 LD_LIBRARY_PATH 패치 블록 skip — 문제 없음)
```

#### B. 비대화형 flow 0~2 실행

```bash
# flow 0 (env 확인) + flow 1 (노드 선택 "1") + flow 2 (env_check.py) 진입 확인
# "1\n" 을 stdin 으로 전달 → flow 1 orin 선택
# timeout 30: check_hardware.sh --mode resume 이 SO-ARM 없으면 non-zero exit 가능 → 오류 메시지 확인용

ssh orin "echo '1' | timeout 30 bash ~/smolvla/orin/interactive_cli/main.sh 2>&1 | head -80"
# 기대 출력 예시:
#   flow 1 — 장치 선택 (헤더)
#   1. [*] Orin (추론 노드) ...
#   [선택] Orin ...
#   flow 2 — 환경 체크 (헤더)
#   [flow 2] 환경 체크 중...
#   (check_hardware.sh 출력 또는 오류 메시지)
# 허용 결과: exit 0 (체크 PASS) 또는 exit 1 (check_hardware.sh SO-ARM 없음 — 예상 범위)
# 비허용: ModuleNotFoundError, cusparseLt ImportError, flow 진입 전 crash
```

#### C. flow 3~5 코드 분기 정합 (import + argparse)

```bash
# entry.py --help (module import 정상 확인)
ssh orin "source ~/smolvla/orin/.hylion_arm/bin/activate && cd ~/smolvla/orin/interactive_cli && python3 -m flows.entry --help 2>&1"
# 기대: usage 출력 (argparse), ModuleNotFoundError 없음

# inference.py 직접 import 확인
ssh orin "source ~/smolvla/orin/.hylion_arm/bin/activate && cd ~/smolvla/orin/interactive_cli && python3 -c 'from flows.inference import flow3_select_ckpt, flow4_run_inference, flow5_show_result; print(\"import_PASS\")' 2>&1"
# 기대: import_PASS
```

#### D. PHYS_REQUIRED 부분 (verification_queue 마킹 — 실 검증 BACKLOG)

다음 항목은 SO-ARM + 카메라 직결 환경 필요 → PHYS_REQUIRED → 시연장 이동 시 처리:

1. `check_hardware.sh --mode first-time` 완주 + `ports.json`·`cameras.json` 생성 확인
2. `check_hardware.sh --mode resume` exit 0 확인 (flow 2 통과)
3. flow 3 기본값 선택 → hil_inference.py dry-run 실행 → `/tmp/hil_dryrun.json` 생성 확인
4. hil_inference 50-step live 모드 SO-ARM 실 동작 확인 (04 G2 verification_queue 통합)

## code-tester 입장에서 검증 권장 사항

- `python3 -m py_compile orin/interactive_cli/flows/inference.py` — PASS 확인
- `python3 -m ruff check orin/interactive_cli/` — All checks passed 확인
- `bash -n orin/interactive_cli/main.sh` — PASS 확인
- flow 4 `dry-run` 분기: inference.py `flow4_run_inference` 내 `if mode == "dry-run": cmd += ["--output-json", DEFAULT_DRYRUN_JSON]` 존재 확인
- hil_inference.py 인자 정합: `grep "model-id\|ckpt-path\|output-json" orin/inference/hil_inference.py` — 247·257·230 행 확인
- entry.py dispatch: `_run_node_flows(node="orin")` 시 `run_env_check` → `run_inference_flow` 순서 확인
- D1a 패치 적용 확인: `grep "cd.*SCRIPT_DIR.*python3 -m flows.entry" orin/interactive_cli/main.sh` — 1건 매칭

## PHYS_REQUIRED 마킹 사항

| 항목 | 환경 레벨 | 처리 방침 |
|---|---|---|
| check_hardware.sh first-time/resume 실 실행 | PHYS_REQUIRED | 시연장 이동 시 BACKLOG |
| hil_inference dry-run flow 완주 + JSON 생성 | PHYS_REQUIRED | 시연장 이동 시 BACKLOG |
| hil_inference 50-step SO-ARM live 모드 | PHYS_REQUIRED | 시연장 이동 시 BACKLOG (04 G2 통합) |

SSH_AUTO 자율 가능 범위:
- py_compile·ruff·bash -n: AUTO_LOCAL PASS (devPC)
- SSH read-only (ls·py_compile·bash -n·import): SSH_AUTO
- main.sh 비대화형 실행 flow 0~2 (SO-ARM 없는 env): SSH_AUTO (exit 1 허용)
- flow 3~5 import·argparse 확인: SSH_AUTO
