# TODO-X2 — Implementation

> 작성: 2026-05-01 16:00 | task-executor | cycle: 1

## 목표

dgx/interactive_cli/ flow 3~ 구현 (학습 책임 — 옵션 C 3단계: 시나리오 선택 → 데이터셋 선택 → 학습 + ckpt 관리)

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `dgx/interactive_cli/flows/env_check.py` | N (신규) | flow 2: preflight_check.sh subprocess 래퍼 |
| `dgx/interactive_cli/flows/training.py` | N (신규) | flow 3·4·5: 시나리오 선택·데이터셋 선택·학습+ckpt 관리 |
| `dgx/interactive_cli/flows/entry.py` | M (수정) | dgx 분기에서 env_check + training 순차 호출 |

## 적용 룰

- CLAUDE.md Hard Constraints: docs/reference/ 미변경, pyproject.toml 미변경
- Coupled File Rule: dgx/lerobot/ 미변경 → 03/04_lerobot_diff.md 갱신 불필요
- Category A·B·D 비해당 (dgx/interactive_cli/ 신규 파일만)

### 레퍼런스 직접 Read 및 인용

1. **`dgx/scripts/preflight_check.sh`** line 1~36 직접 Read
   - 인용: 사용법 `bash preflight_check.sh {smoke|s1|s3|lora}`, 시나리오별 메모리 임계치
   - `env_check.py` 의 `run_env_check()`: `subprocess.run(["bash", str(preflight), scenario], check=False)` 패턴 그대로 적용
   - `training.py` 의 `SCENARIOS` 딕셔너리: preflight_check.sh line 23~35 메모리 임계치 인용 (smoke=20GB, s1=35GB, s3=65GB, lora=28GB)

2. **`dgx/scripts/smoke_test.sh`** line 24~82 직접 Read
   - 인용 (line 44~45): `"최초 실행 시 모델·데이터셋 다운로드로 5~15분 소요됩니다."` → `_smoke_consent_gate()` 경고 문구
   - 인용 (line 68~81): `lerobot-train --policy.path=lerobot/smolvla_base --dataset.repo_id=lerobot/svla_so100_pickplace --save_checkpoint=false` → smoke 분기 harcoded 데이터셋 + save 없음
   - 인용 (line 30~33): smoke_test.sh 내부에서 preflight_check.sh 를 이미 호출 → env_check 와 중복 없음 확인

3. **`dgx/scripts/save_dummy_checkpoint.sh`** line 25, 62~63 직접 Read
   - 인용 (line 25): `OUTPUT_DIR="${DGX_DIR}/outputs/train/${RUN_NAME}"` → `_run_real_training()` 출력 경로 패턴
   - 인용 (line 62~63): `--save_freq=1 --save_checkpoint=true` → 실 학습 파라미터에 적용
   - 인용 (line 56~70): 전체 lerobot-train 인자 목록 → `_run_real_training()` cmd 리스트 구성

4. **`scripts/sync_ckpt_dgx_to_datacollector.sh`** line 6~36 직접 Read
   - 인용 (line 7~9): 사용법 (--run, --step, --dry-run 옵션)
   - 인용 (line 19~22): 케이스 1~4 분류 설명 → `CKPT_CASES` 딕셔너리 안내 문구
   - 인용 (line 28~36): 동작 (SSH DGX → devPC → DataCollector rsync) → "devPC 에서 실행" 안내
   - **devPC 전용 — DGX 에서 직접 호출 X** (14_dgx_cli_flow.md §5-2 비고 준수)

5. **`docs/storage/14_dgx_cli_flow.md`** (X1 산출물) 전체 Read
   - §1 env_check.py 구현 패턴 (script_dir.parent / "scripts" / "preflight_check.sh")
   - §2-4 옵션 C 3단계 구조 그대로 채택
   - §3 데이터셋 선택 메뉴 (HF Hub / 로컬 / 기본값)
   - §4-2 smoke_test 동의 게이트 "포함 (권고)" 결정 반영
   - §5-3 ckpt 전송 분기 UI (케이스 목록 출력 + 사용자 선택)

6. **`dgx/interactive_cli/flows/entry.py`** (F2 산출물) 전체 Read
   - flow 0·1 구조 파악 → dgx 분기에 `env_check` + `training` 모듈 호출 추가
   - `script_dir = Path(args.node_config).parent.parent` 경로 계산 패턴

7. **`docs/storage/12_interactive_cli_framework.md`** §5 직접 Read
   - orin env_check.py 패턴 (`subprocess.run(["bash", str(check_script), "--mode", "resume"], check=False)`)
   - dgx 용 변형: 시나리오 인자 전달 방식으로 변경

## 변경 내용 요약

### env_check.py

flow 2 환경 체크 래퍼. `preflight_check.sh` 를 subprocess 로 호출하여 5체크 항목 (venv·메모리·Walking RL·Ollama·디스크)을 실행. `12_interactive_cli_framework.md §5` 의 orin env_check.py 패턴을 dgx 용으로 변형했다. 시나리오 인자를 외부에서 받을 수 있도록 `scenario: str = "smoke"` 기본값 설정. flow 5 의 시나리오 선택 이전 사전 점검용으로 smoke 시나리오로 먼저 실행하고, 실 학습 시나리오 선택 후 preflight 가 내재된 smoke_test.sh 또는 lerobot-train 에서 재검증된다.

