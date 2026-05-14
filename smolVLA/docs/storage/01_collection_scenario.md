# leftarm 데이터 수집 시나리오

> 작성일: 2026-05-14
> 출처: `docs/work_flow/specs/01_leftarm_v2_collection` spec — TODO-02 (수집 환경 최소 파라미터 기록)
> 목적: leftarm 데이터셋 수집의 task 설계·수집 전략·환경 파라미터를 한 곳에 정리. 시연장/재수집 시 재현용 최소 셋.
> 관련: `realplaying.md` M1, `dgx/finetune/leftarm_v1/`·`leftarm_v2/`

---

## 0) 개요 — v1 에서 v2 로

| | leftarm_v1 | leftarm_v2 |
|---|---|---|
| 성격 | 개념 증명 (수집→학습→추론 사이클 검증) | 실 성능 + 범용성 확보 |
| task 수 | 1 | 2 (멀티태스크) |
| 수집량 | 40 ep (목표 100 중 40 후 동결) | task 당 100, 총 200 (목표) |
| 상태 | **frozen** — 개념적 체크포인트로 보존 | 본 era 작업 대상 |

v1 으로 "단일 task 40 ep → SmolVLA fine-tune → Orin 추론" 한 사이클이 돈다는 것을 확인했다. v2 는 같은 사이클을 **충분한 데이터량 + 멀티태스크 + 수집 다양성**으로 다시 돌려, 재현성뿐 아니라 *실제로 쓸 만한 성능*을 목표로 한다.

---

## 1) leftarm_v1 — 개념적 체크포인트 (frozen)

- **task**: `"Pick up the doll and reach forward"`
- **수집**: 40 episodes (목표 100 중 40 수집 후 동결). HF Hub `BaboGaeguri/leftarm_v1`.
- **학습**: `lerobot/smolvla_base` + LoRA (`r=16`, `all-linear`), batch 16. run `leftarm_v1_explore_2026-05-11_17-04-20` — 의도 5000 step 중 **500 step 에서 조기 중단**, adapter 46MB. 본격 재학습은 미진행.
- **결과**: Orin 추론까지 사이클이 도는 것은 확인. 단 데이터량·학습 step 부족으로 성능 자체는 미검증.
- **교훈 (v2 에 반영)**:
  - 초기 instruction 에 `left/right` 표현을 썼다가 **카메라 영상만으로 좌/우를 구분할 수 없어** dataset 을 재시작한 이력 (spec `status.md` §3 인시던트). → v2 instruction 은 **카메라로 보이는 속성(색상)으로 grounding**.
  - 40 ep / 500 step 은 성능 평가에 부족. → v2 는 task 당 100 ep 목표.

> v1 의 config 는 `dgx/finetune/leftarm_v1/config/` 에 frozen 기록으로 보존 (스크립트 없음, 값만).

---

## 2) leftarm_v2 — 2 task 멀티태스크

### a) task 설계 — instruction + 수집 목표

단일 `BaboGaeguri/leftarm_v2` dataset 안에 instruction 으로 구분되는 2 task 를 수집한다. 한 SmolVLA 모델이 instruction 으로 task 를 분기 (학습은 M2).

| task | instruction | 대상 |
|---|---|---|
| 1 | `Pick up the blue and yellow doll and place it in the yellow plastic box` | 파랑+노랑 인형 → 노란 플라스틱 상자 |
| 2 | `Pick up the yellow can and place it in the yellow plastic box` | 노란 캔 → 노란 플라스틱 상자 |

- instruction 은 색상 속성으로 grounding — v1 의 `left/right` 모호성 사고 회피.
- 목표: task 1 = 100 ep, task 2 = 100 ep, 총 200 ep.
- 수집 도구: `dgx/finetune/leftarm_v2/run_record.py` (config → `lerobot-record`).

### b) v2 수집 전략 — 차수 번갈기 + 캔 배치 변형

수집을 한 task 씩 몰아서 하지 않고 **20 episode 차수(batch) 단위로 task 1 ↔ task 2 를 번갈아** 가며, **task 2(캔) 는 차수마다 캔의 위치·배치를 바꾼다.** 두 가지 목적:

1. **task 분포 균형 + forgetting 방지** — 한 task 만 길게 수집하면 그 구간의 환경 조건(조명·배치)에 분포가 치우치고, 멀티태스크 학습 시 균형이 깨진다. 차수를 번갈면 두 task 가 비슷한 환경 시계열 위에서 고르게 쌓인다.
2. **캔 task 범용성** — 캔을 매번 같은 자리에 두면 모델이 "그 좌표로 가는 것"을 외운다. 차수마다 캔 위치·각도·배치를 바꿔 "노란 캔을 찾아 집는 것"을 학습하도록 한다.

### c) 물리 배치 — top view 가동범위 제약 대응

수집 시작 시 **top view 카메라 화각 내에서 팔 가동범위가 부족**한 문제 발견 (2026-05-14). pick-and-place task 자체는 유지하면서 물리 제약을 푸는 방향으로 결정:

- **상자**: 팔 가동범위 내 + **top view 경계 밖**에 **고정** 배치. top view 에는 잡히지 않고, place 동작 시 **wrist camera + 관절값(proprioception)** 으로 상자 위치를 학습한다. 시각 grounding 이 없으므로 상자 위치 다양화는 하지 않음 — 캔·인형(집는 대상)만 변형한다.
- **카메라**: top view 는 "물건을 *집는* 작업영역"이 최대한 잘 담기게 위치·화각을 병행 조정 (객체가 작아져 인식이 떨어지지 않는 선에서).
- **함의**: instruction 포함 task 정의는 그대로. 다만 상자가 시각에 안 보이고 관절값 기반으로 place 하므로, **수집 내내 상자 위치를 바꾸지 않는 것**이 핵심 — 중간에 옮기면 학습이 깨진다.

---

## 5) 운영 메모 / 리스크

- **그리퍼 overload** — motor id=6. episode 종료 시 그리퍼를 살짝 열고 끝낸다 (leftarm_v1 overload 크래시 이력).
- **`push_to_hub` 크래시** — leftarm_v1 에서 disconnect 크래시로 push 가 skip 된 이력. 크래시 시 `dgx/scripts/push_dataset_hub.sh` 또는 수동 `LeRobotDataset(...).push_to_hub(...)` 로 복구.
- **USB enumeration 변동** — 우측팔 추가로 4 devices 환경. 차수 사이 재부팅·재연결 시 포트·카메라 인덱스 재확인 필수.
- **차수별 휴식** — 20 ep 차수 단위로 분할 수집 + 휴식. 연속 장시간 수집 시 그리퍼·모터 과열 주의.
