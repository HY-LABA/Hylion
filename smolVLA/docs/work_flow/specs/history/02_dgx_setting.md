# 20260427_dgx_setting
<!-- Claude Code + 개발자 협업 작성 -->

> 목표: DGX Spark 학습 환경 구축 + smolVLA 학습/배포 가능성 결정 (양팔 / 자유도 / 병렬학습)
> 환경: DGX Spark Ubuntu 24.04.4 LTS | Python 3.12.3 (시스템) | CUDA SDK 13.0.2 | GPU 드라이버 580.142
> 접근: devPC (`babogaeguri@babogaeguri-950QED`) → `ssh dgx` → DGX Spark (`laba@spark-8434`)
> DGX 코드 경로: `/home/laba/smolvla/` (rsync 배포 기준, 추후 확정)
> 학습 대상: smolVLA (HuggingFace `lerobot/smolvla_base` 또는 동급 베이스 모델)
> 작성: 2026-04-27

---

## 참고 레퍼런스

- `docs/reference/lerobot/` — HuggingFace lerobot upstream (학습 스크립트, 데이터셋 포맷, smolVLA 정책)
- `docs/reference/seeed-lerobot/` — Seeed lerobot fork (SO-ARM 관련 정책 차이)
- `docs/reference/nvidia_official/` — NVIDIA PyTorch on Jetson 공식 문서 (DGX는 Jetson 아님, 호환성 차이 인지 필요)
- `docs/lerobot_study/` — 본 스펙 학습 TODO(03~06) 산출물 저장 위치. 마일스톤 순서대로 prefix 라벨링 (`00_*`, `01_*`, `02_*` 는 사전 학습; `03_*`, `03b_*`, `04_*`, `05_*`, `06_*` 는 학습 TODO 산출물).
- `docs/storage/03_software.md` — DGX Spark 실측 소프트웨어 정보
- `docs/storage/04_devnetwork.md` — devPC ↔ DGX SSH 연결 구조
- `docs/storage/devices_snapshot/dgx_spark_env_snapshot_2026-04-22_0043.txt` — DGX 환경 스냅샷 (직전 실측)
- `arm_2week_plan.md` — `02_dgx_setting` 마일스톤 정의 및 결정사항

## 레퍼런스 활용 규칙

- 레퍼런스에 동일하거나 유사한 구현이 있으면 반드시 그것을 기반으로 작성한다.
- 레퍼런스에 없는 새로운 스크립트·함수·클래스를 만들어야 할 경우, 구현 전에 반드시 사용자에게 설명하고 확인을 받은 뒤 진행한다.

---

## Todo

### [x] TODO-01: Bootcamp → HYlion 레포 이관

- 타입: both
- DOD: 기존 Bootcamp 레포의 smolVLA 관련 코드/문서가 HYlion 조직 산하 레포(`smolVLA`)로 이관되고, devPC/Orin/DGX 모두에서 새 레포 기준으로 작업 가능
- 구현 대상: 없음 (레포 이관 작업)
- 테스트: 없음
- 제약: 4단계 새 레포 이관과 동일한 절차 적용
- **완료**: 이관 완료 상태로 본 스펙 작성 시점에 확정. 현재 `c:\Users\admin\Desktop\Hylion\smolVLA` 레포가 신규 HYlion 레포 기준이며 Orin 측 `~/smolvla/` 도 동일 기준으로 운영 중.

### [x] TODO-02: DGX Spark 실측 재진행

- 타입: test
- DOD: DGX Spark의 하드웨어/소프트웨어 실측값이 최신화되어 `docs/storage/03_software.md` (그리고 필요 시 `docs/storage/02_hardware.md`) 에 반영됨. 학습 환경 세팅(TODO-08)에 필요한 모든 정보(GPU 메모리, CUDA/cuDNN/TensorRT 상태, Python·pip 상태, 디스크 가용량, 외장 SSD 여부) 가 명확화됨.
- 구현 대상: 없음 (실측·기록 작업)
- 테스트: prod 검증 — DGX에서 실측 명령 실행 후 결과를 `docs/storage/devices_snapshot/` 하위에 신규 스냅샷 파일로 저장
- 제약: devPC에서 `ssh dgx` 접속 후 DGX 내부에서 실행. 직전 스냅샷(`dgx_spark_env_snapshot_2026-04-22_0043.txt`) 항목을 기준으로 동일 항목 + 추가 항목 측정.
- 측정 항목 (최소):
  1. OS / 커널 / hostname / arch
  2. CPU 모델·코어 수 / 메모리 총량·가용량
  3. GPU 모델·VRAM·드라이버 버전 (`nvidia-smi`)
  4. CUDA SDK·`nvcc` 경로·버전 / cuDNN / TensorRT
  5. Python 버전·경로 / pip 설치 여부 / venv 또는 conda 사용 가능 여부
  6. Docker / NVIDIA Container Toolkit 설치 여부
  7. 디스크 용량 (`df -h`) / 외장 SSD 마운트 여부
  8. 네트워크 인터페이스 / 현재 WiFi IP (`docs/storage/04_devnetwork.md` 갱신 트리거)
  9. 동작 중 서비스 (Ollama 등) — 학습 시 자원 경합 가능성 점검
- 잔여 리스크:
  - 직전 스냅샷 시점 대비 IP 변경 가능성 → `~/.ssh/config` HostName 갱신 필요할 수 있음
  - cuDNN / TensorRT 미설치 상태 → TODO-08 (학습 환경 세팅) 에서 설치 결정 필요
- **완료 (20260427_2355)**: 20단계 전 PASS. 주요 실측값: Ubuntu 24.04.4 / aarch64, CPU Cortex-X925+A725 20코어, RAM 121Gi (90Gi 가용), GPU NVIDIA GB10 UMA(VRAM N/A), 드라이버 580.142 / CUDA 13.0, Python 3.12.3, pip 24.0, venv 가용(conda 없음), Docker 29.1.3, NVIDIA Container Toolkit 1.19.0, 디스크 3.3T 가용, 외장 SSD 없음, Ollama 서비스 실행 중. cuDNN / TensorRT 미설치. 스냅샷: `docs/storage/devices_snapshot/dgx_spark_env_snapshot_2026-04-27_2342.txt` 저장. `03_software.md` · `02_hardware.md` DGX 섹션 업데이트 완료.

