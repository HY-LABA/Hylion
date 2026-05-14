# SmolVLA 단일팔 — 수집·학습·추론 사이클 로드맵 (leftarm_v2)

> 작성일: 2026-05-14
> 대체: 구 `arm_2week_plan.md` (→ `docs/storage/legacy/arm_2week_plan/` 아카이브). 본 문서는 fresh start 로드맵.
> 기한: 없음 — 단계별 완성 우선.

---

## 최종 목표 상태

접근 가능한 **dev 환경**(시연장이 아닌, 평소 작업 가능한 환경)에서 다음 전체 사이클을 돌려, **학습된 SmolVLA 정책이 실시간 추론으로 task 를 실제로 잘 수행**하게 만든다:

```
데이터 수집 → DGX 학습 → Orin 배포 → 실시간 추론으로 SO-101 이 task 수행
```

- **성공 기준 = 성능**: 사이클이 "돌아가는" 것이 아니라, 산출된 모델이 task 를 실제로 수행해 내는 것이 성공이다.
- **재현성**: 동일 task·동일 에피소드 개수·동일 절차로 사이클을 패키징해 둔다. 나중에 시연장 방문 시 **데이터만 새로 수집해 같은 절차를 마찰 없이 재실행** → 시연장에서도 좋은 성능을 재현하는 것이 목적.

---

## 핵심 전제

- **단일팔**: SO-101 좌측 single-arm. 양팔(bi-arm)은 본 로드맵 범위 밖. (우측팔 gesture 트랙은 별개 — 아래 참조)
- **데이터셋 계보**:
  - `leftarm_v1` — 구 task `"Pick up the doll and reach forward"` (40 episodes). **동결** — 개념적 체크포인트로 보존, 본 로드맵에서 끌어오지 않음.
  - `leftarm_v2` — **본 로드맵의 작업 대상**. 신규 2 task 멀티태스크 dataset (M1 에서 수집).
- **인프라 완료 간주**: 구 마일스톤 00~08 (Orin 추론 런타임, DGX 학습·수집 환경, SO-101 좌측 calibration) 은 완료로 보고 재구축하지 않는다. 필요 시 해당 마일스톤에서 재검증만.
- **VLA 정책**: SmolVLA (`smolvla_base` fine-tune 기반), 1 모델 / 다중 task (instruction 으로 구분). 구체 모델 구성은 M2 결정 포인트.
- **domain shift 인지**: SmolVLA 는 teleoperation 시연 모방학습 정책이라 fine-tune 데이터의 시각적 분포(조명·카메라 앵글·배경·물체 외형)에 성능이 민감하다. 그래서 dev 환경에서 좋은 성능을 먼저 확보하고, 시연장 데이터 재수집·재학습은 본 로드맵 이후로 분리한다.
- **별개 트랙 (로드맵 제외)**: 우측팔 gesture 시스템 (트리거 기반 replay), Berkeley Humanoid Lite 펌웨어 트랙 (`docs/storage/others/다리id다운/`).

---

## 장비 역할 분담

| 장비 | 역할 |
|---|---|
| devPC (Ubuntu) | 개발·배포 오케스트레이션, git 단일 진실 |
| DGX Spark | 데이터 수집 + 학습 (시연장 직접 이동 운영 가능) |
| Orin (Jetson) | 추론 실행·검증 |
| SO-101 좌측 | follower + leader (teleoperation 수집 / 추론 실행) |

---

## 진행 마일스톤

각 마일스톤은 Phase 1 에서 별도 spec 으로 분해된다 (milestone → spec → todo). M1~M4 = spec `01`~`04`. 아래는 milestone 계층의 골격.

### [ ] M1 — leftarm_v2 데이터 수집  (spec `01`)

- **목표**: leftarm_v2 학습용 dataset (2 task, 총 200 episodes) 을 dev 환경에서 수집·검증한다.
- **task (확정 2026-05-14)**: leftarm_v2 = 2 task 멀티태스크
  - ① 인형(doll) 을 집어 상자에 넣기
  - ② 캔(can) 을 집어 상자에 넣기
  - 한 SmolVLA 모델이 instruction 으로 두 task 를 구분해 수행 (M2).
- **에피소드 (확정)**: task 당 100, 총 200 (fresh 수집 — leftarm_v1 끌어오지 않음).
- **주요 작업**:
  - leftarm_v2 dataset 설계 (task instruction 문자열 2종, dataset 구조, HF repo 명명, 에피소드 배분 100/100)
  - 수집 환경 최소 파라미터 기록 (카메라 위치·조명·작업영역 — 시연장 재현용 최소 셋)
  - 좌측 SO-101 + 카메라 calibration·포트·인덱스 재검증
  - teleoperation 으로 200 episodes 수집 → HF Hub push
  - dataset 검증 (200 ep, task 분포 100/100, frame shape·dtype)
