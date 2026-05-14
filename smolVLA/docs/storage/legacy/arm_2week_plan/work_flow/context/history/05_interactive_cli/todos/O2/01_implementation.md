# TODO-O2 — Implementation

> 작성: 2026-05-01 17:00 | task-executor | cycle: 1

## 목표

orin/interactive_cli/ flow 3~ 추론 책임 구현 — env_check.py + inference.py 신규 작성, entry.py 갱신, hil_inference.py argparse 확장.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `orin/interactive_cli/flows/env_check.py` | 신규 | flow 2 — check_hardware.sh --mode resume 호출 |
| `orin/interactive_cli/flows/inference.py` | 신규 | flow 3·4·5 — ckpt 선택·hil_inference 실행·결과 보고 |
| `orin/interactive_cli/flows/entry.py` | M | flow 2+ 노드별 디스패치 로직 + sys.path 패치 + docstring 갱신 |
| `orin/inference/hil_inference.py` | M | --model-id / --ckpt-path argparse 인자 추가 + effective_model 결정 로직 |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미수정 ✓, `.claude/` 미수정 ✓
- Category B 비해당: `orin/inference/hil_inference.py` 는 `orin/inference/` 하위 — Category B 정의 영역(orin/lerobot/) 아님 ✓
- Coupled File Rule: `orin/lerobot/` 미수정 → `03_orin_lerobot_diff.md` 갱신 불필요 ✓
- Category C·D 비해당 ✓
- 레퍼런스 직접 Read 완료:
  - `orin/inference/hil_inference.py` 전체 (argparse line 183~267, load_gate_config line 80~119, apply_gate_config line 122~177)
  - `orin/tests/check_hardware.sh` line 68~83 (지원 인자 확인 — --gate-json 미지원 재확인)
  - `docs/storage/13_orin_cli_flow.md` (cycle 2 정정본 — O1 산출물)
  - `docs/storage/12_interactive_cli_framework.md` §5 (F1 정정본)
  - `orin/interactive_cli/flows/entry.py` (F2 산출물)

## 레퍼런스 인용

### env_check.py — check_hardware.sh 지원 인자 (line 68~83 직접 Read)

```bash
# check_hardware.sh line 68~83: 지원 인자 목록
--mode {first-time|resume}
--config YAML
--quiet
--output-json FILE
# 주의: --gate-json 없음 → env_check.py 에 절대 전달 X (exit 2 실패)
```

패턴 (13_orin_cli_flow.md §1, 12_interactive_cli_framework.md §5):

```python
result = subprocess.run(
    ["bash", str(check_script), "--mode", "resume"],
    check=False,
)
return result.returncode == 0
```

### inference.py — hil_inference.py 호출 구조 (13_orin_cli_flow.md §4 직접 인용)

```python
# 13_orin_cli_flow.md §4 run_inference() 패턴
cmd = [
    "python", str(hil_script),
    "--gate-json", str(config_dir),   # ports.json + cameras.json 자동 채움
    "--mode", mode,
    "--max-steps", str(max_steps),
]
if ckpt_path is not None:
    cmd += ["--ckpt-path", str(ckpt_path)]
elif mode == "dry-run":
    cmd += ["--output-json", "/tmp/hil_dryrun.json"]
```

### hil_inference.py 기존 인자 (line 183~245 직접 Read)

기존 인자 목록 (argparse 충돌 없는지 확인):
- `--mode` (line 184), `--follower-port` (line 192), `--follower-id` (line 200)
- `--cameras` (line 205), `--flip-cameras` (line 211), `--n-action-steps` (line 216)
- `--max-steps` (line 222), `--output-json` (line 228), `--gate-json` (line 235)

추가 인자 (`--model-id`, `--ckpt-path`) 는 기존 인자와 이름 충돌 없음 확인.

### hil_inference.py MODEL_ID 상수 (line 48 직접 Read)

```python
MODEL_ID = "lerobot/smolvla_base"
```

`--model-id` / `--ckpt-path` 미지정 시 이 상수를 `effective_model` 로 사용 → 기존 03 사이클 호출 완전 하위 호환.

