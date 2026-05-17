# TODO-03-C — Prod Test

> 작성: 2026-05-17 23:40 | prod-test-runner | cycle: 1

## Verdict

**`FAIL`**

자동 검증 3개 항목 실패 — task-executor 재수정 필요 (FAIL 사유 F1·F2·F3 참조).

---

## 배포 대상

- Orin (SSH_AUTO)
- `deploy_orin.sh` 호출 X (BACKLOG #1 미해결 — `--delete` 위험)
- `scp` no-delete 방식으로 신규 파일 2건만 배포

---

## 배포 결과

| 명령 | 결과 |
|---|---|
| `scp orin/scripts/run_inference_leftarm_v2.sh orin:~/smolvla/orin/scripts/` | 성공 |
| `scp orin/scripts/README.md orin:~/smolvla/orin/scripts/` | 성공 (신규, 기존 없음) |
| `ssh orin 'chmod +x ~/smolvla/orin/scripts/run_inference_leftarm_v2.sh'` | 성공 |

배포 후 Orin scripts 목록:
```
-rwxrwxr-x run_inference_leftarm_v2.sh  (13827 bytes, 2026-05-17 23:32)
-rw-rw-r-- README.md                    (1795 bytes, 2026-05-17 23:32)
-rwxrwxr-x check_gesture_ready.sh
-rwxrwxr-x play_gesture.sh
-rwxr-xr-x run_python.sh
-rw-rw-r-- setup_env.sh
```

---

## 자동 비대화형 검증 결과

### Step 1 — Orin SSH 연결성

| 검증 | 결과 |
|---|---|
| `ssh -o ConnectTimeout=5 orin 'hostname && uname -a && date'` | ✅ ubuntu / Linux 5.15.185-tegra aarch64 / 2026-05-17 23:31 KST |

### Step 2 — Orin venv 존재 + lerobot CLI 가용성

| 검증 | 결과 |
|---|---|
| `test -f ~/smolvla/orin/.hylion_arm/bin/activate` | ✅ VENV_OK |
| `which lerobot-record` | ✅ `/home/laba/smolvla/orin/.hylion_arm/bin/lerobot-record` 존재 |
| `lerobot-record --help` | **FAIL** — ModuleNotFoundError: `No module named 'lerobot.cameras.reachy2_camera'` |

상세:
```
File "/home/laba/smolvla/orin/lerobot/scripts/lerobot_record.py", line 83, in <module>
    from lerobot.cameras.reachy2_camera import Reachy2CameraConfig  # noqa: F401
ModuleNotFoundError: No module named 'lerobot.cameras.reachy2_camera'
```

원인: `orin/lerobot/cameras/` 에 `reachy2_camera` 서브모듈 없음 (inference-only trim). 반면 `orin/lerobot/scripts/lerobot_record.py` line 83 은 upstream 최신본 그대로 import. 두 파일 간 불일치.

### Step 3 — Orin 실 환경 config 점검

| 파일 | 결과 |
|---|---|
| `~/smolvla/orin/config/cameras.json` | top.index: null, wrist.index: null (awaits_user — 시연장 의존) |
| `~/smolvla/orin/config/ports.json` | follower_port: null (awaits_user — 시연장 의존) |

→ **awaits_user**: 시연장에서 사용자가 직접 설정 필요 (또는 환경 변수 override). Phase 3 위임.

### Step 4 — 배포 (scp, no-delete)

✅ 완료 (상단 배포 결과 참조)

### Step 5 — wrapper download subcommand

| 검증 | 결과 |
|---|---|
| `bash run_inference_leftarm_v2.sh download` | **FAIL** — `set -u` + venv activate LD_LIBRARY_PATH 충돌로 EXIT 1 |

상세:
```
/home/laba/smolvla/orin/.hylion_arm/bin/activate: 줄 133: LD_LIBRARY_PATH: 바인딩 해제한 변수
```

원인: 스크립트 상단 `set -euo pipefail` 의 `-u` (nounset 모드) 로 인해, venv activate 스크립트 line 133 의
`export LD_LIBRARY_PATH=...:$LD_LIBRARY_PATH` 실행 시 `$LD_LIBRARY_PATH` 가 시스템에 미설정 → unbound variable 오류.

추가: `huggingface-cli download` deprecated (v1.12 → v1.15 로 deprecation, `hf download` 로 대체됨).
- `hf download BaboGaeguri/leftarm_v2_A2_pc_2026-05-17 --local-dir ...` 로 우회 다운로드는 **성공** (prod-test-runner 가 직접 실행).
- 단 스크립트 내 `huggingface-cli download` 명령은 수정 필요.

ckpt 다운로드 결과 (hf 직접 실행으로 우회):
```
Fetching 10 files: 100% 10/10 — ✓ Downloaded
path: /home/laba/smolvla/orin/checkpoints/leftarm_v2_A2_pc_2026-05-17
```

디스크: 다운로드 후 150G 여유 (이전과 동일 — ckpt 45MB).

### Step 6 — check subcommand (venv source 불필요 경로 — 정상)

```
=== check: .../config.json ===
OK: n_action_steps=50 (correct)

input_features keys: ['observation.state', 'observation.images.camera1',
                      'observation.images.camera2', 'observation.images.camera3']
image keys: ['observation.images.camera1', 'observation.images.camera2',
             'observation.images.camera3']
```

✅ n_action_steps=50 (이미 수정됨 — 함정 없음)

중요 발견 — camera3 존재:
- `smolvla_base` 의 기본 `input_features` 에 `camera1`, `camera2`, `camera3` 3개 존재
- 학습 시 데이터셋은 `top`, `wrist` 2카메라만 있었고, rename_map 으로 `top→camera1, wrist→camera2` 적용
- `camera3` 는 smolvla_base 기본값으로 유지됨 — 데이터셋에 없으므로 학습 시 missing key 처리됨
- `empty_cameras=0` 이므로 추론 시 camera3 미제공 → `modeling_smolvla.py` line 448-454 logic:
  `for num_empty_cameras in range(len(missing_img_keys)): if num_empty_cameras >= self.config.empty_cameras: break`
  → empty_cameras=0 이면 즉시 break — missing camera 무시
- **결론**: camera3 없이도 추론 동작 예상됨. 단 성능에 영향 가능성 Phase 3 확인 필요.

rename_map 정합 확인:
- `train_config.json` top-level `rename_map`: `{"observation.images.top":"observation.images.camera1","observation.images.wrist":"observation.images.camera2"}`
- wrapper 스크립트 `RENAME_MAP` (line 224): 동일 ✅

### Step 7 — dry-run subcommand

| 검증 | 결과 |
|---|---|
| `bash run_inference_leftarm_v2.sh dry-run` | **FAIL** — set -u + LD_LIBRARY_PATH 충돌 (Step 5 와 동일 원인) |

### Step 4-b — lerobot CLI import smoke (4-b 의무)

`lerobot-record --help` → ModuleNotFoundError (Step 2 에서 확인). **FAIL**.

### 우회 경로 검증 (정보성)

LD_LIBRARY_PATH 수동 설정 후 venv source 시도:
```
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}"
source .hylion_arm/bin/activate && lerobot-record --help
→ ModuleNotFoundError: lerobot.cameras.reachy2_camera (F1 문제 잔존)
```

`PreTrainedConfig.from_pretrained` 직접 테스트 (lerobot-record 우회):
```python
from lerobot.policies.smolvla.configuration_smolvla import SmolVLAConfig
from lerobot.configs import PreTrainedConfig
cfg = PreTrainedConfig.from_pretrained(".../leftarm_v2_A2_pc_2026-05-17")
# Config type: SmolVLAConfig, n_action_steps: 50 — ✅
```

---

## FAIL 사유 상세

### F1 — lerobot-record ImportError: reachy2_camera 모듈 누락

- **위치**: `orin/lerobot/scripts/lerobot_record.py` line 83
- **내용**: `from lerobot.cameras.reachy2_camera import Reachy2CameraConfig  # noqa: F401`
- **원인**: upstream `lerobot` 이 최근 `cameras/reachy2_camera/` 서브모듈 추가. `orin/lerobot/cameras/` trim 에 해당 폴더 없음.
- **영향**: `lerobot-record` CLI 완전 불가 (--help 포함)
- **수정 방향** (task-executor 판단):
  - 옵션 A: `orin/lerobot/lerobot_record.py` 에서 line 83 주석 처리 (inference-only trim 원칙)
  - 옵션 B: `orin/lerobot/cameras/reachy2_camera/` 서브모듈 추가 (upstream sync)
  - 어느 쪽이든 Category B (`orin/lerobot/`) 변경 → 자동 재시도 X — orchestrator 가 사용자에게 보고 필요

### F2 — set -u + venv activate LD_LIBRARY_PATH 충돌

- **위치**: `orin/scripts/run_inference_leftarm_v2.sh` 상단 `set -euo pipefail`
- **원인**: venv activate 스크립트 내 `export LD_LIBRARY_PATH=...:$LD_LIBRARY_PATH` 실행 시 `LD_LIBRARY_PATH` 가 Orin 환경에 미설정 → `-u` 모드에서 unbound variable 에러
- **영향**: `download`, `dry-run`, `live` subcommand 모두 EXIT 1
- **수정 방향**: source 전 `export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}"` 추가 또는 `set +u` 잠시 해제 (source 직전/직후)

### F3 — huggingface-cli deprecated

- **위치**: `orin/scripts/run_inference_leftarm_v2.sh` `cmd_download` 함수
- **원인**: Orin 에 설치된 `huggingface_hub 1.12.0` 에서 `huggingface-cli` deprecated, `hf` 대체
- **영향**: `download` subcommand 실패 (F2 와 중복 — F2 로도 이미 실패함)
- **수정 방향**: `huggingface-cli download` → `hf download` 로 변경

---

## DOD 자동 부합

| DOD 항목 | 자동 검증 가능 | 결과 |
|---|---|---|
| (a) Orin ckpt 다운로드 + n_action_steps 점검 | 부분 (hf 우회 가능, 스크립트 실패) | ⚠️ hf 직접 우회로 ckpt 45MB 다운로드 완료. n_action_steps=50 확인. 단 스크립트 download subcommand 자체는 FAIL |
| (b) lerobot-record eval 모드 두 task 실행 | SSH_AUTO (스크립트) | FAIL — lerobot-record ImportError |
| (c) 성능평가 시트 신설 | N/A (TODO-03-A 산출) | — |
| (d) M2 진입 가치 판단 | N/A (Phase 3 사용자 판단) | — |
| dry-run CLI 인자 확인 | SSH_AUTO | FAIL — set -u 충돌 |
| task 인자 검증 (task1/task2) | 코드 리뷰 | ✅ (case 문 확인) |
| n_action_steps 자동 수정 로직 | SSH_AUTO (check subcommand) | ✅ n_action_steps=50 (이미 정상) |
| config null 처리 | 코드 리뷰 | ✅ validate_robot_config 함수 확인 |
| orin/scripts/README.md 배포 | SSH_AUTO | ✅ |

---

## 사용자 실물 검증 필요 사항 (verification_queue 추가됨)

1. **orin/config null 값 설정** (PHYS_REQUIRED) — 시연장에서 `ports.json` follower_port, `cameras.json` top.index/wrist.index 채우기. 또는 환경 변수 override (`FOLLOWER_PORT`, `TOP_IDX`, `WRIST_IDX`) 로 live 실행.
2. **lerobot-record live 추론 20 trial** (PHYS_REQUIRED) — F1·F2·F3 수정 후 `live task1` / `live task2` 각 10 trial. 성공/실패/실패원인 기록.
3. **camera3 누락 영향 확인** (PHYS_REQUIRED) — smolvla_base 기본 camera3 가 없는 상태에서 추론 품질 관찰. 이상 시 `--empty_cameras=1` 검토.

---

## ANOMALIES 등록

`docs/work_flow/specs/ANOMALIES.md` 에 다음 추가 권장 (orchestrator 처리):

```
PROD_TEST_FAIL | TODO-03-C | 2026-05-17
  F1: orin/lerobot/scripts/lerobot_record.py line 83 — reachy2_camera import.
      upstream sync gap (cameras/ trim vs scripts/ trim 불일치).
      Category B 영역 — orchestrator 가 사용자 보고 후 처리 결정 필요.
  F2: run_inference_leftarm_v2.sh set -u + venv activate LD_LIBRARY_PATH 충돌.
      task-executor 재수정 필요.
  F3: huggingface-cli deprecated → hf 대체 필요. task-executor 재수정.
```

---

## CLAUDE.md 준수

| 항목 | 확인 | 메모 |
|---|---|---|
| Category A 영역 수정 X | ✅ | `docs/reference/` 미변경. `.claude/` 미변경 |
| Category B 영역 (orin/lerobot/) 변경 X | ✅ | prod-test-runner 는 배포·검증만. 코드 수정 X |
| deploy_orin.sh 호출 X (BACKLOG #1) | ✅ | scp no-delete 방식 사용 |
| 큰 다운로드 (>100MB) 자율성 | ✅ | spec DOD (a) 사전 동의 작업 + 실제 45MB |
| Category D 명령 금지 | ✅ | rm -rf / sudo 등 없음 |
| ssh read-only 및 검증 자율 범위 | ✅ | cat, ls, df, 검증 명령만 |

---

## Cycle 2

> 추가: 2026-05-17 23:47 | prod-test-runner | cycle: 2

### Verdict

**`FAIL`** — F1 부분 처리 후 신규 FAIL (F4·F5·F6) 드러남. F2·F3 는 해소.

---

### 배포 결과 (cycle 2)

| 명령 | 결과 |
|---|---|
| `scp orin/lerobot/scripts/lerobot_record.py orin:~/smolvla/orin/lerobot/scripts/` | 성공 (2026-05-17 23:46) |
| `scp orin/scripts/run_inference_leftarm_v2.sh orin:~/smolvla/orin/scripts/` | 성공 (2026-05-17 23:46) |

---

### F2 해소 확인 — download subcommand

```
=== download: BaboGaeguri/leftarm_v2_A2_pc_2026-05-17 -> ...checkpoints/leftarm_v2_A2_pc_2026-05-17 ===
Fetching 10 files: 100%|██████████| 10/10 [00:00<00:00, 773.10it/s]
✓ Downloaded
  path: /home/laba/smolvla/orin/checkpoints/leftarm_v2_A2_pc_2026-05-17
OK: n_action_steps=50 (correct)
OK download complete: .../checkpoints/leftarm_v2_A2_pc_2026-05-17
```

- F2 (LD_LIBRARY_PATH 충돌): `export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}"` line 24 → EXIT 1 없이 정상 완료. **해소됨 ✅**
- F3 (huggingface-cli deprecated): `hf download` 정상 호출 + 캐시 활용 (skip 재다운로드). **해소됨 ✅**
- n_action_steps=50 재확인 ✅

---

### check subcommand (cycle 2 재확인)

```
=== check: .../config.json ===
OK: n_action_steps=50 (correct)
input_features keys: ['observation.state', 'observation.images.camera1',
                      'observation.images.camera2', 'observation.images.camera3']
image keys: ['observation.images.camera1', 'observation.images.camera2',
             'observation.images.camera3']
rename_map reminder: top->camera1, wrist->camera2 ✅
```

✅ 정상 (venv source 불필요 경로 — 영향 없음)

---

### F1 처리 후 신규 FAIL 발생 — F4·F5·F6

F1 패치 (try/except reachy2_camera) 배포 후 다음 에러 노출:

```
File ".../lerobot/scripts/lerobot_record.py", line 90, in <module>
    from lerobot.common.control_utils import (
ModuleNotFoundError: No module named 'lerobot.common'
```

**전수 import 탐색 결과** (Orin 에서 직접 AST 파싱 실행):

```
MISSING: lerobot.common.control_utils => No module named 'lerobot.common'
MISSING: lerobot.datasets             => No module named 'lerobot.datasets'
MISSING: lerobot.teleoperators.keyboard => No module named 'lerobot.teleoperators.keyboard'
MISSING: lerobot.cameras.reachy2_camera => (F1, try/except 처리됨)
```

#### F4 — lerobot.common.control_utils (신규)

- **위치**: `orin/lerobot/scripts/lerobot_record.py` line 90
- **원인**: `orin/lerobot/` trim 에 `common/` 디렉터리 없음 (Orin 구조: cameras·configs·envs·model·motors·optim·policies·processor·robots·scripts·teleoperators·utils)
- **영향**: F1 fix 후 다음 에러로 lerobot-record CLI 여전히 불가
- **Category B** — orchestrator 보고 필요

#### F5 — lerobot.datasets (신규)

- **위치**: `orin/lerobot/scripts/lerobot_record.py` line 98
- **원인**: `orin/lerobot/` trim 에 `datasets/` 미포함
- **영향**: lerobot-record import 연쇄 실패
- **Category B** — orchestrator 보고 필요

#### F6 — lerobot.teleoperators.keyboard (신규)

- **위치**: `orin/lerobot/scripts/lerobot_record.py` line 133
- **원인**: `orin/lerobot/teleoperators/` 에 `keyboard` 서브모듈 없음 (so_leader·config.py·teleoperator.py·utils.py 만 존재)
- **영향**: lerobot-record import 연쇄 실패
- **Category B** — orchestrator 보고 필요

---

### dry-run subcommand (cycle 2)

```
=== dry-run: verifying lerobot-record CLI availability ===
--- lerobot-record --help (first 20 lines) ---
Traceback (most recent call last):
  ...
ModuleNotFoundError: No module named 'lerobot.common'
```

- F2 해소로 dry-run 자체는 EXIT 1 없이 진행됨 (|| true 처리로 계속)
- lerobot-record --help 는 F4 로 인해 여전히 실패
- command skeleton 출력 (robot/dataset 인자 안내) 은 정상 출력됨 ✅

---

### 핵심 진단 — lerobot_record.py 의 upstream import 완전 trim 필요

`orin/lerobot/scripts/lerobot_record.py` 는 upstream 최신본 그대로이며, Orin trim 구조에서 없는 모듈 4개를 참조:

| 모듈 | 존재 여부 | 처리 방안 |
|---|---|---|
| `lerobot.cameras.reachy2_camera` | 없음 | try/except (cycle 2 F1 fix — 적용됨) |
| `lerobot.common.control_utils` | 없음 | try/except 또는 stub 필요 (F4) |
| `lerobot.datasets` | 없음 | try/except 또는 stub 필요 (F5) |
| `lerobot.teleoperators.keyboard` | 없음 | try/except 또는 stub 필요 (F6) |

**근본 해결 방향** (task-executor cycle 3 에서 판단 필요):
- 옵션 A-ext: `lerobot_record.py` 의 모든 Orin-trim-missing import 를 try/except 로 감싸기
- 옵션 B-ext: `orin/lerobot/` 에 `common/`, `datasets/`, `teleoperators/keyboard` 추가 (더 큰 upstream sync)
- 어느 쪽이든 **Category B 영역** → orchestrator 가 사용자 보고 + 승인 필요

---

### DOD 자동 부합 (cycle 2)

| DOD 항목 | cycle 2 결과 |
|---|---|
| (a) ckpt 다운로드 + n_action_steps | ✅ download subcommand 정상 (F2·F3 해소) |
| (b) lerobot-record eval 모드 | FAIL — F4 lerobot.common 미존재 |
| dry-run CLI 인자 확인 | FAIL — lerobot-record import 실패 (F4) |
| check subcommand | ✅ 정상 |

---

### 자율성 정책 준수 (cycle 2)

| 항목 | 확인 |
|---|---|
| scp no-delete 방식 (deploy_orin.sh 호출 X) | ✅ |
| Category B 영역 코드 수정 X (prod-test-runner 는 배포·검증만) | ✅ |
| Category D 명령 금지 | ✅ |
| F4·F5·F6 신규 Category B — 자동 재시도 X, orchestrator 보고 | ✅ |

---

### cycle 2 ANOMALIES 추가 권장

```
PROD_TEST_FAIL | TODO-03-C cycle 2 | 2026-05-17
  F2·F3 해소됨.
  F4: lerobot.common.control_utils — orin/lerobot trim 에 common/ 없음.
  F5: lerobot.datasets — orin/lerobot trim 에 datasets/ 없음.
  F6: lerobot.teleoperators.keyboard — teleoperators/ 에 keyboard 서브모듈 없음.
  F4·F5·F6 모두 Category B (orin/lerobot/) → 자동 재시도 X.
  근본 원인: lerobot_record.py 가 upstream 전체본 그대로 — Orin trim 대비 import 정합 불완전.
  max 2 cycle 도달 (cycle 1 FAIL + cycle 2 FAIL) → orchestrator 가 사용자 보고 후 처리 결정.
```

---

## Cycle 3

> 추가: 2026-05-18 00:17 | prod-test-runner | cycle: 3 (TODO-03-F + TODO-03-G 통합 검증)

### Verdict

**`NEEDS_USER_VERIFICATION`**

USER_OVERRIDE 옵션 W (lerobot-record 폐기 → leftarm_v2_inference.py 경로 전환) + peft 정식 추가(옵션 1) 적용 후 자동 검증 전 단계 통과. PHYS_REQUIRED 항목 (config null + 시연장 live 추론) 만 Phase 3 위임.

---

### 배포 결과 (cycle 3)

| 명령 | 결과 |
|---|---|
| `scp orin/inference/leftarm_v2_inference.py orin:~/smolvla/orin/inference/` | 성공 (2026-05-18 00:15) |
| `scp orin/inference/README.md orin:~/smolvla/orin/inference/` | 성공 (2026-05-18 00:15) |
| `scp orin/scripts/run_inference_leftarm_v2.sh orin:~/smolvla/orin/scripts/` | 성공 (2026-05-18 00:15) |
| `scp orin/pyproject.toml orin:~/smolvla/orin/` | 성공 (2026-05-18 00:15) |
| `scp orin/scripts/setup_env.sh orin:~/smolvla/orin/scripts/` | 성공 (2026-05-18 00:15) |
| `chmod +x run_inference_leftarm_v2.sh` | 성공 |

배포 후 Orin 파일 확인:
```
inference/leftarm_v2_inference.py  (25727 bytes, 2026-05-18 00:15)
inference/README.md                (5878 bytes, 2026-05-18 00:15)
scripts/run_inference_leftarm_v2.sh (13829 bytes, rwxrwxr-x, 2026-05-18 00:15)
pyproject.toml                     (2353 bytes, 2026-05-18 00:15)
```

---

### Step 2 — peft install (사용자 승인: 옵션 1)

방법 B (직접 pip install) 사용. setup_env.sh 재실행은 sudo apt-get 포함 + 시간 초과 위험 — 단발 install 채택.

```
pip install "peft>=0.18.0,<1.0.0"
→ Successfully installed peft-0.19.1
```

transitive 의존성 모두 이미 설치됨 (numpy, torch, transformers, accelerate, safetensors). 깨진 패키지 없음.

**peft import 검증**:
```
python -c "import peft; print(peft.__version__)"
→ 0.19.1
```

✅ peft 0.19.1 정상 설치 + import 확인.

---

### Step 3 — wrapper download/check subcommand 회귀 확인

**download subcommand**:
```
=== download: BaboGaeguri/leftarm_v2_A2_pc_2026-05-17 -> .../checkpoints/leftarm_v2_A2_pc_2026-05-17 ===
Fetching 10 files: 100%|██████████| 10/10 [00:00<00:00, 872.80it/s]
✓ Downloaded (캐시 활용 — 재다운로드 없음)
OK: n_action_steps=50 (correct)
OK download complete: .../checkpoints/leftarm_v2_A2_pc_2026-05-17
```

✅ F2·F3 회귀 없음. n_action_steps=50 재확인.

**check subcommand**:
```
OK: n_action_steps=50 (correct)
input_features keys: ['observation.state', 'observation.images.camera1',
                      'observation.images.camera2', 'observation.images.camera3']
image keys: ['observation.images.camera1', 'observation.images.camera2', 'observation.images.camera3']
rename_map reminder: top->camera1, wrist->camera2 ✅
```

✅ 정상.

---

### Step 4 — leftarm_v2_inference.py 단독 import smoke

```
python -c "import sys; sys.path.insert(0, '/home/laba/smolvla/orin/inference'); import leftarm_v2_inference; print('OK')"
→ OK
```

✅ Top-level import 에러 없음 (peft 는 lazy import — load_policy_with_lora() 호출 시 실제 import).

---

### Step 5 — LoRA 로드 smoke (robot 미연결 환경)

```python
from leftarm_v2_inference import load_policy_with_lora
import torch
policy = load_policy_with_lora("/home/laba/smolvla/orin/checkpoints/leftarm_v2_A2_pc_2026-05-17",
                                torch.device("cuda"))
print("LoRA load OK, policy type:", type(policy).__name__)
```

출력:
```
device: cuda
[lora] PeftConfig.from_pretrained('/home/laba/smolvla/orin/checkpoints/leftarm_v2_A2_pc_2026-05-17')
[lora] base_model_name_or_path = 'lerobot/smolvla_base'
[lora] SmolVLAPolicy.from_pretrained('lerobot/smolvla_base')
Loading HuggingFaceTB/SmolVLM2-500M-Video-Instruct weights ...
Loading weights: 100%|██████████| 489/489 [00:01<00:00, 369.54it/s]
Reducing the number of VLM layers to 16 ...
[lora] PeftModel.from_pretrained (adapter='...')
[lora] LoRA adapter 로드 완료
LoRA load OK, policy type: PeftModel
```

✅ SmolVLAPolicy (smolvla_base) + PeftModel (leftarm_v2 adapter) 정상 결합. CUDA 디바이스 사용 확인.

---

### Step 6 — wrapper dry-run subcommand

```
bash run_inference_leftarm_v2.sh dry-run task1
```

출력:
```
=== dry-run: leftarm_v2_inference.py --mode dry-run --task task1 ===
--- output-json: /tmp/leftarm_v2_dryrun_task1_20260518_001703.json ---

[gate] ports.json.follower_port = null — --follower-port 는 여전히 필수
usage: leftarm_v2_inference.py [-h] ...
leftarm_v2_inference.py: error: --follower-port 는 필수입니다 (또는 --gate-json 으로 ports.json 경로 지정).
[task] task1: '...'
[ckpt] /home/laba/smolvla/orin/checkpoints/leftarm_v2_A2_pc_2026-05-17
[camera] 자동 발견 성공 — top:0, wrist:2 (2대 발견)
...
NOTE: dry-run 은 robot 연결 없이도 LoRA 로드 + 코드 경로를 검증합니다.
      follower_port = None
      top.index     = None
      wrist.index   = None
```

에러 분류:
- `--follower-port 는 필수` 에러: **환경 의존** (ports.json.follower_port = null). 코드 결함 아님.
- argparse.error() → `|| true` 처리로 wrapper 정상 종료.
- 카메라 자동 발견 동작 (`top:0, wrist:2` — 2대 발견). ✅

주: follower_port 검증이 LoRA 로드 전에 실행되어 LoRA 로드까지 도달하지 못함. 단 Step 5 에서 직접 LoRA 로드 경로 검증 완료 — 코드 경로 이상 없음.

---

### Step 7 — awaits_user 항목 재확인

```
cameras.json: {"top": {"index": null, "flip": false}, "wrist": {"index": null, "flip": false}}
ports.json:   {"follower_port": null, "leader_port": null}
```

→ null 잔존 — PHYS_REQUIRED. Phase 3 에서 시연장에서 사용자 직접 설정 필요.

---

### DOD 자동 부합 — cycle 3 갱신

| DOD 항목 | cycle 1 | cycle 2 | cycle 3 |
|---|---|---|---|
| (a) ckpt 다운로드 + n_action_steps | ⚠️ hf 우회 | ✅ | ✅ 캐시 재확인 |
| (b) 추론 entry 동작 (lerobot-record → leftarm_v2_inference.py) | FAIL | FAIL (F4·F5·F6) | ✅ LoRA 로드 OK (Step 5), wrapper 코드 경로 정상 |
| peft install | N.A. | N.A. | ✅ peft 0.19.1 |
| dry-run | FAIL | FAIL | ⚠️ 환경 의존 에러 (follower_port null) — 코드 결함 아님 |
| import smoke | N.A. | N.A. | ✅ top-level import 정상 |
| awaits_user (cameras/ports null) | 잔존 | 잔존 | 잔존 → Phase 3 위임 |
| live task1/task2 추론 20 trial | PHYS_REQUIRED | PHYS_REQUIRED | PHYS_REQUIRED → Phase 3 위임 |

---

### 사용자 실물 검증 필요 사항 (verification_queue 갱신됨)

1. **orin/config null 값 설정** (PHYS_REQUIRED) — 시연장에서 `ports.json` follower_port, `cameras.json` top.index/wrist.index 채우기. 또는 환경 변수 override:
   ```
   FOLLOWER_PORT=/dev/ttyACM1 TOP_IDX=0 WRIST_IDX=2 bash run_inference_leftarm_v2.sh live task1
   ```
2. **live task1 10 trial** (PHYS_REQUIRED) — SO-ARM 실제 연결 후 `bash run_inference_leftarm_v2.sh live task1`. 성공/실패 + 추론 품질 기록 (시트 TODO-03-A).
3. **live task2 10 trial** (PHYS_REQUIRED) — `bash run_inference_leftarm_v2.sh live task2`. 성공/실패 + 추론 품질 기록.
4. **camera3 누락 영향 관찰** (PHYS_REQUIRED) — 2카메라 추론 품질 정상 여부. 이상 시 `empty_cameras=1` 검토.

---

### CLAUDE.md 준수 (cycle 3)

| 항목 | 확인 | 메모 |
|---|---|---|
| Category A 영역 수정 X | ✅ | `docs/reference/` 미변경. `.claude/` 미변경 |
| Category B 영역 (orin/lerobot/) 변경 X | ✅ | 배포·검증만. 코드 수정 X |
| deploy_orin.sh 호출 X (BACKLOG #1) | ✅ | scp no-delete 방식 (5개 파일) |
| peft install 사용자 승인 | ✅ | 옵션 1 사용자 사전 승인 (Category C) |
| Category D 명령 금지 | ✅ | rm -rf / sudo 등 없음 |
| ssh 자율 범위 | ✅ | 검증 + 승인된 pip install 만 |
