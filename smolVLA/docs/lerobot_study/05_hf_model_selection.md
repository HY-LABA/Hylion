# HuggingFace 모델 선택 — SmolVLA 변종 분기점

> 기준: `docs/reference/lerobot/` (v0.5.1-52-g05a52238)
> 작성일: 2026-04-27
> 목적: SmolVLA 사전학습 정책 체크포인트 / VLM 백본 / 기타 변종 중 본 프로젝트에 적합한 조합 선정. **결론적으로 변종 선택 여지가 거의 없음** — 본 문서는 "왜 그런지" 의 근거를 정리.
> 선행 읽기: `docs/lerobot_study/03_smolvla_architecture.md` §B (가중치 출처 분기)

---

## 1) 분기 카테고리 개요

SmolVLA 시스템에서 "모델 선택" 은 두 층으로 나뉨:

| 층 | 의미 | config 플래그 |
|---|---|---|
| **정책 체크포인트** | 사전학습된 SmolVLA 전체 (VLM + Expert + projector) 의 가중치 | CLI `--policy.path=<repo_id>` |
| **VLM 백본** | Expert 가 결합되는 VLM 의 종류 | `vlm_model_name` (config) |

이 두 층은 **결합되어 있음**: 특정 정책 체크포인트는 특정 VLM 백본 위에 학습된 것이라, **백본을 바꾸면 정책 체크포인트의 expert/projector 가중치 호환 깨짐**.

## 2) 정책 체크포인트 — LeRobot 공식 SmolVLA

### 결론: 공식 사전학습 SmolVLA 체크포인트는 1개뿐

| 모델 | 위치 | 파라미터 | 학습 데이터 | 비고 |
|---|---|---|---|---|
| **`lerobot/smolvla_base`** | https://hf.co/lerobot/smolvla_base | **~450M** | LeRobot Community Datasets (SmolVLA 논문 기준) | 공식 권장 |

근거:
- `smolvla.mdx:49` — "Use `smolvla_base`, our pretrained 450M model"
- `modeling_smolvla.py:32` — 공식 학습 예시 `--policy.path=lerobot/smolvla_base`
- `pretrained.py:251` — 모델 타입 `smolvla` 의 base_model 자동 결정값이 `lerobot/smolvla_base`
- 코드 / 테스트 / 문서 전부 `lerobot/smolvla_base` 만 사용. 다른 LeRobot SmolVLA 사전학습 체크포인트는 발견되지 않음.

### 분기 옵션 비교

| 분기 | 옵션 | 학습 결과 | 적합성 |
|---|---|---|---|
| **A. smolvla_base 파인튜닝 (권장)** | `--policy.path=lerobot/smolvla_base` | Expert + VLM 모두 사전학습 가중치로 시작 | ✅ 본 프로젝트 표준 |
| B. VLM 만 사전학습 + Expert random | `--policy.type=smolvla` (path 없이) | SmolVLM2 만 사전학습, Expert random init | ❌ 데이터 양 부족 시 수렴 어려움 |
| C. 처음부터 학습 | `load_vlm_weights=False` + 구조만 정의 | 모두 random init | ❌ 코드도 경고 출력 (`modeling_smolvla.py:509-515`) |

→ 본 프로젝트는 **A 고정**. 데이터 규모 (수백~수천 에피소드) 로 B·C 가 의미 있게 수렴할 가능성 매우 낮음.

## 3) VLM 백본 — `vlm_model_name`

### 코드에 등장하는 SmolVLM 변종

| VLM | 코드 위치 | 파라미터 | 용도 |
|---|---|---|---|
| **`HuggingFaceTB/SmolVLM2-500M-Video-Instruct`** | `configuration_smolvla.py:84`, `smolvlm_with_expert.py:75` | ~500M | **smolvla_base 의 백본 (default)** |
| `HuggingFaceTB/SmolVLM-Instruct` | `tests/processor/test_smolvla_processor.py:73` | - | 테스트 코드 전용 |

HuggingFace SmolVLM 시리즈에는 추가 변종이 존재하지만 (256M / 500M / 2.2B 등), **LeRobot 의 SmolVLA 코드는 SmolVLM2-500M-Video-Instruct 기준으로 작성**됨.

### 분기 옵션 비교

| 분기 | VLM | smolvla_base 호환? | 적합성 |
|---|---|---|---|
| **A. SmolVLM2-500M-Video-Instruct (default, 권장)** | 500M | ✅ | 본 프로젝트 표준 |
| B. 더 작은 SmolVLM (256M 등) | 256M | ❌ — 사전학습 가중치 차원 불일치 | 비추 (학습 처음부터 + 기능 부족) |
| C. 더 큰 SmolVLM (2.2B 등) | 2.2B+ | ❌ | 비추 (Orin 추론 latency 불가능 가능성, 학습 비용 큼) |

