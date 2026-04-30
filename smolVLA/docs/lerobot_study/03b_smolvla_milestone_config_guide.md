# SmolVLA 마일스톤별 Config 분기 가이드

> 기준: `docs/reference/lerobot/` (v0.5.1-52-g05a52238) `src/lerobot/policies/smolvla/`
> 작성일: 2026-04-27
> 목적: 본 프로젝트(`arm_2week_plan.md`) 의 마일스톤 03·05~08 각 단계에서 SmolVLA config 의 어떤 분기를 어떻게 설정할지 가이드. 일반 지식(`03_smolvla_architecture.md`) 과 본 프로젝트 마일스톤(`arm_2week_plan.md`) 을 잇는 다리 역할. (04_infra_setup 은 인프라 셋업이라 SmolVLA config 분기와 직접 관련 없음 — 별도 스펙 참조)
> 선행 읽기: `docs/lerobot_study/03_smolvla_architecture.md` — 본 문서는 그 §3 의 7 카테고리 분기를 마일스톤에 매핑한다.

---

## 0) 전제 — 본 프로젝트 마일스톤 요약

`arm_2week_plan.md` 기준 마일스톤별 학습/추론 성격:

| 마일스톤 | 성격 | 학습? | 카메라 | 자유도 |
|---|---|---|---|---|
| 03_smolvla_test_on_orin | 사전학습 모델 추론 동작 확인 | X | 더미 | - |
| 04_infra_setup | 4-노드 인프라 셋업 (DataCollector 신규) | X | - | - |
| 05_leftarmVLA | 단일팔 (left, 토르소 부착) 사이클 | O | 2대 | 6 DOF |
| 06_biarm_teleop_on_dgx | 양팔 데이터 수집 환경 | X (수집) | 3대 (손목 좌·우 + 조망) | 12 DOF |
| 07_biarm_VLA | 양팔 처음부터 학습 | O | 3대 | 12 DOF |
| 08_biarm_deploy | Orin 배포 + latency 최적화 | X (추론 튜닝) | 3대 | 12 DOF |

**05 와 07 은 독립 학습 사이클** — 05 정책은 07 의 사전 단계가 아니다 (`02_dgx_setting.md` TODO-12 참조). 07 은 양팔 데이터로 **smolvla_base 부터 다시** 파인튜닝.

**자유도는 모든 마일스톤에서 풀 6 DOF (단일팔) / 12 DOF (양팔) 유지** (`02_dgx_setting.md` TODO-11 결론).

---

## 1) 용어

본 문서에서 반복 사용하는 용어:

### Latency (추론 지연시간)
정책에 입력(이미지·state)을 넣은 시점부터 action 출력이 나오기까지의 시간. SmolVLA 에서는 1회 `select_action` 또는 `predict_action_chunk` 호출에 걸리는 시간. Orin 추론 latency 가 본 프로젝트의 핵심 제약.

### 반응성 (Responsiveness)
환경 변화 → 로봇 action 변경까지의 시간. **반응성 ≈ latency + n_action_steps × (1/제어_Hz)**. SmolVLA 는 chunk 기반 정책이라 latency 만 줄여도 반응성이 안 좋을 수 있다.

### Domain shift (도메인 시프트)
사전학습 데이터 분포와 파인튜닝 데이터 분포의 차이. 본 프로젝트의 도메인 시프트 원천:
1. SO-ARM 책상 mount → 휴머노이드 토르소 부착 (좌표계·작업 영역)
2. 단일팔 → 양팔 12 DOF
3. 카메라 1~2대 → 3대, 그리고 손목 카메라(그리퍼 클로즈업) 분포

### S1, S3 (학습 시나리오)
`03_smolvla_architecture.md` §A 의 학습 대상 시나리오 표 참조:
- **S1**: `train_expert_only=True, freeze_vision_encoder=True, train_state_proj=True` — expert + projection 만 학습 (~50M params)
- **S3**: `train_expert_only=False, freeze_vision_encoder=True, train_state_proj=True` — VLM 까지 학습 (~400M params)

