# 07_e2e_pilot_and_cleanup
<!-- Claude Code + 개발자 협업 작성 -->

> 목표: **팔만 시연장에 달면 즉시 데이터수집 → 학습 → 추론 한 사이클을 돌릴 수 있도록 모든 도구·스크립트·문서 완비** + devPC/SSH 자율 가능 영역에서 한 사이클 (svla_so100_pickplace 짧은 fine-tune → DGX→Orin ckpt 전송 → Orin 더미 추론) 실 실행 검증 + datacollector 잔재 활성 영역 0 건 정리. 본 사이클은 시연장 이동 X.
> 환경: orin (JetPack 6.2, `~/smolvla/orin/.hylion_arm`) + dgx (Ubuntu 22.04, Python 3.12.3, `~/smolvla/dgx/.arm_finetune`) + devPC. 3-노드.
> 접근: orin·dgx 모두 VSCode remote-ssh + SSH 비대화형 prod 검증
> 코드 경로: `orin/`, `dgx/`, `scripts/`, `docs/work_flow/specs/`. 신규 디렉터리 생성 X.
> 하드웨어: 본 사이클 SO-ARM·카메라 직결 X. 도구·스크립트만 정비. 실 검증은 BACKLOG (PHYS_REQUIRED).
> 작성: 2026-05-03

---

## 본 마일스톤의 위치

본 spec 은 **08_leftarmVLA 진입 직전 e2e 파이프라인 검증 + 운영 정비** 사이클. 06 wrap 시 PHYS_REQUIRED 로 BACKLOG 이관된 V1·V2·V3 의 자율 가능 부분 + 누적 BACKLOG 의 우선순위 항목 + datacollector 잔재 정리를 흡수.

- 본 사이클 삽입으로 기존 `07_leftarmVLA` → 08, 08~10 → 09~11 시프트
- **종착점**: 시연장 이동 시 `dgx/interactive_cli/main.sh` → 수집 → 학습 → `sync_ckpt_dgx_to_orin.sh` → `orin/interactive_cli/main.sh` → hil_inference 한 줄 흐름이 검증된 도구 위에서 즉시 가능

### 차기 사이클 (08_leftarmVLA) 과의 차이
| | 07 (이번) | 08 leftarmVLA |
|---|---|---|
| 하드웨어 | SO-ARM 단일/페어 그대로 | 토르소 부착 양팔 + 카메라 3 대 |
| 학습 데이터 | 공개 `svla_so100_pickplace` (검증용) | 시연장 직접 수집 데이터 |
| 학습 step | 2,000 (파이프라인 검증용) | 50,000~100,000 (정식 fine-tune) |
| 추론 | Orin 더미 obs forward (1 회) | Orin SO-ARM 직결 hil_inference (정성 평가) |
| 시연장 이동 | X | O |
| 본질 | *도구 검증* | *모델 검증* |

---

## 사용자 결정 사항 (Phase 1 합의)

| # | 결정 항목 | 결과 |
|---|---|---|
| A | spec 이름·시프트 | `07_e2e_pilot_and_cleanup`. 기존 07~10 → 08~11 |
| B | E 그룹 학습 깊이 | SO-ARM 단일/페어 그대로. 토르소·정식 학습은 08 위임. 이번은 *파이프라인 검증* + *interactive-cli 동작 검증* |
| C | BACKLOG 흡수 범위 | 옵션 C (최대) — 도구·운영 정비까지. 시연장 PHYS_REQUIRED 항목은 BACKLOG 유지 |
| D | 시연장 이동 | 본 사이클 X. 도구만 완비 |
| E | `.gitignore` datacollector 패턴 제거 | L6·L10 2 줄 제거 (Category B 동의) |
| F | 학습 step | `--steps=2000 --save_freq=1000` (예상 1.5~3 시간, ckpt 2 회 저장) |
| G | HF Hub 차단 fallback | (a) 작업 보류 → 다른 네트워크 재시도 |
| H | LD_LIBRARY_PATH 패치 방향 | wrapper 스크립트 + settings.json 화이트리스트 — 비대화형 검증 시 권한 prompt 안 뜨도록 |
| I | Category A 자동화 패턴 | 06 wrap 시 적용된 것 그대로 — settings.json hook matcher 임시 비활성화 → 메인 적용 → 복원 |
| J | 진행 모드 | 5 그룹 (P→D→T→O→W) + 게이트 3 회 (D·T·O 분기 종료마다 사용자 `/verify-result`). W 자율 |

---

## 본 사이클 진행 모드

워크플로우 정책 변형 X — Phase 2 wave 의존성 + Phase 3 게이트 분리만으로 사용자 의도 구현.

### Phase 2 wave 의존성

```
[Wave 1] P (5 todo, 자율)
    ↓
[Wave 2] D (3 todo, 자율) ─────→ Phase 3 게이트 1
    ↓
[Wave 3] T (3 todo, 자율) ─────→ Phase 3 게이트 2
    ↓
[Wave 4] O (5 todo, 자율) ─────→ Phase 3 게이트 3
    ↓
[Wave 5] W (5 todo, 자율, 모두 완료 후 wrap)
```

