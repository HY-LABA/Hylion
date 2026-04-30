# 03. orin/lerobot/ vs upstream 코드 변경 이력

> 목적: `lerobot/src/lerobot/` (upstream submodule) 대비 `orin/lerobot/`의 코드 변경 사항을 누적 기록한다.
> upstream 기준 commit: `ba27aab79c731a6b503b2dbdd4c601e78e285048` (v0.5.1-42, 2026-04-22 동기화)
>
> 원칙: `orin/lerobot/`은 추론(inference) 전용 레이어이다.
> upstream의 학습/HIL/시뮬레이션 전용 코드는 Orin에서 필요하지 않으며, 의존성 문제를 일으킬 경우 제거한다.

---

## 변경 이력

### [2026-04-23] `policies/smolvla/smolvlm_with_expert.py` — `AutoProcessor` 복원

**대상 파일:** `orin/lerobot/policies/smolvla/smolvlm_with_expert.py`

**변경 내용:**

기존 우회 클래스 `_TokenizerOnlyProcessor`를 제거하고, processor 로딩을 upstream과 동일하게 복원.

```python
# before
self.processor = _TokenizerOnlyProcessor(model_id)

# after
self.processor = AutoProcessor.from_pretrained(model_id)
```

**변경 이유:**

Orin 환경에 torchvision `0.20.0a0+afc54f7` wheel 설치 및 CUDA `torchvision.ops.nms` 검증이 완료되어,
`AutoProcessor` 경로가 더 이상 `torchvision` 의존성 문제로 막히지 않음.
우회 코드를 제거해 upstream 대비 diff를 축소하고 유지보수 부담을 낮춤.

**영향 범위:**

| 기능 | 영향 |
|---|---|
| smolVLA 추론 경로 | 없음 (정상 동작 유지) |
| 학습/HIL/시뮬레이션 경로 | 없음 (본 변경은 추론 경로 processor 복원만 대상) |
| upstream 동기화 난이도 | 개선 (우회 코드 1건 제거) |

### [2026-04-23] `processor/__init__.py` — hil_processor import 제거

**대상 파일:** `orin/lerobot/processor/__init__.py`

**변경 내용:**

```python
# 제거된 import 블록
from .hil_processor import (
    AddTeleopActionAsComplimentaryDataStep,
    AddTeleopEventsAsInfoStep,
    GripperPenaltyProcessorStep,
    GymHILAdapterProcessorStep,
    ImageCropResizeProcessorStep,
    InterventionActionProcessorStep,
    RewardClassifierProcessorStep,
    TimeLimitProcessorStep,
)
```

`__all__` 에서도 위 8개 심볼 제거.

**제거 이유:**

`hil_processor.py`가 `torchvision.transforms.functional`을 import하는데, Orin JetPack 6.2.2 환경에서 당초 호환 torchvision 버전을 구할 수 없었음.

- jp6/cu126 인덱스: torchvision 0.26.0만 제공 → `torch==2.11.0` 전용, ABI 불일치로 오류 발생
- NVIDIA JP 6.0 디렉토리: torch wheel만 제공, torchvision 없음

> **[2026-04-23 업데이트]** Seeed SharePoint에서 PyTorch 2.5 대응 torchvision **0.20** (JP 6.1 & 6.2, CUDA 12.6) wheel 확인. 설치 가능해졌으나, `hil_processor`는 **HIL 학습 전용** 컴포넌트이므로 import 제거 결정은 유지. torchvision 0.20 설치 후에도 이 import는 복원하지 않는다.

`hil_processor`는 HIL(Human-in-the-Loop) RL 학습 전용 컴포넌트이며 smolVLA 추론 경로에서 사용되지 않는다.
smolVLA 추론은 `processor_smolvla.py`를 통해 아래만 사용:
`AddBatchDimensionProcessorStep`, `DeviceProcessorStep`, `NewLineTaskProcessorStep`,
`NormalizerProcessorStep`, `PolicyProcessorPipeline`, `RenameObservationsProcessorStep`,
`TokenizerProcessorStep`, `UnnormalizerProcessorStep`

**영향 범위:**

| 기능 | 영향 |
|---|---|
| smolVLA 추론 (forward pass) | 없음 |
| SO-ARM 모터 제어 / 텔레옵 | 없음 |
| HIL RL 학습 루프 | **사용 불가** (Orin에서는 원래 미지원) |
| 시뮬레이션 환경 (IsaacLab, Libero) | **사용 불가** (Orin에서는 원래 미지원) |