- **결정 포인트 (M1)**: dev 수집환경 ↔ 시연장 정합 → **"최소 파라미터만 기록" 으로 결정 (2026-05-14)**. 카메라·조명·작업영역 핵심값만 기록하고 dev 환경 그대로 수집.
- **DOD**: leftarm_v2 200 episodes (2 task × 100) 수집 완료 + HF Hub push + 검증 통과 → DGX 학습 입력으로 사용 가능.

### [ ] M2 — 학습 (DGX)  (spec `02`)

- **목표**: leftarm_v2 dataset 으로 SmolVLA 멀티태스크 정책을 fine-tune 한다 (1 모델 / 2 task).
- **주요 작업**:
  - 모델 구성 결정 (체크포인트, LoRA vs full fine-tune, 하이퍼파라미터, step 수)
  - DGX 에서 학습 실행, 학습 곡선·메트릭 점검
  - 학습 산출 체크포인트 검증 (smoke / 로드 테스트)
- **결정 포인트 (M2)**: 모델 구성 — `smolvla_base` 기반 / LoRA 적용 여부·rank / 하이퍼파라미터 (구 `11_smolvla_model_decision` 주제).
- **DOD**: 학습 완료, 체크포인트가 Orin 배포 가능한 형태로 산출, 두 task 모두에 대해 의미있는 수렴.

### [ ] M3 — 배포 + 추론 (Orin)  (spec `03`)

- **목표**: 학습 체크포인트를 Orin 에 배포하고 추론 파이프라인을 구동한다.
- **주요 작업**:
  - 체크포인트 DGX → Orin 전송
  - Orin 추론 파이프라인 구동 (카메라·SO-101 연결, 정책 로드 — LoRA adapter 케이스 시 로딩 검증)
  - 추론 latency·동작 기본 점검
- **결정 포인트 (M3)**: `orin/config/*.json` (포트·카메라) git 추적 정책 (구 `10_orin_config_policy` 주제).
- **DOD**: Orin 에서 정책 로드 + 실시간 추론 루프 동작 확인.

### [ ] M4 — E2E 검증 + 사이클 패키징  (spec `04`)

- **목표**: dev 환경에서 전체 사이클을 검증해 **모델이 두 task 를 실제로 수행**함을 확인하고, 시연장 재실행이 turnkey 가 되도록 절차를 패키징한다.
- **주요 작업**:
  - dev 환경에서 실시간 추론으로 SO-101 이 leftarm_v2 의 두 task 를 수행하는지 확인 (성공률 측정)
  - 수집→학습→배포→추론 전체 사이클 절차 문서화
  - 시연장 재실행 체크리스트 작성 (데이터만 교체하면 되도록)
- **DOD**: dev 환경 E2E 사이클 성공 (두 task 수행 확인), 재실행 절차 문서 완성.

---

## 결정 포인트 요약 (옛 결정 carry forward 금지)

아래는 구 `docs/storage/09·10·11` 이 다뤘던 주제 — fresh start 원칙상 **옛 결정 내용을 default 로 깔지 않고**, 해당 마일스톤 spec 작성 시 사용자에게 새로 질문한다. (메모리 `new-plan-decision-points` 참조. 옛 결정 내용은 git 히스토리에 보존.)

| 결정 포인트 | 배치 | 구 출처 | 상태 |
|---|---|---|---|
| dev 수집환경 ↔ 시연장 환경 정합 방식 | M1 | 구 09_demo_site_mirroring | ✅ "최소 파라미터만 기록" 으로 결정 (2026-05-14) |
| 모델 구성 (체크포인트·LoRA·하이퍼파라미터) | M2 | 구 11_smolvla_model_decision | 미결 — M2 spec 작성 시 질문 |
| `orin/config/*.json` git 추적 정책 | M3 | 구 10_orin_config_policy | 미결 — M3 spec 작성 시 질문 |

---

## 참고 — DGX 측 운영 문서

DGX 머신 `~/smolvla/dgx/docs/` 에 수집·학습 운영 상세 문서가 존재 (`status.md`, `data_collection.md`, `training.md`, `backlog.md` 등). 본 로드맵·spec 은 **milestone·todo 계층**, DGX docs 는 **수집·학습 운영 상세** — 역할이 다르다. devPC repo 와 DGX docs 사이 동기화 정책은 추후 정리 대상.

---

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-14 | 초안 작성 — fresh start 로드맵. 단일팔 / 기한 없음 / 인프라 00~08 완료 전제. |
| 2026-05-14 | 정정 — 최종 목표를 "재현성 검증" → **"실제 성능 확보 (+ 재현성)"** 로 수정. M1 을 현실 반영: task 확정 (leftarm_v2 = 2 task: 인형→상자, 캔→상자), 에피소드 100/task = 200, leftarm_v1(40ep) 은 동결 별개 체크포인트. M2 멀티태스크 1 모델 명시. M1 결정 포인트(환경 정합) "최소 파라미터만 기록" 으로 해소. DGX 운영 문서 참조 섹션 추가. |
