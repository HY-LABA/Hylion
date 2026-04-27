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

### [ ] TODO-07: 결정사항 — Walking RL 과 병렬학습 가능 여부

- 타입: study
- DOD: DGX Spark 단일 장비에서 Walking RL 학습과 smolVLA 학습이 동시 진행 가능한지 결론(가능 / 부분 가능 / 불가) 과 근거(VRAM · CPU · I/O 점유율 추정) 가 본 스펙에 기록됨. 불가/부분 시 백업(연구실 PC) 활용 시나리오 명시.
- 구현 대상: 없음
- 테스트: TODO-02 실측치 기반 자원 점유율 추정으로 1차 결론. 필요 시 후행 단계(TODO-09 1 step 실행) 에서 nvidia-smi 모니터링으로 재검증.
- 제약: TODO-02 완료 후 진행. **TODO-08(환경관리 결정) 보다 선행되어야 함** — DGX 단독 점유 / 공유 여부에 따라 환경 격리 방식(venv vs conda 격리 vs 컨테이너) 이 달라지기 때문.
- 잔여 리스크: Walking RL 측 환경/일정에 대한 외부 의존 — 별도 트랙 담당자 확인 필요

### [ ] TODO-08: 환경관리 / 버전 호환성 결정

- 타입: task
- DOD: DGX Spark 학습용 Python 환경 관리 방식(venv vs conda vs uv) 과 PyTorch/CUDA/cuDNN 버전 조합이 결정되어 본 스펙에 기록. Orin 추론 환경(`~/smolvla/.venv`, Python 3.10) 과의 학습→추론 호환성(체크포인트 호환, torch 버전 차이 영향) 도 명시.
- 구현 대상: 없음 (결정은 본 스펙에 기록, 실제 설치는 TODO-09)
- 테스트: 없음
- 결정 항목:
  1. Python 버전: DGX 시스템 3.12.3 사용 vs 3.10 별도 설치 (Orin 정합성)
  2. 패키지 매니저: venv / conda / uv 중 선택 (TODO-07 결과에 따라 격리 강도 조정)
  3. PyTorch 버전: DGX GPU 드라이버 580.142 / CUDA 13.0.2 호환 wheel 선정
  4. cuDNN / TensorRT 설치 여부 (학습 단계에서는 cuDNN 만 필수, TensorRT 는 배포 단계 옵션)
  5. lerobot 설치 방식: editable install vs pip install
- 제약: TODO-02·TODO-07 완료 후 진행
- 잔여 리스크:
  - DGX 의 `nvidia/cu13` 계열과 lerobot upstream 의 권장 PyTorch 버전이 어긋날 가능성
  - Orin venv (Python 3.10) 와 DGX (Python 3.12) 사이 체크포인트/직렬화 호환성 — 동일 버전 정렬이 안전

### [ ] TODO-09: 학습 환경 세팅

- 타입: task
- DOD: DGX Spark 에서 lerobot 학습 스크립트가 실행 가능한 상태(스모크: 1 step 학습 통과). 환경 구성이 `dgx/scripts/setup_train_env.sh` (또는 동등한 위치) 로 재현 가능하게 스크립트화됨.
- 구현 대상:
  - `dgx/scripts/setup_train_env.sh` (신규) — TODO-08 결정 기반 설치 스크립트. PyTorch · lerobot · 데이터셋 의존성 · cuDNN(필요 시) 설치
  - `dgx/pyproject.toml` 또는 `requirements-train.txt` (방식 결정 후) — 학습 의존성 고정
- 테스트: prod 검증
  1. setup 스크립트 실행 → 에러 없이 종료
  2. `python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"` → True / DGX GPU 표시
  3. lerobot 학습 엔트리포인트 1 step 실행 (smoke) → loss 출력 확인
- 제약: TODO-08 완료 후 진행. Orin 측 `orin/scripts/setup_env.sh` 의 구조를 참고하되 DGX 용으로 분리(`dgx/`)하여 작성한다 — Orin 환경에 영향 주지 않을 것.
- 잔여 리스크:
  - DGX 디스크 용량 부족 시 사전학습 가중치/데이터셋 캐시 위치 분리 필요 (`HF_HOME`, `LEROBOT_HOME`)
  - Ollama (포트 11434) 등 기존 서비스와 GPU 메모리 경합 → 학습 시 종료 필요 여부 점검

### [ ] TODO-10: 배포 환경 세팅

- 타입: task
- DOD: DGX 에서 학습된 체크포인트가 Orin 으로 반입되어 추론 실행 가능함을 확인하는 절차/스크립트가 정리됨. 최소 1회 실 체크포인트(또는 사전학습 가중치) 로 DGX → Orin 반입 → Orin 에서 정책 로드 성공.
- 구현 대상:
  - `scripts/sync_checkpoint_dgx_to_orin.sh` 등 (위치는 기존 `scripts/` 구조에 맞춰 결정) — rsync 또는 scp 기반 체크포인트 복사 스크립트
- 테스트: prod 검증
  1. DGX 에서 dummy / 사전학습 체크포인트 준비
  2. devPC 또는 DGX → Orin 으로 체크포인트 전송
  3. Orin 에서 lerobot 추론 코드로 체크포인트 로드 → forward pass 성공
- 제약: TODO-09 완료 후 진행. `03_smolvla_test_on_orin` 마일스톤과 일부 겹치므로 중복 작업 회피 — 본 TODO 는 "전송 경로 확정" 까지로 한정한다.
- 잔여 리스크:
  - DGX↔Orin 간 직접 SSH 미설정 시 devPC 경유 2-hop 필요 → 시간/대역폭 손실
  - 체크포인트 포맷(safetensors / pickle) 과 Orin venv torch 버전 호환

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