### [2026-04-23] `configs/__init__.py` — DatasetConfig 등 학습 전용 import 제거

**대상 파일:** `orin/lerobot/configs/__init__.py`

**변경 내용:** `from .default import DatasetConfig, EvalConfig, PeftConfig, WandBConfig` 제거 및 `__all__`에서 해당 심볼 제거.

**제거 이유:** `configs/default.py`가 `lerobot.transforms`를 import하고, `transforms.py`가 `torchvision.transforms.v2`를 사용함. 당초 Orin에 설치 가능한 torchvision이 없었으므로 체인을 끊기 위해 제거. torchvision 0.20 설치 후에도 해당 config들은 학습/데이터셋 전용이므로 import 복원하지 않는다. `DatasetConfig`, `EvalConfig`, `PeftConfig`, `WandBConfig`는 학습/데이터셋 전용이며 smolVLA 추론 경로에서 미사용.

---

### [2026-04-23] `utils/io_utils.py` — Python 3.12 generic 함수 문법 패치

**대상 파일:** `orin/lerobot/utils/io_utils.py`

**변경 내용:**

```python
# before (Python 3.12 전용)
def deserialize_json_into_object[T: JsonLike](fpath: Path, obj: T) -> T:

# after (Python 3.10 호환)
_T = TypeVar("_T", bound="JsonLike")
def deserialize_json_into_object(fpath: Path, obj: "_T") -> "_T":
```

**변경 이유:** Python 3.12에서 도입된 generic 함수 선언 문법(`def func[T](...)`)은 Python 3.10에서 `SyntaxError`. `01_compatibility_check.md`에 기록된 Python 버전 불일치 문제의 구체적 사례. `TypeVar` 방식으로 동일한 타입 안전성 유지.

---

### [2026-04-23] `processor/gym_action_processor.py` — hil_processor TELEOP_ACTION_KEY import 제거

**대상 파일:** `orin/lerobot/processor/gym_action_processor.py`

**변경 내용:**

```python
# 제거된 import
from .hil_processor import TELEOP_ACTION_KEY

# 대체: 상수 직접 정의
TELEOP_ACTION_KEY = "teleop_action"
```

**제거 이유:** `gym_action_processor.py`가 `hil_processor.py`에서 `TELEOP_ACTION_KEY`를 import하는데, `hil_processor.py`가 `torchvision.transforms.functional`을 import함. Orin에 torchvision 미설치로 `ModuleNotFoundError` 발생. `TELEOP_ACTION_KEY`는 단순 문자열 상수(`"teleop_action"`)이므로 로컬 정의로 대체.

**영향 범위:** `Numpy2TorchActionProcessorStep`, `Torch2NumpyActionProcessorStep` 동작 변경 없음.

---

### [2026-04-23] `motors/motors_bus.py` — Python 3.12 `type` alias 문법 패치

**대상 파일:** `orin/lerobot/motors/motors_bus.py`

**변경 내용:**

```python
# before (Python 3.12 전용)
type NameOrID = str | int
type Value = int | float

# after (Python 3.10 호환)
from typing import TYPE_CHECKING, Protocol, Union  # Union 추가
NameOrID = Union[str, int]
Value = Union[int, float]
```

**변경 이유:** Python 3.12에서 도입된 `type` 문 (`type Alias = ...`)은 Python 3.10에서 `SyntaxError`. `Union[]` 방식으로 동일한 타입 안전성 유지.

---

### [2026-04-23] `policies/__init__.py`, `policies/factory.py` — smolvla 외 policy import 제거

**대상 파일:**
- `orin/lerobot/policies/__init__.py`
- `orin/lerobot/policies/factory.py`

---

### [2026-04-23] `policies/factory.py` — `Unpack` Python 3.10 호환 패치

**대상 파일:** `orin/lerobot/policies/factory.py`

**변경 내용:**

```python
# before
from typing import TYPE_CHECKING, Any, TypedDict, Unpack

# after
import sys
from typing import TYPE_CHECKING, Any, TypedDict

if sys.version_info >= (3, 11):
    from typing import Unpack
else:
    from typing_extensions import Unpack
```

**변경 이유:** `Unpack`은 Python 3.11에서 `typing` 표준 모듈에 추가됨. Orin Python 3.10에서 `cannot import name 'Unpack' from 'typing'` 오류 발생. `typing_extensions`로 fallback 처리. `pretrained.py`와 `smolvla/modeling_smolvla.py`에도 동일 패턴 적용.

