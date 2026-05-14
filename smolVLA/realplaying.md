# SmolVLA 단일팔 — 재현 가능 파이프라인 로드맵

> 작성일: 2026-05-14
> 대체: 구 `arm_2week_plan.md` (→ `docs/storage/legacy/arm_2week_plan/` 아카이브). 본 문서는 fresh start 로드맵.
> 기한: 없음 — 단계별 완성 우선.

---

## 최종 목표 상태

접근 가능한 **dev 환경**(시연장이 아닌, 평소 작업 가능한 환경)에서 다음 전체 사이클을 **end-to-end 검증**한다:

```
데이터 수집 → DGX 학습 → Orin 배포 → 실시간 추론으로 SO-101 이 task 수행
```

동일 task·동일 에피소드 개수로 이 사이클의 **절차를 패키징**해 둔다. 그러면 나중에 시연장 방문 시 **데이터만 새로 수집해서 같은 절차를 마찰 없이 재실행**할 수 있다.

> **본 로드맵의 성공 = 사이클의 재현성 검증.** 시연장 환경에서의 실제 데이터 재수집·재학습은 본 로드맵 *이후*의 별도 작업이다.

---

## 핵심 전제

- **단일팔**: SO-101 single-arm. 양팔(bi-arm)은 본 로드맵 범위 밖.
- **인프라 완료 간주**: 구 마일스톤 00~08 (Orin 추론 런타임, DGX 학습·수집 환경, SO-101 teleoperate·calibration) 은 완료로 보고 재구축하지 않는다. 필요 시 해당 마일스톤에서 점검만.
- **VLA 정책**: SmolVLA (`smolvla_base` fine-tune 기반). 구체 모델 구성은 M2 결정 포인트.
- **domain shift 인지**: SmolVLA 는 teleoperation 시연 모방학습 정책이라 fine-tune 데이터의 시각적 분포(조명·카메라 앵글·배경·물체 외형)에 성능이 민감하다. 그래서 dev 환경 사이클을 먼저 검증하고, 시연장 데이터 재학습은 본 로드맵 이후로 분리한다.
- **Berkeley Humanoid Lite 펌웨어 트랙** (`docs/storage/others/다리id다운/`) 은 별개 트랙 — 본 로드맵에 포함하지 않는다.

---

## 장비 역할 분담

| 장비 | 역할 |
|---|---|
| devPC (Ubuntu) | 개발·배포 오케스트레이션, git 단일 진실 |
| DGX Spark | 데이터 수집 + 학습 (시연장 직접 이동 운영 가능) |
| Orin (Jetson) | 추론 실행·검증 |
| SO-101 | 단일 follower arm (+ teleoperation 수집 시 leader) |

---

## 진행 마일스톤

각 마일스톤은 Phase 1 에서 별도 spec 으로 분해된다 (milestone → spec → todo). 아래는 milestone 계층의 골격.

### [ ] M1 — Task 정의 + 데이터 수집

- **목표**: 수행할 task 를 확정하고, dev 환경에서 학습용 dataset 을 수집한다.
- **주요 작업**:
  - task 종류·조건 확정 (미정 — 본 마일스톤에서 결정)
  - dev 수집 환경 정의 (책상·조명·카메라·작업영역)
  - 고정 에피소드 개수 결정 (이후 시연장 재수집 시 동일하게 적용)
  - SO-101 + 카메라 셋업, calibration, 포트·인덱스 확인
  - teleoperation 으로 dataset 수집 → 저장·전송
- **결정 포인트**: task 종류 / dev 수집환경 ↔ 시연장 환경의 관계 (구 `09_demo_site_mirroring` 주제) / 에피소드 개수 / 카메라 구성·flip
- **DOD**: 합의된 task·에피소드 개수로 dataset 수집 완료, DGX 에서 학습 입력으로 사용 가능 확인.

### [ ] M2 — 학습 (DGX)

- **목표**: 수집된 dataset 으로 SmolVLA 정책을 fine-tune 한다.
- **주요 작업**:
  - 모델 구성 결정 (체크포인트, LoRA vs full fine-tune, 하이퍼파라미터)
  - DGX 에서 학습 실행, 학습 곡선·메트릭 점검
  - 학습 산출 체크포인트 검증 (smoke / 로드 테스트)
- **결정 포인트**: 모델 구성 — `smolvla_base` 기반 / LoRA 적용 여부 / 하이퍼파라미터 (구 `11_smolvla_model_decision` 주제)
- **DOD**: 학습 완료, 체크포인트가 Orin 배포 가능한 형태로 산출.

### [ ] M3 — 배포 + 추론 (Orin)

- **목표**: 학습 체크포인트를 Orin 에 배포하고 추론 파이프라인을 구동한다.
- **주요 작업**:
  - 체크포인트 DGX → Orin 전송
  - Orin 추론 파이프라인 구동 (카메라·SO-101 연결, 정책 로드)
  - 추론 latency·동작 기본 점검
- **결정 포인트**: `orin/config/*.json` (포트·카메라) git 추적 정책 (구 `10_orin_config_policy` 주제)
- **DOD**: Orin 에서 정책 로드 + 실시간 추론 루프 동작 확인.

### [ ] M4 — E2E 검증 + 사이클 패키징

- **목표**: dev 환경에서 전체 사이클을 end-to-end 검증하고, 시연장 재실행이 turnkey 가 되도록 절차를 패키징한다.
- **주요 작업**:
  - dev 환경에서 실시간 추론으로 SO-101 이 M1 의 task 를 수행하는지 확인
  - 수집→학습→배포→추론 전체 사이클 절차 문서화
  - 시연장 재실행 체크리스트 작성 (데이터만 교체하면 되도록)
- **DOD**: dev 환경 E2E 사이클 1회 성공, 재실행 절차 문서 완성.

---

## 결정 포인트 요약 (옛 결정 carry forward 금지)

아래는 구 `docs/storage/09·10·11` 이 다뤘던 주제 — fresh start 원칙상 **옛 결정 내용을 default 로 깔지 않고**, 해당 마일스톤 spec 작성 시 사용자에게 새로 질문한다. (메모리 `new-plan-decision-points` 참조. 옛 결정 내용은 git 히스토리에 보존.)

| 결정 포인트 | 배치 | 구 출처 |
|---|---|---|
| dev 수집환경 ↔ 시연장 환경 정합 방식 | M1 | 구 09_demo_site_mirroring |
| 모델 구성 (체크포인트·LoRA·하이퍼파라미터) | M2 | 구 11_smolvla_model_decision |
| `orin/config/*.json` git 추적 정책 | M3 | 구 10_orin_config_policy |

---

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-14 | 초안 작성 — fresh start 로드맵. 단일팔 / 기한 없음 / 인프라 00~08 완료 전제. 최종 목표 = dev 환경 수집→학습→추론 사이클 재현성 검증. 구 `arm_2week_plan.md` 는 legacy 아카이브. |
