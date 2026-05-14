# TODO-F1 — Implementation

> 작성: 2026-05-01 18:00 | task-executor | cycle: 1

## 목표

3 노드 (orin / dgx / datacollector) 에 동일 복사할 interactive_cli boilerplate (main.sh + flows/entry.py) 정의. flow 0 (진입 확인) + flow 1 (장치 선택) 완성.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `docs/storage/12_interactive_cli_framework.md` | 신규 | §1~§5 포함 boilerplate 프레임워크 문서 (F2 가 사용할 실 코드 스니펫 포함) |
| `docs/work_flow/context/todos/F1/01_implementation.md` | 신규 | 본 보고서 |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 ✓ / `orin/lerobot/` 미변경 ✓
- Category A·B·C·D 비해당: `docs/storage/` 신규 파일 생성만
- Coupled File Rule: `orin/lerobot/` 미변경 — 03_orin_lerobot_diff.md 갱신 불필요 ✓
- 레퍼런스 활용 (lerobot-reference-usage 스킬 준수):
  - `orin/tests/check_hardware.sh` 직접 Read 완료. 인용:
    - line 41~49: `SCRIPT_DIR` / `VENV_ACTIVATE` / `CUSPARSELT_PATH` 경로 상수 블록
    - line 152~172: `step_venv()` — `source "$VENV_ACTIVATE"` + cusparseLt `LD_LIBRARY_PATH` 패치
    - line 185~203, 226~244: `python3 - <<'PYEOF' ... PYEOF` bash 인라인 heredoc 패턴
  - `orin/inference/hil_inference.py` `--gate-json` 부분 직접 Read 완료. 인용:
    - line 80~120: `load_gate_config()` — `Path.is_dir()` 분기 + 파일 미존재 시 `None` 반환
    - line 122~177: `apply_gate_config()` — CLI 직접 인자 우선 / 기본값 동일 시 gate 값으로 덮어씀
    - line 236~245: `--gate-json` argparse 인자 정의 형식

## 변경 내용 요약

`docs/storage/12_interactive_cli_framework.md` 를 신규 작성하여 F2 task 가 3 노드에 그대로 복사할 boilerplate 코드 (main.sh + flows/entry.py) 를 완전한 실행 가능 상태로 정의했다.

`main.sh` 는 `orin/tests/check_hardware.sh` 의 경로 상수 블록·venv activate·cusparseLt LD_LIBRARY_PATH 패치 패턴을 그대로 인용하여, SSH 비대화형 환경에서도 안전하게 venv 를 활성화하고 python3 으로 `flows/entry.py` 를 호출한다. `flows/entry.py` 의 node.yaml 로딩 방식은 `hil_inference.py` 의 `load_gate_config()` / `apply_gate_config()` 패턴을 응용하여 파일 경로 처리 (디렉터리 분기·None 반환·CLI 우선) 를 동일하게 적용했다.

flow 0 은 datacollector 노드 전용으로 "이 환경에서 실행하시는 게 맞나요? [Y/n]" 확인 단계를 구현하고, orin·dgx 는 VSCode remote-ssh 자체 연결이므로 확인 없이 통과한다. flow 1 은 본 노드만 active 로 선택 가능하고 다른 노드 선택 시 안내 메시지 + 재선택 루프로 처리한다.

## code-tester 입장에서 검증 권장 사항

- bash lint: `bash -n 12_interactive_cli_framework.md` (직접 불가 — F2 task 가 파일 생성 후 `bash -n orin/interactive_cli/main.sh`)
- python lint: `ruff check docs/storage/12_interactive_cli_framework.md` (코드 블록 추출 필요 — F2 task 생성 후 `ruff check orin/interactive_cli/flows/entry.py`)
- DOD 충족 확인:
  - [x] main.sh boilerplate 정의 (§2)
  - [x] flow 0 entry.py 코드 (§3)
  - [x] flow 1 장치 선택 메뉴 (§3 flow1_select_node)
  - [x] datacollector "이 환경 맞나요?" 분기 (§3 flow0_confirm_environment)
  - [x] 04 G1 check_hardware.sh bash·python 혼합 패턴 미러 (§2 설계 근거)
  - [x] 04 G2 hil_inference.py --gate-json JSON 로딩 패턴 참고 (§3 설계 근거)
  - [x] §5 노드별 차이점 (flow 2+ 분기점) 정의

