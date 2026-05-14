# dgx/runs — 마일스톤별 학습 실행 자료

> 마일스톤별 학습 명령·하이퍼파라미터·메모를 보관. (마일스톤 정의는 새 계획 수립 후 갱신 — 옛 `arm_2week_plan.md` 는 `docs/storage/legacy/arm_2week_plan/` 로 아카이브됨)
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

본 디렉터리의 `train*.sh` 는 각 학습 spec 에서 결정한 명령을 셸 스크립트로 옮긴 것.
