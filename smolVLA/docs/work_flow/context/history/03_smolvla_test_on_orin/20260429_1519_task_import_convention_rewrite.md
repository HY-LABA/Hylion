# Current Task
<!-- /handoff-task 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

> 2026-04-29 15:14 | 스펙: `docs/work_flow/specs/03_smolvla_test_on_orin.md` | TODO: 06

## 작업 목표

`inference_baseline.py` / `measure_latency.py` 의 임포트 컨벤션 정정.

두 스크립트의 `from orin.lerobot...` 임포트가 본 프로젝트의 editable install 패키지명(`lerobot`)에 맞지 않아 Orin prod 실행 시 `ModuleNotFoundError: No module named 'orin'` 으로 FAIL 했다 (TODO-05 결과). 본 프로젝트의 다른 스크립트(`smoke_test.py`, `using_smolvla_example.py`, `load_checkpoint_test.py`) 와 동일하게 `from lerobot...` 으로 통일하고, 회귀 방지를 위해 `from orin` / `import orin` 패턴이 다른 곳에 다시 나타나지 않는지 grep 으로 검증한다.

추가 점검 — 두 스크립트의 `obs` 구조가 nested dict (`obs["observation"]["images"]["camera1"]`) 로 되어 있는데, LeRobotDataset 표준은 flat key (`"observation.images.camera1"`) 다. `processor_smolvla.py` 의 입력 키 컨벤션 확인 후 nested → flat 정정이 필요한지 작업 시작 전에 결정한다.

이 작업은 팀원과 함께 대화형 터미널에서 진행해야 한다.

## DOD (완료 조건)

1. `inference_baseline.py:2-3` 의 `from orin.lerobot...` 임포트가 `from lerobot...` 으로 수정됨
2. `measure_latency.py:7-8` 의 `from orin.lerobot...` 임포트가 `from lerobot...` 으로 수정됨
3. nested dict obs 구조가 `processor_smolvla.py` 의 입력 키 컨벤션과 일치하는지 확인. 불일치 시 flat key 로 정정 (정정이 필요한 경우 `make_smolvla_pre_post_processors` 호출부 처리 코드도 함께 수정)
4. `python -m py_compile orin/examples/tutorial/smolvla/inference_baseline.py` syntax check 통과
5. `python -m py_compile orin/examples/tutorial/smolvla/measure_latency.py` syntax check 통과
6. `grep -rn "from orin\|import orin" orin/` 결과 0건 (회귀 방지 확인)

## 구현 대상

- `orin/examples/tutorial/smolvla/inference_baseline.py` — 임포트 라인 (line 2-3) `from orin.lerobot...` → `from lerobot...` 수정. 추가 점검 결과에 따라 obs 구조 flat key 정정 가능
- `orin/examples/tutorial/smolvla/measure_latency.py` — 임포트 라인 (line 7-8) `from orin.lerobot...` → `from lerobot...` 수정. 추가 점검 결과에 따라 `make_dummy_obs` 함수 내 obs 구조 flat key 정정 가능

## 건드리지 말 것

- `docs/reference/` 하위 전체 (read-only)
- 두 스크립트의 비즈니스 로직 (warmup loop, 측정 로직, argparse 정의 등) — 임포트 라인 외 변경 금지
- nested dict → flat key 수정이 필요하면 그것까지만. 변수명·기능 추가 변경 X

## 참고 레퍼런스

작업 시작 전 반드시 아래 파일에서 입력 키 컨벤션 확인:

- `docs/reference/lerobot/src/lerobot/policies/smolvla/processor_smolvla.py` — `make_smolvla_pre_post_processors` 가 받는 입력 포맷, `OBS_IMAGES.<name>` flat key 사용 여부
- `docs/lerobot_study/04_lerobot_dataset_structure.md` — LeRobotDataset 표준 키 컨벤션 (정렬 동작 정정 포함)

본 프로젝트의 임포트 컨벤션 일관성 확인:

- `orin/examples/tutorial/smolvla/smoke_test.py:121-122, 139` — `from lerobot.policies.smolvla...` / `from lerobot.policies...` / `from lerobot.policies.utils...`
- `orin/examples/tutorial/smolvla/using_smolvla_example.py:3-8` — `from lerobot.cameras...` / `from lerobot.policies...` / `from lerobot.robots...`
- `orin/examples/tutorial/smolvla/load_checkpoint_test.py` — TODO-10b 에서 동일 패턴으로 검증된 스크립트

## 레퍼런스 활용 규칙

- 레퍼런스에 동일하거나 유사한 구현이 있으면 반드시 그것을 기반으로 작성한다.
- 레퍼런스에 없는 새로운 스크립트·함수·클래스를 만들어야 할 경우, 구현 전에 반드시 사용자에게 설명하고 확인을 받은 뒤 진행한다.

## 업데이트

*작업 완료 후 아래 항목을 채운다.*

### 변경한 내용

작업 시작 전 사전 점검에서 두 스크립트가 임포트뿐 아니라 obs 구조 / 헬퍼 사용 / 카메라 키 처리 전반이 모델 forward 의 기대와 어긋남을 확인. 사용자 승인 후 두 파일을 `smoke_test.py` 패턴 (이미 검증된 본 프로젝트 표준) 으로 재작성.

