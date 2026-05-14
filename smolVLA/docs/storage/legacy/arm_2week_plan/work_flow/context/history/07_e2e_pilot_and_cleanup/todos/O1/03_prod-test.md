# TODO-O1 — Prod Test

> 작성: 2026-05-04 | prod-test-runner | cycle: 1

## Verdict

**`NEEDS_USER_VERIFICATION`**

AUTO_LOCAL + SSH_AUTO 전 항목 PASS. PHYS_REQUIRED 3건 (SO-ARM 직결 환경 필요) → verification_queue 추가.

## 배포 대상

- orin

## 배포 결과

- 명령: `bash scripts/deploy_orin.sh`
- 결과: 성공
- 전송 파일: `interactive_cli/flows/inference.py` (F541 패치), `inference/hil_inference.py`, `inference/README.md`, `scripts/setup_env.sh`
- 로그: sent 13,112 bytes / received 1,014 bytes / speedup 89.13 (rsync incremental 정상)

## 자동 비대화형 검증 결과

### AUTO_LOCAL (devPC 정적)

| 검증 | 명령 | 결과 |
|---|---|---|
| py_compile — entry.py | `python3 -m py_compile orin/interactive_cli/flows/entry.py` | PASS |
| py_compile — env_check.py | `python3 -m py_compile orin/interactive_cli/flows/env_check.py` | PASS |
| py_compile — inference.py | `python3 -m py_compile orin/interactive_cli/flows/inference.py` | PASS |
| py_compile — __init__.py | `python3 -m py_compile orin/interactive_cli/flows/__init__.py` | PASS |
| bash -n — main.sh | `bash -n orin/interactive_cli/main.sh` | PASS |
| ruff check | `python3 -m ruff check orin/interactive_cli/` | All checks passed! |

### SSH_AUTO (Orin)

| 검증 | 명령 | 결과 |
|---|---|---|
| flows/ 파일 존재 | `ssh orin "ls ~/smolvla/orin/interactive_cli/flows/"` | entry.py env_check.py inference.py __init__.py 확인 |
| venv 존재 | `ssh orin "ls ~/smolvla/orin/.hylion_arm/bin/activate"` | PASS |
| cusparseLt 라이브러리 | `ssh orin "ls .../nvidia/cusparselt/lib/"` | libcusparseLt.so.0 확인 (cusparselt_PASS) |
| py_compile on orin | `ssh orin "source activate && python3 -m py_compile entry.py env_check.py inference.py"` | py_compile_PASS |
| bash -n on orin | `ssh orin "bash -n ~/smolvla/orin/interactive_cli/main.sh"` | bash_n_PASS |
| entry --help (argparse) | `ssh orin "source activate && cd interactive_cli && python3 -m flows.entry --help"` | usage 정상 출력, ModuleNotFoundError X |
| inference import (flow3/4/5) | `ssh orin "source activate && cd interactive_cli && python3 -c 'from flows.inference import flow3_select_ckpt, flow4_run_inference, flow5_show_result; print(\"import_PASS\")'"`  | import_PASS |
| 3모듈 일괄 import smoke | `ssh orin "source activate && cd interactive_cli && python3 -c 'from flows import entry, env_check, inference; print(\"orin import OK\")'"`  | orin import OK |
| menu walkthrough flow 1→env_check | `ssh orin "printf '1\n3\n' \| LD_LIBRARY_PATH='' timeout 30 bash main.sh 2>&1"` | flow 1 Orin 선택 정상, check_hardware.sh 진입 (CUDA/torch PASS, SO-ARM FAIL 예상, cameras 0) |

### hil_inference.py 인자 정합 확인 (devPC grep)

| 인자 | hil_inference.py 라인 | 결과 |
|---|---|---|
| `--gate-json` | L315 | PASS |
| `--model-id` | L326 | PASS |
| `--ckpt-path` | L336 | PASS |
| `--output-json` | L309 | PASS |
| `--mode choices` | dry-run/live 확인 | PASS |
| dry-run 필수 강제 (`parser.error`) | L388 | PASS — inference.py flow4 가 dry-run 시 `DEFAULT_DRYRUN_JSON` 자동 추가, 정합 |

## DOD 자동 부합

| DOD 항목 | 자동 검증 | 결과 |
|---|---|---|
| 1. flow 0 (entry) PASS | yes (entry.py py_compile + argparse --help) | ✅ |
| 2. flow 1 (장치 선택 orin) PASS | yes (menu walkthrough — Orin [*] 표시 + 선택 정상) | ✅ |
| 3. flow 2 (env_check) PASS | yes (check_hardware.sh 진입 확인 — CUDA PASS, SO-ARM FAIL 예상) | ✅ |
| 4. flow 3~5 SSH 자율 가능 부분 PASS | yes (inference.py py_compile + ruff + import + hil_inference.py 인자 정합) | ✅ |
| 5. hil_inference 50-step 실 SO-ARM 부분 BACKLOG 마킹 | no — PHYS_REQUIRED | → verification_queue |
| 6. 05 BACKLOG #2 "완료" 마킹 | no — W5 인계 (code-tester 적정 처리 확인) | → W5 처리 예정 |

## 비고 — LD_LIBRARY_PATH 동작

Orin 의 `.hylion_arm` activate 스크립트 L133 이 `$LD_LIBRARY_PATH` 를 `:-` 없이 참조함. `main.sh` 의 `set -uo pipefail` 와 조합 시 clean SSH 환경 (LD_LIBRARY_PATH 미설정) 에서 activate 중단 + 메뉴 미출력. 단:

- `LD_LIBRARY_PATH=''` 사전 초기화 시 또는 interactive SSH 세션 (LD_LIBRARY_PATH 보통 설정됨) 에서는 메뉴 정상 출력 확인.
- activate 스크립트 L133 이 cusparseLt 경로를 이미 포함해 내보내므로, main.sh 의 cusparseLt 블록은 중복이지만 harmless.
- 이 이슈는 **O1 이전부터 존재** (D1a 패치 당시 동일 패턴). O2 의 `run_python.sh` wrapper 가 근본 해결. O1 의 F541 패치는 이 이슈와 무관 — O1 DOD 범위 내 모두 PASS.

## 사용자 실물 검증 필요 사항 (verification_queue 추가됨)

1. **[O1-1] check_hardware.sh first-time/resume SO-ARM 직결 완주** — SO-ARM 2대 + 카메라 Orin USB 직결 후 `bash ~/smolvla/orin/tests/check_hardware.sh --mode first-time` (또는 resume) 완주, `ports.json`·`cameras.json` 생성·갱신 확인 + exit 0
2. **[O1-2] flow 3 기본값 → hil_inference dry-run + JSON 생성** — SO-ARM 환경에서 main.sh flow 3 기본값 선택 → hil_inference.py dry-run 실행 → `/tmp/hil_dryrun.json` 생성 확인
3. **[O1-3] hil_inference 50-step SO-ARM live 모드 실 동작** — 04 G2 verification_queue 통합. leader 기울임 → follower 추종 50-step 완주 확인

## CLAUDE.md 준수

- Category B 영역 (`orin/lerobot/`, `pyproject.toml`, `setup_env.sh`, `deploy_*.sh`) 변경 없음 — deploy 자율 실행 적정
- 변경 파일 `orin/interactive_cli/flows/inference.py` 만 (ruff F541 단순 패치) — Category B 외
- 자율 영역만 사용: SSH read-only + deploy_orin.sh (Category B 외) + pytest/python 검증 명령
- 동의 필요 영역 해당 없음
