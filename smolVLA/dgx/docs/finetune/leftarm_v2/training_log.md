# leftarm_v2 — 학습 로그

> **목적**: `BaboGaeguri/leftarm_v2` 학습 시도별 실행 기록 — 명령 / 결과 / 관찰 / 이슈. [collection_log.md](collection_log.md) 의 학습 측 대칭 문서.
> **운영**: 학습 시도마다 "학습 시도 로그" 에 entry 추가. 이슈는 "발견된 이슈 / 후속" 에 누적, fix 가 필요하면 [../backlog.md](../backlog.md) 로도 연결.
> **자매 문서**: [model_config.md](model_config.md) (방법론 선택 근거), [../camera_and_codec.md](../camera_and_codec.md).

---

## 학습 사이클 개요

| 항목 | 값 |
|---|---|
| dataset | `BaboGaeguri/leftarm_v2` (110 ep / 59,752 frames @ 30 fps) |
| 베이스 ckpt | `lerobot/smolvla_base` (450M params, VLM 16 layers) |
| 방법 | LoRA (r=16, target=all-linear) — VLM + expert 양쪽 |
| 2A pass | 100 ep balanced subset (ep 0~99) · 20K steps · sanity 검증 |
| 2B pass | 200 ep 완성 후 hyperparameter 정밀 튜닝 — [model_config.md](model_config.md) 참조 |
| 설정 위치 | [config/train_config.yaml](../../../finetune/leftarm_v2/config/train_config.yaml), [config/base_config.yaml](../../../finetune/leftarm_v2/config/base_config.yaml) |
| 실행 래퍼 | [run_train.py](../../../finetune/leftarm_v2/run_train.py) |

---

## 학습 시도 로그

### 시도 1 — 2026-05-15 16:55 · 2A first pass · **❌ FAILED (OOM kill, step ~368)**

**명령**: `python run_train.py train --pass 2a`

| 항목 | 값 |
|---|---|
| run name | `leftarm_v2_2a_2026-05-15_16-55-12` |
| wandb run | `wandb.ai/babogaeguri-hanyang-university/leftarm_v2/runs/9qwxdx5k` |
| output_dir | `/home/laba/smolvla/dgx/outputs/leftarm_v2_2a_2026-05-15_16-55-12` |
| 도달 step | **368 / 20,000** (1.84%) |
| 마지막 logged step | 350 (loss 0.292, grad_norm 0.497, lr 4.9e-05) |
| 종료 모드 | `subprocess.CalledProcessError ... died with <Signals.SIGKILL: 9>` (traceback 없음) |
| checkpoint 저장 | ❌ 없음 (`save_freq=1000` 도달 전 사망) |

**설정 (run 시점)**:

| 파라미터 | 값 |
|---|---|
| batch_size | 16 |
| num_workers | 8 |
| prefetch_factor | 2 |
| persistent_workers | false |
| dataset.return_uint8 | true |
| LoRA | r=16, target=all-linear (VLM + expert) |
| trainable params | 11.5M / 461.6M (2.5%) |

**관찰 (사망 직전)**:

- step 50~300 사이 평균 **2.7~2.85 s/step** (normal)
- step 350 → 368 구간 **4.77 s/step 으로 급증** (~1.7배 슬로다운) — swap 없이도 시스템 메모리 압박 시 page reclaim 비용 증가 패턴
- loss 곡선 자체는 정상 (0.71 → 0.29, 5K samples)

**진단 — wandb 차트 증거 (메모리 누적 패턴)**:

run `9qwxdx5k` 의 train + system metrics 캡처 분석 (~20분 구간):

| 지표 | 값 | 시사점 |
|---|---|---|
| **System Memory Utilization** | **10% → 100% 선형 증가** | spike 가 아닌 **leak 패턴**. 약 20분에 걸쳐 90% 누적 (≈ 110~115 GB) |
| **Process Memory Available** | 100 GB → ~5 GB 선형 감소 | 동일 추세 — system 전체에서 메모리가 사라짐 |
| **Process Memory In Use (MB)** | **3.4 GB 로 안정 (변화 거의 없음)** | ⚡ **메인 lerobot-train 은 안 자람**. wandb 가 카운트하는 건 main 프로세스만이라 누락된 ~110GB 는 다른 곳 |
| Process CPU Threads | 50 → 78 안정 | num_workers=8 × 각 worker 의 thread |
| **GPU Power** | **12 W (매우 낮음)** | GB10 정상 부하는 50~100+W. GPU 가 거의 idle = bottleneck 이 GPU 아님 |
| GPU Time Accessing Memory | 0% | GPU 메모리 access 미미 |
| GPU Utilization | 95% | 매우 짧은 work 도 95% 로 보고하는 wandb metric 특성. power 12W 와 함께 보면 실 GPU 사용은 작음 |
| train/dataloading_s | 첫 step 0.38 → 이후 0 | prefetch 큐가 잘 동작 = **buffer 가 항상 메모리 점유** |
| train/loss | 0.74 → 0.29 | 학습 진행 자체는 정상이었음 |
| Network Traffic | 5~12분 사이 spike | dataset / model 다운로드 (.hf_cache 가 차오름) |
| Disk I/O | 18분 이후 spike | OOM 직전 page reclaim 시작 |

