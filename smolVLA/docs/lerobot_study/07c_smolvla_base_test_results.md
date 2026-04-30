# smolVLA Base Orin Test Results

> 작성일: 2026-04-29
> 대상: `lerobot/smolvla_base`
> 환경: Orin JetPack 6.2, Python 3.10, venv `~/smolvla/orin/.hylion_arm`

## 1. 목적

TODO-06 산출물인 `inference_baseline.py`와 `measure_latency.py`가 Orin prod 환경에서 동작하는지 확인하고, 더미 입력 기준의 smolVLA base 추론 baseline을 기록한다.

본 측정은 SO-ARM 또는 실 카메라 없이 사전학습 모델 입력 스펙에 맞춘 더미 관측으로 수행했다. 따라서 결과는 실 태스크 성능이 아니라 코드 경로와 자원 점유 baseline으로 해석한다.

## 2. 입력 스펙 매칭

`inference_baseline.py`는 `policy.config.input_features`를 기준으로 더미 입력을 생성했다.

| 입력 키 | 타입 | shape | 더미 입력 |
|---|---|---:|---|
| `observation.state` | STATE | `(6,)` | float32 random |
| `observation.images.camera1` | VISUAL | `(3, 256, 256)` | uint8 random image |
| `observation.images.camera2` | VISUAL | `(3, 256, 256)` | uint8 random image |
| `observation.images.camera3` | VISUAL | `(3, 256, 256)` | uint8 random image |

실행 중 `HuggingFaceTB/SmolVLM2-500M-Video-Instruct` weights 로드와 VLM layer 16개 축소 메시지를 확인했다.

## 3. Forward Baseline

`inference_baseline.py`는 exit code 0으로 완료했다.

| 항목 | 관측값 |
|---|---:|
| action shape | `(1, 6)` |
| action dtype | `torch.float32` |
| action min | `0.015049` |
| action max | `0.732357` |

주의: 현재 테스트 DOD의 기대 shape는 `(1, 50, *)`이나, 스크립트는 `policy.select_action()`과 postprocess 이후의 단일 action을 출력하여 `(1, 6)`이 관측됐다. forward pass 자체는 성공했지만, chunk 전체 shape를 검증하려면 별도 계측이 필요하다.

## 4. Latency 비교

측정 JSON은 Orin의 `/tmp`에 저장한 뒤 devPC의 `/tmp`로 회수했다.

| num_steps | warmup | repeats | p50 | p95 | RAM peak |
|---:|---:|---:|---:|---:|---:|
| 10 | 10 | 50 | 5.59 ms | 5.82 ms | 3068.30 MiB |
| 5 | 10 | 50 | 5.59 ms | 6.20 ms | 3041.91 MiB |

`num_steps=5`가 `num_steps=10` 대비 latency 감소를 보이지 않았다. 현재 측정은 `select_action()` 경로를 반복 호출하므로 action queue 영향으로 flow matching step 차이가 직접 드러나지 않았을 가능성이 있다.

## 5. 자원 기준선

| 항목 | 기준선 |
|---|---:|
| 모델 | `lerobot/smolvla_base` |
| device | CUDA |
| peak RSS, num_steps=10 | 3068.30 MiB |
| peak RSS, num_steps=5 | 3041.91 MiB |
| HF Hub 상태 | unauthenticated warning 출력, 캐시 사용 |

latency 원시 배열에는 긴 outlier가 1회씩 포함됐다. p95에는 크게 반영되지 않았지만, 실 카메라와 로봇 루프 측정에서는 outlier 원인도 함께 확인해야 한다.

## 6. 잔여 리스크

- venv를 활성화하지 않고 venv python을 직접 실행하면 `libcusparseLt.so.0` 로드 실패가 발생했다. `activate`의 `LD_LIBRARY_PATH` 패치 의존성이 남아 있다.
- DOD의 action chunk shape 기대값 `(1, 50, *)`와 현재 baseline 출력 `(1, 6)`이 다르다. chunk 전체 검증이 필요하면 `select_action()` 내부 queue 전 단계 또는 policy forward 출력을 별도로 계측해야 한다.
- `num_steps=5` latency가 `num_steps=10`보다 감소하지 않았다. 측정 대상이 full forward가 아니라 action queue 경로인지 확인이 필요하다.
- 더미 이미지는 실 카메라 분포와 다르다. 실 카메라 + SO-ARM latency는 TODO-07b에서 다시 측정해야 한다.

## 7. Hardware-in-the-loop dry-run 검증

> 기록일: 2026-04-29
> 상태: dry-run PASS, live 검증 미실행

### 7.1 환경

| 항목 | 값 |
|---|---|
| Orin venv | `~/smolvla/orin/.hylion_arm` |
| follower 포트 | `/dev/ttyACM1` |
| 카메라 탐지 | `/dev/video0`, `/dev/video2` |
| 최종 카메라 매핑 | `top:2,wrist:0` |
| 테스트 보정 | wrist 카메라 raw observation 상하반전: `--flip-cameras wrist` |

초기 기본 매핑 `top:0,wrist:1`은 `OpenCVCamera(1)` 연결 실패로 중단됐다. `lerobot-find-cameras opencv` 결과 실제 카메라가 `/dev/video0`, `/dev/video2`로 확인되어 매핑을 `top:2,wrist:0`으로 변경했다.

### 7.2 dry-run 결과

실행 명령:

```bash
python ~/smolvla/orin/examples/tutorial/smolvla/hil_inference.py \
  --mode dry-run \
  --follower-port /dev/ttyACM1 \
  --cameras top:2,wrist:0 \
  --flip-cameras wrist \
  --max-steps 5 \
  --output-json /tmp/hil_dryrun.json
```

