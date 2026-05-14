# Current Task
<!-- /handoff-task 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

> 2026-04-29 15:23 | 스펙: `docs/work_flow/specs/03_smolvla_test_on_orin.md` | TODO: 07

## 작업 목표

실 SO-ARM hardware-in-the-loop 추론 스크립트 작성.

03 마일스톤의 핵심 가치 — "사전학습된 smolVLA 가 Orin 에서 **하드웨어와 함께** 정상 동작하는지 검증" — 을 책임지는 단계. TODO-06 까지의 더미 입력 forward 검증 위에, 실 카메라 프레임 + 실 follower joint state 입력으로 forward → action chunk 출력 → (모드별로) 실 follower 에 송신하는 스크립트를 작성한다.

본 작업은 **스크립트 작성만** 이며 실 SO-ARM 연결 환경에서의 동작 검증은 TODO-07b 의 책임.

이 작업은 팀원과 함께 대화형 터미널에서 진행해야 한다.

## DOD (완료 조건)

1. `orin/examples/tutorial/smolvla/hil_inference.py` 작성. argparse 지원:
   - `--mode {dry-run,live}` (필수, 기본값 `dry-run`)
   - `--cameras` (사전학습 분포와 일치하는 카메라 키 — TODO-02 분석 결과 기반, 작업 시작 시 확정)
   - `--n-action-steps 5` (안전을 위해 기본값을 50→5 로 축소)
   - `--max-steps 100` (전체 실행 step 상한)
   - `--output-json` (dry-run 모드에서 action dump JSON 경로)
2. dry-run 모드: action 을 stdout + JSON 으로 dump, follower 에 미송신
3. live 모드: action 을 follower 에 송신, 비상 시 Ctrl+C 가능
4. 안전 장치 (i)+(iii) 적용 — `SO100Follower` 기본 토크 한계 의존 + `n_action_steps=5` 짧은 chunk
5. lerobot 의 카메라/로봇 API 는 `using_smolvla_example.py` 패턴 그대로 재사용 — 신규 robot/camera 클래스 작성 X
6. `python -m py_compile orin/examples/tutorial/smolvla/hil_inference.py` syntax check 통과
7. 회귀 grep `from orin\|import orin` 결과 0건 유지

## 구현 대상

- `orin/examples/tutorial/smolvla/hil_inference.py` (신규 작성)

## 건드리지 말 것

- `docs/reference/` 하위 전체 (read-only)
- `orin/lerobot/` 하위 (curated subset, 필요 시 점검만 — 수정 X)
- 기존 작성된 `inference_baseline.py` / `measure_latency.py` / `smoke_test.py` / `using_smolvla_example.py` / `load_checkpoint_test.py` (TODO-07 은 신규 파일 추가만)
- 신규 robot / camera 클래스 작성 금지 — `lerobot.robots.so_follower.SO100Follower` / `lerobot.cameras.opencv.OpenCVCameraConfig` 그대로 재사용

## 작업 시작 전 사전 점검

작업 시작 시 가장 먼저:

1. **TODO-02 산출물 읽기** — `docs/lerobot_study/07b_smolvla_pretrain_dataset_structure.md` 의 단일팔 섹션에서 `svla_so100_pickplace` 의 카메라 키 이름 확정 (BACKLOG 03_smolvla_test_on_orin #1 — 학습 카메라 키 vs 데이터셋 카메라 키 불일치 이슈)
2. **`using_smolvla_example.py` 의 lerobot API 호출 패턴 정독** — OpenCVCameraConfig / SO100Follower / SO100FollowerConfig 의 인자 구조, observation 수집 흐름, action 송신 흐름

확정된 카메라 키 이름 / 사용 가능한 API 시그니처를 사용자에게 보고한 후 hil_inference.py 의 최종 형태를 보여드리고 동의받은 후 Edit 진입.

## 참고 레퍼런스

작업 시작 전 확인:

- `docs/lerobot_study/07b_smolvla_pretrain_dataset_structure.md` — 사전학습 데이터셋 카메라 키 이름 (TODO-02 산출물)
- `orin/examples/tutorial/smolvla/using_smolvla_example.py` — lerobot 카메라/로봇 API 사용 패턴 (재사용 기준)
- `orin/examples/tutorial/smolvla/inference_baseline.py` — TODO-06 으로 작성된 forward baseline (입력 미러링 / make_pre_post_processors 패턴)
- `orin/lerobot/cameras/opencv/` — OpenCVCameraConfig 시그니처
- `orin/lerobot/robots/so_follower/` — SO100Follower / SO100FollowerConfig 시그니처
- `docs/reference/lerobot/src/lerobot/policies/smolvla/modeling_smolvla.py:486` — forward 가 기대하는 batch 키 (`batch[OBS_STATE]` 등 flat key)

본 마일스톤의 위치 재확인:

- 03 의 책임은 "**파이프라인 검증**" — 사전학습 모델이 실 hardware 루프에 끼워졌을 때 에러 없이 forward 가 돌고 action 이 송신되는지만 본다
- "**태스크 검증**" (실제 큐브 pick-and-place 성공) 은 04 의 책임 — 사전학습 분포와 본 프로젝트 환경의 차이가 크므로 03 단계에서 의미 있는 태스크 성공은 기대하지 않음

## 안전 장치 설계

| 장치 | 적용 방법 |
|---|---|
| (i) 모터 토크 한계 | `SO100Follower` 의 기본 토크 한계에 의존. 별도 코드 X |
| (ii) action 클램프 | 본 마일스톤 미적용. 04 학습 데이터 분포 확보 후 도입 검토 (BACKLOG #7) |
| (iii) chunk 짧게 끊기 | `n_action_steps=5` (chunk_size=50 의 1/10). 폭주 시 영향 시간 대폭 축소 |

추가 안전 — `--max-steps` 인자로 전체 실행 step 상한 부여, Ctrl+C 시 깔끔한 종료 (try/finally 로 follower disconnect)

## 레퍼런스 활용 규칙

- 레퍼런스에 동일하거나 유사한 구현이 있으면 반드시 그것을 기반으로 작성한다.
- 레퍼런스에 없는 새로운 스크립트·함수·클래스를 만들어야 할 경우, 구현 전에 반드시 사용자에게 설명하고 확인을 받은 뒤 진행한다.

## 업데이트

*작업 완료 후 아래 항목을 채운다.*

### 변경한 내용

작업 시작 전 사전 점검 4단계 완료 후 사용자 승인 받아 신규 파일 1개 작성.

2026-04-29 테스트 중 추가:
- `orin/examples/tutorial/smolvla/hil_inference.py` 에 `--flip-cameras` 옵션 추가.
- 지정한 카메라 이름의 raw observation 이미지를 policy 입력 전 상하반전하도록 처리.
- 이번 Orin 검증에서 wrist 카메라가 상하반전된 상태라 `--flip-cameras wrist` 로 테스트 한정 보정 가능.

**사전 점검 산출 결정**:
- TODO-02 산출물 (`docs/lerobot_study/07b_smolvla_pretrain_dataset_structure.md`) 검토:
  - smolvla_base config 카메라 키 = `camera1/2/3` (3대), svla_so100_pickplace 데이터셋 키 = `top/wrist` (2대) — 사전학습은 LeRobot Community Datasets 통합 분포로 추정
  - 03 실 하드웨어 환경: 카메라 2대 (top + wrist) → smolvla_base 의 `camera1/camera2` 슬롯에 매핑, `camera3` 은 `empty_cameras=1` 로 더미(mask=0) 처리
- API 패턴 정독 (`using_smolvla_example.py`): `OpenCVCameraConfig` / `SO100FollowerConfig` / `build_inference_frame` / `make_robot_action` / `hw_to_dataset_features` 의 호출 흐름 확인 — 신규 robot/camera 클래스 작성 X, 그대로 재사용
- 카메라 키 매핑 결정 — 사용자 승인:
  - 전략 A (hil_inference.py 안에서 직접 dict key 를 `camera1/2` 로 생성. processor rename 의존 X)
  - 임의 고정 (`top → camera1`, `wrist → camera2`. argparse `--cameras top:0,wrist:1`)
  - `policy.config.empty_cameras = 1` runtime 설정 (3-2 슬롯 더미)
- 안전 장치 설계 — 사용자 승인:
  - SIGINT 핸들러 → `interrupted=True` 만 set, 현재 step 마무리 후 graceful 종료 (시리얼 통신 중 KeyboardInterrupt 회피)
  - try/finally → 어떤 종료 경로로든 `robot.disconnect()` 호출 (모터 토크 enable 상태 방치 방지)

**신규 파일** — `orin/examples/tutorial/smolvla/hil_inference.py`:
- argparse 6개: `--mode {dry-run,live}`, `--follower-port` (필수), `--follower-id`, `--cameras top:0,wrist:1`, `--n-action-steps 5`, `--max-steps 100`, `--output-json` (dry-run 시 필수)
- `parse_camera_arg("top:0,wrist:1")` 헬퍼 — 입력 순서 보존 dict 반환
- 모델 로드 후 `policy.config.empty_cameras=1` + `policy.config.n_action_steps=args.n_action_steps` runtime override (안전 장치 (iii))
- 카메라 dict: `SLOT_MAP = ["camera1", "camera2"]` 와 `args.cameras.items()` 를 `zip` 으로 결합 → smolvla_base 슬롯 이름으로 카메라 등록
- 추론 루프: `robot.get_observation()` → `build_inference_frame` (raw obs → flat key 변환 + task/robot_type) → `preprocess` → `policy.select_action` (inference_mode) → `postprocess` → `make_robot_action` → 모드별 분기 (dry-run: stdout + history, live: `robot.send_action()`)
- 종료: SIGINT 핸들러 + try/finally `robot.disconnect()` (예외/Ctrl+C/정상 종료 모든 경로 안전)
- dry-run JSON 출력: `model_id`, `mode`, `n_action_steps`, `total_steps`, `interrupted`, `actions[{step, action}]`

### 검증 방법 및 결과

| # | 단계 | 결과 |
|---|---|---|
| 1 | `python -m py_compile orin/examples/tutorial/smolvla/hil_inference.py` | PASS (출력 없음, exit 0) |
| 2 | 회귀 grep `^from orin\|^import orin` (orin/ 전체) | PASS (0건 — TODO-06 완료 상태 유지) |
| 3 | 임포트 심볼 export 확인 — `OpenCVCameraConfig` ([orin/lerobot/cameras/opencv/__init__.py:18](../../orin/lerobot/cameras/opencv/__init__.py)), `make_pre_post_processors` ([orin/lerobot/policies/__init__.py:35](../../orin/lerobot/policies/__init__.py)), `SmolVLAPolicy` ([orin/lerobot/policies/smolvla/__init__.py:19](../../orin/lerobot/policies/smolvla/__init__.py)), `make_robot_action` ([orin/lerobot/policies/__init__.py:29](../../orin/lerobot/policies/__init__.py)), `SO100Follower` / `SO100FollowerConfig` ([orin/lerobot/robots/so_follower/__init__.py:26-27](../../orin/lerobot/robots/so_follower/__init__.py)) | PASS (5건 모두 export) |
| 4 | 모듈 직접 경로 import — `build_inference_frame` ([orin/lerobot/policies/utils.py:140](../../orin/lerobot/policies/utils.py)), `hw_to_dataset_features` ([orin/lerobot/utils/feature_utils.py:47](../../orin/lerobot/utils/feature_utils.py)) | PASS (`__all__` 미등록이나 모듈 경로 직접 import 가능 — `using_smolvla_example.py` 동일 패턴) |
| 5 | `python -m py_compile orin/examples/tutorial/smolvla/hil_inference.py` (`--flip-cameras` 추가 후) | PASS (출력 없음, exit 0) |
| 6 | 회귀 grep `^from orin\|^import orin` (orin/ 전체, `--flip-cameras` 추가 후) | PASS (0건) |
| 7 | Orin: `ssh orin "source ~/smolvla/orin/.hylion_arm/bin/activate && python ~/smolvla/orin/examples/tutorial/smolvla/hil_inference.py --help"` | PASS (`--flip-cameras` help 출력 확인, exit 0) |

devPC 측 PyTorch 미설치로 실 import smoke 는 미수행 — Orin 측 prod 검증은 TODO-07b 의 책임.

### 실 실행 검증 필요 여부

**필요.** TODO-07b (test) 가 본 작업의 prod 검증을 담당. Orin + 실 follower SO-ARM 1대 + 카메라 2대(top + wrist) 환경에서:

1. dry-run 모드로 action shape / dtype / range 점검 (`--max-steps 5 --output-json`)
2. dry-run JSON 의 action 값 검토 — 비정상적으로 큰 값 (절댓값 > 학습 분포 95%ile 추정) 없는지
3. live 모드 5 step 짧게 실행 — 팔 동작 + 안전 (관절 한계·충돌·과전류 미발생) 관찰
4. step 3 정상 시 `--max-steps 50` 으로 확장
5. 결과를 `docs/storage/07_smolvla_base_test_results.md` §7 에 기록

특히 점검할 잔여 리스크:
- `policy.config.n_action_steps = 5` 가 실제로 select_action 의 queue 동작에 반영되는지 — dry-run JSON 의 step 0~4 action 값이 동일 chunk 출처인지 (queue 동작 OK) 또는 매 step 새 forward 출처인지 (queue 미동작 — TODO-07b 결과 검토 후 결정)
- 카메라 키 매핑 (`top→camera1, wrist→camera2`) 이 사전학습 분포의 실제 의미와 어긋나도 03 단계는 정성 검증이라 OK. 04 진입 시 데이터 수집 단계에서 재정렬 필요할 수 있음 — BACKLOG 트리거 항목
- HF Hub 첫 다운로드 5~15분 가능
- SO-ARM USB 포트 번호가 연결 순서로 바뀜 (BACKLOG 01_teleoptest #1) → TODO-07b 실행 전 `lerobot-find-port` 로 재확인 필수

## 배포

- 일시: 2026-04-29 16:41 (TODO-07b 완료 시점 기준)
- 결과: 완료 — devPC 측 `bash smolVLA/scripts/deploy_orin.sh` 로 일괄 배포 후 TODO-06b / TODO-07b prod 검증 모두 PASS
