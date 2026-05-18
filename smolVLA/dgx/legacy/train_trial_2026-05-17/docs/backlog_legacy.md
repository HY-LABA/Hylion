# DGX 학습 관련 backlog (legacy — 2026-05-17 시점 snapshot)

> **목적**: DGX 가 학습 노드였던 시기 (2026-05-15 ~ 2026-05-17) 에 누적된 *학습 관련* backlog 항목들의 보존.
> **출처**: 원본 `dgx/docs/finetune/backlog.md` 에서 추출 (2026-05-18 이관).
> **상태**: DGX 학습 *잠정 중단* 으로 본 항목들은 *현역 backlog 아님*. DGX 학습 재시도 시점에 재참고할 *역사 자료*.
> **현역 backlog**: `dgx/docs/finetune/backlog.md` (수집 관련만 유지).

---

## 우선순위 표기

| 표기 | 의미 |
|---|---|
| 🔥 | High — 다음 학습 / 데이터 수집 세션 진입 전 처리 권장 |
| ⚙️ | Medium — 워크플로우 안정화 후 처리 |
| 💡 | Low — 개선 / 정리 / nice-to-have |

---

## 환경 / 설정

### 🔥 [ ] setup_finetune_env.sh 에 `peft` extra 추가

- **발견**: 2026-05-11, training.md §2-1 LoRA 학습 첫 실행 시 `ModuleNotFoundError: No module named 'peft'`
- **트리거**: 현재 `setup_finetune_env.sh` 의 lerobot 설치가 `lerobot[smolvla]` 만 포함. PEFT (LoRA) 사용 시 필요한 `lerobot[peft]` extra 누락
- **조치**: 스크립트의 lerobot 설치 라인을 `pip install -e ${LEROBOT_SRC}[smolvla,peft]` 로 변경 (또는 별도 라인 추가)
- **영향**: venv 재구축 시 PEFT 자동 설치되어 LoRA 학습 즉시 가능. 현재 venv 에서는 이미 수동 설치 완료 (`pip install -e ~/smolvla/docs/reference/lerobot[peft]`)
- **검증**: 새 venv 만든 뒤 `python -c "import peft; print(peft.__version__)"` 가 동작
- **legacy 처리 사유**: DGX 학습 잠정 중단으로 *peft 의존 불필요* (lerobot-record 등 수집 명령은 peft 임포트 X 확인). DGX 학습 재시도 시점에만 재참고.

### 🔥 [ ] run_train.py preflight — DGX UMA system memory 가드레일 + dataloader 누수 대응

- **발견**: 2026-05-15, leftarm_v2 2A 시도 1, step 368 에서 global OOM (system-wide, CONSTRAINT_NONE). 학습 프로세스 외에 VSCode server 2개도 같이 OOM-killed
- **트리거 (wandb 증거 반영)**: ~5 GB/min 속도로 system memory 가 선형 누적. wandb 의 main process memory 는 3.4GB 안정 → **누수의 정체는 DataLoader workers 8개 + shmem + 동시 점유 프로세스의 합** (main 프로세스 외부). UMA 128GB 단일 풀이라 GPU 요청까지 같이 막힘 (NVRM Out of memory 가 oom-killer 전에 등장)
- **조치**:
  1. run_train.py 시작 시 `MemAvailable` 검사 — < 80 GB 이면 경고, < 60 GB 이면 `--force` 없이 거부
  2. **권장 cleanup 명령 출력** (`pkill -f rerun` + IDE 창 최소화 안내). cleanup 후 다시 `free -h` 출력해 사용자가 효과 확인 가능
  3. `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` 기본 export (우선순위는 낮음 — main 프로세스 안 자랐던 게 wandb 로 확인됨)
  4. train_config.yaml 의 `num_workers` default 를 8 → 4 로 낮추고 주석에 wandb 증거 링크
  5. (검증 가치) video backend 선택지 — torchcodec 시도, 또는 dataset codec h264_nvenc 통일 후 비교
- **영향**: 다음 학습 시도 시 사전에 위험 인지 + 재발 차단. training_log.md "시도 1" 사고 entry 참조
- **연관**: training_log.md, dgx/docs/finetune/leftarm_v1/training.md §troubleshoot ("SIGKILL → OOM killer" 항목)
- **legacy 처리 사유**: DGX 학습 잠정 중단으로 *조치 적용 불필요*. DGX 학습 재시도 시점에 *재참고 가치*.

---

## 학습

### ⚙️ [ ] dgx/runs/05_leftarm/ 디렉토리 + train.sh 셸 스크립트화

- **발견**: 2026-05-11, [dgx/runs/README.md](../runs/README.md) 에 따르면 마일스톤 진입 시 채우는 구조
- **트리거**: 현재 학습 명령이 training.md 내 코드블록에 있어 매번 복붙. `runs/05_leftarm/train.sh` 로 셸 스크립트화하면 1줄 실행 가능
- **조치**: §5 leftarmVLA 마일스톤 진입 시 ([dgx/runs/README.md](../runs/README.md) 참조 — 구조 가이드 있음):
  - `dgx/runs/05_leftarm/train.sh` — 현재 training.md §2-1 명령 셸 스크립트화 (LoRA all-linear r=16)
  - `dgx/runs/05_leftarm/README.md` — 학습 가이드 (학습 실행 / 모니터링 / 결과 해석)
  - `dgx/runs/05_leftarm/notes.md` — exploratory 결과 / 이슈 / 재실험 메모