## 변경 내용 요약

### env_check.py

flow 2 를 담당하는 신규 파일. `check_hardware.sh --mode resume` 을 subprocess 로 호출하여 orin 환경(venv·CUDA·SO-ARM 포트·카메라)을 검증한다. O1 cycle 2 핵심 정정 사항인 `--gate-json` 인자 전달 금지를 엄수하여 exit 2 실패를 방지한다. exit 0 시 True, 비0 시 오류 안내 + False 반환.

### inference.py

flow 3·4·5 를 담당하는 신규 파일. 사용자 결정 (A) 3단계 순차 구조:
- flow 3 (`flow3_select_ckpt`): 3개 소스 메뉴 — (1) HF Hub repo_id 입력, (2) 로컬 경로 직접 입력, (3) 기본값 smolvla_base. `orin/checkpoints/` 자동 탐색(후보 4번)은 사용자 미채택으로 제외.
- flow 4 (`flow4_run_inference`): `sys.executable` + `hil_inference.py` subprocess 실행. `--gate-json orin/config/` 자동 전달. source에 따라 `--model-id` / `--ckpt-path` 추가. dry-run 시 `--output-json /tmp/hil_dryrun.json` 자동 추가.
- flow 5 (`flow5_show_result`): returncode 분기(0=정상/130=Ctrl+C/기타=오류) + 모드/모델/JSON 경로 요약 출력.
- `run_inference_flow()`: 3단계를 순차 실행하는 진입점 — entry.py 에서 호출.

### entry.py 갱신

F2 산출물의 `flow 2+ TODO` 플레이스홀더를 실제 디스패치 로직으로 교체:
- `_run_node_flows(node, script_dir)` 추가 — orin 분기는 env_check + inference_flow 순차 호출, dgx/datacollector 는 후행 TODO placeholder 유지.
- `main()` 내 "flow 2+" 블록을 `_run_node_flows()` 호출로 교체.
- docstring에 flow 2+ 분기 설명 추가.

### hil_inference.py 수정

기존 argparse 블록 (line 235 이후) 에 `--model-id` + `--ckpt-path` 인자 추가:
- 두 인자 모두 `default=None` — 미전달 시 기존 동작 완전 보존 (하위 호환).
- 동시 지정 시 `parser.error()` 로 명시적 오류.
- `effective_model` 결정 우선순위: `--ckpt-path` > `--model-id` > `MODEL_ID` 상수.
- 모델 로드 (`SmolVLAPolicy.from_pretrained`) + `make_pre_post_processors pretrained_path` + dry-run JSON `model_id` 필드를 모두 `effective_model` 로 교체 → 3곳 일관 적용.

## code-tester 입장에서 검증 권장 사항

- 구문 검사 (로컬 이미 통과):
  - `python3 -m py_compile orin/interactive_cli/flows/env_check.py`
  - `python3 -m py_compile orin/interactive_cli/flows/inference.py`
  - `python3 -m py_compile orin/interactive_cli/flows/entry.py`
  - `python3 -m py_compile orin/inference/hil_inference.py`
- argparse 회귀 검증:
  - `python3 orin/inference/hil_inference.py --help` — 신규 인자 2개 표시 확인
  - 인자 미전달 호출 시 기존 동작 유지 (effective_model == MODEL_ID == "lerobot/smolvla_base")
- 충돌 검사:
  - `python3 orin/inference/hil_inference.py --model-id foo --ckpt-path /bar --follower-port /dev/ttyACM0 --gate-json /tmp` → `parser.error` 로 실패 확인
- lint:
  - `ruff check orin/interactive_cli/flows/env_check.py orin/interactive_cli/flows/inference.py orin/interactive_cli/flows/entry.py orin/inference/hil_inference.py`
- DOD 항목 대조:
  - DOD §1 env_check.py (O1 §1 정정 패턴): --gate-json 미전달, subprocess check=False ✓
  - DOD §2 inference.py (flow 3·4·5): 3개 소스 메뉴 + hil_inference subprocess + 시연 데모 결과 ✓
  - DOD §3 entry.py: orin 분기 env_check → inference 순차 호출 ✓
  - DOD §4 hil_inference.py: --ckpt-path / --model-id 추가, 기본값 default=None 하위 호환 ✓

