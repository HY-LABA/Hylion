# 06_dgx_absorbs_datacollector
<!-- Claude Code + 개발자 협업 작성 -->

> 목표: DataCollector 책임을 DGX 가 흡수 — DGX 가 시연장 직접 이동 운영하며 데이터 수집 + 학습 두 책임을 모두 수행. 기존 datacollector/ 노드 자산을 legacy 이관, dgx/interactive_cli/ 가 수집·학습 두 모드 분기 지원, dgx/ 의존성·scripts 에 데이터 수집 도구 흡수.
> 환경: orin (JetPack 6.2, `~/smolvla/orin/.hylion_arm`) + dgx (Ubuntu 22.04, Python 3.12.3, `~/smolvla/dgx/.arm_finetune`). DataCollector 노드 (smallgaint Ubuntu 22.04) **회수 — 본 사이클 종료 시 datacollector 머신 운영 종료**
> 접근: orin·dgx 모두 VSCode remote-ssh (사용자 자체 연결) + `bash <node>/interactive_cli/main.sh` 호출. flow 1 장치 선택은 **orin / dgx 2 옵션**으로 축소
> 코드 경로: 기존 `datacollector/` → `docs/storage/legacy/02_datacollector_separate_node/`. dgx 측 신규 흡수 자산은 `dgx/interactive_cli/flows/` + `dgx/scripts/`
> 작성: 2026-05-02

---

## 본 마일스톤의 위치

`arm_2week_plan.md` 의 마일스톤 구조 변경. 본 spec 은 **04·05 사이클의 4-노드 인프라 가정을 3-노드로 재정의**:

- 4-노드 (devPC + DataCollector + DGX + Orin) → **3-노드 (devPC + DGX + Orin)**
- DGX 가 *시연장 이동 운영* + *학습* + *데이터 수집* 세 책임을 모두 흡수
- 본 사이클이 끼어들면서 기존 `06_leftarmVLA` → 07, 07~09 → 08~10 시프트

### 배경 — 본 결정의 두 동력

**동력 1: 05 사이클 BACKLOG #11 차단 (Python 3.12)**