- **영향**: 학습 명령 / 인자 재사용성 ↑, 실수 가능성 ↓
- **legacy 처리 사유**: DGX 학습 잠정 중단으로 *runs/ 구조 자체 도입 안 함*. prof_computer 의 `run_train.py` + config 패턴이 대체.

### ⚙️ [ ] LoRA adapter inference 명령 검증

- **발견**: 2026-05-11, training.md §5-2 의 inference 명령은 full-FT 체크포인트 가정 (`--policy.path="${OUTPUT_DIR}/checkpoints/last/pretrained_model"`)
- **트리거**: LoRA 학습 결과는 adapter 만 저장됨 (base model 가중치 없음). full-FT 와 inference 호출 방식이 다를 수 있음
- **조치**:
  1. 첫 LoRA 학습 완료 후 `checkpoints/last/` 디렉토리 구조 확인 — LoRA adapter 파일 (예: `adapter_config.json`, `adapter_model.safetensors`) 가 어떻게 저장되는지
  2. lerobot 가 LoRA adapter 자동 로딩 지원하는지 (peft_model.from_pretrained 경로 등) 확인
  3. training.md §5-2 inference 명령을 LoRA 케이스로 갱신
- **영향**: exploratory 학습 후 실기 검증 단계에서 막힘 방지
- **legacy 처리 사유**: M1.5 prof_computer 학습 (2026-05-17) 에서 LoRA adapter 저장·로딩 *실제 검증 완료* (`prof_computer/docs/leftarm_v2/learning_log.md` §M1.5). HF Hub push 도 동작 확인됨. 본 backlog 항목 *해소된 셈* 이나 *DGX 측 training.md 갱신* 은 미진행 (DGX 학습 중단으로 의미 X).

### 🔥 [ ] 학습 시 시스템 메모리 100% 회피 — num_workers 가이드라인

- **발견**: 2026-05-11, LoRA all-linear 학습 중 System Memory Utilization 이 step 100 이후 100% 도달 → UI lag → 강제 중지
- **트리거**: `num_workers=8` + 큰 video dataset (40 ep, 21K frames) + 다른 프로세스 (rerun ×4, claude code ×21) 합산
- **조치**: training.md §2-1 명령의 `num_workers` 기본값을 `4` 로 낮추고, 학습 직전 권장 명령에 다음 추가:
  ```bash
  pkill -f "rerun_sdk/rerun_cli/rerun" 2>/dev/null || true
  ```
  + training.md §3 (모니터링) 에 `System Memory Utilization` 항목 명시 — 95% 초과 시 즉시 중단 권장
- **영향**: 학습 안정성. 100% 메모리 도달 시 학습 자체는 진행되지만 시스템 UI 응답성 손실
- **legacy 처리 사유**: prof_computer 환경 (분리 VRAM 24GB) 에서는 본 메커니즘 자체 발생 X (M1.5 system RAM 누수 0.18 GB/h 확인). DGX 학습 재시도 시점에만 재참고.

### 💡 [ ] wandb run 비교를 위한 일관된 명명 규칙

- **발견**: 2026-05-11, exploratory 학습이 여러 번 시도되면서 wandb 에 정렬되지 않은 run 들이 누적
- **조치**: `job_name` 패턴을 `<dataset>_<stage>_<rank>_<date>` 형식으로 표준화 (예: `leftarm_v1_lora-all-r16_2026-05-11`). LoRA / S1 / S3 비교 시 정렬 / 필터링 용이
- **영향**: 다음 차수 / 비교 실험 시 wandb dashboard 가독성 ↑
- **legacy 처리 사유**: prof_computer 의 `run_train.py` 가 *이미 patterned run_name* 적용 중 (`leftarm_v2_2a_pc_<ts>`). 본 backlog 의 의도 *prof_computer 측에서 자연 달성*.

---

## 추론 / 평가

### ⚙️ [ ] 평가 dataset 명명 규칙 + Hub push 정책

- **발견**: training.md §5-2 에서 `leftarm_v1_eval_$(date +%Y%m%d)` 형식으로 evaluation dataset 생성 예시
- **트리거**: eval dataset 이 학습 dataset 과 별도로 Hub 에 쌓이면 repo 가 많아짐. push_to_hub 여부 / 명명 규칙 정리 필요
- **조치**:
  - eval 은 보통 `push_to_hub=false` 권장 (로컬에만 저장)
  - 필요 시 `<train_dataset>_eval_<date>` 명명
  - 또는 별도 organization / branch 로 분리
- **영향**: HF Hub repo 관리 깔끔
- **legacy 처리 사유**: 학습 사이클이 prof_computer 로 이관되어 본 backlog 가 *prof_computer 측에서 재고해야 할* 영역. 현재 prof_computer 평가는 시연장 정성 평가 (`prof_computer/docs/leftarm_v2/orin_*_eval.md`) 만이라 Hub push 미적용 — 본 backlog *prof_computer 의 *추론 평가 정책* 으로 재정의 가능*.
