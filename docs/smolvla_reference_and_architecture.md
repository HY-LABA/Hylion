# SmolVLA 레퍼런스 우선순위 및 프로젝트 아키텍처

## 1) 레퍼런스 우선순위표

아래 표는 현재 목표 시나리오를 기준으로 레퍼런스 우선순위를 정리한 것입니다.
- Brain이 pick_place 명령을 발행
- 필요 시 카메라 + SmolVLA를 온디맨드로 시작
- 대상 물체: starbucks_cup, tumbler, doll
- pretrained SmolVLA 기반 커스텀 에피소드 파인튜닝

| 우선순위 | 레퍼런스(링크) | 적합한 이유 | 재사용할 요소 | 그대로 복사하면 안 되는 요소 |
|---|---|---|---|---|
| P0 (핵심) | [Sa74ll/smolvla-so100-finetune](https://github.com/Sa74ll/smolvla-so100-finetune) | 조작 태스크 실전 파인튜닝 워크플로우와 가장 유사 | 에피소드 분할 전략, 키 리매핑, chunk/fps 정렬, 평가 정규화 | 원본의 정확한 split, 하이퍼파라미터 |
| P0 (핵심) | [aifoundry-org/ETARS](https://github.com/aifoundry-org/ETARS) | 추론 파이프라인 배포/런타임 패턴이 탄탄함 | 모델 로드, pre/post processor 패턴, 결정론적 비교 평가 | 1차 마일스톤에서 불필요한 ONNX 경로 |
| P1 (강추) | [d3d3shan/smolvla_sim2real](https://github.com/d3d3shan/smolvla_sim2real) | SO-101 실로봇 데이터 수집/운영 흐름이 직접적 | record 스크립트, 카메라 이름 적응, hub policy 로딩 패턴 | 로컬 lerobot 패치 전제 |
| P1 (선택) | [RajatDandekar/RL-Token-SmolVLA](https://github.com/RajatDandekar/RL-Token-SmolVLA) | 기본 성능 이후 복구/일반화 보강에 유용 | 단계형 학습 구상(기본 + RL 보강), 개입(intervention) 개념 | 1차 릴리스에 RL 복잡도 추가 |
| P2 (선택) | [ChihyeonYoon/Unity_PickAndPlace_Integration_SmolVLA](https://github.com/ChihyeonYoon/Unity_PickAndPlace_Integration_SmolVLA) | 명령-추론 연결 구조 참고에 유용 | 명령/이미지/상태/액션 인터페이스 분리 | Unity 특화 구현 세부 |
| P3 (맥락) | [goelshivam1210/smolvla](https://github.com/goelshivam1210/smolvla), [wycliffeoleti/smolVLA](https://github.com/wycliffeoleti/smolVLA) 등 LIBERO 전용 레포 | LoRA/연산 제약 트레이드오프 참고 | LoRA 세팅 힌트, 리소스 제약 대응, 평가 위생 | 실로봇 환경으로 직접 전이 |

권장 방향:
- v1은 P0 + P1만으로 구성
- 충분히 평가한 뒤
- 실패 복구가 부족할 때만 RL-token 계열 확장 추가

## 2) 제안 런타임 노드 아키텍처

기존 ROS2 워크스페이스 패키지를 유지하면서 책임 기준으로 분리합니다.

### 2.1 노드 그래프(런타임)

1. Brain Command Node (hylion_brain)
- 입력: 외부 명령/이벤트
- 출력: /brain/action_json (pick_place intent 포함)

2. SmolVLA Orchestrator Node (robot_bridge_pkg)
- 구독: /brain/action_json
- intent != pick_place이면 무시
- intent == pick_place이면 캡처 + 정책 추론 세션 시작
- 발행: /smolvla/status, /smolvla/episode_event

3. Camera Node (robot_bridge_pkg)
- 동기화된 프레임 발행:
  - /smolvla/camera/front
  - /smolvla/camera/wrist
- always-on 또는 on-demand 가능(권장: warm standby)

4. State Node (robot_bridge_pkg)
- 로봇 상태/고유감각(proprioception) 발행:
  - /smolvla/state

5. SmolVLA Policy Node (robot_bridge_pkg)
- 프레임 + 상태 + 작업 텍스트/물체 정보 구독
- select_action 또는 action chunk 생성 수행
- 정규화된 action chunk 발행:
  - /smolvla/action_chunk

6. Action Executor Node (robot_bridge_pkg)
- action chunk 구독
- 액추에이터 명령으로 변환 후 암 컨트롤러로 전달
- 실행 피드백 발행:
  - /smolvla/execution_result

7. Episode Logger Node (robot_bridge_pkg)
- session/episode 메타데이터 및 frame/action 스냅샷 저장
- configs/schemas 하위 스키마 사용

## 3) 제안 리포지토리 구조(robot_project 내부)

기존 폴더를 유지하면서, 코드 배치는 다음 원칙으로 정리합니다.
- 데이터 수집 관련 코드: `data/`
- 파인튜닝/학습 코드: `dgx/`
- 배포 엔트리(런타임 실행 파일): `scripts/`
- 디바이스 전용 모듈/어댑터 코드: `jetson/arm/`

```text
robot_project/
  configs/
    smolvla/
      train_smolvla.yaml
      infer_smolvla.yaml
      objects.yaml
      cameras.yaml
      runtime.yaml
    schemas/
      action.schema.json
      smolvla_session.schema.json
      smolvla_episode.schema.json

  data/
    smolvla/
      sessions/
      processed/
      splits/
      manifests/
      collect/
        smolvla_collect_episodes.py
        smolvla_prepare_dataset.py
        smolvla_data_contracts.py

  dgx/
    smolvla/
      smolvla_train.py
      smolvla_eval.py
      smolvla_export_best.py
      train_configs/

  scripts/
    smolvla_pipeline.py
    smolvla_infer_once.py
    smolvla_runtime_entry.py

  jetson/
    arm/
      smolvla_runtime/
        smolvla_orchestrator.py
        smolvla_executor_adapter.py
        smolvla_preprocess.py
        smolvla_postprocess.py

  ros2_ws/src/hylion_brain/hylion_brain/
    brain_action_publisher.py

  ros2_ws/src/robot_bridge_pkg/robot_bridge_pkg/
    smolvla_orchestrator_node.py
    smolvla_camera_node.py
    smolvla_state_node.py
    smolvla_policy_node.py
    smolvla_executor_node.py
    smolvla_logger_node.py
    smolvla_types.py
    smolvla_preprocess.py
    smolvla_postprocess.py

  ros2_ws/src/robot_bridge_pkg/robot_bridge_pkg/launch/
    smolvla_runtime.launch.py
    smolvla_collect.launch.py
    smolvla_eval.launch.py

  tests/
    3_interface/
      test_action_json_contract.py
      test_smolvla_io_contract.py
    4_unit/
      test_smolvla_preprocess.py
      test_smolvla_postprocess.py
      test_episode_logger.py
    5_integration/
      test_pick_place_pipeline.py

  docs/
    smolvla_reference_and_architecture.md
    smolvla_data_collection_protocol.md
    smolvla_failure_taxonomy.md
```

## 4) 필요한 코드 파일과 책임

### 4.1 데이터 수집 코드(data)

1. data/smolvla/collect/smolvla_collect_episodes.py
- 수집 세션 시작
- 동기화된 이미지 + 액션 스냅샷 캡처
- smolvla_session, smolvla_episode JSON 기록

2. data/smolvla/collect/smolvla_prepare_dataset.py
- raw episode 스키마 검증
- 물체 + 조명 + 배경 + 시점 기준 train/val/test 분할
- 학습용 compact manifest 생성

3. data/smolvla/collect/smolvla_data_contracts.py
- action/session/episode 계약(스키마 키, 필드 변환, 검증 유틸) 단일화
- 수집 파이프라인과 학습 파이프라인 간 포맷 차이 방지

### 4.2 학습 코드(dgx)

1. dgx/smolvla/smolvla_train.py
- pretrained SmolVLA 로드
- 커스텀 에피소드로 파인튜닝
- 체크포인트 및 best model 저장

2. dgx/smolvla/smolvla_eval.py
- 홀드아웃셋 오프라인 평가
- 물체별 성공률과 실패 사유 리포트

3. dgx/smolvla/smolvla_export_best.py
- best checkpoint를 런타임 배포 포맷으로 export
- 배포용 메타데이터(model_id, 데이터 버전, 날짜) 고정

### 4.3 추론/실행 코드(배포 엔트리: scripts)

1. scripts/smolvla_pipeline.py
- 런타임 통합 엔트리 포인트(명령 수신, 추론, 실행, 로깅 흐름)

2. scripts/smolvla_infer_once.py
- 1개 명령/1개 장면으로 빠른 sanity check 실행

3. scripts/smolvla_runtime_entry.py
- 배포 실행 시 환경별 분기(로컬/젯슨/테스트) 및 실행 옵션 관리

### 4.4 디바이스 전용 모듈(jetson/arm)

1. jetson/arm/smolvla_runtime/smolvla_orchestrator.py
- pick_place 트리거 게이트 및 추론 실행 조건 제어

2. jetson/arm/smolvla_runtime/smolvla_executor_adapter.py
- SmolVLA action chunk를 SO-ARM executor 입력 포맷으로 변환
- 안전 제한값과 timeout/retry 정책 적용

3. jetson/arm/smolvla_runtime/smolvla_preprocess.py, smolvla_postprocess.py
- 키 리매핑, 정규화, 액션 스케일 조정

### 4.5 ROS2 런타임 파일(브리지 계층)

1. smolvla_orchestrator_node.py
- 명령 게이트키퍼 + 생명주기 코디네이터
- SmolVLA 추론 허용 시점 제어

2. smolvla_policy_node.py
- 모델 로드/지연 초기화(lazy-init) 정책
- frame/state -> action chunk 변환

3. smolvla_executor_node.py
- 액션 안전성 검사 및 실행
- timeout/cancel/retry 처리

4. smolvla_logger_node.py
- 런타임 텔레메트리 및 에피소드 추적 기록

5. (선택) 브리지 계층에서 공통 전처리/후처리 래핑
- `jetson/arm/smolvla_runtime` 구현을 ROS2 노드에서 재사용

## 5) 노드 메시지 계약(최소)

처음엔 계약을 명확히 하고, 이후 최적화합니다.

1. /brain/action_json
- configs/schemas/action.schema.json과 필드 정렬
- intent, target_object, safety_allowed 필수

2. /smolvla/policy_input
- front image, wrist image, state, task text/object class

3. /smolvla/action_chunk
- action chunk (T x D), timestamp, model_id, confidence(선택)

4. /smolvla/execution_result
- success, failure_reason, elapsed_ms, retries

## 6) 3개 물체용 학습 데이터셋 정책

물체:
- starbucks_cup
- tumbler
- doll

첫 usable 모델을 위한 최소 권장치:
- 물체당 성공 에피소드 80~120개
- 물체당 실패 에피소드 20~40개(misgrip/drop/collision)
- 조명 조건 최소 3개
- 배경 최소 3개
- 초기 물체 포즈 최소 3개

분할 규칙:
- 프레임 단위 분할 금지, 에피소드 단위 분할
- 물체별 균형 train/val/test 유지
- 시점(front/wrist) 균형 분할 유지

## 7) 권장 구현 순서

Phase A (플러밍)
1. 메시지 계약과 스키마 검증 확정
2. orchestrator + camera/state + logger 스켈레톤 구현
3. one-shot 추론 sanity test 추가

Phase B (데이터)
1. 컵/텀블러/인형 에피소드 수집
2. 준비/분할 스크립트 구축
3. 샘플 품질 및 라벨 일관성 검증

Phase C (모델)
1. pretrained 체크포인트에서 파인튜닝
2. 오프라인 평가 + 물체별 breakdown
3. 런타임 배포용 best checkpoint export

Phase D (런타임)
1. policy node와 executor node 연결
2. brain의 pick_place 트리거 활성화
3. 추론 실패 시 안전 fallback 경로 추가

## 8) v1 실무 의사결정

- 첫 pick_place 이후 SmolVLA를 메모리에 유지하여 cold-start 지연 방지
- 명령 단위 timeout 가드(예: 8~12초) + fallback policy 추가
- 실패는 misgrip/drop/collision/timeout/unknown 중 하나로 반드시 기록
- 인터페이스 계약은 초기에 고정하고, 모델/데이터는 그 뒤에서 반복 개선

## 9) 즉시 다음 액션

확장 전에 아래 파일부터 우선 구현:
- data/smolvla/collect/smolvla_collect_episodes.py
- data/smolvla/collect/smolvla_prepare_dataset.py
- dgx/smolvla/smolvla_train.py
- scripts/smolvla_pipeline.py
- ros2_ws/src/robot_bridge_pkg/robot_bridge_pkg/launch/smolvla_runtime.launch.py

이 5개로 최소 수직 슬라이스를 확보할 수 있습니다:
brain command -> policy inference -> execution -> logging.
