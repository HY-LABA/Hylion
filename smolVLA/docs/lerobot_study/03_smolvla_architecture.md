# SmolVLA 아키텍처 및 Config 분기점

> 기준: `docs/reference/lerobot/` (v0.5.1-52-g05a52238) `src/lerobot/policies/smolvla/`
> 작성일: 2026-04-27
> 목적: SmolVLA 학습 대상·구조·하이퍼파라미터 분기를 코드 레벨에서 정리. 파인튜닝 시 어느 플래그를 어떻게 설정할지 판단 근거.

---

## 1) 모델 컴포넌트 한눈에

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│   image(s) ──► vision_model ──► connector ──┐                │
│                                              │               │
│   lang_tokens ──► text_model.embed ──────────┤               │
│                                              │               │
│   state ──► state_proj ──────────────────────┤               │
│                                              ▼               │
│                                       ┌──────────────┐       │
│                                       │ VLM (text    │       │
│                                       │ decoder, 16  │       │
│                                       │ layers)      │       │
│                                       └─────┬────────┘       │
│                                             │ K, V cache     │
│                                             │ (cross-attn)   │
│                                             ▼                │
│   noise ──► action_in_proj ──┐                               │
│                              │     ┌──────────────┐          │
│   timestep ──► sin/cos pe ───┴───► │ Action Expert│          │
│                                    │ (16 layers,  │          │
│                                    │ 0.75× hidden)│          │
│                                    └─────┬────────┘          │
│                                          ▼                   │
│                                   action_out_proj            │
│                                          ▼                   │
│                                     v_t (flow                │
│                                     matching velocity)       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

핵심 파일:
- `configuration_smolvla.py` — Config dataclass (학습 시 모든 분기 결정)
- `modeling_smolvla.py` — `SmolVLAPolicy` (LeRobot 인터페이스), `VLAFlowMatching` (전체 forward / loss / sample)
- `smolvlm_with_expert.py` — `SmolVLMWithExpertModel` (VLM + Expert 합성, attention 흐름)
- `processor_smolvla.py` — 입력 전처리 (이미지·언어 토크나이즈)

## 2) 학습 가능 컴포넌트 7가지

`modeling_smolvla.py:583-594` + `smolvlm_with_expert.py:150-180` 종합:

| # | 컴포넌트 | 위치 | 역할 |
|---|---|---|---|
| 1 | `vlm.vision_model` | SmolVLM2 SigLIP | 이미지 인코딩 |
| 2 | `vlm.text_model` | SmolVLM2 text decoder (16 layers) | 이미지·언어·state 통합 representation |
| 3 | `vlm.connector` | SmolVLM2 modality projector | vision → text hidden 정합 |
| 4 | `lm_expert` | 별도 transformer (16 layers, hidden×0.75) | action 디코딩 본체 |
| 5 | `lm_expert.layers[i].self_attn.{k,v}_proj` | cross-attn re-projector | VLM hidden → expert hidden 변환 |
| 6 | `state_proj` | `nn.Linear(32 → VLM hidden)` | state vector → VLM 입력 토큰 |
| 7 | action MLP 4종 (`action_in_proj`, `action_out_proj`, `action_time_mlp_in`, `action_time_mlp_out`) | expert 입출력 + timestep 융합 | noise·timestep → expert 입력 / expert 출력 → action |

`5, 6, 7` 이 사용자 표현의 "**adapter**"에 해당하는 부분이며, 명시적 Adapter 모듈명을 가지지는 않는다.

## 3) Config 분기점 — 학습에 영향을 주는 7개 카테고리

### A. 학습 대상 (가장 중요)

| 플래그 | 기본값 | 효과 |
|---|---|---|
| `freeze_vision_encoder` | `True` | vision_model gradient 차단 |
| `train_expert_only` | `True` | VLM 전체 동결, expert 만 학습 |
| `train_state_proj` | `True` | state_proj 학습 여부 별도 제어 |

**학습 대상 매트릭스:**