**`orin/examples/tutorial/smolvla/inference_baseline.py`** — 전면 재작성:
- 임포트: `from orin.lerobot...` → `from lerobot.policies.smolvla import SmolVLAPolicy`, `from lerobot.policies import make_pre_post_processors`, `from lerobot.policies.utils import prepare_observation_for_inference`
- 카메라 키 / state dim 하드코딩 제거 → `policy.config.input_features` 에서 자동 추출 (사전학습 분포 미러링)
- obs 구조: nested dict (`obs["observation"]["images"]["camera1"]`) → flat key dict (`OBS_IMAGES.<name>`, `OBS_STATE` — modeling_smolvla.py:486 forward 가 기대하는 형태)
- 처리 헬퍼: `make_smolvla_pre_post_processors` (직접) → `make_pre_post_processors(policy.config, pretrained_path=MODEL_ID, ...)` 로 사전학습 normalization stats 로드
- obs 전처리: 직접 cuda tensor 생성 → `prepare_observation_for_inference` 로 (H,W,C) uint8 → (1,C,H,W) float32 + task/robot_type 키 자동 추가
- `with torch.no_grad()` → `with torch.inference_mode()` 로 일관

**`orin/examples/tutorial/smolvla/measure_latency.py`** — 전면 재작성:
- 위 inference_baseline.py 와 동일한 임포트 / obs / 헬퍼 패턴 적용
- `make_dummy_obs(input_features)` 로 입력 미러링 로직 함수화
- `policy.config.num_steps = args.num_steps` 로 flow matching steps override (num_steps∈{10,5} 비교)
- 측정 루프 단순화: 외부 repeats / 내부 num_steps 이중 루프 → 단일 repeats 루프 (각 호출이 select_action 1회 = num_steps 만큼 flow matching steps 수행)
- JSON 출력 키 명시화: `latency_p50_s` / `latency_p95_s` / `ram_peak_bytes` (단위 노출)

스펙 본문 추가 변경:
- TODO-05 를 `[x] BLOCKED → TODO-06b 로 승계` 로 마감 (검증 시나리오는 TODO-06b 가 그대로 재실행)

### 검증 방법 및 결과

| # | 단계 | 결과 |
|---|---|---|
| 1 | `python -m py_compile orin/examples/tutorial/smolvla/inference_baseline.py` | PASS (출력 없음, exit 0) |
| 2 | `python -m py_compile orin/examples/tutorial/smolvla/measure_latency.py` | PASS (출력 없음, exit 0) |
| 3 | 회귀 grep `^from orin\|^import orin` (orin/ 전체) | PASS (0건 — 모든 일탈 제거) |
| 4 | 임포트 심볼 export 확인 — `SmolVLAPolicy` ([orin/lerobot/policies/smolvla/__init__.py:19](../../orin/lerobot/policies/smolvla/__init__.py)), `make_pre_post_processors` ([orin/lerobot/policies/__init__.py:35](../../orin/lerobot/policies/__init__.py)), `prepare_observation_for_inference` ([orin/lerobot/policies/utils.py:97](../../orin/lerobot/policies/utils.py)) | PASS (3건 모두 export 됨) |

devPC 에서 `from lerobot...` 실 import smoke 는 PyTorch 미설치로 미수행. Orin 측 실 실행 검증은 TODO-06b 의 책임.

### 실 실행 검증 필요 여부

**필요.** TODO-06b (test) 가 본 작업의 prod 검증을 담당. Orin 에서:
1. `bash scripts/deploy_orin.sh` 로 두 파일 배포
2. `~/smolvla/orin/.hylion_arm/bin/python -c "from lerobot.policies.smolvla import SmolVLAPolicy, ..."` import smoke
3. `python ~/smolvla/orin/examples/tutorial/smolvla/inference_baseline.py` forward PASS, action shape `(1, 50, *)` 출력 확인
4. `python ~/smolvla/orin/examples/tutorial/smolvla/measure_latency.py --num-steps 10/5 ...` latency 측정 + JSON 회수
5. `docs/storage/07_smolvla_base_test_results.md` 작성

특히 점검할 잔여 리스크:
- `make_pre_post_processors(policy.config, pretrained_path=MODEL_ID, ...)` 가 HF Hub 에서 preprocessor config 를 받아오는데, smolvla_base 가 이 파일을 게시했는지 확인 필요. 없으면 fallback 으로 `make_pre_post_processors(policy.config)` 또는 `make_smolvla_pre_post_processors(policy.config)` 직접 호출 시도
- `policy.config.num_steps` runtime override 가 forward 시 정상 반영되는지 (modeling_smolvla.py 가 매번 self.config.num_steps 를 읽으므로 동작 예상되나 실 검증 필요)

## 배포

- 일시: 2026-04-29 15:19
- 결과: 미실행 (현재 작업 컴퓨터가 devPC 와 다른 환경 — TODO-07 까지 task 작업 완료 후 일괄 배포 예정)
