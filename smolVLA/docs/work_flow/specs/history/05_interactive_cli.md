# 20260501_interactive_cli
<!-- Claude Code + 개발자 협업 작성 -->

> 목표: orin·dgx·datacollector 세 노드 공통 대화형 CLI 게이트웨이 — 환경 체크부터 노드별 후속 책임 (datacollector=수집 / orin=추론 / dgx=학습) 까지 한 명령으로 진행. 04 산출물 (check_hardware·run_teleoperate·sync_dataset·push_dataset_hub·deploy_datacollector) 을 사용자 친화 인터페이스로 통합
> 환경: orin (JetPack 6.2, `~/smolvla/orin/.hylion_arm`) + dgx (`~/smolvla/dgx/.arm_finetune`) + datacollector (Ubuntu 22.04 LTS x86_64, `~/smolvla/datacollector/.hylion_collector` — 04 D1 결정)
> 접근: orin·dgx 는 **VSCode remote-ssh 자동 연결** (사용자가 VSCode 의 ssh remote 익스텐션으로 접근), datacollector 는 **해당 머신 직접 터미널** (스크립트 진입 시 "이 환경에서 실행하신 게 맞나요?" 확인 단계 포함)
> 코드 경로: 각 노드 루트의 `<node>/interactive_cli/` 신규 디렉터리 (마일스톤 이름과 동일 폴더, 형제 패턴, 각 노드 중복 — 공통 모듈 디렉터리 X)
> 작성: 2026-05-01

---

## 본 마일스톤의 위치

`arm_2week_plan.md` 의 05 마일스톤은 **04 인프라의 사용자 인터페이스 통합** — 04 에서 셋업된 4-노드 인프라를 사용자 친화 CLI 한 명령으로 운영 가능하게.

### 배경 — 04 산출물의 통합 필요

04 사이클이 인프라 영역별 산출물 (check_hardware.sh, run_teleoperate.sh, push_dataset_hub.sh, sync_dataset_collector_to_dgx.sh, deploy_datacollector.sh 등) 을 다수 만들었지만 **각 스크립트를 개별 호출**해야 하는 구조. 사용자가 데이터 수집 한 번 하려면:

1. SSH 접속 또는 콘솔
2. venv activate
3. check_hardware.sh 수동 실행
4. run_teleoperate.sh 별도 실행
5. lerobot-record 호출 (draccus 인자 환경별 조합)
6. push_dataset_hub.sh 또는 sync_dataset_collector_to_dgx.sh 별도 호출

→ 단계 다중·인자 복잡·실수 가능성. 06_leftarmVLA 진입 시 데이터 수집·학습·추론이 자주 발생할 텐데 매번 위 6~7 단계 수동은 비효율.

### 노드별 책임 (공통 7단계 강제 X)

- **datacollector**: 데이터 수집 (teleoperation → lerobot-record → 전송)
- **orin**: 추론 (학습된 ckpt 로드 → hil_inference 실행 → 사용자 관찰)
- **dgx**: 학습 (preflight → setup_train_env → smoke·실 학습 trigger → 체크포인트 관리)

세 노드 모두 flow 0 (진입) + flow 1 (장치 선택) + flow 2 (환경 체크) 까지 공통. 그 이후는 각 노드 책임에 맞게 분기 — 7단계 강제 X.

### 05 의 종착점

- 사용자가 어느 노드에서든 한 명령으로 진입 → 장치 선택 → 환경 체크 → 노드별 후속 책임 → 결과 출력
- datacollector: 수집·전송 한 번에 종료
- orin: 추론 검증 한 번에 종료
- dgx: 학습·체크포인트 관리 한 번에 종료
- 06_leftarmVLA 진입 시 데이터 수집·학습·추론을 한 명령으로 끝낼 수 있는 환경 완성

### datacollector 측 flow (사용자 명시)

```
0. 인터페이스 진입 (datacollector 머신 직접 터미널)
   → 스크립트 시작 시 "이 환경(datacollector)에서 실행하시는 게 맞나요? [Y/n]" 확인
   → 사용자 N 응답 시 종료 + 올바른 환경 안내
1. 장치 선택 질문 (orin / dgx / datacollector — 본 노드인 datacollector 만 활성, 다른 노드는 안내만)
2. 환경 체크 (04 G1 check_hardware.sh 패턴 미러 — datacollector 환경 맞춤. 04 G3·G4 책임 흡수)
3. "텔레오퍼레이션을 진행하겠습니다 (이 작업이 끝나면 학습 준비가 완료됩니다)" 출력 + enter 시 실행
   → 04 D2 datacollector/scripts/run_teleoperate.sh 호출
4. "잘 작동하면 enter를 눌러주세요" 출력 + enter 입력
5. "어떤 학습 데이터를 모을건가요?" — 학습 종류 옵션 질문
   → 옵션 후보는 docs/lerobot_study/ 참조하여 D1 study 단계에서 task-executor 가 제안 + 사용자 합의
6. 데이터 수집 시나리오 진행 (간단한 설명서 출력 + lerobot-record 호출)
   → draccus 인자 (`--robot.type`, `--robot.cameras`, `--dataset.repo_id`, `--dataset.num_episodes`) 5단계 답 기반 동적 생성
7. "[저장경로]에 저장되었습니다" 출력 + 전송 방식 사용자 선택 (HF Hub / rsync DGX / 안함)
   → HF Hub 선택 시 04 T1 datacollector/scripts/push_dataset_hub.sh 호출
   → rsync 선택 시 04 T1 scripts/sync_dataset_collector_to_dgx.sh 호출
   → 안함 선택 시 로컬 저장 (`datacollector/data/<dataset>/`) 만 유지
```

