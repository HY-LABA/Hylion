# leftarm 데이터 수집 시나리오 (v1 → v2)

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

단일 `BaboGaeguri/leftarm_v2` dataset 안에 instruction 으로 구분되는 2 task 를 수집한다. 한 SmolVLA 모델이 instruction 으로 task 를 분기 (학습은 M2).

| task | instruction | 대상 |
|---|---|---|
| 1 | `Pick up the blue and yellow doll and place it in the yellow plastic box` | 파랑+노랑 인형 → 노란 플라스틱 상자 |
| 2 | `Pick up the yellow can and place it in the yellow plastic box` | 노란 캔 → 노란 플라스틱 상자 |

- instruction 은 색상 속성으로 grounding — v1 의 `left/right` 모호성 사고 회피.
- 목표: task 1 = 100 ep, task 2 = 100 ep, 총 200 ep.
- 수집 도구: `dgx/finetune/leftarm_v2/run_record.py` (config → `lerobot-record`).

---

## 3) v2 수집 전략 — 차수 번갈기 + 캔 배치 변형

수집을 한 task 씩 몰아서 하지 않고 **20 episode 차수(batch) 단위로 task 1 ↔ task 2 를 번갈아** 가며, **task 2(캔) 는 차수마다 캔의 위치·배치를 바꾼다.** 두 가지 목적:

1. **task 분포 균형 + forgetting 방지** — 한 task 만 길게 수집하면 그 구간의 환경 조건(조명·배치)에 분포가 치우치고, 멀티태스크 학습 시 균형이 깨진다. 차수를 번갈면 두 task 가 비슷한 환경 시계열 위에서 고르게 쌓인다.
2. **캔 task 범용성** — 캔을 매번 같은 자리에 두면 모델이 "그 좌표로 가는 것"을 외운다. 차수마다 캔 위치·각도·배치를 바꿔 "노란 캔을 찾아 집는 것"을 학습하도록 한다.

### 차수 운영 (목표 기준 10 차수)

각 task 100 ep = 20 ep × 5 차수. 번갈아 배치하면 총 10 차수:

| 차수 | task | episodes | 누적 T1 | 누적 T2 | 캔 배치 |
|---|---|---|---|---|---|
| 1 | 1 인형 | 20 | 20 | 0 | — |
| 2 | 2 캔 | 20 | 20 | 20 | 배치 A |
| 3 | 1 인형 | 20 | 40 | 20 | — |
| 4 | 2 캔 | 20 | 40 | 40 | 배치 B |
| 5 | 1 인형 | 20 | 60 | 40 | — |
| 6 | 2 캔 | 20 | 60 | 60 | 배치 C |
| 7 | 1 인형 | 20 | 80 | 60 | — |
| 8 | 2 캔 | 20 | 80 | 80 | 배치 D |
| 9 | 1 인형 | 20 | 100 | 80 | — |
| 10 | 2 캔 | 20 | 100 | 100 | 배치 E |

> 차수 수·episode 수는 목표일 뿐 절대값 아님. `--episodes` 는 매 차수 직접 지정 (run_record.py 가 누적 관리하지 않음 — lerobot `num_episodes` 시맨틱 = 이번 세션 추가분). 인형(task 1)도 자연스러운 시작 위치 다양화를 권장하되, 변형의 핵심 강조는 캔.
>
> **캔 배치 변형 축** (차수마다 1~2개씩 바꿔 5 배치 구성): 작업영역 내 위치(중앙/좌/우/앞/뒤), 캔의 서 있는 각도, 상자와의 상대 거리. 변형값은 아래 §4 표에 차수별로 실측 기입.

### 수집 명령

```bash
ssh dgx
cd ~/smolvla/dgx/finetune/leftarm_v2
source ~/smolvla/dgx/.arm_finetune/bin/activate

# 차수 1 — task 1, fresh 생성
python run_record.py record --task 1 --episodes 20
# 차수 2 — task 2, 자동 resume
python run_record.py record --task 2 --episodes 20
# … 차수 10 까지 번갈아
```

각 차수는 `push_to_hub: true` 로 Hub 에 증분 백업된다.

---

## 4) 수집 환경 파라미터 (시연장 재현 최소 셋)

> "최소 파라미터만 기록" 결정 (2026-05-14) — dev 환경 그대로 수집하되, 재현에 필요한 핵심값만 남긴다.
> **[수집 중 실측 기입]** 표시 항목은 leftarm_v2 수집을 진행하며 사용자가 실측값으로 채운다.

### 4-1) 카메라 (녹화 파라미터는 `base_config.yaml` cameras 섹션 확정값)

| 카메라 | 해상도(회전 후) | rotation | fourcc | fps | 물리 배치 |
|---|---|---|---|---|---|
| top | 480×640 | CCW 90° (`-90`) | MJPG | 30 | **[수집 중 실측 기입]** 높이·각도·작업영역과의 거리 |
| wrist | 640×480 | 0 | MJPG | 30 | follower 손목 고정 (기구적) |

> top 은 하드웨어 640×480 캡처를 CCW 90° 회전 → 480×640 출력. 카메라 인덱스는 세션값 → `base_config.yaml` `hardware` 섹션.

### 4-2) 조명 — **[수집 중 실측 기입]**

| 항목 | 값 |
|---|---|
| 주 광원 | (천장등 / 데스크등 / 자연광 등) |
| 밝기·방향 메모 | (그림자가 작업영역에 지지 않도록 등) |

### 4-3) 작업영역 — **[수집 중 실측 기입]**

| 항목 | 값 |
|---|---|
| 작업면 | (책상 / 매트 — 색·재질) |
| 노란 플라스틱 상자 위치 | (follower 기준 상대 위치) |
| 인형 시작 위치 | (task 1 — 위치 다양화 범위) |
| 캔 배치 A~E | (§3 차수별 캔 위치·각도 — 차수 진행하며 기입) |

### 4-4) 하드웨어 (세션값 — `base_config.yaml` `hardware` 섹션)

USB enumeration 의존이라 부팅·재연결마다 변동. 매 세션 `check_port_and_camera_index.py` 로 확인 후 `base_config.yaml` 에 직접 입력. 본 문서에는 기록하지 않음 (세션값이므로).

---

## 5) 운영 메모 / 리스크

- **그리퍼 overload** — motor id=6. episode 종료 시 그리퍼를 살짝 열고 끝낸다 (leftarm_v1 overload 크래시 이력).
- **`push_to_hub` 크래시** — leftarm_v1 에서 disconnect 크래시로 push 가 skip 된 이력. 크래시 시 `dgx/scripts/push_dataset_hub.sh` 또는 수동 `LeRobotDataset(...).push_to_hub(...)` 로 복구.
- **USB enumeration 변동** — 우측팔 추가로 4 devices 환경. 차수 사이 재부팅·재연결 시 포트·카메라 인덱스 재확인 필수.
- **차수별 휴식** — 20 ep 차수 단위로 분할 수집 + 휴식. 연속 장시간 수집 시 그리퍼·모터 과열 주의.