## hil_inference.py 수정 상세

### 추가 argparse 인자 (line 246~266)

```python
parser.add_argument("--model-id", type=str, default=None, ...)
parser.add_argument("--ckpt-path", type=str, default=None, ...)
```

### effective_model 결정 (line 269~282)

```python
if args.ckpt_path is not None:
    effective_model = str(Path(args.ckpt_path).expanduser())
elif args.model_id is not None:
    effective_model = args.model_id
else:
    effective_model = MODEL_ID  # 하드코드 기본값 (하위 호환)
```

### 회귀 영향 분석

- 인자 미전달 (03 사이클 기존 호출 패턴): `args.model_id = None`, `args.ckpt_path = None` → `effective_model = MODEL_ID = "lerobot/smolvla_base"` → 기존과 동일 동작.
- `--follower-port` / `--gate-json` 등 기존 인자 구조 무변경 → 기존 호출 스크립트 무영향.
- `make_pre_post_processors(pretrained_path=effective_model)` 의 `pretrained_path` 는 Hub repo_id 또는 로컬 경로 모두 지원 (SmolVLAPolicy.from_pretrained 과 동일 인터페이스).

## 잔여 리스크

- `make_pre_post_processors(pretrained_path=<local_path>)` 가 로컬 경로를 허용하는지 Orin 실물 검증 필요 (SmolVLAPolicy.from_pretrained 은 경로 지원, preprocessor 는 미확인).
- flow 4 에서 `sys.executable` 사용 → hil_inference.py 실행 시 lerobot 패키지가 orin venv 에서 보여야 함 (main.sh 가 venv activate 하므로 정상 동작 예상, 검증 필요).
- `--output-json /tmp/hil_dryrun.json` 경로는 /tmp 에 쓰기 권한 있는 환경 전제 (Orin Jetson 에서 일반적으로 OK).
- entry.py sys.path 처리: main.sh 가 `python3 ${SCRIPT_DIR}/flows/entry.py` 로 직접 실행하므로 `flows` 패키지 부모(interactive_cli/)가 sys.path 에 없다. 이를 해소하기 위해 entry.py 상단에 `sys.path.insert(0, str(_CLI_DIR))` 추가 — `from flows.env_check import ...` 가 정상 동작.

## 다음 단계 권고 (O3 prod 검증 시 사전 조건)

### 사용자 환경 조건

- **Orin SSH 연결**: VSCode remote-ssh 또는 직접 ssh 로 Orin 접속
- **카메라 2대**: top (USB webcam, /dev/video0 이상) + wrist (USB webcam, flip=True 가능)
  - first-time 설정: `bash orin/tests/check_hardware.sh --mode first-time` 로 cameras.json 생성
- **SO-ARM follower**: /dev/ttyACM0 이상의 시리얼 포트 연결
  - first-time 설정: ports.json 에 follower_port 기록
- **venv**: `~/smolvla/orin/.hylion_arm` 생성 완료 (setup_env.sh 실행 후)
- **04 G2 verification_queue §1**: first-time 환경 체크 사전 완료 필요

### O3 prod 검증 흐름

1. `bash orin/interactive_cli/main.sh` 실행
2. flow 1: orin [*] 선택
3. flow 2: check_hardware.sh resume → exit 0 확인
4. flow 3: 기본값(3) 선택 → `smolvla_base`
5. flow 4: dry-run 선택 → hil_inference subprocess 실행 확인
6. flow 5: `/tmp/hil_dryrun.json` 생성 확인 + step 수 출력 확인

## SKILL_GAP

없음. 모든 구현 패턴에 레퍼런스 기반:
- `env_check.py`: 13_orin_cli_flow.md §1 + 12_interactive_cli_framework.md §5 직접 인용
- `inference.py`: 13_orin_cli_flow.md §3·§4·§5 직접 인용
- `hil_inference.py` 수정: line 183~267 직접 Read 후 기존 패턴에 일관하게 확장
