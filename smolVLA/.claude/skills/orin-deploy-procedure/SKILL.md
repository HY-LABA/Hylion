---
name: orin-deploy-procedure
description: orin·dgx 배포 절차 + 비대화형 검증 명령 시퀀스. prod-test-runner 가 배포·검증 단계에서 활용. 자율성 정책에 따른 자동 vs 동의 작업 분류 포함. TRIGGER when 워커가 prod 환경 배포·검증을 수행할 때.
---

# Orin / DGX Deploy Procedure

본 스킬은 prod-test-runner 가 prod 환경 (Orin·DGX) 에 배포 + 비대화형 검증을 수행할 때 따라야 할 절차.

## 배포 스크립트

| 대상 | 스크립트 | 동작 |
|---|---|---|
| Orin | `bash scripts/deploy_orin.sh` | rsync 로 `smolVLA/orin/` → `laba@orin:/home/laba/smolvla/orin/` |
| DGX | `bash scripts/deploy_dgx.sh` | rsync 로 `smolVLA/dgx/` → `dgx:<remote_path>` |

⚠️ deploy_*.sh 자체는 Hard Constraints Category B 영역. 스크립트 내용 변경 시 사용자 동의 필수.

## rsync 배포 시 사용자 환경 파일 보호 원칙 (07 reflection #6 도출)

배포 스크립트 (`deploy_orin.sh`, `deploy_dgx.sh`) 의 rsync 실행 시 다음 파일·디렉터리는 **반드시 exclude** — 사용자 환경 의존 파일 (시연장 셋업·동기화된 ckpt 등) 을 devPC repo 가 덮어쓰지 않도록 보호:

| 경로 | 이유 |
|---|---|
| `orin/checkpoints/` | sync_ckpt_dgx_to_orin.sh 가 동기화한 ckpt. devPC 미존재 → rsync `--delete` 로 Orin 측 삭제됨 (07 BACKLOG #8 사고) |
| `orin/config/*.json` | 시연장 포트·카메라 설정. 사용자 환경마다 다름 (07 W4 정책 문서 — `docs/storage/15_orin_config_policy.md`) |
| `dgx/interactive_cli/configs/*.json` | DGX 포트·카메라 설정. deploy 마다 placeholder 로 덮어쓰면 precheck 결과 손실 (07 BACKLOG #15 → D13 Part B 로 fix, 본 원칙으로 일반화) |

exclude 추가 패턴:

```bash
rsync ... \
  --exclude 'checkpoints/' \
  --exclude 'config/*.json' \
  --exclude 'interactive_cli/configs/*.json' \
  ...
```

**적용 의무**:
- 신규 deploy 스크립트 작성 시 task-executor 가 위 exclude 목록 확인 의무
- code-tester 가 deploy 스크립트 수정 본 검토 시 위 exclude 미포함 발견 → Recommended 항목으로 지적
- 신규 사용자 환경 의존 파일 추가 시 본 표 + 해당 deploy 스크립트 동시 갱신 (Coupled File 패턴)

## SSH 설정

- `~/.ssh/config` 에 `orin`, `dgx` alias 등록 가정
- devPC ↔ Orin SSH 연결 — `docs/storage/04_devnetwork.md` 참조

## 자율성 정책 (CLAUDE.md § prod-test-runner 자율성)

| 작업 | 정책 | 사유 |
|---|---|---|
| ssh orin/dgx read-only (cat·ls·df·ps·nvidia-smi) | ✅ 자율 | 안전, 환경 변경 없음 |
| ssh 로 pytest·ruff·mypy | ✅ 자율 | 검증 명령 |
| ssh 로 짧은 python -c (<5초 추정) | ✅ 자율 | 검증 |
| `deploy_orin.sh` (Category B 외 변경) | ✅ 자율 | 일반 배포 |
| `deploy_dgx.sh` (Category B 외 변경) | ✅ 자율 | 일반 배포 |
| Category B 영역 변경된 deploy | ⚠️ 동의 | 의존성·옵션B 변경 → prod 영향 큼 |
| 가상환경 재생성·패키지 업그레이드 | ⚠️ 동의 | 환경 깨짐 위험 |
| 큰 다운로드 (>100MB) | ⚠️ 동의 | 시간·디스크 |
| 긴 실행 (>5분 추정) | ⚠️ 동의 | 사용자 인지 |

→ 자율 영역은 즉시 실행. 동의 영역은 작업 전 orchestrator 에 보고하여 사용자 답 받기.

### 자율성 분류 시 직접 확인 의무

신규·미확인 스크립트의 자율성 분류 시 **반드시 스크립트 내용을 Read 하여 확인** (추측 분류 X):

1. **실 실행 여부**: 스크립트가 GPU 학습 / 패키지 설치 / 데이터 다운로드 를 트리거하는가?
   - 포함 시 → 자율 불가 (동의 필요 또는 NEEDS_USER_VERIFICATION)
   - 스크립트 이름만으로 판단 X (예: `save_dummy_checkpoint.sh` 가 "dummy" 라는 이름이라도 GPU 학습 1 step 트리거 — 04 X3 cycle 1 사례)
2. **환경 의존 경로**: 하드코딩된 경로 (예: `~/.cache/huggingface/`) 가 실제 환경과 일치하는가?
   - 불일치 의심 시 → `docs/storage/` 의 해당 환경 문서 (예: `06_dgx_venv_setting.md`) 직접 확인
   - 04 X3 cycle 1 의 HF cache 경로 오류 (`~/.cache/huggingface/hub/` vs 실제 `~/smolvla/.hf_cache/hub/`) 답습 X
3. **기존 환경 문서 교차 확인**: DGX/Orin 의 실제 경로·설정은 `docs/storage/` 에 기록된 실측치 우선

→ 추측 기반 자율성 분류 시 code-tester 가 Critical 마킹. 확인 불가 시 NEEDS_USER_VERIFICATION 또는 CONSTRAINT_AMBIGUITY 누적.

## SSH 명령 패턴 — 자율 (예시)

### 환경 정보

```bash
ssh orin "cat /etc/os-release"
ssh orin "df -h"
ssh orin "free -h"
ssh orin "nvidia-smi"
ssh orin "pip list | grep -E 'torch|lerobot'"
ssh orin "which lerobot-find-port"  # entrypoint 등록 확인
```

### 단위 테스트·lint

```bash
ssh orin "cd ~/smolvla/orin && pytest tests/test_<XX>.py -v"
ssh orin "cd ~/smolvla/orin && ruff check ."
ssh orin "cd ~/smolvla/orin && mypy ."
```

### 짧은 추론 검증

```bash
ssh orin "cd ~/smolvla/orin && python -c 'from lerobot.policies.smolvla import SmolVLAPolicy; print(SmolVLAPolicy)'"
```

## SSH 명령 패턴 — 동의 필요 (예시)

### 가상환경 재생성

```bash
# 동의 받기 전엔 실행 X
ssh orin "cd ~/smolvla/orin && bash scripts/setup_env.sh"
```

### 학습 트리거 (DGX, 긴 실행)

```bash
# 동의 필수
ssh dgx "cd ~/smolvla/dgx && python train_smolvla.py ..."
```

### 데이터셋 다운로드

```bash
# 사이즈 추정 후 >100MB 면 동의
ssh orin "cd ~/smolvla/orin && hf download <dataset>"
```

## 검증 명령 시퀀스 (todo 종류별 가이드)

### Smoke Test (배포 직후 기본)

```bash
ssh orin "bash ~/smolvla/orin/tests/smoke_test.sh"
```

### Smolvla 추론 latency 측정

```bash
ssh orin "cd ~/smolvla/orin && python tests/measure_latency.py"
```

### Hardware Diagnose (모터·인코더)

```bash
ssh orin "cd ~/smolvla/orin && python tests/diagnose_motor_encoder.py"
```

### Camera 정상 동작

```bash
ssh orin "cd ~/smolvla/orin && python tests/inference_baseline.py"
```

각 todo 별 검증 권장 명령은 `context/todos/<XX>/02_code-test.md` 의 "검증 권장 사항" 참조.

## 사용자 실물 검증 필요 패턴 식별

다음은 자동 검증 X — verification_queue 에 항목 추가:

| 검증 항목 | 사용자 실물 절차 |
|---|---|
| 카메라 캡처 | 사용자가 RealSense·OpenCV 카메라 캡처 결과 육안 확인 |
| SO-ARM 동작 | leader 기울여 follower 추종 동작 관찰 |
| 시각적 추론 | smolvla 추론 결과 (joint 각도) 가 기대 동작과 일치하는지 |
| 성능 정성 평가 | FPS·레이턴시 만족도 (정량 OK 라도 사용자 체감 다를 수 있음) |
| 시연장 미러링 | 시연장 환경과 DataCollector 환경 정확히 일치하는지 |

→ verification_queue.md 양식 (CLAUDE.md § 가시화 레이어 / context/README.md 참조).

## Verdict 결정 가이드 (보수적)

| Verdict | 조건 |
|---|---|
| `AUTOMATED_PASS` | 자동 검증 100% 통과 + 사용자 실물 항목 0개 + DOD 자동으로 모두 충족 |
| `NEEDS_USER_VERIFICATION` | 자동 통과 + 사용자 실물 항목 ≥ 1 |
| `FAIL` | 배포 실패, 자동 검증 실패, DOD 자동 미충족, 또는 애매한 경우 |

⚠️ **애매하면 보수적으로** — `NEEDS_USER_VERIFICATION` 또는 `FAIL`. `AUTOMATED_PASS` 는 확신할 때만.

## 실패 처리

- 배포 실패 또는 자동 검증 실패 → ANOMALIES `PROD_TEST_FAIL` 추가
- 자동 재시도 (max 2 cycle, code-tester 와 동일)
- 그래도 FAIL → orchestrator 에 보고, todo 실패 마킹

## ANOMALY 누적 가이드

| 상황 | TYPE |
|---|---|
| 배포 실패 또는 자동 검증 실패 | `PROD_TEST_FAIL` |
| 자율성 룰 모호 (예: 5분 실행 추정 미묘) | `CONSTRAINT_AMBIGUITY` |
| Phase 3 사용자 검증 후 롤백 | `DEPLOY_ROLLBACK` (orchestrator 가 추가) |

## Reference

- `/CLAUDE.md` § prod-test-runner 자율성 (정책 정의)
- `scripts/deploy_orin.sh`, `scripts/deploy_dgx.sh`
- `docs/storage/04_devnetwork.md` (devPC ↔ Orin SSH)
- `docs/storage/05_orin_venv_setting.md` (Orin venv 환경)
