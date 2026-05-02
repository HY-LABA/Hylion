# 13_orin_cli_flow.md

> 작성: 2026-05-01 | task-executor | TODO-O1 study cycle 1
> 목적: orin/interactive_cli/ 의 flow 2 (환경 체크) + flow 3~ (추론 책임) 단계 분석·후보 정의.
>       awaits_user-B 전달 — 사용자 합의 후 O2 task 가 flows/inference.py 를 구현한다.

---

## §1 flow 2 — 환경 체크 (check_hardware.sh 호출)

### 동작

orin 의 flow 2 는 `orin/tests/check_hardware.sh` 를 `--mode resume` 으로 호출한다.
F1 산출물 `12_interactive_cli_framework.md` §5 의 env_check.py 참조 예시:

```python
# orin/interactive_cli/flows/env_check.py (F2/O2 구현 예정)
import subprocess
from pathlib import Path

def run_env_check(script_dir: Path) -> bool:
    check_script = script_dir.parent.parent / "tests" / "check_hardware.sh"
    # check_hardware.sh 지원 인자: --mode, --config, --quiet, --output-json (line 68~83)
    # --gate-json 은 hil_inference.py 전용 인자 — check_hardware.sh 에 전달 불가
    result = subprocess.run(
        ["bash", str(check_script), "--mode", "resume"],
        check=False
    )
    return result.returncode == 0
```

`check_hardware.sh` (orin/tests/check_hardware.sh line 41~49) 의 경로 상수:

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORIN_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONFIG_DIR="${ORIN_DIR}/config"
PORTS_JSON="${CONFIG_DIR}/ports.json"
CAMERAS_JSON="${CONFIG_DIR}/cameras.json"
```

resume 모드는 `orin/config/ports.json` + `cameras.json` 이 실 값으로 채워져 있어야 한다.
first-time 은 04 G2 verification_queue §1번 절차 (카메라·SO-ARM 연결 + `check_hardware.sh --mode first-time`) 로 사전 완료 필요.

### flow 2 출력

```
[flow 2] 환경 체크 중...
  venv: OK
  CUDA: OK
  SO-ARM follower port: /dev/ttyACM0
  카메라: top(idx=0) / wrist(idx=2, flip=True)
[flow 2] 환경 체크 완료 — 추론 준비 완료
```

check_hardware.sh 가 exit 1 을 반환하면 interactive_cli 는 오류 안내 후 종료
(env_check.py 가 False 반환 → main 에서 "환경 체크 실패 — check_hardware.sh 수동 실행을 권장합니다" 출력 + exit).

---

## §2 flow 3~ 후보 옵션

hil_inference.py 전체 직접 Read + 08_orin_structure.md 분석 결과 도출한 후보 3개.

### 후보 A — 3단계 순차

```
flow 3. ckpt 선택
         (HF Hub repo_id 입력 / 로컬 ckpt 경로 입력 / 기본값 smolvla_base 사용)
flow 4. hil_inference.py 실행
         (--gate-json orin/config/ 자동 전달 + ckpt 인자 자동 채움)
         → 사용자가 관찰 중 Ctrl+C 로 종료 또는 --max-steps 도달
flow 5. 결과 보고 출력
         (몇 step 실행 / dry-run vs live 모드 / action_history JSON 경로)
```

특징:
- ckpt 선택 + 추론 실행 + 결과 보고 3단계 명확히 분리
- 시연 데모 관찰 단계 포함 ("로봇이 움직이는 동안 Ctrl+C 로 종료하세요" 안내)
- hil_inference 가 dry-run 이면 결과 JSON 경로 출력, live 이면 SO-ARM 실제 구동

### 후보 B — 2단계 통합

```
flow 3. ckpt 선택 + 실행 옵션 결정
         (ckpt 소스 선택 + dry-run vs live 선택 + max-steps 입력)
         → "시작하겠습니까? [Y/n]" 확인
flow 4. hil_inference.py 실행 (자동)
         → 완료 시 결과 stdout 출력 (별도 데모 단계 없음)