> **학습 TODO 산출물 위치 공통 규칙**: 모든 학습(`타입: study`) TODO 의 산출물은 `docs/lerobot_study/` 하위에 마크다운 문서로 저장하며, 마일스톤 순서대로 prefix 라벨링한다 (예: `03_*`, `04_*`, `05_*`, `06_*`. 동일 마일스톤 내 보조 문서는 `03b_*` 처럼 알파벳 첨자 부여). 기존 문서(`00_lerobot_repo_overview.md`, `01_lerobot_root_structure.md`, `02_lerobot_src_structure.md`) 와 일관된 톤·구조를 유지한다. 본 스펙에는 결론 요약과 문서 경로만 기록한다.

### [x] TODO-03: smolVLA 구조 학습

- 타입: study
- DOD: smolVLA 의 모델 구조(visual encoder · language encoder · action head · attention 흐름) 와 forward/loss 경로를 본인 언어로 설명 가능한 수준으로 정리. 핵심 파일·클래스 위치를 `docs/reference/lerobot/` 기준으로 식별 완료. 각 마일스톤(03~07) 에서의 config 분기 적용 방침까지 정리.
- 구현 대상:
  - `docs/lerobot_study/03_smolvla_architecture.md` — SmolVLA 일반 구조 + config 7 카테고리 분기 매트릭스 (S1~S4 학습 시나리오, B1~B3 가중치 출처, C~G 카테고리)
  - `docs/lerobot_study/03b_smolvla_milestone_config_guide.md` — 위 일반 지식을 본 프로젝트 마일스톤(`arm_2week_plan.md` 03~07) 에 매핑한 마일스톤별 분기 가이드 + RTC 등 추론 단 옵션 보충
- 테스트: 없음 (자가 검증 — 문서 작성으로 대체)
- 참조:
  - `docs/reference/lerobot/src/lerobot/policies/smolvla/` (정책 구현)
  - SmolVLA 논문 (`arXiv:2506.01844`)
  - SmolVLA 블로그 (`huggingface.co/blog/smolvla`)
- 잔여 리스크: 논문/블로그와 실제 코드 간 차이 가능성 — 코드 우선으로 정리
- **완료 (2026-04-27)**: 두 문서로 산출물 분리 작성. `03_smolvla_architecture.md` 는 SmolVLA 일반 지식(재사용 가능), `03b_smolvla_milestone_config_guide.md` 는 본 프로젝트 마일스톤 03~07 의 분기 적용 방침. 마일스톤별 분기 변화는 `03b_smolvla_milestone_config_guide.md §3 한눈에 표` 에서 일괄 확인 가능.

### [x] TODO-04: 데이터셋 구조 학습

- 타입: study
- DOD: lerobot 데이터셋 포맷(LeRobotDataset 스키마, 에피소드/프레임/타임스탬프/관측·액션 키 규칙, 카메라/state/action shape) 을 본인 언어로 설명 가능한 수준으로 정리. SO-ARM teleop 으로 수집된 데이터가 어떤 키 구조로 저장되는지 식별 완료. 05_biarm_teleop_on_dgx 진입 시 결정해야 할 사항 체크리스트 정리.
- 구현 대상:
  - `docs/lerobot_study/04_lerobot_dataset_structure.md` — LeRobotDataset 디렉터리 구조, 표준 키 컨벤션, 카메라 키 명명 규칙(정렬 동작 정정 포함), state/action 12 DOF 매핑, processor 자동 처리 흐름, 05 결정 체크리스트
- 테스트: 없음
- 참조:
  - `docs/reference/lerobot/src/lerobot/datasets/` (LeRobotDataset 구현)
  - `docs/reference/lerobot/src/lerobot/utils/constants.py` (표준 키)
  - `docs/reference/lerobot/src/lerobot/policies/smolvla/processor_smolvla.py` (입력 전처리 파이프라인)
- 잔여 리스크: smolVLA 학습 시 데이터셋 키 매핑이 SO-ARM 양팔 12 DOF / 카메라 3대 구성과 일치하는지는 05/06 단계에서 재확인 필요 (본 문서 §10 참조)
- **완료 (2026-04-27)**: `04_lerobot_dataset_structure.md` 작성 완료. 카메라 키 정렬 관련 이전 추측(prefix 강제 필요) 을 코드 검증 결과로 정정 (dict 삽입 순서 보존, 정렬 안 함 — `policies.py:148-152` `image_features` property 확인). `03b_smolvla_milestone_config_guide.md` 의 관련 섹션도 함께 정정.

### [x] TODO-05: 허깅페이스 모델 선택 기준 학습

- 타입: study
- DOD: smolVLA 계열 베이스 모델·체크포인트 후보들을 비교하고, 본 프로젝트에 가장 적합한 베이스 모델을 선정. 선정 기준(파라미터 수 · 입력 모달리티 · 사전학습 데이터셋 · 라이선스) 명시. VLM 백본 / dtype 등 모델 변종 분기점 식별.
- 구현 대상:
  - `docs/lerobot_study/05_hf_model_selection.md` — 정책 체크포인트 / VLM 백본 / dtype 분기 정리, 선정 기준, 결론
- 테스트: 없음
- 참조:
  - HuggingFace `lerobot` 조직 (`huggingface.co/lerobot`)
  - `docs/reference/lerobot/docs/source/smolvla.mdx` (공식 권장)
  - `docs/reference/lerobot/src/lerobot/policies/smolvla/configuration_smolvla.py` (vlm_model_name default)
- 잔여 리스크: HuggingFace 모델 라이선스·재배포 조건이 본 프로젝트(연구실 데모 / 추후 공개 여부) 와 충돌할 가능성 → smolvla_base 는 Apache 2.0 으로 확인됨 (본 문서 §6)
- **완료 (2026-04-27)**: `05_hf_model_selection.md` 작성 완료. **결론: 정책 체크포인트는 `lerobot/smolvla_base` (450M) 고정, VLM 백본은 `HuggingFaceTB/SmolVLM2-500M-Video-Instruct` 고정, dtype 은 bfloat16 (코드 하드코딩).** 변종 변경 시 사전학습 가중치 호환 깨지므로 사실상 분기 여지 없음.

