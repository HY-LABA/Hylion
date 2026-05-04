# dgx — DGX Spark 학습 환경

> SmolVLA 학습 전용. orin/ (추론) 과 형제 디렉터리.
> 결정 근거: `docs/work_flow/specs/02_dgx_setting.md` TODO-08 / `docs/lerobot_study/06_smolvla_finetune_feasibility.md`
> 갱신: 04_infra_setup TODO-X2 (2026-05-01) — tests/, config/ 신규 디렉터리 추가 + 데이터 수집 인터페이스 안내 추가
> 갱신: 07_cleanup_datacollector_refs TODO-P5 (2026-05-03) — 06_dgx_absorbs_datacollector 결정 반영: DataCollector 노드 운영 종료, DGX 단일 노드 데이터 수집·학습 통합 구조로 갱신

---

## ⚠ 주의사항 — DGX 환경 구성

### pyproject.toml 미존재

`dgx/pyproject.toml` 은 **존재하지 않는다**. DGX 는 `docs/reference/lerobot/` upstream submodule 을 editable install 로 그대로 사용하기 때문에 별도 pyproject 가 불필요하다.

- 학습 entrypoint (`lerobot-train`) 는 `docs/reference/lerobot/pyproject.toml` 의 `[project.scripts]` 에서 제공됨
- DGX 에서 직접 사용하는 entrypoint: `lerobot-train` 만 (데이터 수집·텔레오퍼레이션은 DGX 가 직접 담당, 추론은 Orin 의 책임)
- 사용하지 않는 entrypoint (`lerobot-record`, `lerobot-calibrate`, `lerobot-teleoperate` 등) — DGX 에서 실행 X. SO-ARM 직접 연결 없음

### lerobot 설치 방법

`setup_train_env.sh` 가 `docs/reference/lerobot/` 를 editable install 로 설치한다. `dgx/lerobot/` curated 디렉터리는 존재하지 않으며 도입 계획도 없다 (upstream 무수정 원칙).

```bash
# setup_train_env.sh 가 수행하는 lerobot 설치
pip install -e ~/smolvla/docs/reference/lerobot[smolvla]
```

---

## 디렉터리 구조

```text
dgx/
├── README.md
├── .arm_finetune/           # dgx 학습 전용 venv (hidden, orin/.hylion_arm 과 격리). setup_train_env.sh 가 생성. rsync 배포 제외
├── scripts/                 # 환경 구축·운영 스크립트 (마일스톤 무관, 변경 거의 없음)
│   ├── setup_train_env.sh   # venv 생성 + PyTorch + lerobot editable 설치 + 환경변수 자동 적용
│   ├── preflight_check.sh   # 학습 전 OOM/Walking RL 보호 게이트
│   └── smoke_test.sh        # lerobot-train --steps=1 검증 (svla_so100_pickplace)
├── tests/                   # ★ 신규 (04 TODO-X2) — dgx 측 환경 점검 + 회귀 검증 자산
│   └── README.md            # tests/ 의 책임 + 자산 목록
├── config/                  # ★ 신규 (04 TODO-X2) — dgx 측 학습 설정 캐시
│   ├── README.md            # config/ 의 책임 + dataset_repos.json 스키마
│   └── dataset_repos.json   # DGX 학습에 사용할 HF 데이터셋 repo_id 목록 (placeholder)
├── runs/                    # 마일스톤별 학습 실행 자료 (05 진입 시 채움)
│   └── README.md            # 구조 안내
└── outputs/                 # 학습 출력 (체크포인트, 로그) — 자동 생성. rsync 배포 제외
```

**환경 분리 원칙**:
- `dgx/.arm_finetune/` 는 SmolVLA 학습 전용. orin/ 추론 venv (`orin/.hylion_arm`) 와 충돌 없음
- Walking RL venv (`/home/laba/env_isaaclab/`) 와도 격리
- 활성화: `source /home/laba/smolvla/dgx/.arm_finetune/bin/activate`
- prompt 표시: `(.arm_finetune)` (orin 측은 `(.hylion_arm)`)