## 다음 단계 권고 — F2 task 가 사용할 코드 스니펫

### main.sh (각 노드에 복사 후 VENV_ACTIVATE 한 줄 변경)

```bash
#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NODE_CONFIG="${SCRIPT_DIR}/configs/node.yaml"

# ★ 노드별 변경:
#   orin:          ~/smolvla/orin/.hylion_arm/bin/activate
#   dgx:           ~/smolvla/dgx/.arm_finetune/bin/activate
#   datacollector: ~/smolvla/datacollector/.hylion_collector/bin/activate
VENV_ACTIVATE="${HOME}/smolvla/orin/.hylion_arm/bin/activate"

# ★ orin 전용 — dgx·datacollector 복사 시 삭제
CUSPARSELT_PATH="${HOME}/smolvla/orin/.hylion_arm/lib/python3.10/site-packages/nvidia/cusparselt/lib"

if [[ ! -f "${VENV_ACTIVATE}" ]]; then
    echo "[ERROR] venv not found: ${VENV_ACTIVATE}"
    exit 1
fi

# shellcheck source=/dev/null
source "${VENV_ACTIVATE}"

if [[ -d "${CUSPARSELT_PATH}" ]]; then
    export LD_LIBRARY_PATH="${CUSPARSELT_PATH}:${LD_LIBRARY_PATH:-}"
fi

if [[ ! -f "${NODE_CONFIG}" ]]; then
    echo "[ERROR] configs/node.yaml 미존재: ${NODE_CONFIG}"
    exit 1
fi

exec python3 "${SCRIPT_DIR}/flows/entry.py" --node-config "${NODE_CONFIG}"
```

### flows/__init__.py

```python
# flows/__init__.py
# interactive_cli flows 패키지
```

### flows/entry.py

전체 코드: `docs/storage/12_interactive_cli_framework.md §3` 참조.

### configs/node.yaml (노드별 3 개)

```yaml
# orin/interactive_cli/configs/node.yaml
node: orin
venv: ~/smolvla/orin/.hylion_arm
```

```yaml
# dgx/interactive_cli/configs/node.yaml
node: dgx
venv: ~/smolvla/dgx/.arm_finetune
```

```yaml
# datacollector/interactive_cli/configs/node.yaml
node: datacollector
venv: ~/smolvla/datacollector/.hylion_collector
```

### F2 복사 절차

1. `orin/interactive_cli/` 신규 생성 후 main.sh (VENV_ACTIVATE orin 경로), flows/__init__.py, flows/entry.py, configs/node.yaml (node: orin) 작성
2. `dgx/interactive_cli/` 동일 구조 (VENV_ACTIVATE dgx 경로, cusparseLt 블록 제거, node: dgx)
3. `datacollector/interactive_cli/` 동일 구조 (VENV_ACTIVATE datacollector 경로, cusparseLt 블록 제거, node: datacollector)
4. 각 `interactive_cli/README.md` 작성 (3 노드 동일 복사 동기화 주의 명시)
5. `bash -n <node>/interactive_cli/main.sh` 로 bash 문법 검사

## SKILL_GAP 보고

없음. 본 todo 범위의 모든 패턴이 기존 레퍼런스 (check_hardware.sh, hil_inference.py) 에 존재하여 해당 기반으로 작성했다.

후행 todo (D1·D2) 에서 SKILL_GAP 발생 가능 영역: `record.py` 의 lerobot-record draccus 인자 동적 생성 — D1 study 에서 `docs/reference/lerobot/src/lerobot/scripts/lerobot_record.py` 직접 Read 필수 (04 M1 cycle 1 추측 작성 재발 방지).