### [x] TODO-06: 파인튜닝 가능성 학습

- 타입: study
- DOD: 선정한 베이스 모델 기준 파인튜닝 절차(`lerobot-train` CLI · 하이퍼파라미터 기본값 · 체크포인트 저장 형식) 를 정리. DGX Spark 실측 자원(TODO-02) 기반으로 1회 파인튜닝 예상 소요 시간/메모리 점검. TODO-08 환경관리 결정사항 사전 정리 (venv vs conda 등). 04/06 마일스톤 학습 권장 명령 작성.
- 구현 대상:
  - `docs/lerobot_study/06_smolvla_finetune_feasibility.md` — DGX 실측 자원 요약, 환경관리 결정 사전 정리(§2), `lerobot-train` CLI 동작(§3), 체크포인트 저장 형식(§4), 학습 비용 추정(§5), 04/06 학습 권장값(§6)
- 테스트: 없음
- 참조:
  - `docs/reference/lerobot/src/lerobot/scripts/lerobot_train.py` (학습 엔트리포인트)
  - `docs/reference/lerobot/src/lerobot/configs/train.py` (`TrainPipelineConfig` 디폴트)
  - `docs/reference/lerobot/docs/source/smolvla.mdx` (공식 학습 예시)
  - `docs/reference/lerobot/docs/source/peft_training.mdx` (PEFT/LoRA)
  - SmolVLA 논문 (`arXiv:2506.01844`)
  - `docs/storage/devices_snapshot/dgx_spark_env_snapshot_2026-04-27_2342.txt` (DGX 실측)
- 제약: TODO-02·TODO-03·TODO-05 완료 후 진행 → 모두 충족됨
- 잔여 리스크 (본 문서 §7):
  - GB10 throughput 미확정 → TODO-09 1 step smoke test 후 갱신 필요
  - CUDA 13 PyTorch 호환 → TODO-08 첫 검증 항목
  - UMA 메모리 점유 분포 — 일반 dGPU VRAM 추정과 다름, `free -h` 병행 모니터링 필요
  - Ollama 자원 경합 → 학습 시작 전 stop 권장
  - DGX↔Orin PyTorch 버전 차이 → safetensors 호환성 TODO-10 검증
- **완료 (2026-04-28)**: `06_smolvla_finetune_feasibility.md` 작성 완료. **결론 요약**:
  - **환경**: Python 3.12.3 (시스템) + venv (conda 미설치, 본 프로젝트는 venv 가 효율적), PyTorch 는 CUDA 13 호환 wheel TODO-08 에서 검증
  - **학습 비용 (200k step 기준)**: 40~110 시간 (GB10 throughput 미확정, 보수적 범위). UMA 121 GiB pool 로 S1/S3 모두 여유, S4 도 batch 조정 시 가능
  - **체크포인트**: ~2.7 GB/checkpoint, 200k step 학습 시 약 27 GB (디스크 3.3 TB 대비 충분)
  - **04 권장**: smolvla.mdx 공식 예시 그대로 (`batch_size=64, steps=20000, S1`)
  - **06 권장**: 1차 S1 50k step → 부족 시 S3 + LR 절반 → 부족 시 LoRA. 도메인 시프트가 04 보다 커서 step 더 길게.

### [x] TODO-07: 결정사항 — Walking RL 과 병렬학습 가능 여부

- 타입: study
- DOD: DGX Spark 단일 장비에서 Walking RL 학습과 smolVLA 학습이 동시 진행 가능한지 결론(가능 / 부분 가능 / 불가) 과 근거(VRAM · CPU · I/O 점유율 추정) 가 본 스펙에 기록됨. 불가/부분 시 백업(연구실 PC) 활용 시나리오 명시.
- 구현 대상: 없음
- 테스트: Walking RL 트랙 담당자 회신(`docs/storage/others/walking_rl_smolvla_check_2026-04-28.md`) 기반 결론.
- 제약: TODO-02 완료 후 진행. TODO-08(환경관리 결정) 보다 선행되어야 함.
- **결론 (2026-04-28)**: **부분 가능 — 시간대 분할 + Jupyter 커널 정리 조건부.** 격리 방식은 venv 분리만으로 충분 (Docker 컨테이너 불필요).
- 근거 (회신 문서 기반):
  - **PyTorch / CUDA**: Walking RL 이 `PyTorch 2.10.0+cu130` 사용 중. SmolVLA 도 동일 wheel 사용 권장 → wheel 호환성 확정 (TODO-08 PyTorch 검증 작업이 사실상 종결됨)
  - **GB10 CUDA capability 12.1**: PyTorch 공식 지원 범위(8.0~12.0) 밖이지만 실제 동작 확인됨 (UserWarning 만 발생)
  - **Python 환경**: Walking RL `/home/laba/env_isaaclab/` (uv 생성 venv). SmolVLA 는 `/home/laba/smolvla/dgx/.arm_finetune` 별도 경로로 충돌 없음
  - **GPU 메모리 병목**:
    - Walking RL 훈련: 2,490 MiB (가벼움)
    - **Jupyter kernel 2개**: 12,938 MiB 낭비 중 (DETR 과제, Sleeping 상태) → **SmolVLA 학습 전 반드시 shutdown 필요**
    - Jupyter 정리 후 안전 사용 가능 메모리: 50~60 GiB (Walking RL 훈련 중) / 70~80 GiB (Walking RL 종료 시)
  - **Ollama**: 현재 GPU 미사용 (대기). 단, `gemma3:27b` 로드 시 ~17 GB 순간 점유 위험 — 학습 전 상태 확인 권장
  - **CPU / 디스크 / I/O**: 여유 충분 (Walking RL CPU 1.7코어 / 20코어 중)
  - **스왑 0**: OOM Kill 즉시 발생 — 안전 마진 필수
