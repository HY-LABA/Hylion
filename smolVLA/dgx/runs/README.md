# dgx/runs — 마일스톤별 학습 실행 자료

> 마일스톤(`arm_2week_plan.md` 05, 07 등)별 학습 명령·하이퍼파라미터·메모를 보관.
> 본 디렉터리는 마일스톤 진입 시점에 채운다 (YAGNI). 진입 전엔 비어 있음.

---

## 구조 (마일스톤 진입 시 생성)

```
dgx/runs/
├── 05_leftarm/             # 05_leftarmVLA 진입 시 생성
│   ├── train.sh            # 학습 실행 명령 (lerobot-train ...)
│   ├── README.md           # 학습 가이드 (실행/모니터링/결과 해석)
│   └── notes.md            # 메트릭 분석·재실험 메모
└── 07_biarm/               # 07_biarm_VLA 진입 시 생성
    ├── train_s1.sh         # 1차 학습 (S1)
    ├── train_s3.sh         # 2차 (S3)
    ├── train_lora.sh       # LoRA fallback
    ├── README.md
    └── notes.md
```

## 학습 결과는 어디에?

- 체크포인트 / 로그: `dgx/outputs/<run_name>/` (본 디렉터리 외부, 학습 시 자동 생성)
- 학습 명령은 `--output_dir=../outputs/<run_name>` 형태로 명시 권장

## 권장 명령 출처

각 마일스톤의 학습 권장 명령은 [docs/lerobot_study/06_smolvla_finetune_feasibility.md §6](../../docs/lerobot_study/06_smolvla_finetune_feasibility.md) 에 작성돼 있다. 본 디렉터리의 `train*.sh` 는 그 명령을 셸 스크립트로 옮긴 것.
