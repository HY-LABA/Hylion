# TODO-O2 — Code Test

> 작성: 2026-05-01 18:00 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 0건, Recommended 2건.

---

## 단위 테스트 결과

```
python3 -m py_compile orin/interactive_cli/flows/env_check.py   → PASS
python3 -m py_compile orin/interactive_cli/flows/inference.py   → PASS
python3 -m py_compile orin/interactive_cli/flows/entry.py       → PASS
python3 -m py_compile orin/inference/hil_inference.py           → PASS

AST parse (ast.parse): 4개 파일 전부 SyntaxError 없음

hil_inference.py add_argument 확인:
  --model-id  → line 246~255, default=None  OK
  --ckpt-path → line 256~266, default=None  OK

충돌 검사 (parser.error):
  line 270~271: args.model_id is not None and args.ckpt_path is not None → parser.error() OK

effective_model 우선순위:
  ckpt_path → expanduser() → effective_model (line 275~276)
  model_id  → effective_model (line 278~279)
  else      → MODEL_ID 상수 (line 282)
  총 9회 사용: from_pretrained / make_pre_post_processors / dry-run JSON model_id 모두 OK

check_hardware.sh --gate-json 미지원 재확인:
  line 68~83: 지원 인자 --mode / --config / --quiet / --output-json
  --gate-json 없음 → *)  usage 분기(exit 2) 에 해당
  env_check.py: ["bash", str(check_script), "--mode", "resume"] 만 — --gate-json 절대 미전달 OK

sys.path 패치 (entry.py):
  _THIS_DIR = Path(__file__).parent       (flows/)
  _CLI_DIR  = _THIS_DIR.parent            (interactive_cli/)
  sys.path.insert(0, str(_CLI_DIR))
  → from flows.env_check import run_env_check 가 interactive_cli/flows/env_check.py 탐색 OK
  (orin/interactive_cli/flows/env_check.py 존재 확인됨)

returncode 130 처리:
  run_inference_flow(): return 0 if returncode in (0, 130) else 1 — OK
```

## Lint·Type 결과

```
ruff: 환경에 미설치 (python3 -m ruff → module not found, PATH 에도 없음).
mypy: 동일.

대체 검사 — ast.parse + 수동 코드 리뷰:

env_check.py:
  - 미사용 import 없음. subprocess.run(check=False) OK.
  - check_script.exists() 가드 OK.

inference.py:
  - DEFAULT_MODEL_ID 상수 (line 31) 와 hil_inference.py MODEL_ID 상수 (line 48) 동기화 필요 없음
    (inference.py 는 UI 표시용, 실제 모델 결정은 hil_inference.py 측에서 수행).
  - type hint str | None (Python 3.10+ 문법) 사용 — orin venv Python 버전 확인 필요 [Recommended #1].
  - EOFError/KeyboardInterrupt 보호 OK (모든 input() 호출).

entry.py:
  - F2 보고서 지적 미사용 변수 (options 리스트 append 후 미참조) 여전히 잔존 [Recommended #2].
  - sys.path 패치 중복 방지 (str(_CLI_DIR) not in sys.path) OK.
  - _simple_yaml_load fallback OK.

hil_inference.py:
  - 기존 인자 이름 충돌 없음 (model-id, ckpt-path 는 기존 인자 목록에 없음).
  - line 246~266 추가 인자: 기존 argparse 블록 패턴 일관성 유지됨.
```

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. O1 정의대로 orin flow 구현 | OK | flow 2 (env_check.py) + flow 3·4·5 (inference.py) 구현됨 |
| 2. F2 boilerplate 위에 추론 모듈 추가 | OK | entry.py 가 _run_node_flows() 분기로 orin 경우 env_check + inference_flow 순차 호출 |
| 3. check_hardware.sh 호출 시 --gate-json 미포함 | OK | ["bash", str(check_script), "--mode", "resume"] 만 — O1 cycle 2 정정 사항 준수 |
| 4. hil_inference.py --model-id / --ckpt-path 추가 | OK | line 246~266, default=None, 충돌 시 parser.error |
| 5. 기본값 None — 기존 동작 하위 호환 | OK | 인자 미전달 시 effective_model = MODEL_ID = "lerobot/smolvla_base" |
| 6. flow 3 ckpt 소스 3개 (hub/local/default) | OK | flow3_select_ckpt() — 3개 메뉴, orin/checkpoints/ 자동 탐색 미포함 (사용자 결정 반영) |
| 7. flow 4 --gate-json 자동 전달 | OK | cmd 에 ["--gate-json", str(config_dir)] 항상 포함 |
| 8. dry-run 시 --output-json 자동 추가 | OK | mode == "dry-run" 분기에서 DEFAULT_DRYRUN_JSON 추가 |
| 9. flow 5 시연 데모 결과 (returncode 분기 + 요약) | OK | 0=정상완료 / 130=Ctrl+C / 기타=비정상 분기 + 모델·모드·JSON경로 출력 |
| 10. Category B 비해당 처리 | OK | orin/inference/hil_inference.py 는 orin/lerobot/ 아님 — 일반 코드 수정 |

## Critical 이슈

없음.

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `orin/interactive_cli/flows/inference.py` 전체 | `str \| None` type hint (PEP 604, Python 3.10+) 사용. orin venv Python 버전이 3.9 이하이면 `Optional[str]` 로 교체 필요. O3 prod 검증 전 확인 권장 |
| 2 | `orin/interactive_cli/flows/entry.py` line 181 | `options` 리스트 미사용 변수 (F2 code-test Recommended #1 미수정 잔존). 제거 또는 실제 활용 권장 |

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | OK | docs/reference/ 미수정, .claude/ 미수정 |
| B (자동 재시도 X) | OK | orin/lerobot/ 미수정. orin/inference/hil_inference.py 는 Category B 비해당 (O1 cycle 2 정정 사항) |
| Coupled File Rules | OK | orin/lerobot/ 미수정 → 03_orin_lerobot_diff.md 갱신 불필요. orin/pyproject.toml 미수정 |
| C (사용자 동의) | OK | 새 디렉터리 신규 생성 없음, 의존성 추가 없음 |
| D (절대 금지 명령) | OK | rm -rf / sudo / force-push 등 없음 |
| entry.py 3 사본 분기 | OK (의도된 설계) | F2 시점 IDENTICAL → O2/D2 가 각각 자기 노드 분기 구현하여 분리됨. dgx/datacollector entry.py 도 각각 D2/X2 구현에 의해 수정됨 (untracked 상태 확인). 각 노드 entry.py 가 자기 노드 분기만 완성하고 나머지는 후행 TODO placeholder 유지 — 설계 의도와 일치 |

## 배포 권장

READY_TO_SHIP — prod-test-runner (O3) 진입 권장.

O3 사전 조건 (01_implementation.md §다음 단계 권고 참조):
- Orin SSH 연결 확립
- check_hardware.sh --mode first-time 완료 (orin/config/ports.json + cameras.json 생성)
- orin venv (.hylion_arm) 활성 상태
- SO-ARM follower 포트 연결
- Python 버전 3.10+ 확인 (Recommended #1 해소 또는 type hint 교체 후 진행)