### B1, B2 (가중치 출처)
`03_smolvla_architecture.md` §B 표 참조:
- **B1**: `--policy.path=lerobot/smolvla_base` — 사전학습된 expert + VLM 모두 로드 (권장)
- **B2**: `--policy.type=smolvla` — VLM 만 사전학습, expert random init

---

## 2) 마일스톤별 분기 구성

### 03_smolvla_test_on_orin

**목표**: Orin 에서 사전학습 smolvla_base 가 forward pass 되는지 검증. 학습 안 함.

| 카테고리 | 선택 | 이유 |
|---|---|---|
| A. 학습 대상 | 무관 (eval) | 학습 안 함 |
| B. 가중치 | **B1**: `--policy.path=lerobot/smolvla_base` | 사전학습 그대로 |
| C. 모델 용량 | 모두 기본값 (16 / -1 / 0.75) | 사전학습 호환 |
| D. Attention | `cross_attn` + `self_attn_every_n_layers=2` (기본) | 사전학습 호환 |
| E. Action / Chunking | 모두 기본값 (50 / 50) | 사전학습 호환 |
| F. Flow Matching | `num_steps=10` (기본), 추가로 5 도 측정 | Orin latency 기준점 |
| G. 데이터셋 적응 | 더미 입력 | 추론 동작 확인만 |

**추가 결정**:
- `compile_model=False` 유지 — 첫 동작 확인 단계에서 torch.compile 변수 추가 안 함
- 더미 이미지·state 로 1회 forward → latency / VRAM 측정

**핵심 산출물**: Orin 1회 forward latency, VRAM 점유 (이후 마일스톤의 자원 추정 기준)

---

### 05_leftarmVLA

**목표**: 휴머노이드 토르소 부착 left arm 으로 한 사이클 (수집 → 학습 → Orin 배포) 완주. 풀 6 DOF, 카메라 2대.

**도메인 시프트 정도**: 중간
- 토르소 부착 좌표계 차이 (있음)
- 단일팔 (사전학습과 일치)
- 카메라 2대 (사전학습 분포와 비슷)

| 카테고리 | 선택 | 이유 |
|---|---|---|
| A. 학습 대상 | **S1** | 첫 사이클 변수 최소화. 좌표계 차이는 vision encoder 까지 풀 필요 낮음 |
| B. 가중치 | **B1** | 사전학습 활용 필수 (데이터 수백~수천 에피소드 가정) |
| C. 모델 용량 | 기본값 | 사전학습 호환 |
| D. Attention | 기본값 | 사전학습 호환 |
| E. Action / Chunking | 기본값 (50 / 50) | 첫 사이클은 기본값. 추론 빈도 부족하면 07 배포 단계에서 튜닝 |
| F. Flow Matching | `num_steps=10` 기본 | 03 latency 측정 후 Orin 에서 5 도 실험 |
| G. 데이터셋 적응 | `empty_cameras=0`, `resize_imgs_with_padding=(512,512)` | 카메라 2대 그대로 사용 |

**S1 실패 시 fallback 순서**:

1. **데이터 양 늘리기** (가장 효과적)
2. **PEFT/LoRA** 적용 — `lm_expert.q/v_proj` + projection layer 만 학습. S1 의 더 가벼운 버전. VRAM 절약 + overfitting 회피
3. **S3 전환** (`train_expert_only=False`) — DGX VRAM 확인 후

**05 의 핵심**: **거의 건드릴 게 없음.** 모든 기본값 유지. 핵심은 데이터 품질·양 / Orin 추론 latency 검증.

