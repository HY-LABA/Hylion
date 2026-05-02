# TODO-X3 — Prod Test

> 작성: 2026-05-02 13:05 | prod-test-runner | cycle: 1

## Verdict

**`NEEDS_USER_VERIFICATION`**

자동 정적 검증 전체 통과 + DGX 배포 성공 + DGX 원격 검증 통과.
DOD 의 "실 인터페이스 진입 → 학습 flow 완주" 는 사용자 실물 실행 필요 (smoke_test 5~15분, svla_so100_pickplace ~100MB 다운로드).

---

## 배포 대상

DGX (`laba@spark-8434` alias `dgx`)

---

## 배포 결과

- 명령: `bash scripts/deploy_dgx.sh` (devPC 에서 실행)
- 결과: 성공
- 배포 파일:
  - `interactive_cli/README.md`
  - `interactive_cli/main.sh`
  - `interactive_cli/configs/node.yaml`
  - `interactive_cli/flows/__init__.py`
  - `interactive_cli/flows/entry.py`
  - `interactive_cli/flows/env_check.py`
  - `interactive_cli/flows/training.py`
- rsync 전송: 13,346 bytes sent (incremental, 7개 파일 신규)
- 배포 후 DGX 확인: `~/smolvla/dgx/interactive_cli/` 존재 확인 (타임스탬프 2026-05-02 12:50)

---

## 자동 비대화형 검증 결과

### 자율 1: 정적 검증 (devPC)

| 검증 | 명령 | 결과 |
|---|---|---|
| env_check.py 컴파일 | `python3 -m py_compile .../env_check.py` | OK |
| training.py 컴파일 | `python3 -m py_compile .../training.py` | OK |
| entry.py 컴파일 | `python3 -m py_compile .../entry.py` | OK |
| main.sh 구문 | `bash -n .../main.sh` | OK |
| entry.py --help | `python3 entry.py --help` | ImportError 없음, argparse 정상 |
| ruff lint (3파일) | `python3 -m ruff check flows/*.py` | All checks passed (F401·F541 0건 — X2 patch 적용 완료) |

### 자율 2: 정적 분석 (devPC import 검증)

| 검증 항목 | 결과 |
|---|---|
| `_smoke_consent_gate()` 함수 존재 | ✅ — Y/n prompt + `default_yes=True` 정상 |
| CKPT_CASES 케이스 1·2·3·4 모두 포함 | ✅ — keys: `['1', '2', '3', '4']` |
| `_show_ckpt_management()` 자동 감지 패턴 없음 | ✅ — `glob`/`listdir`/`auto`/`detect` 미사용 |
| `_run_real_training()` lerobot-train 인자 매핑 | ✅ — `save_dummy_checkpoint.sh` line 56~70 인용 정합 |
| SCENARIOS keys | ✅ — `['smoke', 's1', 's3', 'lora']` |

### 자율 3: deploy_dgx.sh 정적 검토 + DGX SSH read-only

**deploy_dgx.sh 분석:**
- sync 대상: `dgx/` 전체 → `dgx:/home/laba/smolvla/dgx/`
- exclude 목록: `.arm_finetune`, `outputs`, `__pycache__`, `*.pyc`, `*.egg-info`
- `dgx/interactive_cli/` 는 exclude 비해당 → 자동 포함 확인
- Category B 영향: `scripts/deploy_dgx.sh` 내용 미변경. 변경 파일 = `dgx/interactive_cli/` 신규 (Category B 외) → 자율 배포 가능

**DGX SSH read-only 결과:**

| 항목 | 명령 | 결과 |
|---|---|---|
| interactive_cli 미배포 확인 (배포 전) | `ls ~/smolvla/dgx/interactive_cli/` | not exist (정상 — 최초 배포 대상) |
| 04 산출물 존재 확인 | `ls .../preflight_check.sh smoke_test.sh save_dummy_checkpoint.sh` | 3개 모두 존재 |
| 디스크 여유 | `df -h ~/smolvla/dgx` | 3.3T 가용 / 3.7T (7% 사용) — 충분 |
| 메모리 | `free -g` | 총 121GB, 여유 69GB, 가용 114GB — smoke (20GB) 충분 |
| Walking RL·Ollama 점유 | `ps aux grep walking\|ollama` | ollama 서비스만 실행 (메모리 35MB 수준), GPU 점유 없음 |
| GPU 상태 | `nvidia-smi` | NVIDIA GB10, P8 (idle), 메모리 표시 지원 안 됨 (GB10 특성) |

**Ollama 서비스 영향 평가:** Ollama 는 메모리 ~35MB (서비스 대기), GPU 점유 없음 (idle 상태). preflight_check.sh 의 메모리 임계치 (smoke 20GB) 대비 가용 메모리 114GB — 영향 없음.