| 항목 | 결과 |
|---|---|
| exit code | 0 |
| total steps | 5 |
| JSON 저장 | `/tmp/hil_dryrun.json` |
| action 값 개수 | 30 |
| action min | `-0.9709` |
| action max | `2.2929` |
| action max_abs | `2.2929` |
| action range 판정 | PASS — 절댓값 수십 이상 튐 없음 |

첫 5 step action dump:

| step | shoulder_pan | shoulder_lift | elbow_flex | wrist_flex | wrist_roll | gripper |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | -0.1428 | -0.1171 | 0.0979 | 0.0280 | 2.2929 | -0.9709 |
| 1 | -0.2644 | -0.0435 | 0.0010 | -0.2060 | 2.2488 | -0.8093 |
| 2 | -0.4388 | -0.0276 | -0.0218 | -0.3115 | 2.2218 | -0.7314 |
| 3 | -0.6286 | 0.0212 | -0.0663 | -0.4214 | 2.1695 | -0.7413 |
| 4 | -0.6791 | 0.0374 | 0.0460 | -0.4756 | 2.1948 | -0.7667 |

### 7.3 live 결과

live 5 step 실행 명령:

```bash
python ~/smolvla/orin/examples/tutorial/smolvla/hil_inference.py \
  --mode live \
  --follower-port /dev/ttyACM1 \
  --cameras top:2,wrist:0 \
  --flip-cameras wrist \
  --n-action-steps 5 \
  --max-steps 5
```

| 항목 | 결과 |
|---|---|
| live 5 step process | PASS |
| 종료 상태 | `[done] mode=live steps=5 interrupted=False` |
| follower disconnect | PASS |
| 물리 동작 관찰 | 5 step에서는 확인 어려움 |
| 관절 한계 / 충돌 / 비정상 모터음 | PASS — 이상 동작 관찰되지 않음 |

live 50 step 실행 명령:

```bash
python ~/smolvla/orin/examples/tutorial/smolvla/hil_inference.py \
  --mode live \
  --follower-port /dev/ttyACM1 \
  --cameras top:2,wrist:0 \
  --flip-cameras wrist \
  --n-action-steps 5 \
  --max-steps 50
```

| 항목 | 결과 |
|---|---|
| live 50 step process | PASS |
| 종료 상태 | `[done] mode=live steps=50 interrupted=False` |
| follower disconnect | PASS |
| 물리 동작 관찰 | PASS — 사용자 관찰상 움직임 확인 |
| 안전 관찰 | PASS — 중단 없이 종료 |
| 태스크 수행 | FAIL/해당 없음 — 특정 물체를 집는 동작 없이 calibration 시작 중간값 근처에서 멈춘 형태 |

카메라 재고정 후 추가 테스트:

| 항목 | 결과 |
|---|---|
| 배경 | 이전 live 50 step 당시 카메라가 떨어져 있었음 |
| 추가 실행 | step을 늘려 재테스트 |
| 사용자 관찰 | 이전 live 50 step과 동일하게 경직된 상태 |
| 해석 | 카메라 고정 문제만으로 설명되지는 않음. 현재 사전학습 모델/카메라 배치/시작 자세/태스크 환경 미스매치 가능성이 큼 |
| 비고 | 정확한 실행 command/max_steps 로그는 미회수. 사용자 관찰 기준 기록 |

### 7.4 사전학습 분포 미스매치

`lerobot/smolvla_base` 사전학습 분포는 lego cube pick-and-place 계열이며, 현재 실제 카메라 배치와 시작 자세는 사전학습 환경과 다르다. `hil_inference.py`는 현재 `TASK = "Pick up the cube and place it in the box."`를 하드코딩하여 policy 입력에 넣는다. 즉 자연어 task 조건은 들어가지만, 03 단계는 사용자가 임의 자연어 명령을 입력해 특정 물체를 성공적으로 집는지 평가하는 단계가 아니다.

이번 실행에서 VLA 파이프라인은 실 카메라 프레임 + follower joint state를 받아 action을 생성하고 follower에 송신했으며, live 50 step에서 물리 움직임이 확인됐다. 다만 특정 물체를 집는 태스크 수행은 관찰되지 않았고, calibration 시작 중간값 근처에서 멈춘 형태였다. 이는 현재 단계의 잔여 리스크로 남기며, 실제 자연어 명령 기반 태스크 성공 검증은 05_leftarmVLA 데이터 수집/학습 이후 판단한다.

### 7.5 카메라 시야 메모

`svla_so100_pickplace` 단일팔 데이터셋은 `observation.images.top`와 `observation.images.wrist` 2개 카메라를 사용한다. 따라서 pick-and-place 태스크 관찰 품질 기준은 다음처럼 잡는다.

| 카메라 | 권장 시야 |
|---|---|
| overview/top | 물체, 목표 위치(박스), 작업 공간, 그리퍼 접근 경로가 가능한 한 계속 보여야 함 |
| wrist | 그리퍼와 물체의 상대 위치, 접촉/파지 순간이 보여야 함. 초기 자세에서 물체가 항상 크게 보이지 않더라도 접근 후에는 물체가 시야에 들어와야 함 |

두 카메라가 모두 항상 물체를 정중앙으로 볼 필요는 없지만, 실제 pick 성공을 기대하려면 target object가 최소 한 시야에는 안정적으로 보여야 하고, grasp 직전에는 wrist 시야에서도 물체/그리퍼 관계가 확인되는 편이 바람직하다. 특히 top이 물체를 못 보면 전역 위치 추정이 약해지고, wrist가 물체를 전혀 못 보면 파지 정렬이 불안정해질 가능성이 크다.
