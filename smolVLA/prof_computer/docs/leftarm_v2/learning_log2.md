# prof_computer — 학습 로그 2 (004+ 사이클)

> 📌 **현행 사이클** — 004 분기부터 본 파일에 누적.
> **출발점**: 003 (loss 0.0324, 8/8 = 100%, 5변수 종합) 으로 *base 학습 방법 유효성* 증명 완료. 본 파일부터는 *성능 향상* 영역.
> **이전 아카이브**: [learning_log1.md](learning_log1.md) — M1.5 ~ 003 사이클 (2026-05-21 freeze).
>
> ⚠️ **cold start 진입자 필독**: 본 파일은 *계층 3 분기 인스턴스* 의 실행 기록만 담음. *계층 1~2* (학습 방법·hp 인자) + 시간 라벨 (마일스톤) 의 정의는 [prof_computer/README §7 명명 3-계층 + 시간 라벨](../../README.md) 참조 — *반드시 본 파일 진입 전 1회독*.
>
> ---
>
> 본 노드 (Windows 10 + WSL2 + RTX 3090) 의 fine-tune 시도별 실행 기록.
> 결정 근거: [model_config.md](../model_config.md) — leftarm_v2/v3+ 공통 학습 방법론.

---

## 출발점 — 003 baseline 요약

> 본 사이클 (004+) 의 *비교 기준*. 상세는 [learning_log1.md §003 분기 학습](learning_log1.md).

| 항목 | 값 |
|---|---|
| HF Hub repo | [`BaboGaeguri/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6`](https://huggingface.co/BaboGaeguri/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6) |
| 분기명 | `003_a2_310ep_empty1_sched_sync_bf16_b6` |
| 학습 메트릭 | 120000 step / 4.38 epoch / **final loss 0.0324** / 16h 11m / VRAM peak 84.77% |
| 추론 평가 | **8/8 = 100%** (단축, 학습 분포 외 perturbation 4 trial 포함) — [`orin/docs/leftarm_v2/003_eval_2026-05-19.md`](../../../orin/docs/leftarm_v2/003_eval_2026-05-19.md) |
| 5변수 종합 (vs M1.5) | dataset 110→310ep · empty_cameras 0→1 · sched_sync 30k→120k · bf16 · batch 4→6 |

---

## 004+ 사이클 entry

> 새 분기 학습이 시작되면 본 섹션 하위에 entry 추가. §003 entry (learning_log1.md L570~) 양식 mirror 권장:
> - 분기 식별 + 변경 변수 + 가설
> - smoke 검증
> - 본 학습 (메트릭 표 + 시스템 메트릭 표)
> - HF Hub 검증
> - 추론 평가 결과 메모 (Orin eval 시트 링크)

_(아직 신규 entry 없음)_
