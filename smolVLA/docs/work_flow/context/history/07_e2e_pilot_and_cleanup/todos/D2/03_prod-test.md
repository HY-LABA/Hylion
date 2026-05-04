# TODO-D2 — Prod Test

> 작성: 2026-05-03 | prod-test-runner | cycle: 1

## Verdict

**`NEEDS_USER_VERIFICATION`**

AUTO_LOCAL + SSH_AUTO 자동 검증 전 항목 PASS. DOD 항목 5건 중 1건 (smoke_test — T1 HF Hub 선결 의존) 이 사용자 실물 검증 필요.

---

## 배포 대상

- dgx (training.py 단일 파일 변경 — `dgx/interactive_cli/flows/training.py`)

## 배포 결과

- 명령: `bash scripts/deploy_dgx.sh`
- 결과: 성공
- 로그 요약:
  - `dgx/` rsync: 1,086 bytes sent (speedup 154x) — training.py 포함 incremental 동기화
  - `docs/reference/lerobot/` rsync: 26,848 bytes sent — cameras/opencv 갱신
  - Category B 영역 변경 없음 (dgx/lerobot/ 미변경) → 자율 deploy 해당

---

## 자동 비대화형 검증 결과

### A. devPC AUTO_LOCAL

| 검증 | 명령 | 결과 |
|---|---|---|
| py_compile | `python3 -m py_compile dgx/interactive_cli/flows/training.py` | PASS |
| ruff lint | `python3 -m ruff check dgx/interactive_cli/flows/training.py` | All checks passed |
| 구조 assertion | `python3 -c "import flows.training as t; assert list(t.CKPT_CASES.keys()) == ['1','2','3','4']..."` | ALL ASSERTIONS PASS |
| SCENARIOS memory_gb 정합 | smoke=20/s1=35/s3=65/lora=28 | ALL PASS (preflight_check.sh L24-27 일치) |
| ckpt 4건 분기 코드 정합 | 소스 검사: none/dummy/fine-tune-step/fine-tune-last 반환 경로 확인 | ALL PASS |
| fine-tune-last is_resume 분기 | `is_resume = (ckpt_case == "fine-tune-last")` → `--resume` 플래그 생성 확인 | PASS |
| G-4 분기 정합 | `mode.py._prompt_transition_to_train()` → `run_training_flow_with_dataset(dataset_name=dataset_name)` | PASS |
| smoke consent gate | `_smoke_consent_gate()` 내 HF 다운로드 경고 문구 존재 확인 | PASS |
| lerobot upstream 인용 정합 | `train.py L49 resume: bool = False` / `L84 checkpoint_path` / `L94-111 elif self.resume` 실제 Read 검증 | ALL PASS |

### B. DGX SSH_AUTO

| 검증 | 명령 | 결과 |
|---|---|---|
| SSH 연결 | `ssh dgx "echo SSH_ALIVE"` | PASS |
| DGX py_compile | `ssh dgx "python3 -m py_compile ~/smolvla/dgx/interactive_cli/flows/training.py"` | PASS |
| DGX 구조 assertion | venv 활성화 후 구조 assertion 6건 | DGX ALL ASSERTIONS PASS |
| preflight [1/5] venv·HF_HOME·CUDA_VISIBLE_DEVICES | `bash preflight_check.sh smoke` | OK |
| preflight [2/5] RAM (121 GiB, 가용 100 GiB, 필요 30 GiB) | | OK |
| preflight [3/5] Walking RL | | INFO (미실행) |
| preflight [4/5] Ollama GPU 점유 | | OK (미점유) |
| preflight [5/5] 디스크 (3314 GiB 가용) | | OK |
| preflight 종합 | `preflight PASS — 학습 진행 가능` | PASS (exit 0) |
| save_dummy_checkpoint 산출물 존재 확인 | `ls ~/smolvla/dgx/outputs/train/dummy_ckpt/checkpoints/000001/pretrained_model/` | PASS — 7개 파일 확인 (model.safetensors 865MB 포함) |
| lerobot-train entrypoint | `which lerobot-train` | `/home/laba/smolvla/dgx/.arm_finetune/bin/lerobot-train` 존재 |

### C. save_dummy_checkpoint 산출물 상세

```
~/smolvla/dgx/outputs/train/dummy_ckpt/checkpoints/000001/pretrained_model/
  config.json                                         (2.5 KB)
  model.safetensors                                   (865 MB)
  policy_postprocessor.json                           (660 B)
  policy_postprocessor_step_0_unnormalizer_processor.safetensors (3.7 KB)
  policy_preprocessor.json                            (2.0 KB)
  policy_preprocessor_step_5_normalizer_processor.safetensors    (3.7 KB)
  train_config.json                                   (6.8 KB)
```

생성 일시: 2026-04-28 (이전 사이클 실행 확인). 7개 파일 정상.

---

## DOD 자동 부합

| DOD 항목 | 자동 검증 | 결과 |
|---|---|---|
| 1. preflight (env·CUDA·driver·메모리·디스크) PASS | SSH_AUTO (preflight_check.sh smoke) | ✅ |
| 2. smoke_test 5~15분 PASS | SSH_AUTO (T1 HF Hub 선결 의존 — svla_so100_pickplace 미캐시) | → verification_queue (T1 완료 후) |
| 3. save_dummy_checkpoint 1회 PASS + 산출물 확인 | SSH_AUTO (기존 산출물 7개 파일 확인) | ✅ |
| 4. ckpt 케이스 4건 코드 분기 정합 | AUTO_LOCAL (소스·assertion 검사) | ✅ |
| 5. G-4 (수집→학습 전환) 단발 종료 검증 | AUTO_LOCAL (mode.py 소스 검사) | ✅ |

---

## 사용자 실물 검증 필요 사항 (verification_queue 추가됨)

### 1. smoke_test — T1 완료 후 (SSH_AUTO)

- 조건: T1 `svla_so100_pickplace` HF Hub 다운로드 PASS 후
- 검증 환경 레벨: SSH_AUTO (사용자 DGX SSH 비대화형 실행)
- 검증 명령:
  ```bash
  ssh dgx "source ~/smolvla/dgx/.arm_finetune/bin/activate && \
      export HF_HOME=~/smolvla/.hf_cache && export CUDA_VISIBLE_DEVICES=0 && \
      bash ~/smolvla/dgx/scripts/smoke_test.sh"
  ```
- 기대 결과: exit 0 + "smoke test 결과" 출력
- 이유: `svla_so100_pickplace` 데이터셋 HF 캐시 미존재 (~/smolvla/.hf_cache/hub/ 에 lerobot 데이터셋 없음). T1 HF Hub 다운로드 완료 후 캐시 확보 시 자율 SSH_AUTO 가능.

---

## CLAUDE.md 준수

- Category B 영역 (dgx/lerobot/) 변경: 없음 → 자율 deploy 해당
- Category A 영역 변경: 없음
- Category D 명령 시도: 없음
- lerobot upstream 인용 정합: train.py L49·L84·L94-111 실제 Read 후 코드 구현과 정확 대응 확인
- smoke_test 동의 게이트: 자율성 정책 (>5분·~100MB) 에 따라 동의 게이트 존재 확인 — 사용자 동의 J(위임) 인지
- save_dummy_checkpoint (>5분 추정): 이전 실행 산출물 확인 — 재실행 불필요