각 wave 의 다음 wave 진입은 **이전 wave 의 모든 verdict PASS 가 자동 보장** (D MAJOR 미해결 시 T 시작 X). Phase 2 종료 후 Phase 3 진입.

### Phase 3 게이트 3 회

`verification_queue.md` 가 D / T / O 3 그룹으로 명시 분리. 사용자가 그룹별 실검증:

- 게이트 1: D 그룹 검증 → `/verify-result "D 분기 통과/실패 + 사유"`
- 게이트 2: T 그룹 검증 → `/verify-result "T 분기 통과/실패 + 사유"`
- 게이트 3: O 그룹 검증 → `/verify-result "O 분기 통과/실패 + 사유"`
- 모두 통과 → `/wrap-spec`

게이트별 PHYS_REQUIRED 부분 (SO-ARM 직결 절차) 은 *도구 정합* 만 통과 조건. 실 SO-ARM 검증은 BACKLOG 유지 (시연장 이동 시).

---

## Todo

> 그룹: P=Prep, D=DGX interactive-cli, T=DGX 학습 사이클, O=Orin interactive-cli + 추론, W=Wrap-up
> 진행: P 모두 병렬 → D 모두 병렬 → 게이트 1 → T 순차 (T1→T2→T3) → 게이트 2 → O 순차 → 게이트 3 → W 모두 병렬 → /wrap-spec

### [그룹 P — Cleanup·시프트 prep]

#### [x] TODO-P1: scripts/dev-connect.sh datacollector 라인 제거

**자동화 완료 (2026-05-03)**: L4 제거 PASS (bash -n + grep 잔재 0건), 3줄 축소, orin/dgx 라인 보존.

- 타입: task
- DOD: `scripts/dev-connect.sh` L4 (`code --remote ssh-remote+datacollector /home/smallgaint`) 제거. 4 줄 → 3 줄.
- 구현 대상: `scripts/dev-connect.sh`
- 테스트: code-tester `bash -n` PASS + 잔재 grep 0
- 제약: 사용자 `~/.ssh/config` 의 `Host datacollector` alias 검토는 사용자 환경 의존 — spec 외 정보 보고만
- 잔여 리스크: —

#### [x] TODO-P2: .gitignore datacollector 패턴 제거 (Category B)

**자동화 완료 (2026-05-03)**: grep 잔재 0건, L6·L10 + orphan comment block 제거 (5줄), 파일 24줄 정합.

- 타입: task
- DOD: L6 `datacollector/.hylion_collector/`, L10 `datacollector/data/` 2 줄 제거. 사용자 동의 (결정 E) 받음.
- 구현 대상: `.gitignore`
- 테스트: code-tester diff + 잔재 grep
- 제약: Category B (.gitignore 패턴 변경) — 사용자 동의 완료
- 잔여 리스크: —

#### [x] TODO-P3: arm_2week_plan.md 07 시프트 + 신규 항목

**자동화 완료 (2026-05-03)**: 마일스톤 번호 unique (06~11), 신규 07 항목 7건, 시프트 주석 누적, 06 결정 이력 14건 보존.

- 타입: task
- DOD:
  - 신규 `[ ] 07_e2e_pilot_and_cleanup` 항목 추가 (06 다음 위치)
  - 기존 07~10 → 08~11 시프트 (06 패턴 따라). 시프트 주석 갱신
  - 04·05·06 의 의도된 history 참조 (예: legacy 이관 사유 라인) 은 보존
- 구현 대상: `arm_2week_plan.md`
- 테스트: 시프트 표·주석 일관성 검토
- 제약: 06 결정 이력 보존
- 잔여 리스크: —

#### [x] TODO-P4: docs/work_flow/specs/README.md 시프트 갱신

**자동화 완료 (2026-05-03)**: 표 행 11개 (01~11), 07 bold+활성, 06 history, 08~11 구 번호 괄호, 시프트 주석 2줄 병렬.

- 타입: task
- DOD: 활성 spec 번호 표 (L107~122) 갱신:
  - 06 → history
  - 07 e2e_pilot_and_cleanup → **활성**
  - 기존 07 leftarmVLA → 08
  - 08~10 → 09~11
- 구현 대상: `docs/work_flow/specs/README.md`
- 테스트: 표 일관성 + 시프트 주석 추가
- 제약: —
- 잔여 리스크: —

#### [x] TODO-P5: 활성 영역 datacollector 잔재 grep 종합

**자동화 완료 (2026-05-03)**: 활성 영역 grep 잔재 0건. 남은 매치 전수 분류 — 모두 의도된 이식 이력/정정/운영종료 주석. dgx/README.md R#1 의미 재작성, training.py L284 R#2 현 워크플로우 반영 안내.

