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
| 1 | `Pick up the blue and yellow doll and place it on the left side of the table` | 파랑+노랑 인형을 테이블 왼쪽 영역에 놓기 (spatial reference) |
| 2 | `Hand the yellow can to the person` | 노란 캔을 사람에게 건네기 (hand-over — pick-and-place 아님) |

- 목표: task 1 = 100 ep, task 2 = 100 ep, 총 200 ep.
- 수집 도구: `dgx/finetune/leftarm_v2/run_record.py` (config → `lerobot-record`).
- 진행 현황·차수 로그·다음 차수 계획: [`dgx/docs/finetune/leftarm_v2/collection_log.md`](../../dgx/docs/finetune/leftarm_v2/collection_log.md).
- task 1 의 "left side of the table" 은 spatial reference 라 v1 의 left/right 모호성 사고와 같은 함정 가능성이 있어 50 ep 시점 점검에서 grounding 확인 완료 (collection_log §50개 시점 점검).

### b) 수집 컨벤션 — 차수 단위 + 다양성 축

수집은 **차수(batch) 단위**로 진행한다 (한 차수 = 한 `python run_record.py record --task N --episodes M` 실행). vision robustness 확보를 위해 차수마다 아래 **다양성 축**을 통제·기록한다 (2026-05-15 컨벤션):

- **task interleaving** — task 1 ↔ task 2 를 차수로 번갈아. 한 task 만 몰아 수집하면 분포가 치우치고 멀티태스크 학습에서 forgetting 위험.
- **물체 orientation** (task 1·2 공통) — 인형은 얼굴(front)/뒤통수(back), 캔은 문양(front)/성분표시(back). 차수마다 한 면 선택 + 차수 종료까지 일관.
- **사람 다양성** (task 2 전용) — instruction `Hand ... to the person` 의 "the person" 외형(옷·신체)이 시연마다 다르면 모델이 "어떤 사람이든 건넨다"를 학습. 차수당 한 사람. 식별자·시각적 구분점은 collection_log.md 수집 컨벤션 §2 표.

**규칙**:
- instruction 은 동일 — orientation/person 은 instruction 에 들어가지 않는 *물리적 다양성*. 차수별 entry 에 명시해 추적.
- 차수별로 한 조합 (한 차수 = 한 orientation + task 2 는 한 person). 시연 중 일관 유지 + 로그 추적 명확.
- 최종 task 1: 앞/뒤 ~50/50. task 2: 앞/뒤 ~50/50 + 사람 분포.

### c) 진화 history — task 정의 변경

- **2026-05-14** (M1 작성 시): 옛 설계는 양 task 모두 "노란 플라스틱 상자에 놓기" pick-and-place. 수집 시작 시 **top view 카메라 화각 내 팔 가동범위 부족** 발견 → "상자를 top view 경계 밖 + 가동범위 내에 고정, wrist cam + 관절값으로 place 학습" 결정.
- **2026-05-15**: 위 결정을 더 진화시켜 **상자 자체를 폐기**하고 task 를 재정의 — task 1 은 "테이블 왼쪽" spatial reference, task 2 는 "사람에게 건네기" hand-over. instruction grounding 다양성·실 시연 적합성 모두 ↑. 어제 시도하려던 "상자 보이지 않는 학습" 우회는 task 재정의로 자연히 해소.

---

## 5) 운영 메모 / 리스크

- **그리퍼 overload** — motor id=6. episode 종료 시 그리퍼를 살짝 열고 끝낸다 (leftarm_v1 overload 크래시 이력).
- **Feetech 모터 통신 크래시** — 2026-05-15 task 2 5차 ep 60 직후 `ConnectionError: TxRxResult — no status packet` 발생. 캘리브로 못 풀고 **전원 사이클로만 reset 가능** (모터 error register set). 차수 사이 짧은 휴식 권장 (collection_log 5차 entry).
- **`push_to_hub` 크래시** — leftarm_v1 에서 disconnect 크래시로 push 가 skip 된 이력. 크래시 시 `dgx/scripts/push_dataset_hub.sh` 또는 수동 `LeRobotDataset(...).push_to_hub(...)` 로 복구.
- **USB enumeration 변동** — 우측팔 추가로 4 devices 환경. 차수 사이 재부팅·재연결 시 포트·카메라 인덱스 재확인 필수.
- **FPS sub-30Hz 워닝** — 1~7차 전반에서 record loop steady-state 21~30Hz 경고. 단 dataset timestamp 전수 분석 결과 33.33ms 균일 (std 0.00, gap 0) — lerobot 이 `frame_index/fps` 로 이상값 저장. **dataset 무결, 학습 영향 경미** — polish 항목으로 격하 (collection_log 발견된 이슈 §). 진짜 fidelity 원하면 입력단 (`display_data`, USB topology, `Corrupt JPEG`) 점검.
- **차수별 휴식** — 20 ep 차수 단위로 분할 수집 + 휴식. 연속 장시간 수집 시 그리퍼·모터 과열 주의.