```

특징:
- 단계 수 최소 (2단계)
- 시연 데모 별도 단계 없음 — 결과는 stdout (hil_inference.py 자체 `[step N] action:` 로그)
- 빠른 재실행 (ckpt 교체 후 즉시 재시작)

### 후보 C — 4단계 (task-executor 추가 분석 후보)

```
flow 3. ckpt 선택 (소스 선택 + ckpt 확인)
flow 4. 실행 옵션 설정 (dry-run / live / max-steps / n-action-steps)
flow 5. hil_inference.py 실행 (모니터링 모드)
         → 실행 중 step 카운터 + 현재 action 실시간 출력
flow 6. 결과 요약 + 재실행 여부 질문
         ("동일 ckpt 로 다시 실행하시겠습니까? / 다른 ckpt 로 바꾸시겠습니까?")
```

특징:
- 실행 옵션 상세 조정 단계 포함
- 결과 후 재실행 루프 (ckpt 교체 반복 실험 편의)
- 복잡도 높음 — 초기 사용 시 오버스펙일 수 있음

---

## §3 ckpt 선택 단계 설계

### 후보 소스

| 소스 | 설명 | 인자 변환 |
|---|---|---|
| (1) HF Hub repo_id | 기본: `lerobot/smolvla_base`. 사용자 학습 결과: `<username>/<repo>` | `hil_inference.py --model-id <repo_id>` (현재 미지원 — O2 에서 인자 추가 필요) |
| (2) 로컬 ckpt 경로 | `~/smolvla/orin/checkpoints/<run>/<step>/pretrained_model/` | `hil_inference.py --ckpt-path <path>` (현재 미지원 — O2 에서 인자 추가 필요) |
| (3) 기본값 (smolvla_base) | ckpt 선택 건너뜀 — MODEL_ID 하드코드 그대로 | 추가 인자 없음 |
| (4) 04 T2 sync 결과 | `~/smolvla/orin/checkpoints/` 내 최근 도착 ckpt 자동 탐색 | (2) 와 동일, 자동 탐색 후 경로 제안 |

### 현재 hil_inference.py 의 MODEL_ID 고정

hil_inference.py line 48:

```python
MODEL_ID = "lerobot/smolvla_base"
```

현재 구현에서 model ID 또는 로컬 ckpt 경로는 CLI 인자로 받지 않는다. O2 에서
`--model-id` 또는 `--ckpt-path` 인자 추가가 필요하다. `orin/inference/hil_inference.py` 는
`orin/inference/` 하위로 Category B 비해당 — 일반 코드 수정 (사용자 보고 게이트 없음).

### orin/checkpoints/ 자동 탐색 패턴

08_orin_structure.md §1-2 의 `orin/checkpoints/` 디렉터리:

```
orin/checkpoints/
└── <run_name>/<step>/pretrained_model/
    ├── model.safetensors
    ├── config.json
    └── ...
```

`sync_ckpt_dgx_to_datacollector.sh` 는 `DGX_OUTPUTS/<run>/checkpoints/<step>/pretrained_model`
경로 구조를 그대로 DataCollector 로 전송. Orin 에 동일 구조로 복사되므로
interactive_cli 는 `orin/checkpoints/` 아래를 순회하여 가장 최근 ckpt 를 자동 탐색할 수 있다.

```python
# ckpt 자동 탐색 패턴 (후행 O2 에서 구현)
from pathlib import Path