- 타입: both
- DOD: `orin/`·`dgx/`·`docs/lerobot_study/`·`scripts/`·`pyproject.toml`·`Makefile` 등 활성 영역 grep `datacollector|smallgaint` 잔재 0 건. 발견 시 모두 제거 또는 history 참조 명시.
- 구현 대상: 발견된 잔재 파일들
- 테스트: code-tester `grep -rIn -E "datacollector|smallgaint" --exclude-dir={legacy,history,.git,docs/storage/legacy,docs/work_flow/context/history}` 결과 0 건
- 제약: `docs/storage/legacy/`·`docs/work_flow/context/history/`·`arm_2week_plan.md` 의 06 시프트 주석 등 의도된 history 참조는 제외
- 잔여 리스크: arm_2week_plan.md 의 의도된 history 참조와 활성 잔재 구별 — code-tester 가 사용자 검토 가능한 형태로 보고

---

### [그룹 D — DGX interactive-cli 검증 + Phase 3 게이트 1]

#### [x] TODO-D1: dgx/interactive_cli/ 수집 mode SSH_AUTO 검증 + 도구 정비 (06 V2 흡수)

**자동화 완료, Phase 3 대기 (2026-05-04)**: AUTO_LOCAL py_compile 8/8 + ruff PASS. SSH_AUTO DGX flow 0~2 fallback PASS, BACKLOG #14 None-safe 원천 차단 확인. PHYS_REQUIRED 4건 → 07 #9 게이트 4 BACKLOG.

- 타입: both
- DOD:
  - SSH_AUTO 부분 PASS: flow 0 (entry), flow 1 (장치 선택 dgx), flow 2 (env_check 7 단계 — SO-ARM 직결 부분은 도구 정합 검증만, fallback 동작 PASS)
  - flow 3~7 (mode 분기 → teleop·data_kind·record·transfer) — devPC 정적 검증 (py_compile·ruff·bash -n)
  - PHYS_REQUIRED 부분 (SO-ARM 직결 calibrate·record) — 스크립트 정합만 검증, 실 검증은 verification_queue.md 의 D 그룹에 "PHYS_REQUIRED, 시연장 이동 시" 마킹
  - 04 BACKLOG #14 (env_check.py NoneType — `port_handler.openPort()` 결과 검사 후 None-safe 처리) 진단·수정 시도 (devPC 코드 패치 분만)
- 구현 대상: `dgx/interactive_cli/flows/{entry,env_check,mode,teleop,data_kind,record,transfer}.py` 정합 + 필요 시 패치
- 테스트: prod-test-runner ssh dgx 비대화형 (flow 0~2 + py_compile flow 3~7)
- 제약: PHYS_REQUIRED 부분 BACKLOG 유지
- 잔여 리스크: SO-ARM 직결 없는 환경에서 env_check.py fallback 처리 적정성

#### [x] TODO-D2: dgx/interactive_cli/ 학습 mode 회귀 검증 (06 V3 + 05 X3 통합)

**자동화 완료, Phase 3 대기 (2026-05-04)**: py_compile PASS, 구조 assertion 6건 PASS, ckpt 4건 분기 PASS, G-4 PASS, save_dummy 7파일 865MB 확인. smoke_test 는 T1 완료 후 SSH_AUTO 자율 가능. 05 X3·06 V3 자연 흡수.

- 타입: test
- DOD:
  - preflight (env·CUDA·driver·메모리·디스크) PASS
  - smoke_test 5~15 분 (DGX 가용 시간) PASS
  - save_dummy_checkpoint 1 회 PASS
  - ckpt 케이스 4 건 동작 검증 (none / dummy / 실 fine-tune step / fine-tune last) — 단 *실 fine-tune* 케이스는 T2 산출물 의존이므로 D2 시점엔 *코드 분기 정합* 만 검증
  - G-4 (수집 → 학습 자동 전환 prompt) 단발 종료 검증
- 구현 대상: 검증 위주. 코드 패치 시 `dgx/interactive_cli/flows/training.py`
- 테스트: prod-test-runner ssh dgx
- 제약: HF Hub 의존 부분 (svla_so100_pickplace 다운로드) 은 T1 결과 의존 — D2 에선 보류 가능
- 잔여 리스크: 학교 WiFi 의존, T1 fallback 결정 의존

#### [x] TODO-D3: dgx 5-step 하드웨어 검증 도구 정비 (06 V1)

**자동화 완료, Phase 3 대기 (2026-05-04)**: bash -n PASS, 5-step 함수 5건 확인. DGX SSH Step 1·2 PASS, Step 3~5 FAIL 안내 정상 (SO-ARM 미연결). PHYS_REQUIRED → 07 #9 BACKLOG.

- 타입: task
- DOD: USB·dialout·v4l2·find-port·find-cameras·`check_hardware.sh` 5-step 도구 자체 정합 정적 검증 + 시연장 이동 시 즉시 사용 가능 보장. 실 SO-ARM 검증은 BACKLOG (PHYS_REQUIRED).
- 구현 대상: `dgx/scripts/check_hardware.sh` + 관련 도구
- 테스트: code-tester `bash -n` + shellcheck + 정적 grep
- 제약: PHYS_REQUIRED 부분 BACKLOG
- 잔여 리스크: —

> **게이트 1 — D 그룹 종료 후 사용자 `/verify-result "D 분기 통과/실패"`**

---

### [그룹 T — DGX 학습 사이클 검증 + Phase 3 게이트 2]

