# TODO-O1 — Code Test

> 작성: 2026-05-04 16:30 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈 0건. Recommended 개선 사항 0건.

## 단위 테스트 결과

```
python3 -m py_compile orin/interactive_cli/flows/inference.py  → PASS
python3 -m py_compile orin/interactive_cli/flows/entry.py      → PASS
python3 -m py_compile orin/interactive_cli/flows/env_check.py  → PASS
python3 -m py_compile orin/interactive_cli/flows/__init__.py   → PASS
bash -n orin/interactive_cli/main.sh                           → PASS
cd orin/interactive_cli && python3 -m flows.entry --help       → PASS (argparse usage 정상 출력, ModuleNotFoundError 없음)
```

## Lint·Type 결과

```
python3 -m ruff check orin/interactive_cli/
All checks passed!
```

F541 잔여 건 없음 확인: `grep -n 'f"[^{]*"' inference.py | grep -v '{'` — 0건.

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. flow 0 (entry) PASS | ✅ | entry.py `flow0_confirm_environment` — orin/dgx True 즉시 반환, argparse PASS |
| 2. flow 1 (장치 선택 orin) PASS | ✅ | entry.py `flow1_select_node` — `[*]` current_node 분기 정합 확인 |
| 3. flow 2 (env_check) PASS | ✅ | env_check.py `run_env_check` — py_compile PASS, subprocess 구조 정합 |
| 4. flow 3~5 SSH 자율 가능 부분 PASS | ✅ | inference.py py_compile + ruff All checks passed. 분기 정합 (아래 상세) |
| 5. hil_inference 50-step 실 SO-ARM 부분 BACKLOG 마킹 | ✅ | 01_implementation.md Step 6 + PHYS_REQUIRED 마킹 섹션 명시 |
| 6. 05 BACKLOG #2 → "완료 (07 O1 흡수)" 마킹 예정 | ✅ | W5 인계 마킹으로 명시됨. 적정 처리 (W5 의존 순서 맞음) |

## Critical 이슈

없음.

## Recommended 개선 사항

없음.

## 검증 세부 — flow 분기 정합

### F541 패치 정합 (lines 61·62·88·89)

git diff 확인 결과:

- line 61: `f"  1. HF Hub repo_id 입력  ..."` → `"  1. HF Hub repo_id 입력  ..."` — 동작 변화 없음
- line 62: `f"  2. 로컬 ckpt 경로 직접 입력"` → `"  2. 로컬 ckpt 경로 직접 입력"` — 동작 변화 없음
- line 88: `f"  HF Hub repo_id 를 입력하세요."` → `"  HF Hub repo_id 를 입력하세요."` — 동작 변화 없음
- line 89: `f"  (예: lerobot/smolvla_base, <username>/<repo>)"` → `"  (예: ...)"` — 동작 변화 없음

f-string 접두사 제거 4건 전부 플레이스홀더 없는 단순 문자열 — 출력 내용 동일, 동작 변화 없음 확인.

### D1a 패치 보존 확인

- `main.sh` L71: `cd "${SCRIPT_DIR}" && exec python3 -m flows.entry --node-config "${NODE_CONFIG}"` — 패턴 1건 확인 (grep FOUND)
- cusparseLt LD_LIBRARY_PATH: `CUSPARSELT_PATH=...` 상수 정의 (L37) + `if [[ -d "${CUSPARSELT_PATH}" ]]; then export LD_LIBRARY_PATH=...` 블록 (L55~56) 존재 확인

### hil_inference.py 인자 정합

- `--gate-json`: line 315 확인
- `--model-id`: line 326 확인
- `--ckpt-path`: line 336 확인
- `--output-json`: line 309 확인
- `--mode` choices `["dry-run", "live"]`: 확인
- dry-run 시 `--output-json` 필수 강제 (line 388 `parser.error`): inference.py flow4 가 dry-run 시 `DEFAULT_DRYRUN_JSON` 자동 추가 — 정합

### flow 4 dry-run 분기

`inference.py` L227~228:
```python
if mode == "dry-run":
    cmd += ["--output-json", DEFAULT_DRYRUN_JSON]
```
존재 확인.

### entry.py dispatch 순서

`_run_node_flows(node="orin", ...)` → L218 `run_env_check(script_dir)` → L223 `run_inference_flow(script_dir)` 순차 호출 확인.

### 05 BACKLOG #2 처리 결정 적정성

W5 인계 마킹 방식은 적정: 다른 O 그룹 todo 완료 후 W5 에서 일괄 BACKLOG 마킹하는 것이 spec DOD 구조와 일치. O1 단독으로 BACKLOG.md 직접 수정할 근거 없으므로 W5 인계는 올바른 처리.

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경. `.claude/` 미변경 |
| B (자동 재시도 X 영역) | ✅ | `orin/lerobot/` 미변경. `pyproject.toml` 미변경. `setup_env.sh` 미변경. `scripts/deploy_*.sh` 미변경. `.gitignore` 미변경 |
| Coupled File Rules | ✅ | Category B 파일 미변경이므로 Coupled File 갱신 불요 |
| 옛 룰 (`docs/storage/` bash 예시) | ✅ | 해당 없음 |

## 배포 권장

READY_TO_SHIP — prod-test-runner 진입 권장.

prod-test-runner 인계 시 01_implementation.md 의 "prod-test-runner 인계 — SSH 검증 명령 시퀀스" 섹션 (A·B·C·D 분류) 참조.
- A (정적 확인): SSH_AUTO 자율
- B (비대화형 flow 0~2): SSH_AUTO 자율 (SO-ARM 없는 env에서 exit 1 허용)
- C (flow 3~5 import·argparse): SSH_AUTO 자율
- D (PHYS_REQUIRED 부분): verification_queue 마킹 후 BACKLOG 처리