### 자율 4: DGX 원격 검증 (배포 후)

| 검증 | 명령 | 결과 |
|---|---|---|
| env_check.py 원격 컴파일 | `ssh dgx python3 -m py_compile env_check.py` | OK |
| training.py 원격 컴파일 | `ssh dgx python3 -m py_compile training.py` | OK |
| entry.py 원격 컴파일 | `ssh dgx python3 -m py_compile entry.py` | OK |
| main.sh 원격 구문 | `ssh dgx bash -n main.sh` | OK |
| entry.py --help 원격 | `ssh dgx python3 entry.py --help` | argparse 정상, ImportError 없음 |
| training.py 구조 원격 검증 | `ssh dgx python3 -c import training; print CKPT_CASES...` | CKPT_CASES `['1','2','3','4']`, SCENARIOS `['smoke','s1','s3','lora']` |

---

## DOD 자동 부합

| DOD 항목 | 자동 검증 가능 | 결과 |
|---|---|---|
| DGX SSH 에서 실 인터페이스 진입 (main.sh 실행) | no — 대화형 실행 필요 | → verification_queue |
| 학습 flow 완주 (flow 0~5) | no — 대화형 + smoke 실행 | → verification_queue |
| smoke 동의 게이트 Y/n 정상 동작 | 정적 확인 가능 (함수 구조) | ✅ 정적 확인 — 실 동작은 verification_queue |
| CKPT_CASES 케이스 1~4 출력 | 정적 확인 | ✅ |
| svla_so100_pickplace 다운로드 + 학습 실행 (04 X3 통합) | no — 실 실행 필요 | → verification_queue |
| HF Hub push 실 검증 (04 T1 통합) | no — 실 실행 필요 | → verification_queue |
| 시연장 ckpt 전송 분기 (04 T2 통합) | 정적 확인 가능 (케이스 안내 출력) | ✅ 정적 — 실 전송은 사용자 선택 사항 |

---

## 사용자 실물 검증 필요 사항 (verification_queue 추가됨)

1. `bash scripts/deploy_dgx.sh` 실행 — **자율 완료** (본 사이클에서 실행·배포 성공)
2. DGX SSH → `bash ~/smolvla/dgx/interactive_cli/main.sh` (또는 VSCode remote-ssh → DGX 터미널)
3. flow 0: 진입 확인 (DGX 노드 표시, 확인 스킵)
4. flow 1: 장치 선택 — DGX 선택
5. flow 2: env_check (preflight_check.sh 결과 확인)
6. flow 3: 시나리오 선택 — smoke 권장 (메모리 20GB, 현재 가용 114GB)
7. flow 4: 데이터셋 선택 — smoke 기본값 `lerobot/svla_so100_pickplace` 채택
8. flow 5: smoke test 동의 게이트 Y 입력 → smoke_test.sh 실행
   - 소요 시간: 5~15분
   - 최초 실행 시 svla_so100_pickplace ~100MB 이상 다운로드
9. smoke_test.sh 완료 후 ckpt 케이스 목록 표시 확인 (케이스 1~4 출력)
10. (선택) 04 T1 검증: HF Hub push 실 검증 — 데이터셋 다운로드 분기 확인
11. (선택) 04 T2 검증: ckpt 케이스 중 하나 선택 → 전송 안내 출력 확인

---

## 04 BACKLOG 통합 처리

| BACKLOG 항목 | 본 X3 흡수 여부 | 처리 |
|---|---|---|
| #7 X3 (smoke_test 5~15분 + svla_so100_pickplace 100MB+) | ✅ 흡수 | verification_queue 항목 7~9 에 통합 |
| #7 T1 (HF Hub push 실 검증) | ✅ 흡수 | verification_queue 항목 10 (선택) |
| #7 T2 (시연장 ckpt 전송 분기) | ✅ 흡수 | verification_queue 항목 11 (선택) |

---

## CLAUDE.md 준수

| 항목 | 결과 |
|---|---|
| Category B 영역 변경된 deploy 여부 | 변경 파일 = `dgx/interactive_cli/` 신규 (Category B 외) → 자율 실행 |
| deploy_dgx.sh 스크립트 내용 직접 Read 확인 | ✅ — GPU 학습 트리거 없음, 순수 rsync |
| DGX 환경 문서 교차 확인 | ✅ — `06_dgx_venv_setting.md` 불필요 (venv 재생성 없음) |
| Category D 명령 미사용 | ✅ — rm -rf / sudo 등 미사용 |
| Category A 영역 수정 없음 | ✅ — docs/reference/, .claude/ 미변경 |
| 자율 영역만 실행 | ✅ — smoke test 실행은 사용자에게 위임 |