**영향 범위:** 타입 힌트에만 사용. 런타임 동작 변경 없음.

---

### [2026-04-23] `policies/pretrained.py` — `TrainPipelineConfig` import를 TYPE_CHECKING으로 이동

**대상 파일:** `orin/lerobot/policies/pretrained.py`

**변경 내용:**

```python
# before
from lerobot.configs.train import TrainPipelineConfig

# after
if TYPE_CHECKING:
    from lerobot.configs.train import TrainPipelineConfig
```

**변경 이유:** `configs/train.py` → `configs/default.py` → `lerobot.transforms` → `torchvision` 체인으로 인해 `No module named 'lerobot.transforms'` 오류 발생. `TrainPipelineConfig`는 `push_model_to_hub`(학습/업로드 전용 메서드)의 타입 힌트에만 사용되므로, `TYPE_CHECKING` 조건부 import로 런타임 체인을 끊음.

**영향 범위:** 추론 경로(`from_pretrained`, `select_action`) 동작 변경 없음. `push_model_to_hub`는 Orin에서 호출하지 않음.

추가 패치: `from __future__ import annotations`를 파일 최상단에 추가하여 `TrainPipelineConfig` annotation이 런타임에 평가되지 않도록 함. (Python 3.10은 `from __future__ import annotations` 없이는 함수 시그니처 annotation을 클래스 정의 시점에 평가함.)

---

### [2026-04-23] `policies/smolvla/smolvlm_with_expert.py` — `AutoProcessor` → `_TokenizerOnlyProcessor` 교체

**대상 파일:** `orin/lerobot/policies/smolvla/smolvlm_with_expert.py`

**변경 내용:**

`_TokenizerOnlyProcessor` 클래스 추가 및 `AutoProcessor.from_pretrained(model_id)` 호출을 대체:

```python
class _TokenizerOnlyProcessor:
    def __init__(self, model_id: str):
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)

# before
self.processor = AutoProcessor.from_pretrained(model_id)

# after
self.processor = _TokenizerOnlyProcessor(model_id)
```

**변경 이유:**

`AutoProcessor.from_pretrained("HuggingFaceTB/SmolVLM2-500M-Video-Instruct")`가 `SmolVLMProcessor`를 로드하는 과정에서 `video_processing_smolvlm.py`를 import하고, 해당 파일이 `import torchvision.transforms.v2.functional`을 시도함. Orin에 torchvision 미설치로 `ModuleNotFoundError` 발생.

> **[2026-04-23 업데이트]** Seeed SharePoint torchvision **0.20** wheel 설치/검증 완료로 `_TokenizerOnlyProcessor`를 제거하고 `AutoProcessor.from_pretrained(model_id)` 복원 완료.

`self.processor`의 실제 사용처는 `modeling_smolvla.py`에서 두 토큰 ID 접근뿐이므로:
- `self.vlm_with_expert.processor.tokenizer.fake_image_token_id`
- `self.vlm_with_expert.processor.tokenizer.global_image_token_id`

`AutoTokenizer`만 로드해도 동일한 기능 제공 가능. `AutoTokenizer`는 torchvision에 의존하지 않음.

**영향 범위:**

| 기능 | 영향 |
|---|---|
| 이미지 토큰 ID 접근 | 없음 (tokenizer에 포함) |
| 이미지 전처리 (SmolVLA processor pipeline) | 없음 (별도 `processor_smolvla.py`가 담당) |
| 비디오 처리 | **사용 불가** (Orin에서는 원래 미지원)

**변경 내용:**

`__init__.py`: `ACTConfig`, `DiffusionConfig`, `GrootConfig`, `MultiTaskDiTConfig`, `PI0Config`, `PI0FastConfig`, `PI05Config`, `RewardClassifierConfig`, `SACConfig`, `SARMConfig`, `TDMPCConfig`, `VQBeTConfig`, `WallXConfig`, `XVLAConfig` — top-level import 및 `__all__` 에서 모두 제거. `SmolVLAConfig`와 inference 유틸리티(`make_robot_action`, `prepare_observation_for_inference`, factory 함수)만 유지.

`factory.py`: top-level import에서 smolvla 외 모든 Config 클래스 제거. `get_policy_class`, `make_policy_config`, `make_pre_post_processors` 세 함수에서 smolvla 분기만 유지하고 나머지 elif 블록 제거. `make_pre_post_processors` 내 GrootConfig 특수 처리 블록 제거.

