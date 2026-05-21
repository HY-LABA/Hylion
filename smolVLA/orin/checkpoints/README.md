# orin/checkpoints/ — 학습된 정책 ckpt 보관

> 책임: prof_computer/DGX 에서 학습된 SmolVLA 정책 ckpt 를 Orin 측에 보관. `leftarm_v2_inference.py` 등 추론 스크립트가 본 디렉터리에서 ckpt 를 로드.

---

## 디렉터리 구조

```
orin/checkpoints/
├── README.md                    # 본 문서 (git 추적)
└── <repo_id_or_run_name>/       # gitignore — ckpt 단위
    └── pretrained_model/
        ├── config.json
        ├── train_config.json
        ├── adapter_model.safetensors    # LoRA adapter (A2 분기)
        └── adapter_config.json
```

`<repo_id_or_run_name>` 은 HF Hub repo 명 (예: `BaboGaeguri/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6`) 또는 학습 run name (`leftarm_v2_<NNN>_<pass>_<ts>`).

## 예시

```
orin/checkpoints/
├── README.md
├── leftarm_v2_A2_pc_2026-05-17/         # 001 분기 ckpt
│   └── pretrained_model/
│       ├── config.json
│       ├── train_config.json
│       ├── adapter_model.safetensors
│       └── adapter_config.json
└── leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6/  # 003 분기 ckpt
    └── pretrained_model/
        └── ...
```

---

## 다운로드 도구

HF Hub 에서 직접 다운로드 (prof_computer 가 학습 후 push 한 ckpt):

```bash
hf download BaboGaeguri/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6 \
  --local-dir ~/smolvla/orin/checkpoints/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6/pretrained_model
```

또는 `scripts/run_inference_leftarm_v2.sh download` subcommand 사용:

```bash
CKPT_REPO_ID=BaboGaeguri/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6 \
  ~/smolvla/orin/scripts/run_inference_leftarm_v2.sh download
```

→ ckpt 다운로드 + `n_action_steps` 자동 점검·수정.

## ckpt 호환성 검증

전송 후 `tests/load_checkpoint_test.py` 로 호환성 PASS 확인:

```bash
source ~/smolvla/orin/.hylion_arm/bin/activate
python ~/smolvla/orin/tests/load_checkpoint_test.py \
    --ckpt-path ~/smolvla/orin/checkpoints/<repo_id>/pretrained_model/
```

forward + action shape `(1, 50, *)` 출력이면 OK.

---

## git 정책

- **본 README 만 추적** — `<repo_id_or_run_name>/` 하위는 gitignore (`orin/checkpoints/*/` 패턴)
- 사유: ckpt 파일 크기 (수십 MB ~ GB), 학습 사이클별로 새 ckpt 생성

---

## 참고

- 추론 entry: [`orin/inference/README.md`](../inference/README.md)
- 학습 ckpt 출처: `prof_computer/finetune/leftarm_v2/branches/<NNN>_<방법>_<인자>/`
- 호환성 검증: [`orin/tests/README.md`](../tests/README.md) → `load_checkpoint_test.py`
- 명명 컨벤션: [`prof_computer/README.md` §7](../../prof_computer/README.md)