---

## ⚠ 절대 원칙: Walking RL 학습 보호

**같은 DGX 에서 Walking RL 트랙(팀원) 이 24시간 학습 중입니다.** 본 SmolVLA 학습은 그 잔여 자원만 사용합니다.

**절대 하지 말 것:**

- Walking RL 프로세스(`env_isaaclab/python`) kill / 일시 정지
- 다른 사용자 Jupyter 커널 / venv / 프로세스 종료
- `sudo` 로 메모리 강제 회수 / OOM killer 강제 발동
- 시스템 단 환경변수 (`/etc/environment` 등) 수정

**해도 되는 것:**

- 본인이 띄운 Jupyter 커널 shutdown
- 본인이 로드한 Ollama 모델 unload
- 본인 SmolVLA venv 활성화/비활성화
- 본인 `outputs/` 디렉터리 정리

---

## 학습 시작 전 필수 체크리스트

### 1. 환경 준비 (최초 1회)

```bash
ssh dgx
bash ~/smolvla/dgx/scripts/setup_train_env.sh
```

→ `/home/laba/smolvla/dgx/.arm_finetune/` 에 venv 생성, PyTorch 2.10.0+cu130 + lerobot editable 설치, 환경변수 자동 적용.

### 2. 매 학습 시작 전

```bash
source /home/laba/smolvla/dgx/.arm_finetune/bin/activate
bash ~/smolvla/dgx/scripts/preflight_check.sh <시나리오>
```

`<시나리오>` 옵션:

| 시나리오 | 필요 메모리 (RAM, UMA pool) | 용도 |
|---|---|---|
| `smoke` | 20 GiB | 1 step 검증 |
| `s1` | 35 GiB | 05_leftarmVLA / 07_biarm_VLA 1차 |
| `s3` | 65 GiB | 07_biarm_VLA 2차 (VLM 까지 풀 학습) |
| `lora` | 28 GiB | LoRA fallback |

(안전 마진 +10 GiB 자동 적용)

**preflight 가 PASS 일 때만 학습 시작.** FAIL 시 출력된 안내에 따라 본인 프로세스 정리 후 재시도.

### 3. 가용 메모리 부족 시 대응 순서

본 SmolVLA 가 필요로 하는 메모리 < 가용 메모리 + 10 GB 마진 이면 학습 불가. 다음 순서로 정리:

1. **본인 Jupyter 커널 shutdown** — VSCode Jupyter 탭 닫기 / `Shutdown Kernel`
2. **본인 Ollama 모델 unload**
   ```bash
   curl http://localhost:11434/api/generate -d '{"model":"<모델명>","keep_alive":0}'
   ```
3. **본인 다른 학습/스크립트 종료**
4. 위 모두 정리해도 부족하면 → **Walking RL 종료 시간대 대기**. Walking RL 프로세스는 절대 건드리지 않는다.

---

## 학습 실행 가이드

### Smoke test (1 step 검증, 약 10~20분)

```bash
source ~/smolvla/dgx/.arm_finetune/bin/activate
bash ~/smolvla/dgx/scripts/smoke_test.sh
```

→ `lerobot/svla_so100_pickplace` 데이터셋 + `lerobot/smolvla_base` 가중치를 자동 다운로드 (최초 1회) 하고 1 step 학습. exit code 0 + loss 출력 확인.

### 05_leftarmVLA 학습

```bash
bash ~/smolvla/dgx/scripts/preflight_check.sh s1
# PASS 확인 후
lerobot-train \
    --policy.path=lerobot/smolvla_base \
    --dataset.repo_id=${HF_USER}/leftarm_so_arm_humanoid_v1 \
    --batch_size=64 \
    --steps=20000 \
    --num_workers=8 \
    --output_dir=~/smolvla/outputs/train/leftarm_v1 \
    --job_name=leftarm_v1 \
    --policy.device=cuda \
    --wandb.enable=true
```