- 운영 권장:
  1. SmolVLA 학습 시작 전 Jupyter 커널 shutdown 확인 (`nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv`)
  2. Ollama `gemma3:27b` 미로드 상태 확인
  3. Walking RL 동시 진행 시 SmolVLA 학습 batch_size 보수적 시작 (예: 32 → 단계적 증가)
  4. Walking RL 훈련 종료 시간대에 SmolVLA 풀 학습(batch=64, S3 등) 진행 권장
- 회신 문서: `docs/storage/others/walking_rl_smolvla_check_2026-04-28.md`

### [x] TODO-08: 환경관리 / 버전 호환성 결정

- 타입: task
- DOD: DGX Spark 학습용 Python 환경 관리 방식 + PyTorch/CUDA/cuDNN 버전 조합이 결정되어 본 스펙에 기록. Orin 추론 환경(`~/smolvla/orin/.hylion_arm`, Python 3.10) 과의 학습→추론 호환성(체크포인트 호환, torch 버전 차이 영향) 명시.
- 구현 대상: 없음 (결정은 본 스펙에 기록, 실제 설치는 TODO-09)
- 테스트: 없음
- 제약: TODO-02·TODO-07 완료 후 진행 → 모두 충족
- **결정 (2026-04-28)** — TODO-07 회신 (`docs/storage/others/walking_rl_smolvla_check_2026-04-28.md`) 의 Walking RL 환경과 정합 우선:

| 항목 | 결정값 | 근거 |
|---|---|---|
| Python 버전 | **시스템 3.12.3** | Walking RL 동일. 시스템 Python = lerobot `>=3.10` 호환. 추가 설치 불필요 |
| 패키지 매니저 | **venv** | 단일 환경, conda 미설치, Walking RL 도 venv 사용. Orin `~/smolvla/orin/.hylion_arm` 와 형제 구조로 운영 일관성 |
| venv 경로 | **`/home/laba/smolvla/dgx/.arm_finetune`** | Walking RL `/home/laba/env_isaaclab/` 와 충돌 없음, Orin venv (`~/smolvla/orin/.hylion_arm`) 와 형제 구조 |
| PyTorch | **`torch==2.10.0+cu130`** (pip nvidia 공식 wheel) | Walking RL 동일 wheel 동작 검증됨. GB10 CUDA capability 12.1 UserWarning 발생하나 기능 정상 |
| cuDNN | **`nvidia-cudnn-cu13==9.15.1.9` (PyTorch wheel 번들)** | 시스템 설치 불필요 — Walking RL 동일 |
| NCCL / 기타 | **`nvidia-nccl-cu13==2.28.9` 등 PyTorch 의존성에 포함** | Walking RL 환경 동일 |
| TensorRT | **미설치** | 학습 단계에서 불필요. 배포(07_biarm_deploy) 시 Orin 에서 검토 |
| lerobot 설치 방식 | **`pip install 'lerobot[smolvla,training]'`** | DGX 는 학습 전용, 코드 수정 안 함. editable 불필요 |

- Orin 호환성:
  - DGX Python 3.12.3 + PyTorch 2.10.0+cu130 vs Orin Python 3.10 + PyTorch (Jetson aarch64 wheel)
  - 체크포인트는 safetensors 포맷이라 Python/torch 마이너 버전 차이는 일반적으로 호환 — TODO-10 배포 환경 세팅 시 더미 체크포인트로 검증
- 잔여 리스크 (TODO-09 진입 시 점검):
  - SmolVLA 학습 시작 전 Jupyter 커널 shutdown / Ollama 상태 확인 (TODO-07 운영 권장 1·2 항목)
  - lerobot extras (`smolvla`, `training`) 설치 시 transformers / accelerate / wandb 가 PyTorch 2.10.0+cu130 과 호환되는지 — 1 step smoke test 로 확인

### [x] TODO-09: 학습 환경 세팅 — 스크립트 작성

- 타입: task
- DOD: DGX Spark 에서 lerobot 학습 스크립트가 실행 가능하도록 환경 구성이 `dgx/scripts/setup_train_env.sh` 로 재현 가능하게 스크립트화됨. 1 step smoke test 검증은 TODO-09b 에서 별도 진행.
- 구현 대상:
  - `dgx/README.md` — 운영 체크리스트 + Walking RL 보호 원칙 + 학습 가이드 + 폴더 구조 (옵션 C: scripts/ + runs/ + outputs/)
  - `dgx/scripts/setup_train_env.sh` — TODO-08 결정 기반 설치. venv 생성 (`dgx/.arm_finetune` 안쪽 격리) → PyTorch 2.10.0+cu130 → lerobot editable (`docs/reference/lerobot/`) → 환경변수 자동 적용 (`HF_HOME`, `PYTORCH_CUDA_ALLOC_CONF`, `CUDA_VISIBLE_DEVICES`)
  - `dgx/scripts/preflight_check.sh` — 학습 전 OOM/Walking RL 보호 게이트. 시나리오별 메모리 임계치(smoke 20GB / s1 35GB / s3 65GB / lora 28GB) + 안전 마진 10GB. Walking RL 프로세스 관찰만 (절대 kill X)
  - `dgx/scripts/smoke_test.sh` — `lerobot-train --policy.path=lerobot/smolvla_base --dataset.repo_id=lerobot/svla_so100_pickplace --steps=1` 실행. nvidia-smi 5초 간격 샘플링으로 자원 점유 기록
  - `dgx/runs/README.md` — 마일스톤별 학습 실행 자료 보관 안내 (04 진입 시 채움)
  - `scripts/deploy_dgx.sh` — devPC → DGX rsync 배포. `dgx/` + `docs/reference/lerobot/` 동기화 (`dgx/.arm_finetune`, `dgx/outputs` 제외)
- 부수 작업: orin/ 도 동일한 형제 구조 적용
  - `orin/.hylion_arm` (orin 디렉터리 안쪽, hidden) 로 venv 위치 명시화
  - `scripts/deploy_orin.sh` Orin 측 배포 경로를 `~/smolvla/` → `~/smolvla/orin/` 로 변경 (dgx/ 와 형제)
  - 모든 운영/현재 스펙 문서의 venv 경로 갱신 (`README.md`, `CLAUDE.md`, `docs/storage/03_software.md`, `docs/storage/05_orin_venv_setting.md`, `docs/storage/logs/todo.md`, `docs/work_flow/specs/00_template.md`, `06_smolvla_finetune_feasibility.md`). history 는 보존 (과거 시점 사실)