| 시나리오 | freeze_vision | train_expert_only | train_state_proj | 학습되는 컴포넌트 (위 표 #) | 동결 |
|---|---|---|---|---|---|
| **S1: 표준 파인튜닝 (기본값)** | True | True | True | 4, 5, 6, 7 | 1, 2, 3 |
| S2: state_proj까지 동결 | True | True | False | 4, 5, 7 | 1, 2, 3, 6 |
| **S3: VLM도 푸는 풀 파인튜닝** | True | False | True | 2, 3, 4, 5, 6, 7 (VLM 마지막 1~2 레이어 + lm_head 제외) | 1, 마지막 레이어 |
| S4: vision까지 푸는 풀 파인튜닝 | False | False | True | 1, 2, 3, 4, 5, 6, 7 (마지막 레이어 제외) | VLM 마지막 1~2 레이어 |

> **S3 / S4 에서 VLM 마지막 1~2 레이어를 동결하는 이유** (`smolvlm_with_expert.py:160-176`):
> 분산학습 시 unused params 이슈 회피. VLM 의 마지막 레이어 출력은 expert 의 K/V cache 채우기에만 쓰이고 본인의 out_proj 결과는 사용되지 않으므로, DDP 가 unused gradient 에러를 내지 않게 명시적으로 동결한다.

**파인튜닝 과정 차이:**

| 항목 | S1 | S2 | S3 | S4 |
|---|---|---|---|---|
| 학습 파라미터 수 (대략) | ~50M | ~50M | ~400M | ~600M+ |
| VRAM (batch=64, fp16 추정) | ~12GB | ~12GB | ~30GB | ~45GB+ |
| 권장 데이터셋 크기 | ~1k 에피소드 | ~1k | ~10k | ~10k+ |
| 도메인 전이 능력 | 낮음 (VLM 동결) | 낮음 | 높음 | 가장 높음 |
| 사전학습 지식 보존 | 강함 | 강함 | 약함 (catastrophic forgetting 위험) | 가장 약함 |
| 권장 LR | 1e-4 (기본) | 1e-4 | 5e-5 ~ 1e-5 | 5e-6 ~ 1e-5 |

**PEFT (LoRA) 옵션** — `modeling_smolvla.py:495-504`:

```python
target_modules = "lm_expert.*.q_proj|v_proj | state_proj | action_in_proj | action_out_proj | action_time_mlp_in/out"
```

→ `train_expert_only=True` 와 같이 사용하는 의도된 설계. S1 의 더 가벼운 버전으로 VRAM 부족 시 1순위 옵션.

### B. 백본 가중치 출처

| 시나리오 | `load_vlm_weights` | CLI `--policy.path` | 결과 |
|---|---|---|---|
| **B1: smolvla_base 파인튜닝** | (자동 True) | `lerobot/smolvla_base` | 사전학습된 expert + VLM 모두 로드 — **권장** |
| B2: VLM만 사전학습 + expert random | True | (지정 안 함, `--policy.type=smolvla`) | SmolVLM2 가중치만 로드 |
| B3: 처음부터 학습 | False | (지정 안 함) | 모두 random init — 비추 (코드도 경고 출력) |

`vlm_model_name` 기본값: `"HuggingFaceTB/SmolVLM2-500M-Video-Instruct"`

**파인튜닝 과정 차이:**
- B1: 200k step 권장, loss 빠르게 감소 (수백 step 내 의미 있는 수치)
- B2: 200k step + 충분한 데이터, 초기 수만 step 거의 학습 안 되는 구간 있음
- B3: 본 프로젝트에서 사용 안 함

### C. 모델 용량

| 플래그 | 기본값 | 의미 |
|---|---|---|
| `num_vlm_layers` | 16 | SmolVLM2 첫 N개 레이어만 사용 (layer skipping) |
| `num_expert_layers` | -1 (=VLM과 동일) | expert 레이어 수 |
| `expert_width_multiplier` | 0.75 | expert hidden = VLM hidden × 0.75 |

**Orin 배포 관점:**
- `num_vlm_layers=16` 은 이미 절반 layer skipping (SmolVLM2 원본은 더 깊음)
- 그러나 **사전학습 가중치(smolvla_base)가 16 기준이므로 줄이면 호환 깨짐**
- **C 카테고리는 사전학습 사용 시 건드리지 말 것**. 처음부터 학습할 때만 의미 있음.

### D. Attention 모드

| `attention_mode` | `self_attn_every_n_layers` | 동작 |
|---|---|---|
| `"self_attn"` | (무시) | 모든 레이어 self-attention. expert 입력에 prefix 까지 함께 attend |
| **`"cross_attn"` (기본)** | `2` | 짝수 레이어 self-attn, 홀수 cross-attn (expert 가 VLM K/V cache 를 attend) |
| `"cross_attn"` | `-1` | 모든 레이어 cross-attn (KV cache 가장 효율적) |

**파인튜닝 과정 차이:**
- cross_attn 모드: 추론 시 VLM 한 번만 forward (KV cache 채움) → expert 만 num_steps 반복. **속도 매우 빠름** (`modeling_smolvla.py:836-843`)
- self_attn 모드: 매 denoise step 마다 prefix 까지 같이 forward → 느림
- **smolvla_base 가 cross_attn 모드로 학습됨** → 변경 비추천

### E. Action 차원 / Chunking

| 플래그 | 기본값 | SO-ARM 6 DOF 단일팔 | SO-ARM 12 DOF 양팔 |
|---|---|---|---|
| `max_state_dim` | 32 | 6 → 32 zero-padding | 12 → 32 padding |
| `max_action_dim` | 32 | 동일 | 동일 |
| `chunk_size` | 50 | 미래 50 step 예측 | 동일 |
| `n_action_steps` | 50 | 50개 그대로 환경에 전달 | 동일 |

**중요:**
1. `max_*_dim=32` 는 padding 메커니즘 (`modeling_smolvla.py:158-169`). SO-ARM 6 DOF 든 12 DOF 든 동일 모델로 처리 가능 — **양팔 가능 여부에 대한 코드 차원 답은 "지원됨"**. 단, 사전학습이 단일팔 위주라 즉시 잘 맞을지는 별개.
2. `chunk_size` 변경 시 사전학습 가중치 호환성에 영향 (학습 시 attention mask 길이 분포 변화).

**`n_action_steps` 트레이드오프:**
- `50` (기본): 50 step open-loop 실행 후 다음 추론 → 추론 빈도 낮음 (60Hz / 50 = 1.2Hz)
- `10`: 10 step 실행 후 재추론 → 더 반응적, 추론 빈도↑, 자원 소모↑

### F. Flow Matching 추론

`modeling_smolvla.py:844-876` 의 denoising loop.

| 플래그 | 기본값 | 의미 |
|---|---|---|
| `num_steps` | 10 | denoising step 수 |
| `min_period`, `max_period` | 4e-3, 4.0 | timestep sinusoidal embedding 주기 |

**Orin 배포:** `num_steps=5` 로 줄이면 추론 latency 절반. flow matching 은 학습/추론 num_steps 일치 강제 아님. 일반적으로 4~10 사이 실험.

### G. 데이터셋 적응

| 플래그 | 기본값 | 의미 | SO-ARM |
|---|---|---|---|
| `adapt_to_pi_aloha` | False | Aloha ↔ Pi 좌표계 변환 | False 유지 (SO-ARM은 Aloha 아님) |
| `empty_cameras` | 0 | 누락 카메라 자리에 zero 이미지 | 사전학습이 N개 가정인데 우리는 2개일 때 padding |
| `resize_imgs_with_padding` | (512, 512) | 이미지 리사이즈 + 패딩 | OV5648 입력에 맞게 검토 |
| `tokenizer_max_length` | 48 | 언어 토큰 최대 길이 | task instruction 길이 따라 |
| `add_image_special_tokens` | False | 이미지 주변 special token | smolvla_base 가 False 학습이므로 유지 |
| `prefix_length` | -1 | prefix 패딩 길이 (-1 = 패딩 안 함) | torch.compile 사용 시 고정 필요 |

## 4) SO-ARM 단일팔 첫 파인튜닝 권장 조합

`modeling_smolvla.py:30-36` 공식 예시 + 본 프로젝트 상황:

```bash
lerobot-train \
  --policy.path=lerobot/smolvla_base \      # B1 (사전학습 활용)
  --dataset.repo_id=<USER>/so_arm_task1 \
  --batch_size=64 \                          # DGX VRAM 따라 조정
  --steps=200000
# 나머지 모두 기본값 (S1, cross_attn, num_vlm_layers=16, chunk_size=50)
```

**원칙: 분기 없이 모두 기본값.** smolvla_base 사전학습 시점의 하이퍼파라미터를 그대로 따라야 가중치 호환 100% 유지.

**튜닝 순서 (수렴 안 좋을 때):**
1. 데이터 양 늘리기 (가장 효과적)
2. `train_expert_only=False` 로 S3 전환 (VRAM 충분하면)
3. PEFT/LoRA 적용 (VRAM 부족하면)
4. `n_action_steps` 10~30 으로 줄여 반응성 향상

## 5) 학습 흐름 요약 (forward / loss)

`modeling_smolvla.py:774-810` `VLAFlowMatching.forward`:

1. `actions` 에 가우시안 noise 가산 → `x_t = t·noise + (1-t)·actions` (flow matching path)
2. target velocity `u_t = noise - actions`
3. `embed_prefix(images, lang, state)` → VLM 입력 토큰 시퀀스
4. `embed_suffix(x_t, t)` → expert 입력 토큰 시퀀스 (action MLP + sinusoidal time pe)
5. `vlm_with_expert.forward(prefix, suffix)` → expert 출력 `suffix_out`
6. `v_t = action_out_proj(suffix_out)` (예측 velocity)
7. **loss = MSE(u_t, v_t)** (per-element, padding 영역 마스킹)

추론 (`sample_actions`, `modeling_smolvla.py:812-881`):
1. prefix 한 번 forward → KV cache 채움
2. `x_t = noise` 에서 시작
3. `num_steps` (=10) 동안 `x_t = x_t + dt · v_t(x_t, t)` Euler 적분
4. 최종 `x_t` 가 action chunk

## 6) 다음 학습 항목으로 이어지는 포인트

- **데이터셋 구조 (TODO-04)**: `embed_prefix` 가 받는 키(`OBS_LANGUAGE_TOKENS`, `OBS_LANGUAGE_ATTENTION_MASK`, `OBS_STATE`, `image_features`) 와 LeRobotDataset 키 매핑 확인 필요
- **HF 모델 선택 (TODO-05)**: `vlm_model_name` 기본값 `SmolVLM2-500M-Video-Instruct` 가 적합한지, 또는 더 작은 변종(135M)이 Orin 추론에 유리한지 비교
- **파인튜닝 가능성 (TODO-06)**: 본 문서의 S1~S4 시나리오 별 DGX VRAM 실측 + 1 step 소요 시간 확인