### 07_biarm_VLA 학습

`docs/lerobot_study/06_smolvla_finetune_feasibility.md §6.2` 의 1차/2차/LoRA 명령 참조.

---

## 환경변수 (자동 적용)

`setup_train_env.sh` 가 venv activate 시 다음 변수 자동 적용:

| 변수 | 값 | 의미 |
|---|---|---|
| `HF_HOME` | `/home/laba/smolvla/.hf_cache` | Walking RL / 시스템 디폴트와 격리 |
| `PYTORCH_CUDA_ALLOC_CONF` | `expandable_segments:True,max_split_size_mb:128` | UMA 환경 메모리 단편화 방지 |
| `CUDA_VISIBLE_DEVICES` | `0` | GPU 0 만 명시 사용 |

이 변수들은 **SmolVLA venv 활성화 시에만 적용** 됩니다. Walking RL venv (`/home/laba/env_isaaclab/`) 활성화 시엔 격리됨.

---

## 결정 사항 / 환경 사양

- **Python**: 시스템 3.12.3 (Walking RL 동일)
- **PyTorch**: 2.10.0+cu130 (Walking RL 검증 완료, GB10 capability 12.1 UserWarning 무시 가능)
- **cuDNN / NCCL**: PyTorch wheel 번들 (시스템 별도 설치 X)
- **lerobot**: `docs/reference/lerobot/` submodule editable 설치 (분석한 SHA 와 학습 환경 일치)
- **venv 경로**: `/home/laba/smolvla/dgx/.arm_finetune` (Walking RL `/home/laba/env_isaaclab/` 와 충돌 없음)
- **HF 캐시**: `/home/laba/smolvla/.hf_cache` (rsync 영향 밖)

자세한 근거: `docs/work_flow/specs/02_dgx_setting.md` TODO-07 / TODO-08 / `docs/lerobot_study/06_smolvla_finetune_feasibility.md`

---

## DGX 단일 노드 데이터 수집·학습 인터페이스

<!-- 06_dgx_absorbs_datacollector 결정 (2026-05-03): DataCollector 노드 운영 종료.
     DGX 가 데이터 수집(lerobot-record·lerobot-teleoperate) + 학습(lerobot-train) 책임을 단일 노드에서 담당.
     이전 DataCollector ↔ DGX 2-노드 구조는 legacy 로 이관 (docs/storage/legacy/ 참조). -->

DGX 에서 직접 데이터 수집 후 학습을 진행한다. 설정은 `dgx/config/dataset_repos.json` 에서 관리.

```
DGX (데이터 수집):
  lerobot-teleoperate → 텔레오퍼레이션
  lerobot-record → 데이터셋 (LeRobotDataset 포맷)
      ↓
  HF Hub push (lerobot-record --push-to-hub) 또는 로컬 저장
      ↓
DGX (학습):
  lerobot-train --dataset.repo_id=<HF_USER>/... 또는 --dataset.local_path=...
      ↓
  outputs/train/<run_name>/checkpoints/<step>/pretrained_model/
      ↓
Orin (추론):
  sync_ckpt_dgx_to_orin.sh → Orin 체크포인트 배포
```

- `dataset.repo_id` 포맷: `{hf_username}/{dataset_name}` (lerobot upstream 표준)
- HF 데이터셋 캐시: `$HF_HOME/lerobot/` = `/home/laba/smolvla/.hf_cache/lerobot/`
- 실 데이터셋 목록은 `dgx/config/dataset_repos.json` 에 등록 (05_leftarmVLA 진입 시 채움)

---

## 배포 (devPC → DGX)

devPC 에서:

```bash
bash smolVLA/scripts/deploy_dgx.sh
```

→ `dgx/` + `docs/reference/lerobot/` (editable 설치 대상) 을 `~/smolvla/` 로 rsync.
※ `dgx/outputs/`, `dgx/.arm_finetune/` 는 rsync 배포 제외 (런타임 생성 자산).
