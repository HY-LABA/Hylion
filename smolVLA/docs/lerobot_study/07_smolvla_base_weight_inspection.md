# `lerobot/smolvla_base` 가중치 검증

> 기준: HuggingFace `lerobot/smolvla_base` (snapshot `c83c316`)
> 작성일: 2026-04-29
> 목적: safetensors 키 dump + config.json 분석 → expert 가중치 포함 여부 확인 + 학습 시나리오 추정
> 선행 읽기: `03_smolvla_architecture.md`, `05_hf_model_selection.md`

---

## 1) 리포지토리 파일 목록

```
lerobot/smolvla_base (HuggingFace Hub)
├── config.json                                             ← 학습 config 전체
├── model.safetensors                                       ← 가중치 (단일 파일, ~3.6GB)
├── policy_preprocessor.json                                ← 입력 전처리 파이프라인
├── policy_preprocessor_step_5_normalizer_processor.safetensors  ← STATE / ACTION 정규화 통계
├── policy_postprocessor.json
└── policy_postprocessor_step_0_unnormalizer_processor.safetensors
```

---

## 2) config.json 분석

### 2-1) 핵심 학습 플래그

| 플래그 | 값 | 의미 |
|---|---|---|
| `freeze_vision_encoder` | `true` | vision_model gradient 차단 |
| `train_expert_only` | `true` | VLM 전체 동결, expert만 학습 |
| `train_state_proj` | `true` | state_proj도 학습 |
| `load_vlm_weights` | `true` | SmolVLM2 사전학습 가중치 로드 |
| `attention_mode` | `"cross_attn"` | expert가 VLM K/V cache를 attend |
| `self_attn_every_n_layers` | `2` | 짝수 레이어(0,2,4…) self-attn / 홀수 cross-attn |

### 2-2) 모델 구조 플래그

| 플래그 | 값 | 비고 |
|---|---|---|
| `vlm_model_name` | `"HuggingFaceTB/SmolVLM2-500M-Video-Instruct"` | VLM 백본 |
| `num_vlm_layers` | `16` | VLM layer skipping 결과 (원본보다 적음) |
| `num_expert_layers` | `0` | 0 = VLM과 동일 (16 layers) |
| `expert_width_multiplier` | `0.75` | expert hidden = 960 × 0.75 = **720** |

### 2-3) 데이터셋 입력 스펙

| 항목 | 값 |
|---|---|
| `input_features.observation.state` | shape `[6]` (단일팔 6 DOF) |
| `input_features.observation.images.camera1` | shape `[3, 256, 256]` |
| `input_features.observation.images.camera2` | shape `[3, 256, 256]` |
| `input_features.observation.images.camera3` | shape `[3, 256, 256]` |
| `output_features.action` | shape `[6]` |
| `empty_cameras` | `0` (더미 카메라 없음) |
| `resize_imgs_with_padding` | `[512, 512]` |
| `chunk_size` | `50` |
| `n_action_steps` | `50` |
| `num_steps` | `10` (denoising steps) |
| `normalization_mapping` | VISUAL=IDENTITY, STATE=MEAN_STD, ACTION=MEAN_STD |

---

## 3) safetensors 키 Dump — 카테고리별 파라미터 수

**전체 500 tensors, 450,046,176 params (450.0M)**

### 3-1) 카테고리 요약

| 카테고리 | 텐서 수 | 파라미터 수 | 비율 |
|---|---|---|---|
| VLM (`model.vlm_with_expert.vlm.*`) | 345 | 350,165,184 (350.2M) | 77.8% |
| Action Expert (`model.vlm_with_expert.lm_expert.*`) | 145 | 98,245,840 (98.2M) | 21.8% |
| Action MLP 4종 (`model.action_*_proj.*`) | 8 | 1,603,472 (1.6M) | 0.4% |
| State projector (`model.state_proj.*`) | 2 | 31,680 (0.03M) | 0.01% |

### 3-2) VLM 서브 카테고리

| 서브 카테고리 | 텐서 수 | 파라미터 수 |
|---|---|---|
| vision_model (SigLIP) | 197 | 86.4M |
| connector (modality_projection) | 1 | 11.8M |
| embed_tokens | 1 | 47.3M |
| text_model.layers (16 layers) | 145 | 157.3M |
| lm_head | 1 | 47.3M |

### 3-3) Action Expert (lm_expert) 상세

16 layers × 9 tensors = 144 tensors + norm 1 tensor.

각 레이어는 다음 텐서를 포함:

| 텐서명 패턴 | dtype | shape | 비고 |
|---|---|---|---|
| `layers.N.input_layernorm.weight` | BF16 | `[720]` | |
| `layers.N.post_attention_layernorm.weight` | BF16 | `[720]` | |
| `layers.N.mlp.down_proj.weight` | BF16 | `[720, 2048]` | |
| `layers.N.mlp.gate_proj.weight` | BF16 | `[2048, 720]` | |
| `layers.N.mlp.up_proj.weight` | BF16 | `[2048, 720]` | |
| `layers.N.self_attn.q_proj.weight` | BF16 | `[960, 720]` | self-attn 레이어 (짝수) |
| `layers.N.self_attn.o_proj.weight` | BF16 | `[720, 960]` | |
| `layers.N.self_attn.k_proj.weight` | BF16 | `[320, 720]` | self-attn (짝수): input=expert_dim |
| `layers.N.self_attn.k_proj.weight` | **F32** | `[320, 320]` | cross-attn (홀수): input=vlm_kv_dim |
| `layers.N.self_attn.v_proj.weight` | BF16 | `[320, 720]` | self-attn (짝수) |
| `layers.N.self_attn.v_proj.weight` | **F32** | `[320, 320]` | cross-attn (홀수) |

**cross-attn K/V re-projector 해설:**
- 홀수 레이어(1, 3, 5, …, 15)는 expert가 VLM의 K/V cache를 attend
- `smolvlm_with_expert.py:125-133`에서 k_proj/v_proj를 `nn.Linear(vlm_kv_dim, expert_kv_dim)`으로 교체
- VLM: `num_kv_heads=5`, `head_dim=64` → `kv_dim = 320`
- Expert: 동일 `kv_dim = 320` (hidden=720이나 kv head 구조는 VLM과 동일)
- F32인 이유: HuggingFace 저장 시 새로 초기화된 projector는 float32로 저장되는 경향

### 3-4) Action MLP + State proj 상세

| 키 | dtype | shape | 의미 |
|---|---|---|---|
| `model.state_proj.weight` | F32 | `[960, 32]` | state (max 32 dim) → VLM hidden 960 |
| `model.state_proj.bias` | F32 | `[960]` | |
| `model.action_in_proj.weight` | F32 | `[720, 32]` | action chunk noise → expert hidden 720 |
| `model.action_in_proj.bias` | F32 | `[720]` | |
| `model.action_out_proj.weight` | F32 | `[32, 720]` | expert hidden → action (max 32 dim) |
| `model.action_out_proj.bias` | F32 | `[32]` | |
| `model.action_time_mlp_in.weight` | F32 | `[720, 1440]` | sinusoidal pe (1440) → hidden 720 |
| `model.action_time_mlp_in.bias` | F32 | `[720]` | |
| `model.action_time_mlp_out.weight` | F32 | `[720, 720]` | timestep hidden → hidden 720 |
| `model.action_time_mlp_out.bias` | F32 | `[720]` | |

---

## 4) HuggingFace 저장 시 키 prefix 매핑

`SmolVLAPolicy`는 내부적으로 `self.model = VLAFlowMatching(...)` 구조. HF `save_pretrained` 시 `model.` prefix가 추가됨.

| safetensors key prefix | 코드 모듈 | 클래스 |
|---|---|---|
| `model.vlm_with_expert.vlm.*` | `VLAFlowMatching.vlm_with_expert.vlm` | SmolVLM2 (SmolVLMForConditionalGeneration) |
| `model.vlm_with_expert.lm_expert.*` | `VLAFlowMatching.vlm_with_expert.lm_expert` | Action Expert transformer |
| `model.state_proj.*` | `VLAFlowMatching.state_proj` | nn.Linear(32 → 960) |
| `model.action_in_proj.*` | `VLAFlowMatching.action_in_proj` | nn.Linear(32 → 720) |
| `model.action_out_proj.*` | `VLAFlowMatching.action_out_proj` | nn.Linear(720 → 32) |
| `model.action_time_mlp_in.*` | `VLAFlowMatching.action_time_mlp_in` | nn.Linear(1440 → 720) |
| `model.action_time_mlp_out.*` | `VLAFlowMatching.action_time_mlp_out` | nn.Linear(720 → 720) |

`modeling_smolvla.py`의 `_get_default_peft_targets`에서도 이 prefix 구조를 확인할 수 있음:
```python
target_modules = rf"(model\.vlm_with_expert\.lm_expert\..*\.(q|v)_proj|model\.({common_projections}))"
```

---

## 5) 학습 시나리오 추정

### 결론: **S1 × B1 조합**으로 학습됨