### orin 측 flow (추론 책임)

flow 0~2 공통 후, 추론 책임에 맞게 분기. 구체 단계는 O1 study 에서 사용자와 합의 — 후보:

- 학습된 ckpt 선택 (다양한 정책 후보 중) → ckpt 다운로드·로드
- hil_inference.py 실행 (04 G2 cycle 2 의 `--gate-json` 활용 — 자동 인자 채움)
- 시연 데모 모드 (사용자 정성 관찰 + 종료 후 보고)

orin 진입은 **VSCode remote-ssh** 로 사용자가 SSH 연결한 후 터미널에서 `bash orin/interactive_cli/main.sh` 호출.

### dgx 측 flow (학습 책임)

flow 0~2 공통 후, 학습 책임에 맞게 분기. 구체 단계는 X1 study 에서 사용자와 합의 — 후보:

- preflight 실행 (04 X3 의 5가지 체크 — venv/메모리/Walking RL/Ollama/디스크)
- 데이터셋 선택 (HF Hub repo_id 또는 로컬 datacollector/ 동기화 결과)
- 학습 trigger (smoke·실 학습 — 04 BACKLOG #7 X3 verification_queue 처리와 통합 가능)
- 체크포인트 관리 (저장·전송 — 04 T2 sync_ckpt_dgx_to_datacollector 활용)

dgx 진입도 **VSCode remote-ssh** 로 SSH 연결 후 터미널에서 `bash dgx/interactive_cli/main.sh` 호출.

---

## 합의된 새 디렉터리 구조

각 노드 루트에 동일 이름 폴더 신설 (마일스톤 이름과 동일, **각 노드 중복** — 공통 모듈 디렉터리 X):

```
orin/interactive_cli/
├── README.md
├── main.sh                # bash 진입점 (venv activate + python 호출)
├── flows/                 # python flow 모듈 (단계별 구현)
│   ├── __init__.py
│   ├── entry.py           # flow 0·1 (환경 확인 + 장치 선택)
│   ├── env_check.py       # flow 2 (check_hardware 호출)
│   └── inference.py       # 추론 책임 단계 (O1 결정)
└── configs/               # orin 환경 설정 (선택)

dgx/interactive_cli/        # 동일 구조, dgx 책임 맞춤
├── main.sh
├── flows/
│   └── training.py        # 학습 책임 단계 (X1 결정)
└── configs/

datacollector/interactive_cli/   # 동일 구조, datacollector 책임 맞춤
├── main.sh
├── flows/
│   ├── teleop.py          # flow 3·4 (run_teleoperate 호출)
│   ├── data_kind.py       # flow 5 (학습 종류 질문)
│   ├── record.py          # flow 6 (lerobot-record draccus 호출)
│   └── transfer.py        # flow 7 (전송 방식 선택)
└── configs/
```

**구현 언어**: bash 진입점 (main.sh) + python flow 모듈. 04 G1 check_hardware.sh 의 `bash + python heredoc` 패턴 미러.
- main.sh: venv activate + cusparseLt LD_LIBRARY_PATH 패치 (orin 한정) + python flow 모듈 호출
- flows/*.py: 대화형 입력·분기·문자열·JSON 처리. 5~7단계의 lerobot-record draccus 인자 동적 생성·subprocess 호출 깔끔.

**코드 공유**: 각 노드 중복. 공통 boilerplate (flow 0·1 entry.py, main.sh 진입점) 는 F1 study 산출물에 작성하고 F2 task 에서 각 노드에 동일 복사. devPC 에서 한 곳 수정 후 deploy_orin/deploy_dgx/deploy_datacollector 3 번으로 동기화 — 04 패턴 그대로.

---

## 참고 레퍼런스

### 04 산출물 (직전 마일스톤)

- `docs/work_flow/specs/history/04_infra_setup.md` — 04 마일스톤 전체 흐름
- `orin/tests/check_hardware.sh` (TODO-G1) — 환경 체크 패턴 (5단계: venv·CUDA·SO-ARM 포트·카메라·cache) + bash·python 혼합 패턴 (본 spec 진입점 참조)
- `orin/tests/configs/{first_time,resume}.yaml` — 환경 체크 cache 형식
- `datacollector/scripts/run_teleoperate.sh` (D2 시점 이관) — teleop 실행
- `datacollector/scripts/push_dataset_hub.sh` (T1 cycle 2) — HF Hub push (LeRobotDataset.push_to_hub + heredoc 환경변수 보안 패턴)
- `scripts/sync_dataset_collector_to_dgx.sh` (T1 cycle 2) — rsync devPC 2-hop
- `scripts/sync_ckpt_dgx_to_datacollector.sh` (T2) — 케이스 3 우회 ckpt 전송
- `scripts/deploy_datacollector.sh` (T3) — devPC sync hub
- `orin/inference/hil_inference.py` (G2 cycle 2) — `--gate-json` 자동 인자 패턴 (사용자 편의 구현 사례)

### 04 study 산출물 (구조 정의)

- `docs/storage/08_orin_structure.md` — orin/ 디렉터리 책임 매트릭스
- `docs/storage/09_dgx_structure.md` — dgx/ 디렉터리 책임 매트릭스
- `docs/storage/10_datacollector_structure.md` — datacollector/ 구조·책임·외부 의존성 (구 09_datacollector_setup.md 정보 분해 흡수됨)

### lerobot 레퍼런스 (interactive_cli 가 호출할 도구)

- `docs/reference/lerobot/src/lerobot/scripts/lerobot_record.py` — draccus dataclass 인자 (`--robot.type`, `--robot.cameras`, `--dataset.repo_id`, `--dataset.num_episodes`) — flow 6단계 정확 활용 (M1 cycle 1 추측 작성 답습 X)
- `docs/reference/lerobot/src/lerobot/scripts/lerobot_find_port.py` / `lerobot_find_cameras.py` — 환경 체크 (G1 wrapping 활용)
- `docs/reference/lerobot/src/lerobot/datasets/lerobot_dataset.py:501` — `LeRobotDataset.push_to_hub(branch, tags, license, tag_version, push_videos, private, allow_patterns, upload_large_folder)` 시그니처 (T1 cycle 2 검증 완료)

### 5단계 학습 종류 옵션 후보 (D1 입력)

- `docs/lerobot_study/` 디렉터리 전체 — 학습·도메인·데이터셋 관련 기존 study 자료. D1 study 단계에서 task-executor 가 직접 Read 하여 5단계 옵션 후보 제안 (단순 pick-place / 복잡 manipulation / dual-arm coordination 등). 사용자 답 받아 확정.

### 본 사이클 룰

- `.claude/skills/lerobot-reference-usage` — 레퍼런스 직접 Read + 인용 의무 (04 wrap 갱신)
- `.claude/skills/orin-deploy-procedure` — 자율성 분류 시 스크립트 직접 Read 의무 (04 wrap 갱신)
- `.claude/settings.json` — `bash -n` / `shellcheck` 화이트리스트 추가됨 (04 wrap)

## 레퍼런스 활용 규칙

- 레퍼런스에 동일하거나 유사한 구현이 있으면 반드시 그것을 기반으로 작성 (직접 Read + 01_implementation.md 에 인용 의무 — 04 wrap lerobot-reference-usage 적용)
- 레퍼런스에 없는 새로운 스크립트·함수·클래스를 만들어야 할 경우, 구현 전에 반드시 사용자에게 설명하고 확인을 받은 뒤 진행
- 본 spec 은 신규 자산 (interactive_cli) 비중이 크므로 SKILL_GAP 발생 가능성 높음 — F1 study 단계에서 미리 식별

---

## 사용자 결정 사항

| 결정 항목 | 상태 | 결과 |
|---|---|---|
| 공통 console 코드 공유 방식 | ✅ 확정 (2026-05-01) | **(a) 각 노드 중복** — `<node>/interactive_cli/` 자체 완결, 공통 모듈 디렉터리 X. devPC 한 곳 수정 → deploy 3 번으로 동기화 |
| CLI 구현 언어 | ✅ 확정 (2026-05-01) | **(c) bash 진입점 + python flow 모듈** — main.sh 가 venv activate, flows/*.py 가 대화형·draccus·subprocess |
| flow 0 인터페이스 진입 형태 | ✅ 확정 (2026-05-01) | orin·dgx = VSCode remote-ssh 사용자 자체 연결 후 `bash <node>/interactive_cli/main.sh` 호출 / datacollector = 직접 터미널 + "이 환경에서 실행하신 게 맞나요?" 확인 단계 |
| flow 1 장치 선택 의미 | ✅ 확정 (2026-05-01) | 본 노드 외 다른 노드 선택 시 안내만 (CLI 가 ssh 자동 호출 X — 사용자가 다른 노드에서 다시 진입). 본 노드만 active |
| 5단계 학습 종류 옵션 | ✅ 확정 (2026-05-02) | **(1) 단순 pick-place** — `svla_so100_pickplace` 사전학습 분포 동일. instruction `Pick up the object and place it in the target area.`, 50ep |
| orin 측 flow 3~ 단계 (추론 책임) | ✅ 확정 (2026-05-02) | **(A) 3단계 순차** (ckpt 선택 → hil_inference 실행 → 시연 데모 결과). ckpt 소스: HF Hub repo_id + 로컬 ckpt 경로 + 기본값 `smolvla_base` 고정 3개 조합. 시연 데모 모드 포함. (`hil_inference.py` 수정은 Category B 비해당 — O2 자동 처리) |
| dgx 측 flow 3~ 단계 (학습 책임) | ✅ 확정 (2026-05-02) | **(C) 3단계 권고** (preflight → 데이터셋 선택 → 학습+ckpt 관리 통합). smoke_test 동의 게이트 포함 (CLAUDE.md `>100MB 다운로드 사용자 동의` 정책). ckpt 전송 케이스 목록 출력 + 사용자 선택 방식 (자동 감지 X — 구현 복잡) |

---

## Todo

> 그룹 구분: F=Framework (공통 boilerplate), D=DataCollector (사용자 우선), O=Orin (추론), X=DGX (학습)
> 진행 순서: F1 → F2 → (D1·O1·X1 동시 study) → (D2·O2·X2 구현) → (D3·O3·X3 prod 검증) — D 우선 사용자 합의

**[그룹 F — 공통 console 프레임워크 boilerplate]**

### [x] TODO-F1: 공통 boilerplate 코드·문서 작성 (flow 0·1 + main.sh 진입점 패턴)

**자동화 완료 (2026-05-01)**: `docs/storage/12_interactive_cli_framework.md` 작성 (5개 절: 디렉터리·main.sh·flow 0 entry.py·flow 1 장치 선택·노드별 차이점). 04 G1 `check_hardware.sh` + G2 `hil_inference.py --gate-json` 패턴 인용. code-tester verdict READY_TO_SHIP (Critical 0, Recommended 2건 — §5 예시의 `--gate-json` 표기 정정·라인 인용 통일은 F2 인계 시 task-executor 가 처리).

- 타입: study (디렉터리·언어·코드 공유 결정은 spec 작성 시 이미 확정 — 본 todo 는 boilerplate 정의)
- DOD: 3 노드 동일 복사할 main.sh + flows/entry.py boilerplate 작성. flow 0 (환경 확인 단계 — datacollector 의 "이 환경 맞나요?" 포함) + flow 1 (장치 선택 메뉴 — 본 노드만 active, 다른 노드는 안내만) 완성. 04 G1 check_hardware.sh 의 bash·python 혼합 패턴 미러.
- 구현 대상:
  - `docs/storage/12_interactive_cli_framework.md` — 절 구성:
    - §1 디렉터리 구조 (3 노드 형제 동일 — 결정됨)
    - §2 진입점 main.sh 패턴 (bash + venv activate + python 호출)
    - §3 flow 0 entry.py 코드 (환경 확인 단계 + datacollector "이 환경 맞나요?" 분기)
    - §4 flow 1 장치 선택 메뉴 (본 노드 active / 다른 노드 안내만)
    - §5 노드별 차이점 (datacollector·orin·dgx 의 flow 2~ 분기점)
- 테스트: 없음
- 참조: 04 G1 `orin/tests/check_hardware.sh` (bash·python 혼합 패턴 직접 Read + 인용), 04 G2 cycle 2 `orin/inference/hil_inference.py` (`--gate-json` JSON 로딩 패턴)
- 잔여 리스크: 공통 boilerplate 가 3 노드의 venv 의존성 차이 (record+hardware+feetech / smolvla / training) 흡수 — 단순 boilerplate 면 venv 의존성 무관 (subprocess 호출만)

### [x] TODO-F2: 각 노드에 boilerplate 동일 복사 + 노드별 환경 설정 분리

**자동화 완료 (2026-05-01)**: orin·dgx·datacollector 각 `interactive_cli/` 신규 디렉터리 + main.sh + flows/{__init__, entry}.py + configs/node.yaml + README.md 총 15개 파일 생성. F1 §3 entry.py 3 사본 IDENTICAL 확인. cusparseLt 블록 orin only. code-tester verdict READY_TO_SHIP (Recommended 1건은 F1 원본 cascade — F1 갱신 시 자연 처리). F2 prod-test 별도 진입 X — D3·O3·X3 통합 검증.

- 타입: task
- DOD: F1 산출물 (main.sh + flows/entry.py) 을 3 노드에 동일 복사. 각 노드의 configs/ 에 환경 설정 분리 (venv 경로·노드 식별자 등). main.sh 가 자기 노드를 인식하여 flow 1 의 본 노드 active 처리.
- 구현 대상:
  - `orin/interactive_cli/{main.sh, flows/__init__.py, flows/entry.py, configs/node.yaml}` (신규)
  - `dgx/interactive_cli/` 동일 구조 (신규)
  - `datacollector/interactive_cli/` 동일 구조 (신규)
  - 각 `interactive_cli/README.md` (신규)
- 테스트: 없음 (각 노드 prod 검증에서 통합 검증)
- 제약: F1 완료 후
- 잔여 리스크: 3 노드 동일 복사 동기화 — devPC 에서 한 곳 수정 후 deploy 3 번 해야 함을 README 에 명시

**[그룹 D — DataCollector (사용자 우선)]**

### [x] TODO-D1: datacollector flow 2~7 정의 + 5단계 학습 종류 옵션 결정

**자동화 완료 (2026-05-01)**: `docs/storage/15_datacollector_cli_flow.md` 작성 (5개 절: flow 2 환경 체크 / flow 3·4 텔레오퍼레이션 / flow 5 학습 옵션 5개 후보 / flow 6 lerobot-record draccus 인자 매핑 / flow 7 전송 분기). `lerobot_record.py DatasetRecordConfig` (line 161~211) 직접 인용. code-tester verdict READY_TO_SHIP (Recommended 2건은 라인 인용 trivial). **awaits_user-A 발송 명세** 작성 완료 (5단계 옵션 후보 5개) — 사용자 답 받기 전 D2 dispatch X.

- 타입: study
- DOD: datacollector 측 flow 2~7 단계 구체 동작 정의. 5단계 "어떤 학습 데이터" 옵션 (≤5개 후보) 확정. 6단계 lerobot-record draccus 인자 매핑 결정.
- 구현 대상:
  - `docs/storage/15_datacollector_cli_flow.md` — 절 구성:
    - §1 flow 2 (환경 체크 — 04 G3·G4 책임 흡수) 동작
    - §2 flow 3·4 (텔레오퍼레이션 + 사용자 확인) 동작
    - §3 flow 5 학습 종류 옵션 후보 (`docs/lerobot_study/` 참조 — task-executor 가 직접 Read 후 후보 제안)
    - §4 flow 6 lerobot-record draccus 인자 매핑 (5단계 답 → 인자 동적 생성)
    - §5 flow 7 전송 방식 선택 분기 (HF Hub / rsync / 안함)
- 테스트: 없음
- 참조: `docs/lerobot_study/` 전체 (5단계 옵션 후보 입력), `docs/reference/lerobot/src/lerobot/scripts/lerobot_record.py` (draccus 인자 직접 Read + 인용), 04 D2·T1 산출물
- 사용자 결정 사항: 5단계 학습 종류 옵션 (awaits_user — task-executor 후보 제안 후 사용자 답)
- 잔여 리스크: 5단계 옵션이 너무 많으면 CLI UX 복잡 — 후보 ≤ 5개 강제

### [x] TODO-D2: datacollector/interactive_cli/ flow 2~7 구현

**자동화 완료 (2026-05-02, cycle 2)**: `datacollector/interactive_cli/flows/{env_check, teleop, data_kind, record, transfer}.py` 신규 + `entry.py` 수정 (cycle 2 — sys.path 절대 import 패턴, orin·dgx 와 일관). cycle 1 verdict MAJOR_REVISIONS (Critical 1: entry.py 상대 import → main.sh 호출 시 ImportError). cycle 2 정정 + Recommended 3건 (record validation 자기비교, 이중 호출, env_check 5단계 순서) 함께 처리. 사용자 결정 옵션 1 (단순 pick-place) 적용. 04 G3 (DataCollector check_hardware) 책임 흡수. **Phase 3 검증 대기 (D3)**: DataCollector 머신 + SO-ARM + 카메라 실물 — 04 BACKLOG #7·#8·#9 통합.

- 타입: task
- DOD: datacollector flow 2~7 단계 모두 구현. 04 산출물 (`run_teleoperate.sh`, `push_dataset_hub.sh`, `sync_dataset_collector_to_dgx.sh`) subprocess 호출 + lerobot-record draccus 인자 동적 생성.
- 구현 대상:
  - `datacollector/interactive_cli/flows/{env_check.py, teleop.py, data_kind.py, record.py, transfer.py}`
  - 04 G3 (DataCollector check_hardware.sh 이식) 책임 흡수 — env_check.py 가 04 G1 패턴 재구현 또는 datacollector/scripts/check_hardware.sh 신규 (G3 자연 처리)
- 테스트: 없음 (D3 검증)
- 제약: F1·F2·D1 완료 후
- 잔여 리스크:
  - lerobot-record draccus 인자 5단계 답 동적 매핑 — 사용자 잘못 답하면 lerobot-record 실패 (validation 단계 추가 권고)
  - 7단계 사용자 선택 후 전송 실패 시 데이터 보존 (재시도 옵션) — UX 결정 필요

### [ ] TODO-D3: datacollector/interactive_cli/ prod 검증 (04 BACKLOG #7·#8·#9 통합)

**자동화 완료, Phase 3 부분 검증 (2026-05-02)**: prod-test-runner verdict NEEDS_USER_VERIFICATION → Phase 3 사용자 검증 진행:

**완료된 검증** (사용자 실물 확인):
- ✅ DataCollector 머신 셋업 (`smallgaint`·Ubuntu 22.04 LTS x86_64) — 04 D3 16단계 사실상 처리
- ✅ SSH 인프라 (key 배포·~/.ssh/config·dev-connect.sh)
- ✅ 트랙 A (apt 6 패키지 + dialout 그룹)
- ✅ deploy_datacollector.sh dry-run + 실배포 — **04 BACKLOG #7 T3 자연 처리**
- ✅ venv 셋업 (lerobot 0.5.2·torch 2.11.0·9 entrypoint OK — 단 cuda wheel + nvidia deps 2.7GB dead weight, BACKLOG #10)
- ✅ USB 디바이스 (외부 카메라 2대 + SO-ARM 2대) 인식 + 모터 ID 1~6 등록 확인
- ✅ env_check 7단계 통합 동작 검증 (사용자 요청 §6·§7 추가 — **04 BACKLOG #8 G3 자연 처리**, **04 BACKLOG #9 G4 부분 처리**)
- ✅ interactive_cli main.sh flow 0~2 진입 검증

**다음 사이클 이관** (BACKLOG #11·#12·#13):
- ❌ Python 3.12 셋업 또는 lerobot 옵션 B backport — lerobot upstream PEP 695 syntax 5+ 파일이 Python 3.12+ 강제. 학교 WiFi 의 launchpad.net timeout 으로 deadsnakes PPA 차단 (ANOMALIES #2·#3)
- ❌ lerobot-calibrate (follower + leader)
- ❌ flow 3~7 (teleop·record·transfer) 실 호출 — lerobot import 의존
- ❌ flow 7 분기 3건 (HF Hub / rsync / 안함) — 04 BACKLOG #7 T1 미완

**사용자 결정 (2026-05-02)**: "interactive-cli 작동하는지까지만 05 에서 진행, 추가 검증은 다음 spec" → 옵션 A (끝까지) → 옵션 B (부분 검증 + wrap-spec) fallback. ANOMALIES #4 USER_OVERRIDE 기록.

상세: `context/verification_queue.md` D3 항목 + `auto_grants_05_interactive_cli.md` 17건 누적.

- 타입: test
- DOD: datacollector 머신에서 실 인터페이스 진입 → flow 0~7 완주. 데이터 수집 후 7단계 분기 (HF Hub / rsync / 안함) 모두 동작. **04 BACKLOG #7 (D3 verification_queue) + #8·#9 (G3·G4 dispatch 누락) 자연 처리** — 본 D3 prod 가 DataCollector 환경 셋업 + check_hardware 이식 + 검증을 통합 수행.
- 구현 대상: 없음 (검증·기록)
- 테스트: prod 검증 (DataCollector 머신 + SO-ARM + 카메라 임시 연결 + dummy dataset 수집)
- 제약: D2·04 BACKLOG #7 (DataCollector 머신 셋업) 완료 후
- 잔여 리스크: DataCollector 머신 미셋업 시 본 todo 진입 불가 — 04 BACKLOG #7 처리 후 가능

**[그룹 O — Orin (추론 책임)]**

### [x] TODO-O1: orin flow 3~ 단계 정의 (추론 책임)

**자동화 완료 (2026-05-02, cycle 2)**: `docs/storage/13_orin_cli_flow.md` 작성 (5개 절: flow 2 환경 체크 / flow 3~ 후보 / ckpt 선택 / hil_inference.py --gate-json 호출 / 시연 데모). cycle 1 verdict MAJOR_REVISIONS (Critical 2건: hil_inference.py Category B 오분류 + check_hardware.sh `--gate-json` 잘못된 호출). cycle 2 에서 양쪽 정정 + F1 §5 cascade (`12_interactive_cli_framework.md` §5 의 `--gate-json` 패턴) 함께 정정. **awaits_user-B 발송 명세** 작성 완료 (3가지 결정 사항: flow 구조 / ckpt 소스 / 시연 데모 포함 여부) — 사용자 답 받기 전 O2 dispatch X.

- 타입: study
- DOD: orin 측 flow 3~ 단계 (datacollector 와 다른 추론 책임) 구체 정의. ckpt 선택·hil_inference 실행·시연 데모 중 어느 책임을 어떻게 묶을지 사용자 합의.
- 구현 대상:
  - `docs/storage/13_orin_cli_flow.md`
- 테스트: 없음
- 사용자 결정 사항: orin 측 flow 의 구체 단계·책임 (awaits_user — task-executor 후보 제안 후 사용자 답)
- 참조: `orin/inference/hil_inference.py` (`--gate-json` 패턴 — interactive_cli 가 hil_inference 호출 구조), `docs/storage/08_orin_structure.md`, 04 G2 verification_queue (실 카메라·SO-ARM 환경)

### [x] TODO-O2: orin/interactive_cli/ flow 3~ 구현

**자동화 완료 (2026-05-02)**: `orin/interactive_cli/flows/{env_check, inference}.py` 신규 + `entry.py` 수정 (`_run_node_flows` + sys.path 패턴) + `orin/inference/hil_inference.py` line 246~266 `--model-id`·`--ckpt-path` argparse 인자 추가 (default None — 03 사이클 회귀 방지). 사용자 결정 (A) 3단계 + ckpt 소스 3개 조합 + 시연 데모 포함 적용. O1 cycle 2 정정 (`check_hardware.sh --gate-json` 미전달) 준수. code-tester verdict READY_TO_SHIP (Recommended 2건 trivial: type hint PEP 604, options 미사용 변수). **Phase 3 검증 대기 (O3)**: Orin SSH + 카메라 2대 + SO-ARM follower 실물 — 04 G2 verification_queue 자연 통합.

- 타입: task
- DOD: O1 정의대로 orin 측 flow 구현. F2 boilerplate (entry/env_check) + orin 환경 맞춤 추론 모듈 (`flows/inference.py` 등).
- 구현 대상:
  - `orin/interactive_cli/flows/inference.py` 등 (O1 결정에 따라)
- 테스트: 없음 (O3 검증)
- 제약: F1·F2·O1 완료 후

### [ ] TODO-O3: orin/interactive_cli/ prod 검증 (04 BACKLOG #7 G2 통합)

**자동화 완료, Phase 3 대기 (2026-05-02)**: prod-test-runner verdict NEEDS_USER_VERIFICATION. devPC 정적 검증 (py_compile 4파일·AST parse·entry.py importlib·hil_inference.py argparse line 247·257 존재) 통과. effective_model 우선순위 시뮬레이션으로 03 사이클 회귀 없음 확인 (인자 미전달 시 `smolvla_base` 동작). Orin SSH connection timed out (172.16.137.232:22) — 네트워크 연결 후 deploy + 실물 검증 필요. **사용자 실물 검증**: deploy_orin.sh 실행 + 카메라 2대 + SO-ARM follower 연결 + main.sh 실행 → flow 0~5 완주. 04 BACKLOG #7 G2 (first-time/resume + hil_inference 50-step) 통합 처리. 상세: `context/verification_queue.md` O3 항목.

- 타입: test
- DOD: Orin 에서 실 인터페이스 진입 → 추론 flow 완주. **04 G2 verification_queue (Orin 카메라 2대 + SO-ARM follower first-time/resume + hil_inference 50-step) 자연 통합**.
- 구현 대상: 없음 (검증·기록)
- 테스트: prod 검증 (Orin SSH + 04 G2 verification_queue 환경 활용)
- 제약: O2·04 G2 verification_queue 처리 완료 후

**[그룹 X — DGX (학습 책임)]**

### [x] TODO-X1: dgx flow 3~ 단계 정의 (학습 책임)

**자동화 완료 (2026-05-01)**: `docs/storage/14_dgx_cli_flow.md` 작성 (5개 절: flow 2 환경 체크 / flow 3~ 후보 / 데이터셋 선택 / 학습 trigger smoke_test 동의 게이트 / 체크포인트 관리). `dgx/scripts/{preflight_check, smoke_test, save_dummy_checkpoint}.sh` + `sync_ckpt_dgx_to_datacollector.sh` 직접 인용. code-tester verdict READY_TO_SHIP (Recommended 2건 line 인용 trivial). **awaits_user-C 발송 명세** 작성 완료 — 사용자 답 받기 전 X2 dispatch X.

- 타입: study
- DOD: dgx 측 flow 3~ 단계 구체 정의. preflight·데이터셋 선택·학습 trigger·체크포인트 관리 중 어느 책임을 어떻게 묶을지 사용자 합의.
- 구현 대상:
  - `docs/storage/14_dgx_cli_flow.md`
- 사용자 결정 사항: dgx 측 flow 책임 (awaits_user)
- 참조: `dgx/scripts/{setup_train_env,preflight_check,smoke_test,save_dummy_checkpoint}.sh`, `docs/storage/09_dgx_structure.md`, 04 X3 verification_queue (smoke_test·save_dummy_checkpoint 사용자 동의)

### [x] TODO-X2: dgx/interactive_cli/ flow 3~ 구현

**자동화 완료 (2026-05-02)**: `dgx/interactive_cli/flows/{env_check, training}.py` 신규 + `entry.py` 수정. 사용자 결정 옵션 C (3단계: preflight → 데이터셋 선택 → 학습+ckpt 통합) + smoke_test 동의 게이트 포함 (CLAUDE.md 자율성 정책 충족) + ckpt 케이스 목록 출력 방식 적용. CKPT_CASES 케이스 1~4 (sync_ckpt_dgx_to_datacollector.sh line 19~22 인용) 완전 정합. code-tester verdict MINOR_REVISIONS → patch 1회 (ruff F401·F541 6건 정정 + 케이스 4 추가 + 동적 종료 번호). **Phase 3 검증 대기 (X3)**: DGX SSH + smoke_test 사용자 동의 + svla_so100_pickplace 다운로드 — 04 X3·T1·T2 verification_queue 통합.

- 타입: task
- DOD: X1 정의대로 dgx 측 flow 구현.
- 구현 대상:
  - `dgx/interactive_cli/flows/training.py` 등 (X1 결정에 따라)
- 제약: F1·F2·X1 완료 후

### [ ] TODO-X3: dgx/interactive_cli/ prod 검증 (04 BACKLOG #7 X3·T1·T2 통합)

**자동화 완료, Phase 3 대기 (2026-05-02)**: prod-test-runner verdict NEEDS_USER_VERIFICATION. devPC 정적 검증 (py_compile 3파일·bash -n·ruff All passed·CKPT_CASES 1~4·SCENARIOS 4종·_smoke_consent_gate Y/n·_show_ckpt_management 자동 감지 X) 통과. **deploy_dgx.sh 자율 실행 완료** (7개 파일 신규 sync). DGX 원격 read-only 검증 (py_compile·bash -n·entry.py --help·디스크 3.3T·메모리 114GB·GPU idle·Ollama 점유 없음) 통과. **사용자 실물 검증**: VSCode remote-ssh → DGX → main.sh 실행 → flow 0~5 완주 (smoke 시나리오 + 동의 게이트 Y + svla_so100_pickplace ~100MB 다운로드 동의 + 5~15분 실행 + ckpt 케이스 목록). 04 BACKLOG #7 X3 (smoke 캐시 MISS) + T1 (HF Hub push) + T2 (시연장 ckpt 전송) 통합 처리. 상세: `context/verification_queue.md` X3 항목.

- 타입: test
- DOD: DGX SSH 에서 실 인터페이스 진입 → 학습 flow 완주. **04 X3 verification_queue (smoke_test 5~15분 사용자 동의·svla_so100_pickplace 다운로드) + T1 verification_queue (HF Hub push 실 검증) + T2 verification_queue (시연장 ckpt 전송) 자연 통합 가능**.
- 구현 대상: 없음 (검증·기록)
- 테스트: prod 검증 (DGX SSH)
- 제약: X2 완료 후

---

## 잔여 리스크 / 의존성

### 04 BACKLOG·verification_queue 통합 표 (사용자 review 3 — 04 미검증 통합 환영)

| 04 BACKLOG / verification_queue | 본 spec 흡수 todo | 처리 방향 |
|---|---|---|
| 04 BACKLOG #7 (Phase 3 검증 6건) | D3·O3·X3 prod | DataCollector 머신·시연장 환경 셋업 후 본 spec prod 검증 단계에 통합 |
| 04 BACKLOG #8 (G3 미진행 — DataCollector check_hardware 이식) | D2 (env_check.py) + D3 prod | D2 의 env_check.py 가 G1 패턴 재구현 또는 신규 datacollector/scripts/check_hardware.sh — G3 자연 해소. D3 prod 시 G4 도 함께 검증 |
| 04 BACKLOG #9 (G4 미진행 — DataCollector check_hardware prod) | D3 prod | D3 prod 시 자연 통합 |
| 04 G2 verification_queue (first-time/resume + hil_inference 50-step) | O3 prod | O3 prod 시 본 spec 의 orin 추론 flow 가 G2 의 검증 단계 모두 활용 |
| 04 D3 verification_queue (DataCollector 셋업 16단계) | D3 prod | D3 prod 의 사전 조건. 사용자 환경 셋업 단계 (A~F 블록) 완료 후 본 spec prod 진입 |
| 04 X3 verification_queue (smoke_test 캐시 MISS 동의) | X3 prod | X3 prod 시 본 spec 의 dgx 학습 flow 가 smoke_test·save_dummy_checkpoint 사용자 동의를 통합 처리 |
| 04 T1 verification_queue (dummy dataset push --private 실 HF Hub) | D3·X3 prod | D3 의 7단계 HF Hub 분기 + X3 의 데이터셋 다운로드 검증 통합 |
| 04 T2 verification_queue (시연장 네트워크 케이스 분류) | X3 prod | X3 의 체크포인트 관리 단계에서 sync_ckpt_dgx_to_datacollector 호출 분기로 통합 |
| 04 T3 verification_queue (deploy_datacollector dry-run·실배포) | F2 (3 노드 boilerplate 복사 시 deploy 사용) | F2 task 진행 시 deploy_datacollector 실 사용 — 04 T3 자연 검증 |

→ 04 wrap 시점 BACKLOG 이관된 미검증 7건이 본 spec 의 prod 검증 단계 (D3·O3·X3) 에서 자연 처리. 별도 사용자 작업 없이 통합 완료 가능.

### 본 spec 자체 리스크

- 신규 자산 (interactive_cli) 비중이 크므로 SKILL_GAP 발생 가능성 높음 — F1 study 단계에서 미리 식별
- 5단계 학습 종류 옵션 결정 (D1) 이 6단계 lerobot-record 인자 구조와 직결 — D1 study 에서 함께 확정
- bash + python 혼합 패턴의 venv activate 순서 — main.sh 가 source venv 후 python 호출. 04 G1 패턴 그대로

### META 제안 #8 (04 reflection 후속)

- `.claude/settings.json` PreToolUse hook 에 메인 세션 우회 조건 추가 (현재는 사용자가 hook matcher 임시 변경 → 적용 → 복원 흐름)
- 본 spec 진행 중 reflection 갱신 발생 시 동일 흐름 반복 가능 — 본 spec 의 첫 반영 후보. 단 본 spec 의 핵심 작업이 아니라 별도 미니 todo 또는 차기 사이클 위임

---

> Backlog → [docs/work_flow/specs/BACKLOG.md](BACKLOG.md) 에 본 스펙 섹션을 추가하여 운영
