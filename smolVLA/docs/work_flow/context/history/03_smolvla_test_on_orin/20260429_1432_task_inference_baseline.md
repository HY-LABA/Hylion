# Current Task
<!-- /handoff-task 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

> 2026-04-29 14:19 | 스펙: `docs/work_flow/specs/03_smolvla_test_on_orin.md` | TODO: 03

## 작업 목표

`orin/examples/tutorial/smolvla/inference_baseline.py` 작성.

사전학습 smolvla_base 의 학습 환경(카메라 키·shape, state dim, language instruction)을 그대로 미러링한 더미 입력으로 `SmolVLAPolicy.select_action` 1회 호출 → action shape / dtype / range 출력.

이 작업은 팀원과 함께 대화형 터미널에서 진행해야 한다.

## DOD (완료 조건)

아래 두 조건을 모두 만족하면 완료:

1. `orin/examples/tutorial/smolvla/inference_baseline.py` 파일이 존재하고 `python -m py_compile` syntax check 통과
2. 스크립트가 아래 기능을 모두 포함:
   - `SmolVLAPolicy.from_pretrained("lerobot/smolvla_base")` 로딩
   - 더미 입력 생성 (카메라 3개 × zero 텐서, state zero, language instruction)
   - `select_action` 1회 호출
   - action shape / dtype / value range 출력 후 정상 종료

실 실행 검증은 TODO-05 (Orin prod 검증) 에서 수행. 여기서는 syntax check 만.

## 구현 대상

- `orin/examples/tutorial/smolvla/inference_baseline.py` — **신규 작성**

## 더미 입력 스펙 (TODO-02 실측값 기준 — 추측 금지)

| 항목 | 값 | 출처 |
|---|---|---|
| 카메라 키 | `observation.images.camera1`, `camera2`, `camera3` | smolvla_base config.json `input_features` |
| 이미지 shape | `[1, 3, 480, 640]` (B=1, C=3, H=480, W=640) | info.json 해상도 기준 |
| state 키 | `observation.state` | info.json |
| state shape | `[1, 6]` (단일팔 6 DOF) | info.json |
| language instruction | `"Pick up the cube and place it in the box."` | tasks.parquet 실측 |
| device | `cuda` | smolvla_base config.json |
| `compile_model` | `False` | 03b §2 B1 가이드 |
| `num_steps` | 10 (기본값) | smolvla_base config.json |
| `n_action_steps` | 50 (기본값) | smolvla_base config.json |

이미지 값: 모두 0 (zero 텐서). `[0, 1]` 범위 float32.

## 참고 레퍼런스

- `docs/reference/lerobot/src/lerobot/policies/smolvla/modeling_smolvla.py` — `SmolVLAPolicy.from_pretrained`, `select_action` 시그니처
- `orin/examples/tutorial/smolvla/smoke_test.py` — 형제 스크립트 (환경 검증)
- `orin/examples/tutorial/smolvla/load_checkpoint_test.py` — 형제 스크립트 (ckpt 호환성)
- `docs/lerobot_study/07b_smolvla_pretrain_dataset_structure.md` §4 — 확정 입력 스펙 표
- `docs/lerobot_study/03b_smolvla_milestone_config_guide.md` §2 — B1 config 가이드

## 레퍼런스 활용 규칙

- 레퍼런스에 동일하거나 유사한 구현이 있으면 반드시 그것을 기반으로 작성한다.
- 레퍼런스에 없는 새로운 스크립트·함수·클래스를 만들어야 할 경우, 구현 전에 반드시 사용자에게 설명하고 확인을 받은 뒤 진행한다.

## 건드리지 말 것
[## 업데이트]

| 날짜       | 작업 항목 | 내용 및 결과 |
|------------|-----------|--------------|
| 2026-04-29 | TODO-03   | orin/examples/tutorial/smolvla/inference_baseline.py 신규 작성 및 문법 체크 완료 (에러 없음) |

### 상세 내역

- SmolVLAPolicy.from_pretrained("lerobot/smolvla_base")로 모델 로딩
- 더미 입력(카메라 3개 × zero 텐서, state, 언어 명령) 생성
- select_action 1회 호출, action의 shape/dtype/range 출력
- python -m py_compile로 문법 체크 완료 (Exit code 0)

#### 완료 조건 충족 여부

1. 파일 생성 및 문법 체크 통과: O
2. 요구 기능(모델 로딩, 더미 입력, select_action, 결과 출력) 포함: O

#### 검증 방법

- python -m py_compile orin/examples/tutorial/smolvla/inference_baseline.py

#### 남은 단계

- Orin 환경에서 실 실행 및 결과 확인 필요 (TODO-05에서 진행)

- `docs/reference/` 하위 전체 (read-only, upstream submodule)
- `orin/examples/tutorial/smolvla/smoke_test.py` — 수정 금지 (형제 스크립트)
- `orin/examples/tutorial/smolvla/load_checkpoint_test.py` — 수정 금지 (형제 스크립트)
- smolvla_base 의 config 플래그 변경 금지 (`num_steps`, `n_action_steps`, `chunk_size` 등 모두 기본값 유지)

## 업데이트
<!-- Copilot이 작업 완료 후 여기에 기록:
- 변경한 내용
- 검증 방법 및 결과 (python -m py_compile 통과 여부)
- 실 실행 검증이 필요한 경우 명시 -->

## 배포
- 일시: 2026-04-29 14:32
- 결과: 완료 (`bash smolVLA/scripts/deploy_orin.sh` 실행, `inference_baseline.py` → `orin:/home/laba/smolvla/orin/examples/tutorial/smolvla/` 전송 확인)