| 판단 항목 | config 값 | 해석 |
|---|---|---|
| 가중치 출처 | `load_vlm_weights: true` + safetensors에 VLM 가중치 포함 | B1: SmolVLM2 사전학습 가중치 로드 |
| 학습 대상 | `train_expert_only: true`, `freeze_vision_encoder: true` | S1: expert + state_proj + action MLP만 학습 |
| VLM 가중치 | safetensors에 포함되어 있으나 학습 중 frozen | 저장 시 frozen 상태로 함께 저장됨 |
| 동결 컴포넌트 | VLM text_model + vision_model + connector | 사전학습 SmolVLM2 지식 그대로 보존 |

**S1 학습 시 학습된 컴포넌트 (≈ 100M params 내외):**
- `lm_expert` (cross-attn K/V re-projector 포함)
- `state_proj`
- `action_in_proj`, `action_out_proj`, `action_time_mlp_in`, `action_time_mlp_out`

**S1 학습 시 동결된 컴포넌트 (≈ 350M params):**
- `vlm.model.vision_model` (SigLIP)
- `vlm.model.text_model.layers` (16 layers)
- `vlm.model.connector`

---

## 6) Expert 가중치 포함 여부 — 결론

**✅ Expert (Action Expert) 가중치가 실제로 포함되어 있음**

근거:
1. `model.vlm_with_expert.lm_expert.layers.0` ~ `layers.15` — 16개 레이어 전부 존재
2. 총 145 tensors, 98.2M params — `03_smolvla_architecture.md §3 #4` 에서 기술한 `lm_expert` 컴포넌트에 정확히 대응
3. cross-attn K/V re-projector (홀수 레이어 k_proj/v_proj, F32) 8쌍도 포함 — VLM K/V → expert K/V 매핑 학습 완료
4. action MLP 4종 (action_in_proj, action_out_proj, action_time_mlp_in, action_time_mlp_out) + state_proj — 모두 존재

**주의: VLM 가중치도 동일 파일에 저장됨**
- `lerobot/smolvla_base`의 safetensors는 VLM(frozen, 350M) + Expert(학습됨, 98M) + MLP(1.6M) 전부를 담은 단일 파일
- 파인튜닝 시 `train_expert_only=True`를 설정해도 VLM 가중치는 저장 파일에 포함됨 (추론 시 필요)

---

## 7) `05_hf_model_selection.md`와의 일관성 보충

본 문서 결과로 `05_hf_model_selection.md`의 기술을 다음과 같이 보충:

| 항목 | 05 기술 | 07 실측 보충 |
|---|---|---|
| 파라미터 수 | ~450M | 450,046,176 params (450.0M) 실측 확인 |
| 사전학습 방식 | A. smolvla_base 파인튜닝 | S1 × B1 조합 확인: VLM frozen, expert만 학습 |
| 학습 데이터 | LeRobot Community Datasets | 단일팔 6DOF, 카메라 3대 (256×256) 구성 확인 |
| dtype | bfloat16 하드코딩 | VLM + expert body = BF16, action MLP = F32 |
| expert width | `expert_width_multiplier=0.75` | expert hidden = 960 × 0.75 = 720 실측 |

---

## 8) 본 프로젝트 추론 환경에 대한 시사점

| 항목 | smolvla_base 학습 설정 | 03 마일스톤(Orin 추론) |
|---|---|---|
| 카메라 수 | 3대 (`camera1/2/3`) | 2대 예정 → `empty_cameras=1` 필요 |
| 이미지 해상도 | 256×256 (학습 입력) → 512×512로 resize+pad | 동일 설정 유지 |
| state dim | 6 DOF (max_state_dim=32로 padding) | 동일 (단일팔) |
| action dim | 6 DOF (max_action_dim=32로 padding) | 동일 |
| language instruction | `single_task` 필드 확인 필요 (TODO-02) | svla_so100_pickplace 데이터셋 분석 후 결정 |
| `compile_model` | (저장값 없음, 기본 False) | False 유지 (03b §2 B1 가이드) |

> **카메라 수 주의**: 사전학습은 카메라 3대(`empty_cameras=0`). 본 프로젝트가 카메라 2대를 사용할 경우 `empty_cameras=1`로 1번 슬롯을 zero image로 채워야 함. TODO-02에서 `svla_so100_pickplace` 데이터셋의 카메라 키 실측 후 최종 결정.

---

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-04-29 | 초안 작성. safetensors 헤더 직접 inspect (500 tensors, 450M params). config.json 분석. 학습 시나리오 S1×B1 확인. |