#### [x] TODO-T1: svla_so100_pickplace HF Hub 다운로드 prod 검증

**자동화 완료 (2026-05-04)**: hf CLI 9/9 파일 다운로드 PASS (16초), 캐시 449MB, LeRobotDataset num_frames=19631 num_episodes=50 camera_keys=[top wrist] fps=30. 학교 WiFi 차단 미발생. T2 dispatch 가능.

- 타입: test
- DOD:
  - DGX 측 `huggingface-cli download lerobot/svla_so100_pickplace` 또는 `from datasets import load_dataset("lerobot/svla_so100_pickplace")` 시도
  - 성공: 캐시 경로 + 크기 보고
  - 실패 (학교 WiFi 차단): 차단 사유 보고 + 사용자 결정 G-(a) 트리거 → spec 일시 보류, 다른 네트워크 재개
- 구현 대상: 검증 명령. 별도 스크립트 X (직접 실행)
- 테스트: prod-test-runner ssh dgx
- 제약: 학교 WiFi 차단 시 spec 일시 보류
- 잔여 리스크: HF Hub timeout, 디스크 공간 (DGX 3.3 TB 충분)

#### [x] TODO-T2: DGX 짧은 fine-tune 1 회 완주 (--steps=2000 --save_freq=1000)

**자동화 완료, Phase 3 대기 (2026-05-04)**: 백그라운드 실행 후 step 2000 완주 확인 PASS (PID 462216 → 정상 종료). step 50·100 loss 정상. checkpoints/{001000,002000,last}/ 3개 모두 생성 확인. throughput ~1.5~2.0 step/s. Ollama GPU 점유 없음 확인 (02 BACKLOG #5 흡수).

- 타입: test
- DOD:
  - lerobot train 명령 실행 (DGX 권장값):
    ```
    lerobot-train \
      --policy.path=lerobot/smolvla_base \
      --dataset.repo_id=lerobot/svla_so100_pickplace \
      --steps=2000 --save_freq=1000 --batch_size=8 \
      --output_dir=~/smolvla/dgx/outputs/train/<run>/
    ```
  - 산출물: `~/smolvla/dgx/outputs/train/<run>/checkpoints/{001000, 002000, last}/` 모두 존재
  - throughput·loss·gradient norm 기록 (WandB 또는 stdout)
  - **02 BACKLOG #5 자연 흡수**: ollama.service 학습 전 중단 절차 — fine-tune 진입 전 사전 체크 + 절차 문서화 (`docs/storage/06_dgx_venv_setting.md` 또는 `dgx/interactive_cli/flows/training.py` preflight)
- 구현 대상: 실 학습 명령 + ollama 사전 체크 추가
- 테스트: prod-test-runner ssh dgx (1.5~3 시간 추정)
- 제약: T1 의존 (HF Hub PASS 후), DGX 가용 시간
- 잔여 리스크: GB10 throughput·메모리 변동, Walking RL 동시 실행 영향

#### [x] TODO-T3: scripts/sync_ckpt_dgx_to_orin.sh 실 실행 검증 + 06 BACKLOG #4 갱신

**자동화 완료 (2026-05-04)**: dry-run PASS + 실 실행 PASS (DGX→devPC→Orin 906MB, 7파일). Orin `/home/laba/smolvla/orin/checkpoints/07_pilot_2k/002000/` 확인. safetensors 헤더 8 byte OK. 06 BACKLOG #4 "완료" 마킹 확인. verdict: AUTOMATED_PASS — 사용자 검증 미요.

- 타입: test
- DOD:
  - dry-run 1 회 PASS
  - 실 실행: T2 산출물 (`002000/pretrained_model/`) → Orin (`~/smolvla/orin/checkpoints/<run>/002000/`) 전송 PASS
  - safetensors 헤더 8 byte 검증 PASS
  - 06 BACKLOG #4 → "완료 (06 사이클 중 작성, 07 T3 검증, 2026-05-XX)" 마킹
- 구현 대상: `scripts/sync_ckpt_dgx_to_orin.sh` 정합 + 필요 시 패치 + `docs/work_flow/specs/BACKLOG.md` 갱신
- 테스트: prod-test-runner devPC ssh DGX·Orin
- 제약: T2 의존
- 잔여 리스크: devPC ↔ DGX/Orin 네트워크, 디스크 공간

> **게이트 2 — T 그룹 종료 후 사용자 `/verify-result "T 분기 통과/실패"`**

---

### [그룹 O — Orin interactive-cli + 추론 + Phase 3 게이트 3]

#### [x] TODO-O1: orin/interactive_cli/ flow 0~5 SSH_AUTO 검증 (05 O3 흡수)

**자동화 완료, Phase 3 대기 (2026-05-04)**: deploy PASS, venv/cusparseLt PASS, menu walkthrough flow 0~2 정상, inference.py import PASS. PHYS_REQUIRED 3건 → 07 #9 BACKLOG. 05 BACKLOG #2 완료 마킹.

- 타입: both
- DOD:
  - flow 0 (entry), flow 1 (장치 선택 orin), flow 2 (env_check) PASS
  - flow 3~5 (mode·ckpt 선택·hil_inference 분기) — SSH 자율 가능 부분 PASS (코드 분기 정합)
  - hil_inference 50-step 실 SO-ARM 부분은 BACKLOG (PHYS_REQUIRED) — verification_queue 마킹
  - 05 BACKLOG #2 → "완료 (07 O1 흡수, 2026-05-XX)" 마킹
- 구현 대상: `orin/interactive_cli/flows/*.py`
- 테스트: prod-test-runner ssh orin
- 제약: PHYS_REQUIRED 부분 BACKLOG
- 잔여 리스크: —

#### [x] TODO-O2: orin/scripts/run_python.sh wrapper + settings.json 화이트리스트 (03 BACKLOG #14)

**자동화 완료 (2026-05-03)**: run_python.sh 신규 (bash -n PASS, 100755). deny-only 모델 전환으로 settings.json 추가 화이트리스트 redundant — 미변경. SSH 실검증 PASS (torch.cuda.is_available()=True, cuSPARSELt ImportError X). 03 BACKLOG #14 완료 마킹.

- 타입: task
- DOD:
  - `orin/scripts/run_python.sh` 신규 — 내부 `source ~/smolvla/orin/.hylion_arm/bin/activate && exec python "$@"`
  - `.claude/settings.json` `permissions.allow` 에 wrapper 호출 패턴 화이트리스트 추가 (Category A — 메인 + 사용자 승인 패턴 I, hook matcher 임시 비활성화)
  - 검증: `ssh orin "~/smolvla/orin/scripts/run_python.sh -c 'import torch; print(torch.cuda.is_available())'"` PASS — `LD_LIBRARY_PATH` 자동 적용으로 cuSPARSELt ImportError X
  - 03 BACKLOG #14 → "완료 (07 O2, wrapper + 화이트리스트, 2026-05-XX)" 마킹
- 구현 대상: `orin/scripts/run_python.sh` (신규), `.claude/settings.json` (Category A)
- 테스트: prod-test-runner ssh orin
- 제약: settings.json 변경은 메인 직접 + 사용자 승인 (Category A 패턴 I)
- 잔여 리스크: 다른 venv (`.cu_test` 등) 사용 시 wrapper 분기 필요 — 본 사이클은 `.hylion_arm` 단일 venv 가정

#### [x] TODO-O3: orin/scripts/setup_env.sh 정비 (02 BACKLOG #7·#8)

**자동화 완료 (2026-05-03)**: bash -n PASS. SMOLVLA_ROOT 기반 wheel 자동 설치 경로 정정 (02 #7), dpkg pre-flight 체크 + 안내 추가 (02 #8). 경로 시뮬 PASS. 02 BACKLOG #7·#8 완료 마킹.

- 타입: task
- DOD:
  - 02 BACKLOG #7: torchvision wheel (`docs/storage/others/torchvision-0.20.0a0+afc54f7-cp310-cp310-linux_aarch64.whl`) 자동 설치 step 추가 (현재 수동 안내만)
  - 02 BACKLOG #8: 앞단 dpkg 상태 체크 + 중단 시 안내 (`sudo dpkg --configure -a` 권고 출력)
  - 두 BACKLOG 항목 → "완료 (07 O3, 2026-05-XX)" 마킹
- 구현 대상: `orin/scripts/setup_env.sh` (Category B — coupled file rule)
- 테스트: code-tester `bash -n` + dry-run. 실 셋업 검증은 새 환경에서만 (BACKLOG 유지 가능)
- 제약: Category B (setup_env.sh 변경) — spec 합의로 한 번 작성 OK, code-tester MAJOR 시 자동 재시도 X
- 잔여 리스크: torchvision wheel hash 미검증 (현 wheel 그대로 사용)

#### [x] TODO-O4: orin/inference/hil_inference.py 카메라 인덱스/wrist flip 도구 정비 (03 BACKLOG #15·#16)

**자동화 완료, Phase 3 대기 (2026-05-04)**: py_compile + ruff PASS, --cameras 기본값 None → 자동 발견 fallback, README 사전 단계 + wrist flip 섹션 추가. 미연결 graceful 처리 PASS. PHYS_REQUIRED 1건 → 07 #9 BACKLOG. 03 BACKLOG #15·#16 완료 마킹.

- 타입: task
- DOD:
  - argparse 기본값 또는 README 에 "1. `lerobot-find-cameras opencv` 사전 발견 / 2. wrist 플립 필요 시 `--flip-cameras wrist`" 사전 단계 명시
  - 가능 시 hil_inference.py 진입 시 카메라 자동 발견 fallback 추가
  - 03 BACKLOG #15·#16 → "완료 (07 O4, 2026-05-XX)" 마킹
- 구현 대상: `orin/inference/hil_inference.py` + 인근 README
- 테스트: code-tester argparse 검증. 실 카메라 검증은 PHYS_REQUIRED → BACKLOG
- 제약: —
- 잔여 리스크: 사전학습 카메라 분포와의 의미 매칭은 03 BACKLOG #11 (08 트리거)

#### [x] TODO-O5: Orin 사전학습 ckpt 로드 + 더미 obs 추론

**자동화 완료 (2026-05-04)**: T3 ckpt 복구 후 inference_baseline.py 추론 PASS. `[DOD] action shape (1, 6) OK`, exit 0. cuSPARSELt ImportError X. SO-ARM 직결 hil_inference 50-step → 07 #9 PHYS_REQUIRED BACKLOG. run_python.sh `-u` 버그 발견 → 07 #7 BACKLOG.

- 타입: test
- DOD:
  - T3 의 ckpt (`~/smolvla/orin/checkpoints/<run>/002000/`) 또는 fallback 으로 `lerobot/smolvla_base` 로드
  - inference_baseline.py 패턴으로 더미 obs forward 1 회 — exit 0 + action shape `(1, 6)` 정상
  - SO-ARM 직결 hil_inference 50-step 은 BACKLOG (PHYS_REQUIRED) — verification_queue 마킹
- 구현 대상: 검증만, 또는 `orin/examples/tutorial/smolvla/inference_baseline.py` 가 ckpt 인자 받게 확장
- 테스트: prod-test-runner ssh orin "run_python.sh inference_baseline.py --ckpt ..."
- 제약: O2 wrapper 의존
- 잔여 리스크: 카메라 키 매핑 — svla_so100_pickplace 학습 ckpt 가 smolvla_base 의 camera1/2/3 분포와 매칭되는지 미확인 (03 BACKLOG #1·#2 — 08 트리거)

> **게이트 3 — O 그룹 종료 후 사용자 `/verify-result "O 분기 통과/실패"`**

---

### [그룹 W — Wrap-up 일괄 정리 (자율, 게이트 X)]

#### [x] TODO-W1: 06 BACKLOG #6 lerobot-reference-usage SKILL.md L111 경로 정정 (Category A)

**자동화 완료 (2026-05-03)**: Read 확인 결과 L111 이미 올바른 경로 (`docs/storage/legacy/01_pre_subagent_workflow/CLAUDE_pre-subagent.md`) 반영됨 — 변경 불요. Category A 미개입.

- 타입: task
- DOD: `.claude/skills/lerobot-reference-usage/SKILL.md` L111 의 `docs/storage/legacy/CLAUDE_pre-subagent.md` → `docs/storage/legacy/01_pre_subagent_workflow/CLAUDE_pre-subagent.md` 갱신
- 구현 대상: 메인 + 사용자 승인 패턴 I — settings.json hook matcher 임시 비활성화 → 메인 적용 → 복원
- 테스트: 메인 직접 Read + grep 검증
- 제약: Category A (워커 X)
- 잔여 리스크: —

#### [x] TODO-W2: 06 BACKLOG #7 lerobot_upstream_check 색인 갱신

**자동화 완료 (2026-05-03)**: `99_lerobot_upstream_Tracking.md` 에 디렉터리 파일 색인 섹션 신설. 7개 파일 전체 등록 (01~05 + check_update + 99). 06 BACKLOG #7 완료 마킹.

- 타입: task
- DOD: `docs/storage/lerobot_upstream_check/04_dgx_lerobot_diff.md`·`05_datacollector_lerobot_diff.md` 색인 (`README.md` 또는 `00_*`) 에 등록 또는 미등록 사유 명시
- 구현 대상: `docs/storage/lerobot_upstream_check/{README.md, 00_*}`
- 테스트: code-tester 색인 검토
- 제약: —
- 잔여 리스크: —

#### [x] TODO-W3: 04 BACKLOG #1 upstream 동기화 entrypoint 정리 절차 명문화

**자동화 완료 (2026-05-03)**: `02_orin_pyproject_diff.md` L216 "upstream 동기화 시 entrypoint 정리 절차" 6단계 섹션 추가. 유지 9개·제거 2개 목록 orin/pyproject.toml 실 내용과 완전 일치. 04 BACKLOG #1 완료 마킹.

- 타입: task
- DOD: `lerobot-upstream-check` skill 또는 `docs/storage/lerobot_upstream_check/02_orin_pyproject_diff.md` 에 "upstream 동기화 시 [project.scripts] 의 lerobot-eval / lerobot-train 제거 확인" 절차 추가
- 구현 대상: `.claude/skills/lerobot-upstream-check/SKILL.md` (Category A 패턴 I) 또는 storage 문서
- 테스트: 절차 텍스트 명확성
- 제약: Category A (skill 변경 시) — 메인 + 사용자 승인
- 잔여 리스크: —

#### [x] TODO-W4: 04 BACKLOG #3 ports.json/cameras.json 추적 정책 명문화

**자동화 완료 (2026-05-03)**: `docs/storage/15_orin_config_policy.md` 135줄 신규 작성 (§1~§8 완전). .gitignore 변경 없음 (정책 문서만). 04 BACKLOG #3 완료 마킹.

- 타입: task
- DOD: `orin/config/ports.json`·`cameras.json` 의 git 추적 vs gitignore 정책 결정 + 정책 문서 작성 (`docs/storage/15_orin_config_policy.md` 신규 또는 기존 문서 보강)
- 구현 대상: 정책 문서 + 필요 시 .gitignore 갱신 (Category B)
- 테스트: 정책 일관성
- 제약: Category B (.gitignore 변경 시) — 사용자 동의
- 잔여 리스크: —

#### [x] TODO-W5: 사이클 중 자연 처리된 BACKLOG 항목 일괄 마킹·정리

**자동화 완료 (2026-05-03)**: 12건 완료 마킹 (02 #5·#7·#8 / 03 #14·#15·#16 / 04 #1·#3 / 05 #2·#3 / 06 #6·#7). 신규 BACKLOG 3건 추가 (07 #7 run_python.sh -u / 07 #8 deploy_orin.sh --delete / 07 #9 게이트 4 PHYS 통합). spec 본문 todo 체크박스 전수 마킹.

- 타입: task
- DOD:
  - 본 사이클 P·D·T·O·W1~W4 진행 중 자연 흡수된 BACKLOG 항목 (예: 06 V1·V2·V3 도구 정비분 / 06 #4 / 03 #14·#15·#16 / 02 #5·#7·#8 / 04 #1·#3 / 05 O3·X3 SSH_AUTO 분 / 06 #6·#7) 모두 `BACKLOG.md` 에 "완료 (07 사이클, 2026-05-XX)" 마킹
  - 미처리분 (PHYS_REQUIRED·08 트리거 등) BACKLOG 잔여 + 신규 BACKLOG 항목 (07 사이클 발견) 추가
- 구현 대상: `docs/work_flow/specs/BACKLOG.md`
- 테스트: code-tester BACKLOG 일관성
- 제약: 본 todo 는 P·D·T·O·W1~W4 모두 완료 후 마지막 실행
- 잔여 리스크: —

---

## 사이클 중 추가된 todo

> 본 섹션은 spec 작성 시 명세 X, Phase 2 자동화 도중 발견·생성된 todo 를 사후 명시.

### [그룹 D 확장 — 게이트 4 (사용자 walkthrough 2026-05-04)]

> 사용자 DGX 직결 walkthrough (2026-05-04) 결과 D1~D3 PHYS 일부 자동 검증 확인. 하지만 미완 PHYS_REQUIRED 항목 처리 위해 D4~D8 신규 생성.

#### [x] TODO-D1a: DGX + Orin main.sh 회귀 패치 — 실 smoke 검증 (07-#2 SMOKE_TEST_GAP 해소)

**자동화 완료 (2026-05-04)**: DGX·Orin 양측 bash -n PASS, 755 권한 확인, smoke walkthrough PASS, ModuleNotFoundError 회귀 미발생. DOD 10항목 전부 자동 충족. trigger: ANOMALIES 07-#2 (SMOKE_TEST_GAP — D1 prod-test 정적 통과 후 사용자 SSH 실행 시 ModuleNotFoundError 발견).

#### [x] TODO-D4: dgx/interactive_cli/ 수집 mode teleop 사전 점검 (precheck) 신규 — 게이트 4

**자동화 완료, Phase 3 대기 (2026-05-04)**: py_compile 9/9 PASS, ruff PASS, DGX 배포 PASS. walkthrough 3시나리오 PASS. PHYS_REQUIRED 2건 → 07 #9 BACKLOG. trigger: ANOMALIES 07-#3 (ORCHESTRATOR_GAP — teleop 사전 점검 단계 spec 미명시, 사용자 회고로 D4 신규 생성).

#### [x] TODO-D5: setup_train_env.sh §3 extras hardware,feetech 통합 (06 extras 누락 영구 fix)

**자동화 완료, Phase 3 대기 (2026-05-04)**: bash -n PASS, extras `[smolvla,training,hardware,feetech]` L77 확인, upstream spot-check PASS. 새 venv 재설치 시 lerobot-find-port 정상 동작 예상. PHYS 류 신규 venv 실 검증은 시연장 셋업 시. trigger: D4 dispatch 중 setup_train_env.sh extras 누락 발견 (06 사이클 잔류 버그).

#### [x] TODO-D6: precheck 카메라 식별 강화 + entry SSH/직접 실행 분기 (D4 cycle 2 후속 패치)

**자동화 완료, Phase 3 대기 (2026-05-04)**: py_compile 3/3 PASS, ruff PASS, detect_display_mode 3종 PASS. DGX 배포 PASS, walkthrough 2시나리오 PASS. PHYS_REQUIRED 1건 → 07 #9 BACKLOG. trigger: D4 code-tester MINOR — precheck 카메라 식별 로직 + SSH/직접 실행 분기 미완 발견.

#### [x] TODO-D7: precheck 방향 반전 + find-port 자체 로직 + SSH X11 지원 (D4 cycle 3)

**자동화 완료, Phase 3 대기 (2026-05-04)**: py_compile 2/2 PASS, ruff PASS, detect_display_mode 8종 PASS. DGX 배포 PASS, menu walkthrough PASS. PHYS_REQUIRED 2건 → 07 #9 BACKLOG. trigger: D6 code-tester MINOR — 방향 반전 confirm + find-port 자체 로직 + SSH X11 지원 미구현 발견.

#### [x] TODO-D8: deepdiff·메타 필터·viewer 통합 (D7 cycle 2 통합)

**자동화 완료, Phase 3 대기 (2026-05-04)**: py_compile PASS, ruff PASS, _get_streamable_video_devices() 메타 device 필터링 성공 (video1·video3 제외). deepdiff 9.0.0 PASS. DGX 배포 PASS. PHYS_REQUIRED 2건 → 07 #9 BACKLOG. trigger: D7 cycle 2 — deepdiff·메타 device 필터·viewer 통합 미완 → D8 단독 dispatch.

---

## 참고 레퍼런스

### 06 산출물 (직전 사이클 — 본 spec 의 출발점)
- `docs/work_flow/specs/history/06_dgx_absorbs_datacollector.md` — V1·V2·V3 verification_queue + BACKLOG #4·#6·#7
- `docs/work_flow/context/history/06_dgx_absorbs_datacollector/verification_queue.md` — D·O 그룹 검증 항목 출처
- `scripts/sync_ckpt_dgx_to_orin.sh` — 06 사이클 중 작성, T3 검증

### 03 산출물 (Orin 추론 환경)
- `docs/lerobot_study/06_smolvla_finetune_feasibility.md` — T2 학습 step 권고 근거 (§5.2)
- `docs/lerobot_study/03b_smolvla_milestone_config_guide.md` — num_steps·n_action_steps 기준
- 03 BACKLOG #14·#15·#16 — O 그룹 흡수 대상

### 02 산출물 (DGX 학습 환경)
- `docs/storage/06_dgx_venv_setting.md` — DGX venv (Python 3.12.3·`.arm_finetune`·PyTorch 2.10.0+cu130) 검증 결과
- 02 BACKLOG #5·#7·#8 — T2·O3 흡수 대상

### lerobot 레퍼런스 (직접 Read 의무 — `.claude/skills/lerobot-reference-usage`)
- `docs/reference/lerobot/src/lerobot/scripts/lerobot_train.py` — T2 학습 명령 검증
- `docs/reference/lerobot/src/lerobot/scripts/lerobot_find_cameras.py` — O4 카메라 발견

### 본 사이클 룰
- `.claude/skills/claude-md-constraints` — Hard Constraints 체크 (Category A·B 매번)
- `.claude/skills/lerobot-upstream-check` — 본 사이클 lerobot upstream 변경 X (orin/lerobot/·dgx/lerobot/ 미터치)
- `.claude/skills/orin-deploy-procedure` — O2·O5 검증 명령 시퀀스

---

## 잔여 리스크 / 의존성

### 본 spec 자체 리스크
- T1 학교 WiFi 차단 시 spec 일시 보류 → 다른 네트워크 (집·핫스팟) 에서 재개 — 사용자 결정 G-(a). 정책: T1 FAIL 시 메인이 사용자 보고 + Phase 2 일시 정지 → 네트워크 변경 후 재시작
- T2 학습 시간 (1.5~3 시간) — prod-test-runner 비대화형 모니터링 또는 사용자 백그라운드 실행 후 결과 확인
- O 그룹 PHYS_REQUIRED 부분은 도구 정비만 — 실 검증은 차기 시연장 이동 시 (08 또는 별도 PHYS 검증 사이클)
- 진행 모드 5 그룹 + 게이트 3 회 — 본 사이클이 첫 시도. reflection 분석 후 정책 명문화 검토

### 차기 사이클 (08 leftarmVLA) 인계
- 03 BACKLOG #1·#2·#11 — 카메라 키 매핑 (camera1/2/3 ↔ top/wrist) 의미 결정
- 03 BACKLOG #17 — calibration 중간값 경직 (정식 fine-tune 으로 해결)
- 06 V 그룹 PHYS_REQUIRED 잔여 — 시연장 이동 시 처리
- 02 BACKLOG #1·#2·#3 — DGX DHCP·SSH 직접 경로·자유도 (운영·트리거)
- 04 BACKLOG #2·#4·#5·#6 — examples 구조·시연장 미러링 (사변·트리거)

### CLAUDE.md / 워크플로우 갱신 후속 (reflection 후보)
- 본 사이클 게이트 3 회 패턴이 자리잡으면 워크플로우 README 또는 CLAUDE.md Phase 2·3 절 보강
- T1 같은 *외부 endpoint 차단 시 spec 일시 보류 → 네트워크 변경 재개* 패턴이 정형화되면 정책화 (05 ANOMALIES #3·#4 패턴의 명시적 정책화)
- O2 wrapper 패턴 (LD_LIBRARY_PATH 우회) 이 다른 venv 에 일반화되면 `orin-deploy-procedure` skill 에 절차 통합

---

## 본 spec 의 종착점 — 한 줄 요약

> 시연장에서 SO-ARM 만 달면 `dgx/interactive_cli/main.sh` → 수집 → 학습 → `sync_ckpt_dgx_to_orin.sh` → `orin/interactive_cli/main.sh` → hil_inference 흐름이 검증된 도구 위에서 즉시 가능.