05 D3 검증 단계에서 DataCollector (smallgaint, Ubuntu 22.04, Python 3.10) 가 lerobot upstream import 실패. lerobot 5+ 파일이 PEP 695 generic syntax 사용 → Python 3.12+ 강제. 학교 WiFi 가 launchpad.net (deadsnakes PPA endpoint) timeout 으로 차단되어 우회 불가능 (05 ANOMALIES #2·#3).

→ DGX 가 데이터 수집 책임 흡수 시: DGX 는 **이미 Python 3.12.3 + `.arm_finetune` venv 운영 중** (06_dgx_venv_setting.md). BACKLOG #11 우회.

**동력 2: 시연장 미러링 원칙의 단순화**

04 가 DataCollector 별도 노드 둔 이유: *시연장 인근 데이터 수집*. 본 결정으로 **DGX 자체가 시연장 직접 이동** 하므로 미러링 원칙 유지. 데이터 수집 → 학습 → 시연장 추론 흐름이 *DGX 한 곳* 에서 처음 두 단계 통합 + Orin 시연장 추론 한 단계로 단순화.

### 본 사이클의 종착점

- DGX 단일 노드에서 데이터 수집 + 학습 두 책임 모두 동작
- `dgx/interactive_cli/` 가 flow 3 단계에서 *수집 / 학습* 모드 분기 (사용자 결정: 옵션 α)
- 기존 `datacollector/` 노드 자산 legacy 이관 — 후속 사이클에서 머신 회수 또는 다른 용도 재활용
- 06 진입 (= 옛 06_leftarmVLA → 신 07_leftarmVLA) 시 DGX 한 곳에서 데이터 수집·학습·체크포인트 관리가 한 명령으로 가능

---

## 사용자 결정 사항 (Phase 1 합의)

| 결정 항목 | 상태 | 결과 |
|---|---|---|
| A. 시연장 미러링 원칙 | ✅ 확정 (2026-05-02) | DGX 가 시연장 직접 이동 — 04 의 "DataCollector 별도 노드" 가정 폐기. 미러링은 *DGX 가 시연장에 가는 것* 으로 충족 |
| B. DGX 측 SO-ARM·카메라 직결 가능 여부 | ✅ 확정 (2026-05-02) | 직결 가능. 단 USB·dialout·v4l2 실 검증은 V 그룹 prod 검증 todo 로 이관 |
| C. interactive_cli 통합 방식 | ✅ 확정 (2026-05-02) | **옵션 α** — 단일 진입점 (`bash dgx/interactive_cli/main.sh`) + flow 3 단계에서 *수집 / 학습 / 종료* mode 질문 분기. flow 1 장치 선택은 orin / dgx 2 옵션으로 축소 |
| D. 04 BACKLOG datacollector 항목 처리 | ✅ 확정 (2026-05-02) | (i) 04 BACKLOG #11·#12·#13 + 05 BACKLOG (D3·O3·X3 datacollector 미검증) 항목 모두 "완료(불요)" 마킹 + 사유 명시. 통째 삭제 X — 결정 이력 보존 |
| E. CLAUDE.md 정합 갱신 | ✅ 적용 완료 (2026-05-02 Phase 1) | 4 곳 정리: §Project Snapshot Platform, §Architecture At A Glance dgx 행, §Hard Constraints Category B (datacollector/lerobot/ 제거), §Coupled File Rules 3-b 제거. 메인 Claude 가 사용자 승인 후 직접 수정 (Category A) |
| F. spec 번호·시프트 | ✅ 확정 (2026-05-02) | 본 spec = `06_dgx_absorbs_datacollector`. 기존 `06_leftarmVLA` → `07_leftarmVLA`, `07_biarm_teleop_on_dgx` → `08`, `08_biarm_VLA` → `09`, `09_biarm_deploy` → `10`. arm_2week_plan.md 본문 갱신 = M1 |

### Phase 2 진행 중 확정될 추가 결정

| 결정 항목 | 처리 | 예상 결과 |
|---|---|---|
| G. dgx flow mode 옵션 라벨·종료 분기 | ✅ 확정 (2026-05-02, X1 후) | **G-4 (custom)** — 메뉴 `(1) 수집 / (2) 학습 / (3) 종료`. (1) 수집 진입 후 flow 3~7 완주 시점에 `"수집 완료. 바로 학습으로 진행할까요? [Y/n]"` prompt. Y → 학습 mode flow 3~ 자동 진입 (방금 수집 데이터셋 자동 선택), n → 저장 후 종료. mode.py 가 G-1 단발 + 수집 끝 학습 전환 prompt 하이브리드 |
| H. flow 7 전송 분기 옵션 변경 | ✅ 확정 (2026-05-02, X1 후) | **(b)** — flow 7 = `(1) 로컬 저장만 / (2) HF Hub 백업도 같이`. rsync DGX·Orin 류 폐지 (학습 데이터 외부 전송 무의미 — DGX 자체 보관). HF Hub 옵션은 백업·외부 공유 목적 유지. ckpt 전송은 학습 mode 의 ckpt 관리 단계 책임 (DGX → Orin rsync — 본 spec 외) |
| I. dgx/pyproject.toml 의존성 추가 (record + hardware + feetech) | ✅ 확정 (2026-05-02, X4 조사 후) | **Option B (권고 채택)** — `dgx/pyproject.toml` *신규 생성 X*. DGX 가 lerobot upstream editable 설치 + 9 entrypoint 이미 등록 → pyproject 중복 불요. **X4 = skip (변경 X)**. extras 설치는 X5 가 `setup_env.sh` 에서 단독 처리. torchcodec 호환 OK (0.10.0+cu130 wheel + `--index-url https://download.pytorch.org/whl/cu130`), 패키지 충돌 0건 |
| J. dgx/scripts/setup_env.sh record extras 설치 추가 | X5 task — 단일 책임 (Option B) | record + hardware + feetech extras 설치 step 추가. Coupled File Rule 1 비활성 (pyproject 미변경) |

---

## 합의된 디렉터리 구조

### legacy 정리 (그룹 L)

```
docs/storage/legacy/
├── README.md                                    # 두 하위 폴더 색인 + 각 그룹 사유
├── 01_pre_subagent_workflow/                    # 기존 8 파일 이동
│   ├── README.md                                # 기존 legacy/README.md 그대로
│   ├── agent_plan_pre-subagent.md
│   ├── AGENTS_codex-guide.md
│   ├── CLAUDE_pre-subagent.md
│   ├── copilot-instructions_pre-subagent.md
│   ├── current_task_pre-subagent.md
│   ├── current_test_pre-subagent.md
│   └── HANDOFF_2026-04-30.md
└── 02_datacollector_separate_node/              # 신규 — datacollector 노드 자산 통째
    ├── README.md                                # 이동 사유·일자·후속 (DGX 흡수 결정)
    ├── datacollector/                           # smolVLA/datacollector 통째 이동
    │   ├── config/
    │   ├── data/
    │   ├── interactive_cli/
    │   ├── pyproject.toml
    │   ├── README.md
    │   ├── scripts/
    │   └── tests/
    ├── docs_storage_07_datacollector_venv_setting.md  # 원래 docs/storage/07_*
    ├── docs_storage_10_datacollector_structure.md     # 원래 docs/storage/10_*
    ├── docs_storage_15_datacollector_cli_flow.md      # 원래 docs/storage/15_*
    ├── scripts_sync_dataset_collector_to_dgx.sh       # 원래 smolVLA/scripts/
    ├── scripts_sync_ckpt_dgx_to_datacollector.sh      # 원래 smolVLA/scripts/
    └── scripts_deploy_datacollector.sh                # 원래 smolVLA/scripts/
```

### dgx 측 흡수 (그룹 X)

```
dgx/interactive_cli/
├── main.sh                       # 그대로 (flow 1 장치 선택만 orin/dgx 2 옵션으로 갱신)
├── README.md                     # 흡수 책임 명시 — 학습 + 데이터 수집
├── flows/
│   ├── __init__.py               # 그대로
│   ├── entry.py                  # flow 0·1 — flow 1 장치 옵션 datacollector 제거
│   ├── env_check.py              # flow 2 — 기존 학습 환경 체크 + 신규 SO-ARM·카메라 체크 통합
│   ├── mode.py                   # flow 3 — NEW: "수집 / 학습 / 종료" mode 분기 질문
│   ├── teleop.py                 # NEW (datacollector/flows/teleop.py 이식)
│   ├── data_kind.py              # NEW (datacollector/flows/data_kind.py 이식)
│   ├── record.py                 # NEW (datacollector/flows/record.py 이식)
│   ├── transfer.py               # NEW (datacollector/flows/transfer.py 이식 — flow 7 옵션 H 재정의)
│   └── training.py               # 그대로 (mode = 학습 분기 시 호출)
└── configs/
    └── node.yaml                 # 갱신 — venv 경로 dgx 그대로, 책임에 "data_collection" 추가

dgx/scripts/
├── setup_env.sh                  # 갱신 — record + hardware + feetech extras 설치 추가
├── run_teleoperate.sh            # NEW (datacollector/scripts/run_teleoperate.sh 이식 + dgx 환경 맞춤)
├── push_dataset_hub.sh           # NEW (datacollector/scripts/push_dataset_hub.sh 이식)
├── check_hardware.sh             # NEW (datacollector/scripts/check_hardware.sh 이식 또는 신규)
├── preflight_check.sh            # 그대로 (학습 환경 체크)
├── smoke_test.sh                 # 그대로
├── save_dummy_checkpoint.sh      # 그대로
└── (기타 학습 스크립트 그대로)

dgx/pyproject.toml                # 갱신 — record + hardware + feetech extras 추가 (Category B 사용자 동의)
```

### orin 측 영향

- `orin/interactive_cli/flows/entry.py` — flow 1 장치 옵션 (orin/dgx/datacollector → orin/dgx) 1 줄 수정
- 그 외 orin 영향 없음 (orin 추론 책임 변동 X)

### scripts/ 측 영향

`smolVLA/scripts/` 의 datacollector 관련 3 개:

- `sync_dataset_collector_to_dgx.sh` → legacy (DGX 가 자기 자신에게 sync 무의미)
- `sync_ckpt_dgx_to_datacollector.sh` → legacy (DGX → DataCollector 케이스 무효. DGX → Orin sync 는 별도 신규 또는 기존 그대로)
- `deploy_datacollector.sh` → legacy (DataCollector 머신 회수)

후속 (DGX → Orin ckpt sync) 는 06 신규 todo 안 만들고, 차기 사이클 (07_leftarmVLA) 진입 시 필요 시 신규.

---

## 참고 레퍼런스

### 05 산출물 (직전 사이클 — 본 spec 의 출발점)

- `docs/work_flow/specs/history/05_interactive_cli.md` — interactive_cli 3 노드 패턴 + 옵션 α 흡수 후 X1 study 시 mode.py 설계 기반
- `docs/storage/12_interactive_cli_framework.md` — main.sh + flows/entry.py boilerplate (flow 0·1 패턴)
- `docs/storage/14_dgx_cli_flow.md` — dgx 학습 flow 3~ (preflight → 데이터셋 선택 → 학습+ckpt) — 본 spec 의 학습 mode 그대로 유지
- `docs/storage/15_datacollector_cli_flow.md` — datacollector flow 2~7 (teleop·record·transfer) — **legacy 이관 전 X1 study 에서 직접 Read + 수집 mode flow 설계 기반**
- `datacollector/interactive_cli/flows/{teleop, data_kind, record, transfer}.py` — 코드 자산 (이식 대상)
- `datacollector/scripts/{run_teleoperate.sh, push_dataset_hub.sh, check_hardware.sh}` — 스크립트 자산 (이식 대상)

### 04 산출물 (DGX 학습 환경)

- `docs/storage/06_dgx_venv_setting.md` — DGX venv (Python 3.12.3·.arm_finetune·PyTorch 2.10.0+cu130·lerobot editable) 검증 결과
- `docs/storage/09_dgx_structure.md` — dgx/ 디렉터리 책임 매트릭스 (M3 docs/storage/README 갱신 시 참조)

### lerobot 레퍼런스 (직접 Read 의무 — `.claude/skills/lerobot-reference-usage`)

- `docs/reference/lerobot/src/lerobot/scripts/lerobot_record.py` — flow 6 draccus 인자 (X2 record.py 이식 시 재확인)
- `docs/reference/lerobot/src/lerobot/scripts/lerobot_find_port.py` / `lerobot_find_cameras.py` — env_check.py 통합 시

### 본 사이클 룰

- `.claude/skills/claude-md-constraints` — Hard Constraints Category B (dgx/lerobot/ 옵션 B 영역, dgx/pyproject.toml 의존성 추가) 사용자 동의
- `.claude/skills/lerobot-upstream-check` — dgx 영역 변경 시 옵션 B 원칙 + Coupled File Rules
- `.claude/skills/lerobot-reference-usage` — 이식 시 datacollector 자산 + lerobot upstream 양쪽 직접 Read + 인용 의무

---

## Todo

> 그룹 구분: L=Legacy 이관, M=Plan/Doc 정합, X=DGX 흡수, V=실물 검증
> 진행 순서: [L1·L2 병렬] → [M1·M2·M3 병렬] → X1 study → [X2·X3·X4·X5 sequential] → [V1·V2·V3 sequential prod]

**[그룹 L — datacollector 자산 legacy 이관]**

### [x] TODO-L1: 기존 legacy/ 8 파일 → `legacy/01_pre_subagent_workflow/` 이동

**자동화 완료 (2026-05-02)**: git mv 8건 (모두 R rename 인식) + `docs/storage/legacy/README.md` 신규 작성. grep 결과 1건 발견 — `.claude/skills/lerobot-reference-usage/SKILL.md:111` 의 `docs/storage/legacy/CLAUDE_pre-subagent.md` 하드코딩 (Category A → 워커 수정 X, M3 또는 reflection 인계). code-tester verdict READY_TO_SHIP (Recommended 1: legacy/README.md `git add` 미실행 — 커밋 시점 처리).

- 타입: task
- DOD: `docs/storage/legacy/01_pre_subagent_workflow/` 신규 디렉터리 생성 + 기존 8 파일 (`agent_plan_pre-subagent.md`, `AGENTS_codex-guide.md`, `CLAUDE_pre-subagent.md`, `copilot-instructions_pre-subagent.md`, `current_task_pre-subagent.md`, `current_test_pre-subagent.md`, `HANDOFF_2026-04-30.md`, `README.md`) `git mv` 이동. `legacy/README.md` 신규 작성 (두 하위 폴더 색인).
- 구현 대상:
  - `docs/storage/legacy/01_pre_subagent_workflow/` (신규 디렉터리 + 기존 8 파일 git mv)
  - `docs/storage/legacy/README.md` (신규 — 두 하위 폴더 색인)
- 테스트: `git mv` 후 git status 확인 (rename 으로 인식)
- 제약: Category C 새 디렉터리 생성 — `docs/storage/legacy/` 하위는 **이미 docs/ 내부**라 Category C 비해당 (CLAUDE.md "새 디렉터리 생성 (`orin/`·`dgx/`·`docs/` 외)" — docs 내부 자유)
- 잔여 리스크: 기존 8 파일 중 하드코딩된 상호 참조 (예: `HANDOFF_2026-04-30.md` 가 다른 파일 명시) 가 깨지면 안 됨 — 이동 후 grep 검증

### [x] TODO-L2: datacollector 자산 통째 이관 → `legacy/02_datacollector_separate_node/`

**자동화 완료 (2026-05-02)**: git mv 7 자산 (datacollector/ 디렉터리 + docs 3 + scripts 3, 모두 R rename 인식, 합 23+3+3=29건) + `02_datacollector_separate_node/README.md` 신규. `datacollector/` smolVLA 직하에서 완전 제거 확인. grep 후속 인계 다수 발견 — **X2 처리**: `dgx/interactive_cli/flows/training.py` (L15·L54·L70·L72·L92·L494·L497 = 7건 sync_ckpt_dgx_to_datacollector.sh 인용). **M3·X2 처리**: `orin/interactive_cli/README.md`·`dgx/interactive_cli/README.md` (각 L7·L8·L35·L37·L39·L50 = 6건). **M3 처리**: `docs/storage/12·14·08·09·02·03·11_*.md`·`others/ckpt_transfer_scenarios.md` 다수. code-tester verdict READY_TO_SHIP (Recommended 2: 인계 라인 번호 보강 — 보고서 일부 라인 번호 누락, 실제는 더 많음).

- 타입: task
- DOD: `docs/storage/legacy/02_datacollector_separate_node/` 신규 디렉터리에 다음 자산 모두 git mv:
  - `datacollector/` 전체 (config/, data/, interactive_cli/, scripts/, tests/, pyproject.toml, README.md)
  - `docs/storage/07_datacollector_venv_setting.md` → `docs_storage_07_datacollector_venv_setting.md`
  - `docs/storage/10_datacollector_structure.md` → `docs_storage_10_datacollector_structure.md`
  - `docs/storage/15_datacollector_cli_flow.md` → `docs_storage_15_datacollector_cli_flow.md`
  - `scripts/sync_dataset_collector_to_dgx.sh` → `scripts_sync_dataset_collector_to_dgx.sh`
  - `scripts/sync_ckpt_dgx_to_datacollector.sh` → `scripts_sync_ckpt_dgx_to_datacollector.sh`
  - `scripts/deploy_datacollector.sh` → `scripts_deploy_datacollector.sh`
  - `02_datacollector_separate_node/README.md` 신규 (이동 사유·일자·후속 — *DGX 가 책임 흡수, datacollector 머신 운영 종료*)
- 구현 대상: 위 7 자산 git mv + README 1건
- 테스트: 이동 후 (a) 다른 파일에 datacollector 경로 하드코딩 grep — 발견 시 후속 수정 (M1 arm_2week_plan, M2 BACKLOG 자연 처리), (b) `datacollector/` 디렉터리 완전 제거 확인
- 제약: L1 이동과 디렉터리 신설 동시 처리 가능 — 단 L1 의 `legacy/README.md` 작성 시 02 폴더 색인도 포함 → L1·L2 동시 또는 L2·L1 순서로 작성
- 잔여 리스크:
  - 다른 파일에서 `smolVLA/datacollector/` 또는 `docs/storage/07/10/15_datacollector_*` 경로 하드코딩 — grep 으로 검출 후 M1·M2 갱신 시 함께 처리
  - `.claude/settings.json` permissions.allow 의 `Bash(ssh datacollector*:*)` 등 datacollector 관련 권한 — 본 spec 종료 후 남아있어도 무해 (사용 X), reflection 시점 정리 후보

**[그룹 M — Plan/Doc 정합 갱신]**

### [x] TODO-M1: arm_2week_plan.md 04·05·06~ 마일스톤 갱신

**자동화 완료 (2026-05-02)**: `arm_2week_plan.md` 5 영역 갱신 — 장비 역할 분담 (DGX 행 + 데이터 수집 + 시연장 이동), 04·05 마일스톤 본문 보존 + HTML 주석 정정 경위 추가, 신규 06 마일스톤 추가 (결정 A~F 인용), 시프트 4건 (06~09 → 07~10). 역사적 결정 본문 텍스트 완전 보존. code-tester verdict READY_TO_SHIP (Critical 0, Rec 1: L132 구 번호 텍스트 — M3 인계).

- 타입: task
- DOD: `arm_2week_plan.md` 본문 갱신:
  - 04 마일스톤 본문 — "DataCollector 별도 노드" 가정 → "DGX 가 시연장 이동 + 데이터 수집 흡수" 로 정정 (단 04 는 이미 history, 본문 텍스트만 정정 + "본 결정 이전 가정" 주석)
  - 05 마일스톤 본문 — datacollector 측 flow 언급 → DGX 흡수 후 통합 표시
  - 06 마일스톤 — 신규 추가: `06_dgx_absorbs_datacollector` (목표·결정·DOD 요약)
  - 07 (구 06) `_leftarmVLA` — 환경 행 갱신 (DataCollector → DGX 시연장 이동)
  - 08·09·10 (구 07·08·09) — 시프트
- 구현 대상: `arm_2week_plan.md` (single file 갱신)
- 테스트: 없음 (문서 정합)
- 제약: L1·L2 완료 후 (그래야 datacollector 경로 참조 정정 가능)
- 잔여 리스크: 기존 04·05 마일스톤 본문에 *역사적 결정* (DataCollector 별도 노드) 도 포함되어야 — 단순 삭제 X. "본 가정은 06 사이클에서 DGX 흡수로 정정" 같은 주석 처리 권고

### [x] TODO-M2: BACKLOG.md 정리 — datacollector 관련 항목 "완료(불요)" 마킹

**자동화 완료 (2026-05-02)**: 04 BACKLOG 8건 갱신 (#7 부분 / #8·#9·#10·#11·#12·#13 완료(불요) / #14 미완 06 V2 통합 처리). 05_interactive_cli 섹션 신규 추가 — 05 wrap 시점 누락 발견 후 함께 처리 (D3 완료 불요 / O3·X3 미완 06 V 그룹 통합). 항목 통째 삭제 X (사용자 결정 D — 결정 이력 보존). code-tester verdict READY_TO_SHIP (Critical 0, Rec 0).

- 타입: task
- DOD: `docs/work_flow/specs/BACKLOG.md` 다음 항목 처리 (사용자 결정 D — 완료(불요) 마킹 + 사유 명시):
  - 04 BACKLOG #11 (Python 3.12 셋업) — *완료(불요): DGX 가 데이터 수집 흡수, BACKLOG #11 우회 (06 결정)*
  - 04 BACKLOG #12 (DataCollector lerobot-calibrate) — *완료(불요): DataCollector 운영 종료 (06 결정). DGX 측 calibrate 는 06 의 V2 prod 검증으로 통합*
  - 04 BACKLOG #13 (DataCollector flow 7 분기) — *완료(불요): DGX flow 7 옵션 H 재정의로 흡수 (06 X1 study)*
  - 05 BACKLOG (D3 미완 7건 — Python 3.12·calibrate·flow 3~7·flow 7 분기) — 모두 *완료(불요): DGX 흡수 (06 결정). 06 의 V 그룹 prod 검증으로 통합*
  - 04 BACKLOG #14 (env_check.py NoneType) — **유지**: 06 V2 검증에서 dgx env_check.py 통합 시 함께 진단·수정 (DGX 환경 재현 가능)
- 구현 대상: `docs/work_flow/specs/BACKLOG.md` (single file 갱신)
- 테스트: 없음 (문서 정합)
- 제약: L1·L2 완료 후
- 잔여 리스크: 04·05 BACKLOG 항목 처리 결정 = 사용자 D 답 확정. 추가 발견 항목 (BACKLOG.md 의 다른 datacollector 행) 은 M2 에서 함께 처리

### [x] TODO-M3: docs/storage/README.md + docs/work_flow/ README 정합 갱신

**자동화 완료 (2026-05-02)**: 11 파일 정리 — `docs/storage/README.md` (datacollector 3 행 legacy 이관 표기 + 누락 행 6건 추가), `docs/work_flow/specs/README.md` (활성 spec 번호 현황 절 신규 + 시프트 표), L2 grep 인계 8 파일 (12·08·09·02·03·11·ckpt_transfer + orin·dgx interactive_cli README) — HTML 주석 + 취소선 방식 역사적 결정 보존. X2 인계 (training.py 다수 라인) + reflection 인계 (Category A SKILL.md L111). code-tester verdict READY_TO_SHIP (Critical 0, Rec 2 trivial — `05_datacollector_lerobot_diff.md` 실존 오기재 / `04_dgx_lerobot_diff.md` 색인 누락은 차기 처리).

- 타입: task
- DOD: docs 색인·README 정합 갱신:
  - `docs/storage/README.md` — datacollector 관련 3 파일 (07·10·15) 행 제거 또는 *legacy 이관* 표기
  - `docs/work_flow/specs/README.md` — 본 spec 추가 + 기존 spec 시프트 (06 → 07 등) 반영
  - `docs/storage/lerobot_upstream_check/README.md` 또는 색인 — `05_datacollector_lerobot_diff.md` 행 제거 (실제 파일은 미작성이었음, BACKLOG #11 (c) 옵션이 진행 안 됨)
- 구현 대상:
  - `docs/storage/README.md`
  - `docs/work_flow/specs/README.md`
  - `docs/storage/lerobot_upstream_check/README.md` (있는 경우)
- 테스트: 없음
- 제약: L1·L2·M1 완료 후 (이동·시프트 결정이 README 에 반영)
- 잔여 리스크: 다른 docs README 에 datacollector 관련 행 — grep 으로 검출 후 함께 정정

**[그룹 X — DGX 데이터 수집 흡수 (interactive_cli + scripts + 의존성)]**

### [x] TODO-X1: dgx flow 재설계 study (옵션 α mode 분기 구체화)

**자동화 완료 (2026-05-02)**: `docs/storage/14_dgx_cli_flow.md` 갱신 (학습 + 수집 통합) — §1 env_check mode 파라미터 / §2 mode 분기 G-1·G-2·G-3 / §3 수집 mode 이식 4 파일 명세 / §4 학습 mode 보존 / §5 transfer 분기 H-1·H-2·H-3 / §6 awaits_user G·H 발송 명세 / §7 X2 인계. legacy 4 파일 (`teleop·data_kind·record·transfer.py`) 직접 Read + 인용. code-tester verdict READY_TO_SHIP (Critical 0, Rec 1 trivial). **awaits_user G·H 사용자 발송 가능 — X2 dispatch 전 답 받기 대기**.

- 타입: study
- DOD: `docs/storage/13_dgx_cli_flow.md` (또는 기존 `14_dgx_cli_flow.md` 갱신 + rename) 신규/갱신:
  - flow 3 mode 질문 옵션 라벨·종료 분기 (사용자 결정 G)
  - flow 7 전송 분기 옵션 재정의 (HF Hub / 로컬 dgx 보관 / Orin rsync — 사용자 결정 H)
  - flow 5 학습 종류 옵션 (datacollector D1 §3 의 5개 후보 그대로 dgx 환경 적용 여부)
  - 기존 dgx 학습 flow (preflight → 데이터셋 선택 → 학습+ckpt) 의 mode = 학습 분기 진입 흐름
  - mode.py 코드 구조 (재진입 또는 단발 종료)
- 구현 대상: `docs/storage/14_dgx_cli_flow.md` (갱신 — 학습+수집 통합)
- 테스트: 없음
- 사용자 결정 사항: G·H (awaits_user 가능 — task-executor 후보 제안 후 사용자 답)
- 참조: `docs/storage/legacy/02_datacollector_separate_node/docs_storage_15_datacollector_cli_flow.md` (이식 직전 직접 Read), `datacollector/interactive_cli/flows/{teleop, data_kind, record, transfer}.py` (이식 대상 코드 직접 Read), 기존 `docs/storage/14_dgx_cli_flow.md` (학습 flow 보존)
- 잔여 리스크: study 단계에서 flow 6 lerobot-record draccus 인자가 dgx 환경 (Python 3.12·.arm_finetune venv) 에서 동일 동작하는지 — datacollector D1 §4 매핑 그대로 사용 가능한지 사전 검증

### [x] TODO-X2: dgx/interactive_cli/ 재구현 (mode.py + 수집 flow 이식)

**자동화 완료 (2026-05-02)**: 신규 5 + 수정 5 파일. G-4 (mode.py — 메뉴 + 수집 후 학습 전환 prompt + dataset_name 인계 4 단계) + H-(b) (transfer.py — 로컬/HF Hub 2 옵션, rsync 함수 완전 제거) 적용. record.py data_root 2곳 변경 (datacollector → dgx). training.py 7 라인 sync_ckpt 참조 정정 (실행 코드 0건). entry.py·orin entry.py VALID_NODES (orin, dgx). env_check.py mode 파라미터 selective check. ruff·py_compile 9/9 PASS. code-tester verdict READY_TO_SHIP (Critical 0, Rec 1: orin entry.py docstring datacollector 잔재 non-blocking).

- 타입: task
- DOD: dgx/interactive_cli/flows/ 에 다음 파일 신규/수정:
  - `mode.py` 신규 — flow 3 mode 분기 (X1 study 결정 G 적용)
  - `teleop.py`, `data_kind.py`, `record.py`, `transfer.py` 신규 — datacollector/flows/ 이식 + dgx 환경 (venv 경로 `~/smolvla/dgx/.arm_finetune` 등) 맞춤. transfer.py 는 H 결정 옵션 적용
  - `entry.py` 수정 — flow 1 장치 옵션 (orin/dgx/datacollector → orin/dgx)
  - `env_check.py` 수정 — 기존 학습 환경 체크 + 신규 SO-ARM·카메라 체크 통합 (datacollector env_check.py 의 7단계 통합 동작 흡수)
  - `training.py` 수정 — mode = 학습 분기 시 호출되도록 entry 변경
  - `configs/node.yaml` 수정 — 책임 행에 "data_collection" 추가
- 구현 대상: 위 7 파일 + README.md 갱신
- 테스트: 없음 (V2 검증)
- 제약: L2·X1 완료 후 (datacollector 자산이 legacy 로 이동된 상태에서 직접 Read + 이식)
- 잔여 리스크:
  - 이식 시 orin·dgx 형제 패턴 깨짐 가능성 — orin/interactive_cli/flows/entry.py 의 flow 1 장치 옵션도 동일하게 갱신 필요 (X2 와 함께 처리)
  - 이식 후 ruff 린트 오류 (datacollector → dgx 경로 리네임 시 import 자동 갱신 누락 가능)
  - `record.py` 의 lerobot-record draccus 인자 동적 생성이 dgx 환경에서 다른 venv 경로 사용 — subprocess 호출 시 venv activate 순서 정확히

### [x] TODO-X3: dgx/scripts/ 데이터 수집 책임 흡수

**자동화 완료 (2026-05-02)**: 신규 3 스크립트 — `run_teleoperate.sh` (datacollector 이식 + venv 경로 dgx), `push_dataset_hub.sh` (이식 + data_root + HF_TOKEN unset 안전 처리), `check_hardware.sh` (orin/tests/check_hardware.sh 04 G1 패턴 미러 — datacollector 원본 미존재). 책임 분담: `preflight_check.sh` (학습) + `check_hardware.sh` (수집) 1:1 대응. bash -n PASS (shellcheck 미설치). `sync_ckpt_dgx_to_orin.sh` 차기 사이클 (07) 위임. code-tester verdict READY_TO_SHIP (Critical 0, Rec 2 trivial).

- 타입: task
- DOD: dgx/scripts/ 에 다음 스크립트 신규 (datacollector/scripts/ 이식):
  - `run_teleoperate.sh` — datacollector/scripts/run_teleoperate.sh 이식. dgx venv 경로·python 호출 갱신
  - `push_dataset_hub.sh` — datacollector/scripts/push_dataset_hub.sh 이식. heredoc 환경변수 보안 패턴 그대로
  - `check_hardware.sh` — datacollector/scripts/check_hardware.sh 이식 또는 기존 dgx/scripts/preflight_check.sh 와 통합
  - 기존 dgx/scripts/{preflight_check, smoke_test, save_dummy_checkpoint}.sh 그대로 유지
- 구현 대상: dgx/scripts/ 신규 3 개
- 테스트: bash -n + shellcheck 정적 검증 (Phase 2 code-tester)
- 제약: L2·X2 완료 후
- 잔여 리스크: 이식 시 dgx 환경 (Python 3.12·.arm_finetune·CUDA 13) 과 datacollector 환경 (Python 3.12·.hylion_collector·CPU only) 차이 — venv 경로 외에 PyTorch/CUDA 의존성도 영향 가능

### [x] TODO-X4: dgx/pyproject.toml record + hardware + feetech extras 추가 (Category B awaits_user)

**자동화 완료 — skip 결정 (2026-05-02)**: task-executor 1단계 조사 결과 — torchcodec 0.10.0+cu130 호환 OK, 패키지 충돌 0건, **DGX 에 lerobot upstream editable 이미 설치 + 9 entrypoint 이미 등록**. 사용자 결정 (Option B 권고 채택) — `dgx/pyproject.toml` *신규 생성 불요* (중복 회피·단순성). **본 todo 변경 0건**. extras 설치 책임은 X5 단독. 조사 보고서 (`docs/work_flow/context/todos/X4/01_implementation.md`) 보존.

- 타입: task
- DOD: dgx/pyproject.toml 갱신:
  - `[project.optional-dependencies]` 에 `record`, `hardware`, `feetech` 3 extras 추가 (datacollector/pyproject.toml 그대로 이식)
  - `[project.scripts]` 에 lerobot-record·lerobot-replay·lerobot-find-port·lerobot-find-cameras·lerobot-calibrate·lerobot-setup-motors·lerobot-find-joint-limits·lerobot-info·lerobot-teleoperate 9 entrypoint 추가 (datacollector pyproject 그대로). 기존 lerobot-train 등 학습용 entrypoint 와 충돌 없음 사전 검증
  - 기존 학습 의존성 (smolvla·training extras) 과 record extras 의 패키지 충돌 사전 grep 검증
- 구현 대상: dgx/pyproject.toml (single file 갱신)
- 테스트: 정적 검증 (TOML parse + uv pip resolve dry-run — 가능 시)
- 제약: **사용자 동의 필수** (Category B — pyproject.toml 의존성 추가). awaits_user 분류
- 사용자 결정 사항: I (의존성 충돌 사전 검증 결과 보고 후 사용자 OK)
- 잔여 리스크:
  - record extras 의 torchcodec (>=0.3.0,<0.11.0) 가 DGX PyTorch 2.10.0+cu130 와 호환되는지 — torchcodec 는 PyTorch 2.x 까지만 지원 가능성. 사전 grep 의무
  - dgx 가 학습+수집 두 책임이라 venv 단일성 유지 vs 별도 venv 분리 결정 — 본 spec 은 단일 venv 가정 (X4 결정). 충돌 발견 시 별도 venv 분리 옵션 고려

### [x] TODO-X5: dgx/scripts/setup_env.sh record extras 설치 추가 (Coupled File Rule 1)

**자동화 완료 (2026-05-03)**: `dgx/scripts/setup_train_env.sh` (실제 파일명 — spec 본문 setup_env.sh 는 오기재) §3-c 블록 추가 — torchcodec 두 단계 분리 설치 (cu130 인덱스 → torchcodec, 그 다음 PyPI 기본 → 9 패키지). record + hardware + feetech 11 패키지 (중복 제외 9) 정확 인용. 기존 §3 (lerobot editable smolvla,training) 미접촉. bash -n PASS, idempotent OK. code-tester verdict MINOR_REVISIONS → patch 1회: Rec 1 (echo 메시지 버전 범위 표현) + Rec 2 (Option B 주석 정정) + Rec 3 (이력 — 09_dgx_structure.md 변경 이력 표 한 줄 추가, YAGNI 적용). Coupled File Rule 1 비활성 (Option B — pyproject 미변경).

- 타입: task
- DOD: dgx/scripts/setup_env.sh §3 (PyTorch 설치) 또는 §4 (lerobot 설치) 직후에 record + hardware + feetech extras 설치 step 추가:
  - `uv pip install -e ".[record,hardware,feetech]"` 또는 `pip install -e ".[record,hardware,feetech]"` (기존 setup_env.sh 패턴 따름)
  - x86_64 가 아닌 DGX 환경에서 `torchcodec` 조건부 설치 (X4 결정 결과 따름 — 호환 시 포함, 비호환 시 record extras 에서 제외)
- 구현 대상: dgx/scripts/setup_env.sh (single file 갱신)
- 테스트: bash -n + shellcheck 정적 검증
- 제약: X4 완료 후 (의존성 결정에 따른 setup_env 갱신)
- 잔여 리스크: setup_env.sh 변경은 Category B 자동 재시도 X 영역 — code-tester MAJOR 시 사용자 보고 게이트

**[그룹 V — Phase 3 사용자 실물 검증]**

### [ ] TODO-V1: DGX 시연장 이동 후 SO-ARM·카메라 직결 하드웨어 검증

**자동화 완료, BACKLOG 이관 (2026-05-03)**: devPC 정적 검증 통과 — bash -n exit 0, check_hardware.sh 5-step 구성 + orin 패턴 미러 정합. **사용자 무시 결정 (/verify-result B-3)**: DGX·Orin 시연장 환경 떨어진 상태로 실물 6항목 (USB 직결·dialout·v4l2·find-port·find-cameras·check_hardware.sh 실행) 검증 불가. BACKLOG 06 #1 이관 — 다음 사이클 (DGX 시연장 이동 가능 시) 처리.

- 타입: test
- DOD: 사용자 실물 환경 검증:
  - DGX 시연장 이동 (또는 시연장 환경 재현) 후 SO-ARM 2 대 (leader + follower) USB 직결
  - 카메라 2 대 (top + wrist) USB 직결 + v4l2-ctl 인식
  - DGX 사용자 (현재 사용자 또는 별도 sudo 가능 계정) `dialout` 그룹 권한 확인
  - lerobot-find-port 비대화형 호출 시 SO-ARM 포트 인식 (예: `/dev/ttyACM0`, `/dev/ttyACM1`)
  - lerobot-find-cameras opencv 호출 시 카메라 인덱스 발견
- 구현 대상: 없음 (검증·기록)
- 테스트: prod 검증 (DGX 시연장 + SO-ARM 2대 + 카메라 2대 직결)
- 제약: X4·X5 완료 + DGX 시연장 이동 가능 환경
- 잔여 리스크:
  - DGX Spark USB-C·USB-A 포트 수 부족 가능성 — USB hub 필요 시 사용자 별도 준비
  - DGX 사용자 계정의 dialout 그룹 미설정 시 sudo usermod 필요 (04 BACKLOG #4 와 동일 절차)
  - 시연장 환경 (전원·네트워크·조명) 미러링 검증 별도 — 04 M1·M2 verification_queue 와 통합 처리 가능

### [ ] TODO-V2: dgx/interactive_cli/ 수집 mode flow 0~7 완주 검증

**자동화 완료, BACKLOG 이관 (2026-05-03)**: devPC 정적 검증 통과 — py_compile 9/9 + ruff All passed + bash -n 3/3 + G-4 인계 체인 4단계 정합 + H-(b) rsync 함수 grep 0건 + record.py data_root 양쪽 정합. 04 BACKLOG #14 사전 진단: env_check.py 가 serial.Serial context manager 패턴이라 NoneType 재현 불가 (구조적). **사용자 무시 결정 (/verify-result B-3)**: DGX·Orin 시연장 환경 떨어짐. 실물 12항목 BACKLOG 06 #2 이관.

- 타입: test
- DOD: DGX VSCode remote-ssh → `bash dgx/interactive_cli/main.sh` → flow 0~2 → flow 3 mode = "데이터 수집" → flow 4~7 (teleop → record → transfer) 완주:
  - flow 4 lerobot-calibrate (follower + leader) 실 수행
  - flow 5 학습 종류 선택 (옵션 1 단순 pick-place 그대로)
  - flow 6 lerobot-record dummy episode 1~3 수집 (`--dataset.num_episodes=2`)
  - flow 7 전송 분기 3건 모두 검증:
    - HF Hub push (private) 실 검증 (05 T1 verification_queue 통합)
    - 로컬 dgx 보관 (`dgx/data/<dataset>/` 등 — 04 BACKLOG #7 통합)
    - Orin rsync (X1 study 결정에 따라 — 옵션 추가 시)
  - 04 BACKLOG #14 (env_check.py NoneType) 진단 + 수정 함께 처리
- 구현 대상: 없음 (검증·기록)
- 테스트: prod 검증
- 제약: V1 완료 후
- 잔여 리스크:
  - DGX 직결 후 첫 lerobot-calibrate 가 SO-ARM follower id_=3 (elbow_flex) Torque_Enable write 실패 (01 BACKLOG #10) 재발 가능 — 재실행 절차 사전 안내
  - flow 7 HF Hub push 가 학교 WiFi 환경에서 huggingface.co timeout 발생 시 (05 ANOMALIES 와 유사) 다른 네트워크에서 처리

### [ ] TODO-V3: dgx/interactive_cli/ 학습 mode 회귀 검증 (05 X3 통합)

**자동화 완료, BACKLOG 이관 (2026-05-03)**: devPC 정적 검증 통과 17/17 — sync_ckpt 실행 코드 0건 / 케이스 3 차기 사이클 안내 메시지 교체 / `run_training_flow_with_dataset` 신규 시그니처 + 기존 공존 / mode.py G-4 분기 호출 정합 / smoke 동의 게이트 정합 / dgx/scripts 3종 미접촉 / CKPT_CASES 4건 구조 정상. **사용자 무시 결정 (/verify-result B-3)**: DGX·Orin 시연장 환경 떨어짐. 실물 10항목 BACKLOG 06 #3 이관 (05 X3 통합 포함).

- 타입: test
- DOD: DGX `bash dgx/interactive_cli/main.sh` → flow 3 mode = "학습" → 기존 학습 flow (preflight → 데이터셋 선택 → 학습 + ckpt 관리) 회귀 검증:
  - V2 에서 수집한 dummy 데이터셋 학습 (smoke_test 5~15분)
  - 또는 svla_so100_pickplace HF Hub 다운로드 후 smoke 학습
  - save_dummy_checkpoint 실 검증 + ckpt 케이스 목록 출력 (05 X3 NEEDS_USER_VERIFICATION 통합 처리)
  - 04 X3·T1·T2 verification_queue 통합 — 05 사이클 미완 부분 자연 흡수
- 구현 대상: 없음 (검증·기록)
- 테스트: prod 검증
- 제약: V2 완료 후 (수집 데이터셋 활용 또는 V2 와 독립적으로 HF Hub 데이터셋 활용 가능)
- 잔여 리스크:
  - DGX 환경에서 record extras 추가 후 기존 학습 의존성 (smolvla / training) 회귀 — V3 가 최초 통합 검증
  - smoke_test 동의 게이트 + 큰 다운로드 (>100MB) 동의 정책 적용 (05 X2 동의 게이트 패턴 그대로)

---

## 잔여 리스크 / 의존성

### 본 spec 자체 리스크

- **dgx pyproject 의존성 충돌**: torchcodec 가 DGX PyTorch 2.10.0+cu130 와 비호환일 가능성 — X4 사전 grep + uv pip resolve dry-run 으로 사전 차단
- **DGX 시연장 이동 운영 부담**: DGX Spark 가 학교 연구실 ↔ 시연장 사이 이동 시 무게·전원·네트워크 — 본 spec 범위 외 (사용자 운영 결정)
- **datacollector 머신 (smallgaint) 처리**: legacy 이관 후 머신 자체는 그대로 — 회수 또는 다른 용도 재활용 결정은 본 spec 외 사용자 결정
- **05 verification_queue 7건 통합**: 04 + 05 의 미검증 7건 (D3·O3·X3 + Python 3.12 등) 이 본 spec V 그룹 prod 검증으로 자연 통합. M2 BACKLOG 정리에서 추적 보장

### CLAUDE.md 갱신 후속

- E 답으로 4 곳 정리 완료 (Phase 1 시점). Phase 2 진행 중 추가 datacollector 흔적 발견 시 reflection 시점 처리 — 본 spec wrap 시점 META 후보
- §Architecture At A Glance 의 `smolVLA/orin/` 행 (`Main development layer: smolVLA/orin/`) 은 *추론 layer 만* 의미라 그대로. 본 결정으로 *학습 + 수집 layer = dgx* 명시는 §Project Snapshot 첫 줄에서 충분

### META 제안 (04·05 사이클 후속 잔재)

- 05 ANOMALIES #1 (settings.json permissions allow 추가) — 본 spec 진행 중 ssh datacollector*·deploy_datacollector 등 datacollector 관련 권한이 자연 무효화. 사용자 권한 prompt 횟수 측정 → reflection 시점 정리 후보
- 05 META #9 (hook 메인 세션 우회 조건) — 본 spec 의 CLAUDE.md 갱신 (Phase 1 시점) 시 hook block 발생 안 했는지 확인. 발생 시 META #9 차기 사이클 격상

---

> Backlog → [docs/work_flow/specs/BACKLOG.md](BACKLOG.md) 에 본 스펙 섹션을 추가하여 운영
