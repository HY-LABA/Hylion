# orin/checkpoints/ — 학습된 정책 ckpt 보관

> 책임: DGX 에서 학습된 smolVLA 정책 ckpt 를 시연장 Orin 측에 보관. `hil_inference.py` 등 추론 스크립트가 본 디렉터리에서 ckpt 를 로드.
> 신설: 04_infra_setup TODO-O2 (2026-04-30)
> 첫 ckpt 도착 시점: 05_leftarmVLA TODO-13

---

## 디렉터리 구조

```
orin/checkpoints/
├── README.md                    # 본 문서 (git 추적)
└── <run_name>/                  # gitignore — 학습 run 단위
    └── <step>/                  # 학습 step 단위 (예: 050000, last)
        └── pretrained_model/
            ├── config.json
            ├── train_config.json
            └── model.safetensors
```

`<run_name>` 은 DGX 측 `dgx/outputs/train/<run_name>/` 와 일치. `<step>` 은 `last` 또는 학습 step 수.

## 예시

```
orin/checkpoints/
├── README.md
├── leftarm_v1/
│   ├── 050000/
│   │   └── pretrained_model/
│   │       ├── config.json
│   │       ├── train_config.json
│   │       └── model.safetensors
│   └── last/
│       └── pretrained_model/
│           └── ... (동일)
└── biarm_v1/
    └── 100000/
        └── pretrained_model/
            └── ...
```

---

## 전송 도구

DGX → 시연장 Orin 의 ckpt 전송은 `scripts/sync_ckpt_dgx_to_orin.sh` (devPC 경유 2-hop):

```bash
# devPC 에서 실행
bash scripts/sync_ckpt_dgx_to_orin.sh --run leftarm_v1 --step last
```

- 02_dgx_setting TODO-10b 에서 검증된 절차 (903 MB safetensors byte-exact 일치 PASS)
- 시연장 Orin 의 네트워크 격리 시 우회 경로는 04 TODO-T2 에서 재검토

## ckpt 호환성 검증

전송 후 `orin/examples/tutorial/smolvla/load_checkpoint_test.py` 로 호환성 PASS 확인:

```bash
source ~/smolvla/orin/.hylion_arm/bin/activate
python ~/smolvla/orin/examples/tutorial/smolvla/load_checkpoint_test.py \
    --ckpt-path ~/smolvla/orin/checkpoints/leftarm_v1/last/pretrained_model/
```

forward + action shape `(1, 50, *)` 출력이면 OK.

---

## git 정책

- **본 README 만 추적** — `<run_name>/` 하위는 gitignore (`orin/checkpoints/<run_name>/` 패턴)
- 사유: ckpt 파일 크기 (수백 MB ~ GB), 학습 사이클별로 새 run 생성

---

## 참고

- `docs/storage/07_orin_structure.md` §2 (checkpoints/ 컴포넌트 책임) + §4-1 (devPC sync hub)
- `docs/storage/06_dgx_venv_setting.md` §10 (DGX → Orin 체크포인트 전송 절차, 02 TODO-10b 검증)
- `docs/work_flow/specs/04_infra_setup.md` TODO-T2 (시연장 Orin 의 ckpt 전송 경로 재확인)
- `orin/examples/tutorial/smolvla/load_checkpoint_test.py` (ckpt 호환성 검증)
- `orin/examples/tutorial/smolvla/hil_inference.py` (ckpt 로드 후 실 SO-ARM 추론 — 05 TODO-14 에서 ckpt 인자 추가 예정)
