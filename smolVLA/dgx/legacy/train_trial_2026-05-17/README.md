# DGX 학습 시도 — 종료 (2026-05-17)

> **결론**: DGX (NVIDIA DGX Spark, GB10 aarch64 + UMA 128GB) 에서의 학습 시도는 *지속 OOM 사고* 로 *잠정 중단*. 학습 책임은 **`prof_computer`** (Windows 10 + WSL2 + RTX 3090 24GB) 로 이관.
> 본 디렉터리는 *2026-05-15 ~ 2026-05-17 DGX 학습 시도들의 보존* 용. 실행·갱신 안 함 (read-only 역사 자료).

---

## 1) 종료 사유 — DGX 학습이 왜 실패했나

3 차례 학습 시도 *모두 실패*. 근본 원인 = **video decode 자체의 메모리 누수** (backend 무관).

| 시도 | 일자 | 결과 | 직접 원인 |
|---|---|---|---|
| 시도 1 | 2026-05-15 16:55 | step 368/20000 OOM SIGKILL | system 5GB/min 누수 (CONSTRAINT_NONE, global_oom). VSCode 도 함께 oom-kill |
| 시도 2 | 2026-05-15 18:13 | OOM 예측 적중 (workers 8→2 축소도 부족) | steady-state 1.25GB/min 누수. workers 가 *주범 아님* 확정 (worker RSS 안정) |
| 시도 3 | 2026-05-16 10:58 | 사용자 Ctrl+C (3시간 26분 후 thrashing) | `video_backend=pyav` 강제 적용 후에도 동일 누수 패턴 |

→ **확정**: backend (torchcodec / pyav) 무관, *video decode 자체* 가 OS-level buffer leak (libav buffer 또는 shmem). DGX 의 *aarch64 + cu130 + FFmpeg 6.1.1* 환경에서는 lerobot upstream 의 video pipeline 이 안정 동작 *불가*.

상세 진단·증거: [`docs/training_log.md`](docs/training_log.md) (보존)

---

## 2) 잠정 중단 후 이관 경로 — prof_computer

DGX 의 *aarch64 ecosystem* (torchcodec wheel 부재 + FFmpeg 6 ABI 미스매치) 우회 위해 *일반 x86_64 환경* 으로 학습 노드 이관:

| 차원 | DGX (실패 환경) | prof_computer (이관 환경) |
|---|---|---|
| 아키텍처 | aarch64 (Grace+Blackwell) | x86_64 |
| GPU 메모리 | UMA 128GB (CPU 공유) | RTX 3090 24GB (분리 VRAM) |
| FFmpeg | 6.1.1 | 4.4.2 |
| video backend | pyav (torchcodec ABI 깨짐) | **torchcodec 0.10 정상** |
| 시스템 RAM 누수율 | 1.25 GB/min (DGX 시도 2) | **0.18 GB/h** (1660× 감소) |
| 100ep × 75K step 학습 완주 | ❌ | ✅ (M1.5, 2026-05-17) |

→ **이관 결과**: prof_computer 에서 *DGX 의 pyav buffer leak 가설 직접 증명* (torchcodec 정상 환경에서는 누수 메커니즘 자체가 발생 X). [`prof_computer/docs/leftarm_v2/learning_log.md`](../../../prof_computer/docs/leftarm_v2/learning_log.md) 참조.

---

## 3) DGX 의 새 역할 — 데이터 수집기

DGX 는 *학습 책임 해제* 후 **데이터 수집·텔레오퍼레이션 전용** 노드로 역할 재정의:

- 활성 entry: `dgx/finetune/leftarm_v2/run_record.py`, `run_teleop.py` (변경 없이 그대로 사용)
- 수집 결정 근거: `dgx/docs/finetune/leftarm_v2/collection_log.md`
- 학습은 *전적으로 prof_computer 책임* — `prof_computer/finetune/leftarm_v2/`

---

## 4) 보존된 자료 — 본 디렉터리 내용

```
legacy/train_trial_2026-05-17/
├── README.md                              # 본 파일
├── finetune/
│   ├── run_train.py                       # DGX 학습 wrapper (DGX 의 시도 1·2·3 실행본)
│   ├── _lib.py                            # 사본 (dgx/finetune/leftarm_v2/_lib.py 와 동일)
│   └── config/
│       └── train_config.yaml              # DGX 학습 config (batch 16, num_workers 2, pyav 등 시도별 최종 상태)
└── docs/
    ├── training_log.md                    # 시도 1·2·3 상세 진단 (wandb 증거 + dmesg + 가설 분리)
    └── backlog_legacy.md                  # 학습 관련 backlog 항목 (preflight, num_workers 가이드 등 — DGX 학습 재시도 시 참고)
```

> ⚠️ **재실행 의도 없음**. 본 디렉터리 파일들은 *DGX 학습 재시도가 필요해질 때* 의 *복원 시작점* 으로만 보존. 실행하려면 *DGX ecosystem 정비 (torchcodec aarch64 wheel 또는 FFmpeg 7+)* 가 *선결 조건*.

---

## 5) DGX 학습 재진입 검토 시점 (장기 backlog)

DGX 학습 재시도가 *합리적 선택이 될* 조건:

- lerobot upstream 이 *torchcodec aarch64 wheel* 공식 배포 (또는 FFmpeg 7+ 호환)
- 또는 *video dataset → image dataset 변환* 사이클 진입 (image 로 가면 video decode leak 자체 회피)
- 또는 *DGX UMA 압박 해소* (Walking RL 종료 시간대 가용 시)

이 중 어느 조건도 *2026-05-18 현재* 충족 X. 본 디렉터리는 *조건 충족 시점까지 동결*.