**데이터셋 키 명명 — 06 과 일관되게**:
- 카메라 키: `observation.images.<camera_name>` (LeRobotDataset 표준, `lerobot_dataset.py:122-138` 예시)
- 본 프로젝트 권장: `observation.images.{wrist_left, wrist_right, overview}` — 05 는 이 중 2개만 사용
- 이유: SmolVLA 는 `config.input_features` 의 dict 삽입 순서대로 카메라를 처리 (`policies.py:148-152` `image_features` property + `modeling_smolvla.py:421-422`). **알파벳/숫자 정렬 안 함** — 따라서 숫자 prefix(`cam_0_*`) 강제는 불필요.
- 05 와 06/07 사이에서는 카메라 이름 자체를 일관되게 유지 (예: 05 의 `wrist_left` 키가 06 에서도 동일 이름·동일 부착 위치 카메라를 가리킴). 05→07 모델 호환 자체는 별도 학습이라 강제 아니지만, 학습 결과 비교 시 변수 줄임

---

### 06_biarm_teleop_on_dgx

**목표**: 양팔 + 카메라 3대 데이터 수집. **학습 안 함**, 데이터셋 빌드만.

이 단계는 SmolVLA config 분기와 직접 관련 없음. 다만 **수집되는 데이터의 키·shape 가 06 학습 분기에 영향** 을 주므로 데이터셋 단의 분기 결정이 필요.

| 결정 항목 | 옵션 | 권장 / 영향 |
|---|---|---|
| `observation.state` 키 구조 | (a) 단일 키 12 DOF `[left_6, right_6]` | **(a) 권장** — `max_state_dim=32` padding 한 번이면 됨 (`modeling_smolvla.py:158-169`) |
| | (b) 좌·우 분리 키 | 키 매핑 코드 추가 필요 |
| `action` 키 구조 | 위와 동일 | (a) 권장 |
| 카메라 키 명명 | `observation.images.{wrist_left, wrist_right, overview}` | LeRobotDataset 표준 prefix `observation.images.` 고정. 카메라 이름은 자유. SmolVLA 는 dict 삽입 순서대로 처리 (정렬 안 함) — 04 와 05/06 에서 동일한 카메라 이름 사용으로 변수 최소화 |
| 카메라 해상도 | OV5648 native vs 다운샘플 | smolvla 가 학습 시 `resize_imgs_with_padding=(512,512)` 으로 자동 리사이즈 → **수집은 native 유지** (정보 손실 회피). 단, 디스크 용량 고려 |
| FPS | 30 vs 60 | SO-ARM teleop 60Hz 면 **수집 60Hz** 권장 (제어 빈도와 일치). 학습 시 다운샘플 가능 |
| Task instruction (language) | 짧은 자연어 | `tokenizer_max_length=48` 안에 들어가야 함 (`configuration_smolvla.py:60`) |

**중요**: 카메라 키 명명을 **05 와 06 이 일관되게** 결정. 05 가 2대(`observation.images.wrist_left`, `observation.images.overview`) → 06 에서 `observation.images.wrist_right` 만 추가하는 식.

---

### 07_biarm_VLA

**목표**: 양팔 12 DOF + 카메라 3대 데이터로 **처음부터** 파인튜닝 (04 결과 사용 안 함, 양팔 데이터로 smolvla_base 부터 다시 학습).

**도메인 시프트 정도**: 큼
- 양팔 (사전학습은 단일팔 위주)
- 카메라 3대 (사전학습은 1~2대 위주)
- 손목 카메라 그리퍼 클로즈업 (SmolVLM2 분포와 다름)
- 토르소 부착 좌표계

→ **04 보다 분기 선택을 더 적극적으로**.

#### 1차 시도 (default)

| 카테고리 | 선택 |
|---|---|
| A. 학습 대상 | **S1** |
| B. 가중치 | **B1**: smolvla_base |
| C. 모델 용량 | 기본값 |
| D. Attention | 기본값 |
| E. Action / Chunking | 기본값 (50 / 50) |
| F. Flow Matching | `num_steps=10` |
| G. 데이터셋 적응 | `empty_cameras=0` (3대 모두 채움), `resize_imgs_with_padding=(512,512)` |