- 테스트: 없음 (스크립트 작성 단계 — `bash -n` syntax check 통과 확인. 실제 실행 검증은 TODO-09b)
- 제약: TODO-08 완료 후 진행 → 충족. Orin 측 `orin/scripts/setup_env.sh` 의 구조를 참고하되 DGX 용으로 분리(`dgx/`).
- 잔여 리스크 (TODO-09b 검증 시 점검):
  - Orin 머신에 이미 배포된 `~/smolvla/.venv` 가 새 위치 `~/smolvla/orin/.hylion_arm` 와 다름 — Orin 재배포 + venv 재생성 필요 (구버전 venv 수동 정리 또는 `rm -rf`)
- **완료 (2026-04-28)**: 스크립트 7개 + 문서 8개 작성/갱신 완료. `bash -n` syntax check 6개 모두 PASS. 실 실행 검증은 TODO-09b.

### [x] TODO-09b: 학습 환경 세팅 — DGX prod 검증

- 타입: test
- DOD: TODO-09 작성 산출물이 DGX 에서 실제 동작함을 확인. setup → preflight → smoke test 순차 PASS, GB10 throughput 실측치 기록.
- 구현 대상: 없음 (검증·기록만)
- 테스트: prod 검증 (DGX 접속 필요)

#### Codex 검증 (비대화형 SSH)

| # | 단계 | 기대 결과 |
|---|---|---|
| 1 | devPC: `bash scripts/deploy_dgx.sh` | rsync 정상 종료, DGX 측 `~/smolvla/dgx/` 와 `~/smolvla/docs/reference/lerobot/` 갱신 |
| 2 | DGX: `bash -n ~/smolvla/dgx/scripts/setup_train_env.sh` | syntax check 통과 |
| 3 | DGX: `bash -n ~/smolvla/dgx/scripts/preflight_check.sh` | syntax check 통과 |
| 4 | DGX: `bash -n ~/smolvla/dgx/scripts/smoke_test.sh` | syntax check 통과 |
| 5 | DGX: `ls ~/smolvla/dgx/scripts/` | 3개 스크립트 (setup_train_env, preflight_check, smoke_test) 존재 확인 |
| 6 | DGX: `ls ~/smolvla/docs/reference/lerobot/src/lerobot/policies/smolvla/` | submodule 정상 배포 (configuration_smolvla.py 등 5개 파일) |

#### 개발자 직접 검증 (대화형, 약 30~60 분 소요)

| # | 단계 | 기대 결과 |
|---|---|---|
| 1 | DGX: `bash ~/smolvla/dgx/scripts/setup_train_env.sh` | venv 생성, PyTorch 2.10.0+cu130 설치, lerobot editable 설치, 검증 출력에 `torch.cuda.is_available()=True` + `GPU name: NVIDIA GB10` + `lerobot import OK` |
| 2 | DGX: `source ~/smolvla/dgx/.arm_finetune/bin/activate && bash ~/smolvla/dgx/scripts/preflight_check.sh smoke` | preflight PASS (HF_HOME / venv / 메모리 / Walking RL / Ollama / 디스크 모두 PASS) |
| 3 | DGX: `bash ~/smolvla/dgx/scripts/smoke_test.sh` | preflight 자동 통과 + lerobot-train 1 step 통과 (loss 값 출력, exit code 0). HF Hub 다운로드 약 5~15분 + 학습 1~3분 |
| 4 | DGX: smoke_test 출력의 GPU util peak / GPU mem peak / 소요 시간 기록 | 결과를 `06_smolvla_finetune_feasibility.md §5.2` 표에 갱신 |

- 제약: TODO-09 완료 후 진행 → 충족. **Walking RL 프로세스(env_isaaclab) 절대 건드리지 말 것.** preflight FAIL 시 본인 다른 프로세스만 정리 (Jupyter 커널, 본인 Ollama 등).
- 잔여 리스크:
  - HF Hub 다운로드가 네트워크 상황에 따라 시간 길어질 수 있음
  - 첫 실행 시 GB10 capability 12.1 UserWarning 출력될 수 있으나 무시 가능 (`05_hf_model_selection.md` §3 / TODO-07 회신 참조)
  - lerobot extras (`smolvla`, `training`) 의 transformers / accelerate / wandb 가 PyTorch 2.10.0+cu130 과 호환 안 될 가능성 — 1 step smoke test 가 그 검증 역할
- **완료 (2026-04-28)**: 전 단계 PASS (Codex 6 + 개발자 4). 주요 실측: `torch 2.10.0+cu130`, `CUDA: True`, `GPU: NVIDIA GB10`, preflight 전항목 PASS (RAM 76 GiB 가용, Ollama GPU 미점유). smoke_test: `loss 0.545`, `5.97 s/step`, 전체 소요 48초, GPU util peak 90%, RAM used peak 48226 MiB. `06_smolvla_finetune_feasibility.md §5.2` 갱신 완료. 테스트 중 `dgx/scripts/smoke_test.sh` 4건 수정 (venv 활성 순서, output dir 선생성 방지, `push_to_hub=false`, camera `rename_map`). `docs/storage/lerobot_upstream_check/04_dgx_lerobot_diff.md` 신규 작성.
- **후행 작업 완료 (2026-04-28)**: `docs/storage/06_dgx_venv_setting.md` 신규 작성 완료 (`05_orin_venv_setting.md` 와 형제 구조). 9 절로 구성 — DGX/Orin 디렉터리 형제 구조, venv 선택 근거, 실측 설치 패키지, 환경변수 자동 적용, PyTorch 2.10.0+cu130 선택 근거, capability 12.1 UserWarning, setup_train_env.sh 동작, preflight 시나리오별 임계치, TODO-09b smoke 결과 (loss 0.545 / 5.97s/step / RAM peak 48 GiB), Walking RL 동시 점유 환경 관찰, 디스크 사용 추정, 잔여 리스크.