def find_local_ckpts(checkpoints_dir: Path) -> list[Path]:
    """orin/checkpoints/<run>/<step>/pretrained_model/ 경로 목록 반환 (최신순)."""
    candidates = sorted(
        checkpoints_dir.glob("*/*/pretrained_model"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    return candidates
```

---

## §4 hil_inference.py 호출 구조 (`--gate-json` 인자 자동 채움)

### `--gate-json` 인자 정의 (hil_inference.py line 235~245)

```python
# hil_inference.py line 235~245
parser.add_argument(
    "--gate-json",
    type=str,
    default=None,
    help=(
        "orin/config/ 디렉터리 경로 또는 ports.json 파일 경로. "
        "check_hardware.sh 가 생성한 cache 를 읽어 미지정 인자 "
        "(--follower-port, --cameras, --flip-cameras) 를 자동으로 채운다. "
        "CLI 에 직접 인자를 지정한 경우 그쪽이 우선 (하위 호환)."
    ),
)
```

### `load_gate_config()` 핵심 로직 (hil_inference.py line 80~119)

```python
# hil_inference.py line 80~119
def load_gate_config(gate_json_path: str) -> tuple[dict | None, dict | None]:
    p = Path(gate_json_path)
    if p.is_dir():
        config_dir = p
    else:
        config_dir = p.parent
    ports_path = config_dir / "ports.json"
    cameras_path = config_dir / "cameras.json"
    # ... json.load(f) 로 각각 로드, 실패 시 None 반환
    return ports_data, cameras_data
```

### `apply_gate_config()` 우선순위 규칙 (hil_inference.py line 122~177)

```python
# hil_inference.py line 122~177
# 우선순위: CLI 직접 지정 > gate 파일 > 기본값
# --follower-port: args.follower_port is None 인 경우만 ports_data 에서 채움
# --cameras: args.cameras == default_cameras ("top:0,wrist:1") 인 경우만 gate 값으로 덮어씀
# --flip-cameras: not args.flip_cameras (빈 set) 인 경우만 gate 값 추가
```

### interactive_cli 가 hil_inference.py 를 호출하는 구조

```python
# flows/inference.py 호출 패턴 (O2 구현 예정)
import subprocess
from pathlib import Path

def run_inference(script_dir: Path, ckpt_path: Path | None, mode: str, max_steps: int) -> int:
    hil_script = script_dir.parent.parent / "inference" / "hil_inference.py"
    config_dir = script_dir.parent.parent / "config"

    cmd = [
        "python", str(hil_script),
        "--gate-json", str(config_dir),   # ports.json + cameras.json 자동 채움
        "--mode", mode,
        "--max-steps", str(max_steps),
    ]

    # ckpt 인자 (O2 에서 hil_inference.py 에 추가될 예정)
    if ckpt_path is not None:
        cmd += ["--ckpt-path", str(ckpt_path)]
    elif mode == "dry-run":
        # dry-run 은 --output-json 필수 (hil_inference.py line 257~259)
        cmd += ["--output-json", "/tmp/hil_dryrun.json"]

    result = subprocess.run(cmd, check=False)
    return result.returncode
```

`--gate-json orin/config/` 를 자동으로 전달하면 `--follower-port`, `--cameras`, `--flip-cameras`
를 별도로 입력받지 않아도 된다. flow 2 (check_hardware.sh resume) 가 성공했다면
orin/config/ 에는 실 값이 캐시되어 있는 상태이므로 자동 채움이 동작한다.

---

## §5 시연 데모 모드 (포함 여부 사용자 결정)

### 포함 시 (후보 A·C 해당)

```
[flow 4 또는 5] hil_inference 실행 중...
  --mode live 일 때: "로봇이 움직이고 있습니다. 관찰 후 Ctrl+C 로 종료하세요."
  --mode dry-run 일 때: "dry-run 중 (SO-ARM 미구동). action 로그를 확인하세요."

  [step 0] action: {'shoulder_pan.pos': ..., ...}
  [step 1] action: ...
  ...
  ^C [interrupt] Ctrl+C detected — finishing current step then disconnect.

[flow 5] 추론 완료
  총 실행 step: 47
  결과 JSON: /tmp/hil_dryrun.json  (dry-run 시)
  재실행하시겠습니까? [Y/n]  (후보 C 재실행 루프)
```

### 미포함 시 (후보 B 해당)

- hil_inference.py 자체 `[step N] action:` stdout 로그가 사용자에게 보임
- interactive_cli 는 subprocess.run() 완료 후 종료 코드만 확인
- 결과 요약 출력 없음

### 시연 데모 vs 단순 추론 비교

| 항목 | 포함 (후보 A·C) | 미포함 (후보 B) |
|---|---|---|
| 사용자 안내 메시지 | "로봇이 움직이고 있습니다" 출력 | hil_inference stdout 그대로 |
| 종료 방법 | Ctrl+C 안내 + 결과 보고 | max-steps 도달 또는 Ctrl+C |
| 재실행 편의 | 결과 후 재실행 질문 (후보 C) | 스크립트 재시작 필요 |
| 구현 복잡도 | 중 ~ 높음 | 낮음 |

---

## §6 orin flow 전체 흐름 요약 (후보 A 기준)

```
bash orin/interactive_cli/main.sh
  │
  ├─ venv activate (orin .hylion_arm)
  ├─ cusparseLt LD_LIBRARY_PATH 패치
  └─ python flows/entry.py --node-config configs/node.yaml
       │
       ├─ [flow 0] 노드 확인 (orin: 확인 단계 없음)
       ├─ [flow 1] 장치 선택 (orin[*] 선택)
       ├─ [flow 2] 환경 체크
       │    └─ check_hardware.sh --mode resume
       │         → exit 0: 계속 / exit 1: 오류 안내 + 종료
       ├─ [flow 3] ckpt 선택
       │    (1) HF Hub repo_id 입력
       │    (2) 로컬 ckpt 경로 입력 (orin/checkpoints/ 자동 탐색 제안)
       │    (3) 기본값 smolvla_base 사용
       ├─ [flow 4] hil_inference.py 실행
       │    --gate-json orin/config/   # follower-port + cameras + flip 자동 채움
       │    --mode [dry-run|live]      # 사용자 선택
       │    --max-steps N              # 기본 100
       │    --ckpt-path <path>         # flow 3 결과 (없으면 smolvla_base)
       └─ [flow 5] 결과 보고
            step 수 / 모드 / action JSON 경로 (dry-run 시) 출력
```

---

## §7 O2 task 입력 명세 (사용자 답 후 결정될 사항)

사용자가 §2 후보 중 하나를 선택하면 O2 가 다음을 구현:

| 구현 항목 | 후보 A | 후보 B | 후보 C |
|---|---|---|---|
| flows/inference.py 단계 수 | 3단계 (ckpt·실행·결과) | 2단계 (ckpt+옵션·실행) | 4단계 (ckpt·옵션·실행·재실행) |
| ckpt 소스 UI | 3가지 선택 메뉴 | 3가지 선택 메뉴 | 4가지 (자동 탐색 포함) |
| hil_inference 호출 | subprocess.run() | subprocess.run() | subprocess.run() + 재실행 루프 |
| 시연 데모 출력 | "로봇이 움직이고 있습니다" + Ctrl+C 안내 | stdout 그대로 | 실시간 step 카운터 |
| hil_inference.py 수정 | --ckpt-path 인자 추가 필요 | --ckpt-path 인자 추가 필요 | --ckpt-path + --model-id 인자 추가 |
| 수정 분류 | 일반 코드 수정 (orin/inference/ — Category B 비해당) | 일반 코드 수정 | 일반 코드 수정 |

**공통 결정 사항** (후보 A·B·C 무관):
- `--gate-json orin/config/` 자동 전달 — 추가 인자 입력 없음
- flow 2 (check_hardware.sh resume) 실패 시 flow 3+ 진입 차단
- dry-run 기본 제안 (live 는 사용자 명시 선택)

---

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-01 | 초안 작성 — 04 O1 study 산출물. flow 2 환경 체크 + flow 3~ 후보 3개 + ckpt 선택 메커니즘 + hil_inference 호출 구조 + 시연 데모 모드 정의 |
| 2026-05-01 | cycle 2 정정 — (1) §1 run_env_check() 에서 --gate-json 제거 (check_hardware.sh line 68~83 미지원 인자). (2) §3 hil_inference.py 수정 Category B 오분류 정정 → 일반 코드 수정. (3) §6 흐름도 check_hardware.sh 라인에서 --gate-json 제거. (4) §7 테이블 Category B 행 → "수정 분류: 일반 코드 수정" 로 교체. |