→ **핵심**: 메인 프로세스 안 자람 (3.4GB) + system 95GB 증발 = **DataLoader workers 8개 + shmem + 동시 점유 (VSCode 등) 의 합산 누수**. wandb 의 "Process Memory" 는 main 만 추적해 무력. GPU 는 거의 idle 이라 GPU/CUDA cache 가 주범 아님.

**진단 — dmesg 증거 (global OOM 캐스케이드)**:

```
17:13:22  oom-kill ... task=code, pid=16264 → killed (VSCode server 1차)
17:13:31  NVRM: nvCheckOkFailedNoLog: Out of memory [NV_ERR_NO_MEMORY] (UMA → GPU 메모리도 압박)
17:14:44  oom-kill ... task=code, pid=16177 → killed (VSCode server 2차)
17:15:01~17:15:17  NVRM Out of memory 에러 약 10회 연쇄
17:15:26  node invoked oom-killer ... order=0
17:15:28  Out of memory: Killed process 173318 (lerobot-train)
          total-vm:320,402,920kB  anon-rss:2,276,744kB  shmem-rss:508,592kB
          oom_score_adj:200  constraint=CONSTRAINT_NONE  global_oom
```

→ **시스템 전체 (CONSTRAINT_NONE, global_oom) 메모리 부족**. cgroup 한도가 아니라 128GB UMA 자체가 모자랐음. OOM-killer 가 VSCode server 부터 죽이며 메모리 확보를 시도했고, 결국 lerobot-train 본체까지 도달.

**원인 가설 (wandb 증거 반영 후 재순위)**:

1. **🔥 DataLoader workers × pyav video decode 누수** — 가장 유력. wandb 의 main process 메모리 3.4GB 안정 vs system 95GB 증발 = workers 가 주범. `num_workers=8` × `prefetch_factor=2` 로 항상 16 배치 prefetch + 각 worker 가 pyav 로 libsvtav1 비디오 디코딩. pyav 는 ffmpeg 의 libsvtav1 decoder 가 frame buffer 를 release 안 하고 누적하는 알려진 패턴 (또는 worker 내 캐싱 leak). `persistent_workers=false` 라 epoch 끝마다 reset 되지만 한 epoch ≈ 3,750 step 이고 사망 시점은 step 368 (epoch 0.1 미만) — 즉 단일 epoch 내에서 100GB 가까이 누적
2. **🔥 동시 점유 프로세스 (VSCode server / Claude Code agent / 기타 user-slice)** — dmesg 가 `code` 를 두 번 죽인 게 직접 증거. wandb 는 이걸 추적 안 함. main 3.4GB + workers 추정 ~50GB + VSCode 등 ~40GB = system 100% 도달 시나리오 plausible
3. **⚙️ DGX GB10 UMA 의 CPU/GPU 메모리 통합** — Grace+Blackwell 128GB 풀이 모두 공유. NVRM OOM 이 일반 oom-killer 직전 발생한 게 증거. 하지만 GPU Power 12W / Time Accessing Memory 0% 면 *GPU 활용 자체는 약해* CUDA cache 가 주범은 아님. UMA 는 가용량 단일 풀이라는 사실이 압박을 증폭한 것
4. **💡 PyTorch CUDA allocator fragmentation** — main 프로세스 메모리 3.4GB 안정이라 가능성 낮음 (있다면 main 이 자랐어야)

**조치 — 다음 시도 (시도 2) 진입 전**:

wandb 증거 반영 후 우선순위 갱신 — **dataloader workers 가 주범으로 확정** → workers 축소가 가장 효과적.

| # | 조치 | 이유 (wandb 증거 반영) |
|---|---|---|
| 1 | **`num_workers` 8 → 2** (8→4 가 아닌 2) | 주범 직접 타격. 8 workers 가 ~50GB+ 누수 가정 시 1/4 로. throughput 손실은 GPU 가 어차피 idle (12W) 이라 무관 |
| 2 | `prefetch_factor` 2 → 1 | prefetch 큐 16 → 2. dataloading_s 가 첫 step 후 0 인 게 prefetch 가 항상 ready 라는 뜻 = buffer 점유 큼 |
| 3 | `batch_size` 16 → 8 (선택, 1·2 만 으로 부족 시) | activation 메모리 절반. 단 main process memory 가 3.4GB 안정이었으니 본 사고의 주범은 아님 — 1·2 효과 측정 후 결정 |
| 4 | **실행 전 cleanup 필수** | VSCode 창 닫기 (web/extension host 전부) / `pkill -f rerun` / `pkill -f claude` (agent worker 정리). dmesg 가 `code` 두 번 죽인 게 직접 증거 — 학습과 경합 |
| 5 | `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` | UMA fragmentation 완화. 우선순위 낮음 (main process 안 자람) 이지만 무료 |
| 6 | 별도 터미널에서 worker-level 모니터링 | `watch -n 5 'free -h; ps -eo pid,rss,cmd \| grep -E "lerobot\|python" \| sort -k 2 -n -r \| head'`. main vs workers RSS 분리해서 보면 다음 진단 빠름 |