#### 2차 시도 (1차 실패 시)

| 카테고리 | 변경 | 이유 |
|---|---|---|
| A. 학습 대상 | **S1 → S3** (`train_expert_only=False`) | 카메라 3대·토르소 좌표계 도메인 시프트 흡수에 VLM 까지 풀 필요. learning rate 5e-5~1e-5 로 낮추기 |
| 나머지 | 동일 | 사전학습 호환 유지 |

**1차 → 2차 전환 트리거**:
- 1차 학습 50k step 후 loss plateau / 정성 평가 실패
- 손목 카메라 표현 학습 실패 정황 (그리퍼 동작 학습 안 됨)

**왜 S3 까지만? S4 (vision encoder 까지) 는 왜 안 권장?**
- vision encoder 까지 푸는 것 (S4) 은 **catastrophic forgetting 위험 가장 큼**, 데이터 매우 많이 필요
- 손목 카메라 분포 차이는 **vision encoder 보다 connector / VLM 텍스트 디코더 가 흡수** 하는 경우가 더 일반적
- → S1 → S3 까지 시도, 그래도 안 되면 **데이터 양 확대 / 더듬이 카메라** (비상 옵션) 가 다음 액션

#### 3차 시도 (2차도 실패 시)

`arm_2week_plan.md` 06 마일스톤의 비상 옵션:
- **더듬이 카메라 추가** (머리 위 추가 조망)
- 데이터 양 2~3배 확대
- 그래도 안 되면 자유도 축소 재검토 (`02_dgx_setting.md` TODO-11 Backlog #3 트리거)

#### VRAM 부족 시 (DGX 실측 의존)

권장 순서: **S1 + LoRA → S1 + 풀 → S3 + LoRA → S3 + 풀**
- LoRA target: `lm_expert.q/v_proj` + projection layer (`modeling_smolvla.py:495-504`)

#### Learning rate

`03_smolvla_architecture.md` §A 표:
- S1: 1e-4 (기본)
- S3: 5e-5 ~ 1e-5 (catastrophic forgetting 회피)

---

### 08_biarm_deploy

**목표**: 06 체크포인트를 Orin 에 반입 → 추론 동작 확인 → 데모 가능 latency 달성.

학습 단 분기 (A~D, G) 는 06 결정 그대로 고정. **추론 단 옵션만 튜닝**.

| 카테고리 | 분기 | 튜닝 폭 | 영향 |
|---|---|---|---|
| F. Flow Matching | `num_steps`: 10 → 8 → 5 | latency / 정확도 | latency 비례 감소 |
| E. Chunking | `n_action_steps`: 50 → 25 → 10 | 반응성 / 추론 부하 | 반응성 비례 향상 |
| 추론 옵션 | `use_cache=True` | 항상 True | KV cache 활용 |
| 추론 옵션 | `compile_model=True` 검토 | 첫 호출 비용 vs 정상 후 속도 | torch.compile 적용 |
| RTC | `rtc_config` 활성화 검토 | latency 흡수 | 사전학습 RTC 학습 여부 의존 |

#### 튜닝 절차 권장 순서

1. 06 학습 그대로 (`num_steps=10, n_action_steps=50`) baseline latency 측정
2. **`num_steps=5`** 시도 — 정성 평가에서 동작 품질 유지되면 채택. 안정성 우선이면 8 부터 단계적 감소
3. **`n_action_steps=10~25`** 감소 — 반응성 향상 vs 추론 빈도 ↑ 부하 트레이드오프
4. **`compile_model=True`** 시도 — Orin 에서 실측 메모리/속도 변화 비교
5. **RTC 활성화** 시도 — 효과 있으면 적용 (아래 RTC 절 참조)

**핵심**: 학습 단 (A~D 카테고리) 은 절대 건드리지 않음. 06 체크포인트가 그 분기로 학습됐기 때문.

#### RTC (Real-Time Chunking) 보충 설명

**문제 상황**: chunk 기반 정책의 약점 — 추론 latency 동안 환경이 변해도 로봇은 옛 chunk 끝낼 때까지 안 멈춤.

**RTC 동작** (`modeling_smolvla.py:860-872`, `configuration_smolvla.py:104`):
- 새 chunk 추론 시작 시점에, **이전 chunk 의 남은 부분(`prev_chunk_left_over`) 을 "이어 붙이는 noise" 로 활용**
- `inference_delay` 만큼의 latency 를 알고 있으면, 그 시간 동안 실행될 action 을 노이즈에 미리 반영 → 결과 chunk 가 **이전 chunk 와 부드럽게 연결**
- 즉 latency 를 흡수해서 끊김 없는 동작

**왜 "추가 검토 필요" 인가**:
- RTC 는 **추론 단에서만 활성화 가능** 한 옵션이지만, **사전학습/파인튜닝 시 RTC 를 학습한 모델** 이 추론 시 RTC 활성화 했을 때 더 잘 동작
- smolvla_base 가 RTC 학습됐는지, 06 파인튜닝에서 RTC 학습할지 결정 필요
- `seeed-lerobot/tests/policies/smolvla/test_smolvla_rtc.py` 가 존재하므로 SmolVLA 정식 지원 기능
- 본 프로젝트 적용 가치는 **07 까지의 latency 실측 결과** 에 의존 → 08 진입 시 결정

---

## 3) 마일스톤 간 분기 변화 한눈에

| | 03 | 04 | 05 | 06_1차 | 06_2차 | 07 |
|---|---|---|---|---|---|---|
| 학습 모드 | 추론만 | S1 | (수집) | S1 | S3 | (배포) |
| 가중치 | smolvla_base | smolvla_base | - | smolvla_base | smolvla_base | 06 체크포인트 |
| 카메라 수 | 더미 | 2 | 3 (수집 결정) | 3 | 3 | 3 |
| chunk_size / n_action_steps | 50/50 | 50/50 | - | 50/50 | 50/50 | 50/N(튜닝) |
| num_steps | 10 (5 비교) | 10 | - | 10 | 10 | 10→5 (튜닝) |
| 핵심 변수 | latency 측정 | 데이터 품질·양 | 키·해상도·FPS | 데이터 양 / S1 수렴 | VLM 풀기 / forgetting | latency·반응성 |

---

## 4) 사용 방법

본 문서는 **권장값의 시작점** 이며, 실제 마일스톤 진입 시:

1. 해당 마일스톤의 스펙 (`docs/work_flow/specs/0X_*.md`) 작성 시 본 문서의 권장값을 출발점으로 인용
2. 진행 중 발견한 사실 (DGX 실측, 데이터 분포, 1차 학습 결과) 에 따라 권장값을 마일스톤 스펙 내에서 정정
3. 정정한 결과가 일반화 가능한 지식이라면 본 문서를 업데이트, 마일스톤 특수 사항이라면 마일스톤 스펙에만 기록

**선행 조건 미해결 항목** (본 문서 권장값의 가정):
- DGX VRAM 실측 (`02_dgx_setting.md` TODO-02) — S1 / S3 / S4 선택의 자원 근거
- 05 카메라 키 명명 확정 — 06 과 일관되게 결정
- smolvla_base 의 RTC 사전학습 여부 — 07 RTC 활성화 결정의 근거

---

## 5) 변경 이력

| 날짜 | 변경 | 출처 |
|---|---|---|
| 2026-04-27 | 초안 작성 (`03_smolvla_architecture.md` §3 의 7 카테고리 + `arm_2week_plan.md` 마일스톤 매핑) | TODO-03 후속 작업 |