### [x] TODO-09c: 학습 환경 세팅 — Orin 배포 경로 마이그레이션 검증

- 타입: test
- DOD: TODO-09 부수 작업으로 Orin 측 배포 경로가 `~/smolvla/` → `~/smolvla/orin/` 으로 변경된 후, 옛 잔여 파일이 정리되고 새 venv 가 정상 동작함을 확인. teleop 동작이 기존과 동일한지 확인 (이미 검증된 01_teleoptest 기능 회귀 X).
- 구현 대상: 없음 (검증·정리만)
- 테스트: prod 검증 (Orin 접속 필요)
- 배경: `scripts/deploy_orin.sh` 의 배포 대상 경로가 변경되었으나, 이전 배포로 Orin 머신에 옛 경로 잔존 가능성 있음. rsync 는 새 경로만 동기화하므로 옛 파일 자동 삭제 X.

#### Codex 검증 (비대화형 SSH)

| # | 단계 | 기대 결과 |
|---|---|---|
| 1 | devPC: `bash scripts/deploy_orin.sh` | rsync 정상 종료, `~/smolvla/orin/` 새로 생성/갱신 |
| 2 | Orin: `ls ~/smolvla/` | `orin/` 디렉터리 존재. 옛 잔여물 (`lerobot/`, `scripts/`, `calibration/`, `examples/`, `pyproject.toml`) 식별 |
| 3 | Orin: `ls ~/smolvla/orin/scripts/` | `setup_env.sh`, `run_teleoperate.sh` 존재 |
| 4 | Orin: `ls ~/smolvla/orin/lerobot/policies/smolvla/` | `configuration_smolvla.py` 등 정책 파일 존재 |
| 5 | Orin: `bash -n ~/smolvla/orin/scripts/setup_env.sh` | syntax check 통과 |

#### 개발자 직접 검증 (대화형, 약 20~40 분 소요)