**왜 변경 시 호환이 깨지는가**:
- `smolvlm_with_expert.py:106-116` — Expert 의 hidden_size 가 VLM hidden_size × `expert_width_multiplier` 로 결정. VLM 변경 시 Expert 차원도 변경 → smolvla_base 의 expert 가중치 로드 실패
- `smolvlm_with_expert.py:120-134` — cross-attn 의 K/V re-projection 차원도 VLM 의 `head_dim` × `num_key_value_heads` 의존. VLM 변경 시 함께 변경 필요

→ **VLM 백본 변경은 사실상 처음부터 학습 (B2 시나리오)** 와 동일한 비용.

### 본 프로젝트 결정

> **`vlm_model_name = "HuggingFaceTB/SmolVLM2-500M-Video-Instruct"` (default 그대로 유지).**

## 4) 기타 모델 분기 (실질적 의미 낮음)

### dtype

`smolvlm_with_expert.py:90-92`:
```python
self.vlm = AutoModelForImageTextToText.from_pretrained(
    model_id, torch_dtype="bfloat16", low_cpu_mem_usage=True,
)
```

→ 항상 **bfloat16**. DGX Spark / Orin Nano Super 모두 bfloat16 지원. 변경 옵션 없음 (코드 하드코딩).

### PEFT/LoRA

`modeling_smolvla.py:495-504` `_get_default_peft_targets`:
```python
target_modules = "lm_expert.*.q_proj|v_proj | state_proj | action_in_proj | action_out_proj | action_time_mlp_in/out"
```

→ LoRA 적용은 **모델 변종 결정** 이 아니라 **학습 분기** (`03b_smolvla_milestone_config_guide.md §2 06` 의 VRAM 부족 시 fallback). 본 문서 범위 밖.

### compile_model (torch.compile)

`configuration_smolvla.py:106-107`:
```python
compile_model: bool = False
compile_mode: str = "max-autotune"
```

→ 추론 속도 최적화 옵션. 모델 자체 변경 아님. 07 배포 시 검토 (`03b_smolvla_milestone_config_guide.md §2 07`).

## 5) 종합 권장값 — 모델 변종

| 항목 | 권장값 | 변경 가능성 |
|---|---|---|
| 정책 체크포인트 | `lerobot/smolvla_base` | 사실상 고정 (대안 없음) |
| VLM 백본 | `HuggingFaceTB/SmolVLM2-500M-Video-Instruct` | 사실상 고정 (smolvla_base 호환 필수) |
| dtype | bfloat16 | 코드 하드코딩, 변경 불가 |

### 실험 가능 여지가 생기는 시나리오 (본 프로젝트 범위 밖)

1. **smolvla_base 사전학습이 도메인 차이로 도움 안 됨이 명백** → B 시나리오 (VLM 만 사전학습 + Expert random) 검토. 단, 데이터 양 10k 에피소드 이상 필요 추정.
2. **Orin 추론 latency 가 너무 길어 데모 불가** → 더 작은 VLM 백본 + 처음부터 학습. 비용/리턴 trade-off 매우 나쁨. 07 의 추론 단 옵션 (num_steps↓, n_action_steps↓, compile, RTC) 을 모두 시도해본 후 마지막 옵션.

위 두 시나리오 모두 본 프로젝트의 `arm_2week_plan.md` 기간 안에는 비현실적. **시나리오 발생 시 마일스톤 일정 자체 재검토 필요** 사항으로 분류.

## 6) 모델 선정 기준 정리

본 프로젝트가 모델을 선정한 기준:

| 기준 | 가중치 | smolvla_base 평가 |
|---|---|---|
| 파라미터 수 | 중 | 450M — Orin 추론 가능, DGX 학습 가능 (실측 대기) |
| 입력 모달리티 | 높음 | 다중 카메라 + state + 자연어 task — 본 프로젝트와 일치 |
| 사전학습 데이터셋 | 높음 | LeRobot Community (SO-ARM 포함) — 본 프로젝트 데이터와 분포 가까움 |
| 라이선스 | 높음 | Apache 2.0 — 연구·데모 용도 자유 |
| LeRobot 통합 수준 | 최고 | 공식 정책. CLI 한 줄로 파인튜닝 가능 |

대안 부재: HuggingFace 에 다른 vision-language-action policy (OpenVLA, RT-X 계열 등) 가 존재하지만, **LeRobot 통합 / SO-ARM 호환 / Orin 추론 가능성** 모두 만족하는 다른 옵션은 본 프로젝트 시점에서 발견되지 않음.

## 7) 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-04-27 | 초안 작성. 정책 체크포인트 / VLM 백본 / dtype 분기 정리. 결론: 모두 default 유지. |