**제거 이유:**

`policies/__init__.py`가 upstream 그대로 복사된 상태였으며, `act`, `diffusion`, `groot` 등 Orin에 존재하지 않는 policy 디렉토리를 top-level에서 import해 `ModuleNotFoundError: No module named 'lerobot.policies.act'` 발생. Orin은 smolvla 추론 전용 레이어이므로 해당 policy들은 불필요.

**영향 범위:**

| 기능 | 영향 |
|---|---|
| smolVLA 추론 (forward pass) | 없음 |
| ACT / Diffusion / PI0 등 타 policy | **import 불가** (Orin에서는 원래 미지원) |
| `get_policy_class("smolvla")` | 정상 동작 유지 |
| `make_pre_post_processors(SmolVLAConfig)` | 정상 동작 유지 |

---

### [2026-04-30] 04_infra_setup TODO-O2 — 옵션 B (논리적 비활성화) 원칙 명문화

**대상 파일:** `orin/lerobot/` 전체 (변경 없음 — 본 변경은 원칙 명문화)

**원칙:**

`orin/lerobot/` 의 **파일·디렉터리는 upstream 보존**한다. inference-only 책임에 맞지 않는 모듈은 다음 두 방식으로만 비활성화:

1. **`__init__.py` 의 import 차단** — 본 문서 위 변경 이력 (`policies/__init__.py`, `processor/__init__.py`, `configs/__init__.py` 등) 의 패턴
2. **`orin/pyproject.toml [project.scripts]` 의 entrypoint 등록 해제** — `lerobot-eval` / `lerobot-train` 2개 (04_infra_setup TODO-O2, `02_orin_pyproject_diff.md` 참조)

**제외:** `orin/lerobot/scripts/` 의 18개 파일 (lerobot_train.py, lerobot_eval.py, augment_dataset_quantile_stats.py 등) 자체는 upstream 그대로 보존. 사용자가 CLI 진입할 수 없도록 entrypoint 등록만 해제.

**변경 이유:**

04_infra_setup 마일스톤 진행 중 사용자가 명시적으로 "upstream 의 구조와 내용 최대한 변형 안 함" 원칙 강조. 실태 점검 결과 `orin/lerobot/` 은 이미 본 원칙대로 운영 중 (scripts/ 18개 = upstream 18개 그대로) 이었음을 확인. 본 항목은 향후 트리밍 결정 시 본 원칙을 적용하도록 명문화.

**영향 범위:**

| 기능 | 영향 |
|---|---|
| 기존 추론 경로 (smolvla forward, hil_inference 등) | 영향 없음 (변경 없음) |
| upstream 동기화 시 재트리밍 부담 | 감소 — 파일은 그대로 받고 entrypoint·import 만 관리 |
| 04 진입 후 트리밍 결정 흐름 | 본 원칙대로 entrypoint·import 단에서 처리 |

---

## upstream 동기화 시 재확인 항목

`orin/lerobot/`을 upstream에서 재동기화할 때 아래 파일들이 변경되었는지 확인하고, 필요 시 변경 이력을 추가한다.

- [ ] `processor/__init__.py` — hil_processor import 재추가 여부 확인 후 다시 제거
- [ ] `processor/hil_processor.py` — torchvision 의존성 추가/변경 여부 확인
- [ ] `processor/gym_action_processor.py` — `TELEOP_ACTION_KEY` 정의 위치 변경 여부 확인 (현재 local 정의로 우회)
- [x] `motors/motors_bus.py` — Python 3.12 전용 문법(`type` alias) → `Union[]` 패치 완료. 재동기화 시 lines 51-52 재확인
- [ ] `policies/__init__.py` — smolvla 외 Config import 재추가 여부 확인 후 다시 제거
- [ ] `policies/factory.py` — smolvla 외 policy 분기 재추가 여부 확인 후 다시 제거; `Unpack` import 패치(typing_extensions) 유지 여부 확인
- [ ] `policies/pretrained.py` — `TrainPipelineConfig` import가 TYPE_CHECKING 밖으로 나오면 다시 이동; `Unpack` 패치 유지 여부 확인
- [ ] `policies/smolvla/smolvlm_with_expert.py` — `AutoProcessor` 경로 유지 여부 확인 (upstream 변경 시 재검토)