| # | 단계 | 기대 결과 |
|---|---|---|
| 1 | Orin: `deactivate 2>/dev/null \|\| true` (옛 venv 활성 상태면 해제) | 영향 없음 |
| 2 | Orin: 옛 잔여물 삭제 — `rm -rf ~/smolvla/.venv ~/smolvla/lerobot ~/smolvla/scripts ~/smolvla/calibration ~/smolvla/examples` 와 `rm -f ~/smolvla/pyproject.toml ~/smolvla/README.md` (Codex 검증 #2 에서 식별된 항목만) | 옛 파일 모두 제거 |
| 3 | Orin: `ls ~/smolvla/` | `orin/`, `dgx/`(있다면), `docs/`(있다면) 만 남음 |
| 4 | Orin: `bash ~/smolvla/orin/scripts/setup_env.sh` | 새 venv `~/smolvla/orin/.hylion_arm` 생성, PyTorch + lerobot 설치, CUDA 검증 PASS |
| 5 | Orin: `source ~/smolvla/orin/.hylion_arm/bin/activate && python ~/smolvla/orin/examples/tutorial/smolvla/smoke_test.py` | smolVLA 모델 로드 + forward pass 성공 (01_teleoptest TODO-01 동등 검증) |
| 6 | Orin: `bash ~/smolvla/orin/scripts/run_teleoperate.sh --help` | help 출력 정상 (포트 인자 등) — teleop 회귀 검증의 minimal 단계 |

- 제약: TODO-09 완료 후 진행 → 충족.
- 잔여 리스크:
  - 옛 venv 의 LD_LIBRARY_PATH 패치(cusparselt 우회) 가 새 venv 에 다시 적용돼야 함 — `setup_env.sh` 가 알아서 처리하지만 setup 출력에서 확인 필요
  - calibration JSON 파일 (`~/.cache/huggingface/lerobot/calibration/...`) 은 사용자 홈 캐시에 저장되어 있어 본 마이그레이션과 무관 — 그대로 유지됨
  - teleop 회귀 검증을 풀로 하려면 SO-ARM 양 팔 연결 + 물리 조작 필요. 본 TODO 에선 `--help` 출력만 minimal 검증 (calibration 재실행은 불필요)
- **완료 (2026-04-28)**: 전 단계(Codex 5 + 개발자 6) PASS. 주요 우회 이슈: `dpkg` 중단 상태 → `sudo dpkg --configure -a` 후 재실행; `python3-venv` 미설치 → `virtualenv` fallback 동작; `libcusparseLt` 시스템 미설치 → venv activate LD_LIBRARY_PATH 패치 적용; `torchvision` 미설치 → 수동 wheel 설치(`torchvision-0.20.0a0+afc54f7-cp310-cp310-linux_aarch64.whl`). smoke_test.py PASS (`action shape: torch.Size([1, 6])`), teleop `--help` PASS. 새 경로 `~/smolvla/orin/` 확정.

### [x] TODO-10: 배포 환경 세팅 — 스크립트 작성

- 타입: task
- DOD: DGX 에서 학습된 체크포인트가 Orin 으로 반입되어 추론 실행 가능함을 확인하는 절차/스크립트가 정리됨. prod 실 검증은 TODO-10b 에서 별도 진행.
- 구현 대상 (2026-04-28 작성 완료):
  - `scripts/sync_ckpt_dgx_to_orin.sh` — devPC 경유 2-hop 전송 (DGX → devPC 임시 → Orin). `--run` / `--step` / `--dry-run` 인자 지원. 자동 선택 시 DGX 의 가장 최근 run + last 체크포인트. Orin 측 도착 후 safetensors 헤더 minimal 검증
  - `dgx/scripts/save_dummy_checkpoint.sh` — TODO-10b 검증용 dummy 체크포인트 생성 (`lerobot-train --steps=1 --save_checkpoint=true`). smoke_test.sh 와 책임 분리 (smoke_test 는 검증만, save_dummy 는 디스크 저장)
  - `orin/examples/tutorial/smolvla/load_checkpoint_test.py` — 임의 체크포인트 경로 받아 `SmolVLAPolicy.from_pretrained` 로드 + 더미 forward. smoke_test.py 와 형제 (smoke_test 는 환경 검증, load_checkpoint_test 는 호환성 검증)
- 테스트: 없음 (스크립트 작성 단계 — `bash -n` / `python -m py_compile` syntax check 통과. 실 실행 검증은 TODO-10b)
- 제약: TODO-09 완료 후 진행 → 충족. `03_smolvla_test_on_orin` 마일스톤과 일부 겹치므로 중복 회피 — 본 TODO 는 "전송 경로 + 로드 검증 스크립트" 까지로 한정.
- 설계 결정:
  - **전송 경로**: devPC 경유 2-hop (`scripts/sync_ckpt_dgx_to_orin.sh`). 직접 SSH 미사용 — 현재 `~/.ssh/config` 그대로 사용 가능, repo_management 의 sync hub 패턴 일관성, IP 변동 대응 한 곳만
  - **체크포인트 포맷**: PyTorch safetensors 직접 호환 (ONNX/TensorRT 변환 X). 07_biarm_deploy 단계에서 latency 부족 시 `torch.compile` 우선 검토, 그래도 부족하면 별도 TODO 로 ONNX 검토
  - **bf16 호환**: DGX (cu130) 와 Orin (JP 6.0 wheel, cu126) 모두 bf16 지원. 실측 검증은 TODO-10b
- 잔여 리스크 (TODO-10b 점검):
  - lerobot SHA mismatch — DGX editable submodule SHA = Orin curated `orin/lerobot/` SHA 라야 모델 클래스 호환. orin/lerobot/ 트리밍이 SmolVLA policy 일부를 빠뜨렸으면 로드 실패
  - DGX bf16 (cu130 환경) → Orin bf16 (cu126 + JP 6.0 wheel) 의 미세 numerical 차이 가능성 (로드는 OK 여도 출력값 차이)
  - Orin 측 추론 시 `image_features` 키 매핑 — DGX 학습 시 `--rename_map` 사용 여부에 따라 키 이름이 달라질 수 있음 (load_checkpoint_test.py 의 `cfg.image_features` 가 자동 처리하나 실 환경 검증 필요)
- **완료 (2026-04-28)**: 스크립트 3개 작성 완료. `bash -n` / `py_compile` 모두 PASS. 실 검증은 TODO-10b.

### [x] TODO-10b: 배포 환경 세팅 — DGX→Orin 체크포인트 전송 prod 검증

- 타입: test
- DOD: TODO-10 작성 산출물이 실제 동작함을 확인. dummy 체크포인트 생성 → DGX→Orin 전송 → Orin 로드 + forward pass 모두 PASS. bf16/safetensors 호환성 + lerobot SHA 호환성 검증.
- 구현 대상: 없음 (검증·기록만)
- 테스트: prod 검증 (DGX + Orin 양쪽 접속 필요)
- 제약: TODO-09b (DGX 학습 환경 prod 검증) 및 TODO-09c (Orin 마이그레이션 검증) 완료 후 진행

#### Codex 검증 (비대화형 SSH)

| # | 단계 | 기대 결과 |
|---|---|---|
| 1 | devPC: `bash -n scripts/sync_ckpt_dgx_to_orin.sh` | syntax check 통과 |
| 2 | devPC: `bash -n dgx/scripts/save_dummy_checkpoint.sh` | syntax check 통과 |
| 3 | devPC: `python -m py_compile orin/examples/tutorial/smolvla/load_checkpoint_test.py` | syntax check 통과 |
| 4 | devPC: `bash scripts/deploy_dgx.sh` | save_dummy_checkpoint.sh 가 DGX 에 배포됨 (rsync 정상 종료) |
| 5 | devPC: `bash scripts/deploy_orin.sh` | load_checkpoint_test.py 가 Orin 에 배포됨 |
| 6 | DGX: `ssh dgx "ls ~/smolvla/dgx/scripts/"` | `save_dummy_checkpoint.sh` 존재 |
| 7 | Orin: `ssh orin "ls ~/smolvla/orin/examples/tutorial/smolvla/"` | `load_checkpoint_test.py` 존재 |
| 8 | devPC: `bash scripts/sync_ckpt_dgx_to_orin.sh --dry-run` (TODO-10b #1 dummy 체크포인트 생성 후) | dry-run 모드 정상 종료, 전송 대상 파일 목록 출력 |

#### 개발자 직접 검증 (대화형, 약 30~60 분 소요)

| # | 단계 | 기대 결과 |
|---|---|---|
| 1 | DGX: `bash ~/smolvla/dgx/scripts/save_dummy_checkpoint.sh` | preflight PASS + 1 step 학습 + 체크포인트 저장 (`~/smolvla/dgx/outputs/train/dummy_ckpt/checkpoints/000001/pretrained_model/`). 약 5~15분 소요 |
| 2 | DGX: `ssh dgx "ls -la ~/smolvla/dgx/outputs/train/dummy_ckpt/checkpoints/000001/pretrained_model/"` | `config.json`, `train_config.json`, `model.safetensors` (≈ 900 MB) 존재 |
| 3 | devPC: `bash scripts/sync_ckpt_dgx_to_orin.sh --run dummy_ckpt` | DGX → devPC 임시 → Orin 2-hop 전송 정상 종료, Orin 측 safetensors 헤더 검증 PASS |
| 4 | Orin: `ssh orin "ls -la ~/smolvla/orin/checkpoints/dummy_ckpt/000001/"` | safetensors 파일 크기가 DGX 측과 동일 |
| 5 | Orin: `source ~/smolvla/orin/.hylion_arm/bin/activate && python ~/smolvla/orin/examples/tutorial/smolvla/load_checkpoint_test.py --ckpt-path ~/smolvla/orin/checkpoints/dummy_ckpt/000001/` | 4단계 모두 통과: 정책 로드 → config 출력 → forward pass → action shape `(1, 50, *)` 출력. exit code 0. **체크포인트 호환성 검증 PASS** |
| 6 | Orin: 결과 기록 — DGX 학습 PyTorch 버전, Orin 추론 PyTorch 버전, action 출력 dtype, action range | 호환성 결과를 본 TODO 결론으로 정리 |

- 잔여 리스크 (실행 중 점검):
  - dummy_ckpt 1 step 학습은 의미 있는 가중치가 아니라 거의 사전학습 그대로. **수치 검증보다는 "로드/forward 가 에러 없이 돌아가는지" 가 핵심**
  - lerobot SHA mismatch 발생 시 에러: `ImportError`, `KeyError` (state_dict 의 키 불일치). 발생 시 orin/lerobot/ 트리밍 재검토 필요
  - HF Hub 다운로드 (smolvla_base + SmolVLM2 백본) 가 Orin 측에서도 발생할 수 있음 — 첫 실행 시 추가 5~15분
- 후행 액션:
  - 검증 결과로 본 TODO `[x]` 처리
  - 04_leftarmVLA 진입 시 본 sync 스크립트로 실 학습 체크포인트 반입 가능
  - latency 측정은 03_smolvla_test_on_orin 마일스톤에서 별도 진행
- **완료 (2026-04-28)**: 전 단계 PASS (Codex 8 + 개발자 6). 체크포인트 전송: DGX→devPC→Orin 2-hop, `model.safetensors` 906,712,520 bytes byte-exact 일치, 헤더 검증 PASS. Orin 로드: `SmolVLAPolicy.from_pretrained` 성공, forward PASS, action shape `(1, 50, 6)`. 호환성 실측: DGX `torch 2.10.0+cu130` → Orin `torch 2.5.0a0+nv24.08`, policy `bfloat16`, action `float32`, range `[-2.32, 2.64]`. lerobot SHA mismatch 없음, bf16 전송 이상 없음.
  - **`docs/storage/06_dgx_venv_setting.md` 에 §10 "배포 환경 (DGX→Orin 체크포인트 전송)" 절 추가** — TODO-10b 완료 시 작성:
    - 체크포인트 디렉터리 구조 (`outputs/train/<run>/checkpoints/<step>/pretrained_model/`) + 파일 크기 실측치
    - 전송 경로: devPC 경유 2-hop (`scripts/sync_ckpt_dgx_to_orin.sh`) — 절차·인자·dry-run
    - DGX bf16 (cu130) → Orin bf16 (cu126 + JP 6.0 wheel) 호환성 검증 결과 (action shape / dtype / range)
    - lerobot SHA 호환성: DGX editable submodule SHA 와 Orin curated `orin/lerobot/` SHA 매칭 확인
    - 첫 1회 실측치 (전송 시간, Orin 측 forward latency)
    - 04_leftarmVLA 실 학습 진입 시 운영 절차 (사전 dry-run → 본 sync → load_checkpoint_test.py 사후 검증)

### [x] TODO-11: 결정사항 — 자유도 낮추기 가능 여부

- 타입: study
- DOD: smolVLA 입력/출력 차원에서 SO-ARM 6 DOF 를 일부 자유도(예: gripper 단순 binary, wrist_roll 고정) 로 축소하는 변경이 데이터셋·정책·추론 파이프라인 어디까지 영향 주는지 정리. 04_leftarmVLA 진입 전 적용 가능 여부 결론.
- 구현 대상: 없음
- 테스트: 없음
- **결론 (2026-04-27)**: **자유도를 낮추지 않는다.** SO-ARM 6 DOF 를 그대로 유지하여 학습·추론 파이프라인을 구성한다. 이유: 자유도 축소는 사전학습 가중치 일부 무효화 / 데이터셋·정책 양쪽 변경을 동시에 강제하므로 초기 사이클(04_leftarmVLA) 의 변수 수를 늘림. 일단 풀 6 DOF 로 한 사이클 완주 후 성능/리소스 병목이 확인되면 그때 재검토.
- 추후 재검토 트리거:
  - DGX VRAM 부족으로 풀 파인튜닝 불가가 확인된 경우 (TODO-09 1 step 실행 또는 04_leftarmVLA 학습 시도 시)
  - Orin 추론 latency 가 실시간 제어 임계치 초과 시
  - 04_leftarmVLA 또는 06_biarm_VLA 단계에서 학습 수렴이 명확히 실패할 때
- 재검토 항목은 Backlog #3 으로 등록하여 후행 사이클에서 추적한다.

### [x] TODO-12: 결정사항 — 양팔 가능 여부

- 타입: study
- DOD: smolVLA 정책이 양팔(2 × SO-ARM, action 12 DOF + state 12 DOF) 입력을 그대로 수용 가능한지, 아니면 정책 구조 수정/확장이 필요한지 결론. 데이터셋 키 매핑 컨벤션 확정 위치 명시.
- 구현 대상: 없음
- 테스트: 없음
- **결론 (2026-04-27)**: **양팔로 진행 확정.** SmolVLA `max_state_dim=32` / `max_action_dim=32` padding 메커니즘으로 12 DOF 를 정책 구조 수정 없이 그대로 수용 가능 (`docs/lerobot_study/03_smolvla_architecture.md` §A·§E, `modeling_smolvla.py:158-169` 참조).
- 학습 전략: **단일팔에서 양팔로의 전이 학습이 아닌, 최종 데모용 양팔 정책은 양팔 데이터로 처음부터 학습 (06_biarm_VLA).** 04_leftarmVLA 의 단일팔 사이클은 "한 사이클 완주 검증·데모" 가 목적이며 06 의 사전 단계가 아니다.
- 후행 마일스톤 위임 항목:
  - 05_biarm_teleop_on_dgx: 카메라 3대 구성 (손목 좌·우 + 전체 조망, base 미포함) 확정, 12 DOF 데이터셋 키 컨벤션 확정 (`[left_6, right_6]` 단일 키 vs 좌·우 분리 키)
  - 06_biarm_VLA: 카메라 3대 분포가 smolvla_base 사전학습 분포와 다른 점 대응 (S1 표준 파인튜닝 우선, 안 되면 S3 풀 파인튜닝 검토)
  - 07_biarm_deploy: 카메라 3대 + 양팔 SO-ARM USB 구성과 Orin 자원 점검

---

> Backlog → [docs/work_flow/specs/BACKLOG.md](BACKLOG.md) 로 이전 (2026-04-27)