→ 조치 1·2 합치면 **DataLoader 풋프린트 ≈ 1/8** 으로 감소 예상 (workers ¼ × prefetch ½). GPU 가 어차피 idle 이라 throughput 손해 사실상 없음 — 즉 *공짜로 누수 영향 축소*.

**대안 — 더 근본적 fix (시도 2 가 또 실패하면)**:

- pyav 대신 torchcodec 으로 video backend 전환 — pyav 의 libsvtav1 decode 누수 가설 검증
- 또는 codec 자체를 h264_nvenc 로 통일 (leftarm_v2 의 7개 chunk 중 일부는 h264_nvenc, 일부는 libsvtav1 — collection_log §개요 확인) → re-encode 후 학습
- `persistent_workers=true` 로 변경 — workers 재시작 비용 vs leak 누적 trade-off. v2 의 경우 leak 가 빠르니 persistent 가 *오히려 더 빨리 죽을* 가능성. 시도 1 종료 후에만 실험

**미해결 질문**:

- v1 학습 (40 ep, LoRA r=16, batch 16, 5000 step) 은 같은 셋업에서 완주 — v2 (100 ep, 동일 LoRA, batch 16, 20000 step) 가 OOM 난 차이는?
  - **데이터셋 크기**: 40 → 100 ep (2.5×). dataset object 자체 메모리는 video metadata 만이라 작음 — main process 가 3.4GB 안정이라는 wandb 증거와 일치 (dataset 크기 영향 미미)
  - **step 수**: 5K → 20K (4×). 사망 시점이 step 368 (v1 의 5K 보다 훨씬 이른 시점) 이라 step 수 자체는 무관
  - **누수 속도**: system 95GB / 20분 ≈ **5 GB/min**. v1 환경 (40 ep) 도 누수 했다면 5분 안에 죽었을 텐데 안 죽음. 차이가 있다는 뜻
  - **codec 차이 가설**: leftarm_v1 은 전부 libsvtav1. leftarm_v2 는 **차수 1~4 (ep 0~59) libsvtav1 + 차수 5~7 (ep 60~109) h264_nvenc** 가 섞임 (collection_log §개요 확인). 2A subset 이 ep 0~99 라 두 codec 모두 포함 → pyav 가 두 codec 을 다르게 처리하며 한쪽에서 더 큰 buffer leak 가능성. **검증 가치 있음**
  - **VSCode/Claude Code agent 점유 차이**: v1 시점 메모리 사용 기록 없음, v2 시점에 IDE/agent 더 적극 사용 가능성
  - **결론**: codec mix + 동시 점유 둘 다 가설. 시도 2 의 cleanup + workers 축소 후 결과로 가설 분리

---

## 발견된 이슈 / 후속

### 🔥 [ ] DGX UMA 환경에서 system-wide OOM 재현 — 메모리 가드레일 표준화

- **발견**: 2026-05-15 시도 1, lerobot-train SIGKILL @ step 368
- **상태**: global_oom (CONSTRAINT_NONE), GPU NVRM OOM 선행 → CPU oom-killer 가 VSCode server 와 학습 프로세스 순차 처리
- **조치 (단발성)**: 시도 2 에서 num_workers/prefetch_factor/batch_size 동시 축소 + 실행 전 cleanup. 결과 본 entry 갱신
- **조치 (구조적)**: run_train.py 또는 setup_finetune_env.sh 에 preflight 추가 — `free -h` 의 available 메모리 < 임계값이면 경고/거부. 추가로 `PYTORCH_CUDA_ALLOC_CONF` 기본값 export
- **연관**: [../backlog.md](../backlog.md) "환경 / 설정" 아래 새 항목으로 추가

### ⚙️ [ ] 시도 1 의 wandb run 처리

- run `9qwxdx5k` 가 350 step 만 기록된 채로 wandb 에 남아있음 (early death). 그대로 두면 비교/조회 시 노이즈
- **조치**: wandb 웹에서 해당 run 에 `failed-oom` 태그 추가, 또는 삭제. 시도 2 가 성공하면 시도 1 은 archive