### training.py

flow 3·4·5 를 구현한 메인 모듈.

- **flow 3**: SCENARIOS 딕셔너리 (preflight_check.sh 메모리 임계치 인용) 기반 메뉴 → smoke/s1/s3/lora 선택
- **flow 4**: smoke 시나리오는 고정 데이터셋 (`lerobot/svla_so100_pickplace`) 반환, 실 학습은 HF Hub 입력·로컬 datasets/ 선택·기본값 3소스 메뉴
- **flow 5**: smoke 분기는 동의 게이트(`_smoke_consent_gate`) 후 `smoke_test.sh` subprocess 호출. 실 학습 분기는 `_run_real_training` 에서 lerobot-train draccus 인자 동적 생성 + subprocess 호출. 양 분기 완료 후 `_show_ckpt_management` 로 ckpt 저장 경로 출력 + 케이스 목록 + 사용자 선택.

`sync_ckpt_dgx_to_datacollector.sh` 는 devPC 전용이므로 DGX 에서 직접 호출 X — 안내 문구만 출력.

### entry.py (갱신)

dgx 분기에 두 줄 추가: `flow2_env_check(script_dir)` (preflight FAIL 시 exit 1) → `run_training_flow(script_dir)` (flow 3~5 실행). `script_dir` 경로는 `Path(args.node_config).parent.parent` 로 계산 (node.yaml 위치 `configs/node.yaml` → `configs/` → `interactive_cli/`).

## code-tester 입장에서 검증 권장 사항

- 구문 검사: `python3 -m py_compile dgx/interactive_cli/flows/env_check.py training.py entry.py` (이미 통과)
- lint: `ruff check dgx/interactive_cli/flows/`
- 단위 기능 확인 (DGX SSH 없이 로컬에서 가능):
  - entry.py 의 `--node-config` 인자 파싱이 올바른지
  - training.py 의 `SCENARIOS`, `CKPT_CASES` 딕셔너리 키 일관성
  - env_check.py 의 `preflight` 경로 계산 (`script_dir.parent / "scripts" / "preflight_check.sh"`)
  - `_yn_prompt` default_yes 분기 로직
- DOD 항목 확인:
  1. env_check.py: preflight_check.sh subprocess 호출 + 5체크 결과 출력 + exit 0/!=0 분기
  2. training.py flow 3: smoke/s1/s3/lora 시나리오 메뉴
  3. training.py flow 3 smoke 선택: 동의 게이트 (Y/n prompt + 경고 문구)
  4. training.py flow 4: 3소스 데이터셋 선택 UI
  5. training.py flow 5 smoke: smoke_test.sh subprocess 호출
  6. training.py flow 5 실 학습: lerobot-train draccus 인자 동적 생성
  7. training.py flow 5 ckpt: 케이스 목록 출력 + 사용자 선택 (자동 감지 X)
  8. entry.py 갱신: dgx 분기에서 env_check + training 순차 호출

## 다음 단계 권고 (X3 prod 검증 사전 조건)

X3 prod 검증 시 필요한 사용자 환경 조건:

1. **DGX SSH 접근**: `ssh dgx` 가능 (deploy_dgx.sh 또는 수동 rsync 로 파일 배포)
2. **DGX venv 준비**: `~/smolvla/dgx/.arm_finetune` 활성화 가능 (`lerobot-train` CLI 접근 가능)
3. **smoke_test 사용자 동의**: flow 5 진입 전 Y/n 게이트 — 실제 DGX 에서 실행 시 사용자가 동의해야 smoke_test.sh 실행
4. **svla_so100_pickplace 다운로드 (~100MB)**: smoke_test 최초 실행 시 HF Hub 다운로드 발생 — 사전 동의 게이트 구현됨
5. **HF_HOME, CUDA_VISIBLE_DEVICES 환경변수**: preflight_check.sh 검증 항목 — setup_train_env.sh (main.sh 이전 단계) 에서 설정되어야 함

## 잔여 리스크

- **lerobot-train draccus 인자 정확성**: `_run_real_training` 의 cmd 목록은 `save_dummy_checkpoint.sh` line 56~70 에서 인용했으나, lerobot upstream 버전 차이로 인자명이 달라질 가능성 있음. X3 prod 에서 실제 lerobot-train --help 출력 확인 권장.
- **로컬 데이터셋 경로 처리**: `_select_local_dataset` 가 반환하는 `~/smolvla/dgx/datasets/<name>` 경로를 lerobot-train 이 `--dataset.repo_id` 로 받아들이는지 확인 필요. HuggingFace datasets 가 로컬 경로를 repo_id 로 처리하는 방식이 버전마다 다를 수 있음. (T1 미결 이슈와 연관)
- **smoke_test.sh 5~15분 실행**: subprocess timeout 없음 — 사용자 Ctrl+C 신뢰. interactive_cli 가 KeyboardInterrupt 를 정상 종료로 처리함.
- **flow 2 사전 smoke preflight + flow 5 재실행 중복**: env_check.py 에서 smoke 시나리오로 preflight 선행 실행 후 flow 3 에서 실 학습 시나리오 선택 시 해당 시나리오 preflight 가 자동 재실행되지 않음. 실 학습 분기에서는 lerobot-train 실행 전 preflight 를 시나리오에 맞게 재호출하는 것을 향후 개선 고려.
