# smolVLA 디렉토리 가이드

`LABA5_Bootcamp/smolVLA` 하위 구조와 문서 역할을 정리한 안내 파일입니다.

## 디렉토리 구조

```text
smolVLA/
├── CLAUDE.md                            # Claude Code 자동 참조 컨텍스트
├── AGENTS.md                            # OpenAI Codex 컨텍스트
├── README.md
├── arm_2week_plan.md                    # 2주 실행 계획 및 마일스톤
├── agent_plan.md                        # agent 작업 계획
├── scripts/                             # devPC 측 운영 스크립트
│   ├── deploy_orin.sh                   # devPC → Orin rsync 배포 (orin/)
│   ├── deploy_dgx.sh                    # devPC → DGX rsync 배포 (dgx/ + docs/reference/lerobot/)
│   ├── sync_ckpt_dgx_to_orin.sh         # DGX 학습 체크포인트 → Orin (devPC 경유 2-hop)
│   ├── dev-connect.sh                   # VS Code Remote SSH로 Orin/DGX 동시 연결
│   ├── sync_to_laba5.sh                 # Hylion/BG smolVLA → LABA5_Bootcamp 백업 (Linux/macOS)
│   └── sync_to_laba5.ps1                # 같은 기능 (Windows)
├── .codex                               # Codex 설정
├── .github/
│   └── copilot-instructions.md         # GitHub Copilot 컨텍스트
├── .claude/
│   └── commands/                        # Claude Code 커스텀 슬래시 커맨드
│       ├── handoff-task.md              # 스펙 미완료 todo → current_task.md
│       ├── handoff-test.md              # 스펙 미완료 todo → current_test.md
│       ├── complete-task.md             # 구현 결과 → 스펙 반영 + history 보관
│       ├── complete-test.md             # 테스트 결과 → 스펙 반영 + history 보관
│       └── update-docs.md              # navigator 문서 최신화
├── docs/
│   ├── repo_management.md               # Hylion/BG 운영 + 두 컴퓨터 동기화 + LABA5 백업 흐름
│   ├── work_flow/                       # 업무 과정 전체 기록
│   │   ├── specs/                       # 에이전트 간 인계 스펙 (NN_*.md)
│   │   │   ├── README.md
│   │   │   ├── 00_template.md           # 스펙 파일 템플릿
│   │   │   ├── BACKLOG.md               # 누적 백로그 (각 스펙의 Backlog 통합)
│   │   │   ├── 02_dgx_setting.md        # (예시) 현재 진행 중인 스펙
│   │   │   └── history/                 # 완료된 스펙 보관 (예: 01_teleoptest.md)
│   │   └── context/                     # 현재 작업 컨텍스트 및 히스토리
│   │       ├── current_task.md          # 현재 진행 중인 작업 상태
│   │       ├── current_test.md          # 현재 테스트 상태
│   │       └── history/                 # 완료된 task/test 히스토리
│   ├── lerobot_study/                   # lerobot/SmolVLA 학습 노트 (마일스톤 순서 prefix)
│   │   ├── 00_lerobot_repo_overview.md
│   │   ├── 01_lerobot_root_structure.md
│   │   ├── 02_lerobot_src_structure.md
│   │   ├── 03_smolvla_architecture.md           # TODO-03: SmolVLA 구조 + config 분기
│   │   ├── 03b_smolvla_milestone_config_guide.md # TODO-03 보조: 마일스톤별 분기 가이드
│   │   ├── 04_lerobot_dataset_structure.md      # TODO-04: 데이터셋 구조
│   │   └── 05_hf_model_selection.md             # TODO-05: HF 모델 선택
│   ├── reference/                       # 외부 참조 문서 + 읽기 전용 서브모듈
│   │   ├── lerobot/                     # HuggingFace lerobot upstream submodule
│   │   ├── reComputer-Jetson-for-Beginners/ # Seeed Jetson beginner reference submodule
│   │   ├── seeed-lerobot/               # Seeed lerobot fork submodule
│   │   ├── nvidia_official/             # NVIDIA PyTorch on Jetson 설치 공식 문서 (md+pdf)
│   │   ├── seeedwiki/                   # Seeed Wiki 문서 한국어 번역 보관
│   │   │   └── seeedwiki_so101.md       # SO-ARM100/101 + LeRobot 튜토리얼 번역
│   │   └── reference_link.md
│   └── storage/                         # 환경/장비 기록 문서
│       ├── 01_smolvla_arm_env_requirements.md   # 요구사항 + 문서 네비게이션
│       ├── 02_hardware.md
│       ├── 03_software.md
│       ├── 04_devnetwork.md
│       ├── 05_orin_venv_setting.md
│       ├── devices_snapshot/            # 장치 점검 스크립트 + 수집 결과
│       │   ├── collect_snapshot.sh
│       │   ├── run_snapshots.sh
│       │   └── *_snapshot_*.txt
│       ├── lerobot_upstream_check/      # lerobot upstream 추적 및 충돌 점검
│       │   ├── 01_compatibility_check.md
│       │   ├── 02_orin_pyproject_diff.md
│       │   ├── 03_orin_lerobot_diff.md
│       │   ├── 99_lerobot_upstream_Tracking.md
│       │   └── check_update_diff.sh
│       ├── logs/                         # 작업 로그/진행 TODO 기록
│       │   └── todo.md
│       └── others/                      # 수동 설치용 사전 빌드 wheel 등 보관
│           └── torchvision-0.20.0a0+afc54f7-cp310-cp310-linux_aarch64.whl   # Seeed SharePoint JP 6.1&6.2 + PyTorch 2.5 대응
├── orin/                                # Jetson Orin 배포 패키지 (추론)
│   ├── pyproject.toml                   # Orin용 (torch>=2.5, Python>=3.10, smolvla extras)
│   ├── lerobot/                         # curated 추론 필수 모듈
│   │   ├── __init__.py, __version__.py, types.py
│   │   ├── cameras/{opencv,realsense,zmq}/
│   │   ├── configs/
│   │   ├── envs/
│   │   ├── model/
│   │   ├── motors/feetech/
│   │   ├── optim/
│   │   ├── policies/{smolvla,rtc}/
│   │   ├── processor/
│   │   ├── robots/so_follower/
│   │   ├── scripts/                     # lerobot_eval / lerobot_teleoperate / lerobot_train 등 18개 스크립트
│   │   ├── teleoperators/so_leader/
│   │   └── utils/
│   ├── calibration/                     # Orin에서 생성된 calibration 파일 보관 (rsync 배포 제외)
│   ├── examples/
│   │   └── tutorial/smolvla/
│   │       ├── smoke_test.py
│   │       └── using_smolvla_example.py
│   └── scripts/
│       ├── run_teleoperate.sh           # SO-ARM calibrate·teleoperate 편의 스크립트
│       └── setup_env.sh                 # Orin에서 실행 — venv + pip install
└── dgx/                                 # DGX Spark 학습 환경 (orin/ 과 형제)
    ├── README.md                        # 운영 체크리스트 + Walking RL 보호 원칙
    └── scripts/
        ├── setup_train_env.sh           # venv + PyTorch 2.10.0+cu130 + lerobot editable
        ├── preflight_check.sh           # 학습 전 OOM/Walking RL 보호 게이트
        ├── smoke_test.sh                # lerobot-train --steps=1 검증
        └── save_dummy_checkpoint.sh     # TODO-10b 검증용 dummy 체크포인트 생성
```

---

## lerobot 업데이트 워크플로우

lerobot upstream이 업데이트되면 아래 순서로 진행합니다.

**0. 의존성 충돌 사전 점검**

`docs/storage/lerobot_upstream_check/check_update_diff.sh` 로 변경 내용을 확인한 후,
`docs/storage/lerobot_upstream_check/01_compatibility_check.md` 에 점검 결과를 기록합니다.

주요 확인 항목: Python 3.12 전용 문법 추가 여부, pyproject.toml 의존성 범위 변경, 신규 패키지의 aarch64/cp310 빌드 존재 여부.

**1. submodule pull**

```bash
git submodule update --remote smolVLA/docs/reference/lerobot
```

**2. orin/lerobot/ 수동 갱신**

`smolVLA/docs/reference/lerobot/src/lerobot/` 에서 필요한 파일을 `smolVLA/orin/lerobot/` 로 직접 복사합니다.  
(자동 동기화 스크립트는 제거됨 — 필요 시 재작성)

**3. Orin에 배포**

```bash
./smolVLA/scripts/deploy_orin.sh
```

`smolVLA/orin/` 전체를 Orin의 `~/smolvla/orin/` 로 rsync 합니다 (dgx 와 형제 구조).

**4. Orin에서 환경 재설치 (의존성이 바뀐 경우)**

```bash
ssh orin
rm -rf ~/smolvla/orin/.hylion_arm
bash ~/smolvla/orin/scripts/setup_env.sh
```

---

## Orin 최초 설치

```bash
# devPC
./smolVLA/scripts/deploy_orin.sh

# Orin
ssh orin
bash ~/smolvla/orin/scripts/setup_env.sh
source ~/smolvla/orin/.hylion_arm/bin/activate
```

---

## 폴더별 용도

| 폴더/파일 | 용도 |
|---|---|
| `CLAUDE.md` | Claude Code 자동 참조 컨텍스트 |
| `AGENTS.md` | OpenAI Codex 컨텍스트 |
| `.github/copilot-instructions.md` | GitHub Copilot 컨텍스트 |
| `.claude/commands/` | Claude Code 커스텀 슬래시 커맨드 정의 |
| `.codex` | Codex 설정 파일 |
| `arm_2week_plan.md` | 2주 실행 계획, 마일스톤 |
| `agent_plan.md` | agent 작업 계획 |
| `scripts/deploy_orin.sh` | orin/ → Orin rsync (devPC에서 실행) |
| `scripts/deploy_dgx.sh` | dgx/ + docs/reference/lerobot/ → DGX rsync (devPC에서 실행) |
| `scripts/sync_ckpt_dgx_to_orin.sh` | DGX 학습 체크포인트 → Orin (devPC 경유 2-hop, devPC에서 실행) |
| `scripts/dev-connect.sh` | VS Code Remote SSH로 Orin/DGX 동시 연결 (devPC에서 실행) |
| `scripts/sync_to_laba5.sh` | Hylion/BG smolVLA → LABA5_Bootcamp 단방향 백업 (Linux/macOS, 우분투) |
| `scripts/sync_to_laba5.ps1` | 같은 기능 (Windows) |
| `docs/repo_management.md` | Hylion 레포 운영 + 두 컴퓨터 동기화 + 메인 머지 흐름 + LABA5 단방향 백업 |
| `docs/work_flow/` | 업무 과정 전체 기록 — specs + context 통합 관리 |
| `docs/work_flow/specs/` | 에이전트 간 인계 스펙 (`NN_*.md`) — `/handoff-*`가 읽고, `/complete-*`가 결과 반영 |
| `docs/work_flow/context/` | 현재 작업 컨텍스트(`current_task.md`, `current_test.md`) 및 날짜별 히스토리 |
| `docs/reference/` | 외부 참조 전체 — **수정 금지** |
| `docs/reference/lerobot/` | HuggingFace lerobot upstream submodule (수정 금지) |
| `docs/reference/reComputer-Jetson-for-Beginners/` | Seeed Jetson beginner reference submodule (수정 금지) |
| `docs/reference/seeed-lerobot/` | Seeed lerobot fork submodule (수정 금지) |
| `docs/reference/nvidia_official/` | NVIDIA PyTorch on Jetson 설치 공식 문서 (수정 금지) |
| `docs/reference/seeedwiki/` | Seeed SO-101 위키 참조 문서 (수정 금지) |
| `docs/lerobot_study/` | lerobot/SmolVLA 학습 노트 — 마일스톤 순서 prefix (`00_*`~`02_*` 사전 학습, `03_*`~`05_*` 학습 TODO 산출물, `03b_*` 는 동일 마일스톤 보조 문서) |
| `docs/storage/` | 환경/장비 실측 기록 문서 |
| `orin/` | Orin 배포 패키지 — curated lerobot + 예제 + 설치 스크립트 (추론) |
| `dgx/` | DGX Spark 학습 환경 — venv setup + preflight + smoke test (학습) |

---

## `docs/storage/` 문서 역할

| 파일 | 역할 |
|---|---|
| `01_smolvla_arm_env_requirements.md` | 요구사항 정의 + 하위 문서 네비게이션 |
| `02_hardware.md` | 하드웨어 실측값 (devPC / Orin / DGX Spark / SO-ARM BOM) |
| `03_software.md` | 소프트웨어 실측값 (OS, JetPack, CUDA, 패키지 버전) |
| `04_devnetwork.md` | devPC ↔ Orin ↔ DGX Spark 네트워크/SSH 연결 설정 |
| `05_orin_venv_setting.md` | Orin Python venv 구성 상세 — PyTorch 설치 방식·근거, pip 패키지 현황 |

### `devices_snapshot/`

| 파일 | 역할 |
|---|---|
| `collect_snapshot.sh` | Orin/DGX 환경 정보 수집 payload (원격 실행용) |
| `run_snapshots.sh` | 두 디바이스 동시 수집 후 `devices_snapshot/` 저장 |
| `*_snapshot_*.txt` | 수집된 스냅샷 결과 |

### `lerobot_upstream_check/`

| 파일 | 역할 |
|---|---|
| `check_update_diff.sh` | upstream 업데이트 비교 스크립트 (`HEAD@{1} -> HEAD`) |
| `01_compatibility_check.md` | 의존성 충돌 점검 기록 (Python 버전, 신규 문법, 패키지 변경) |
| `02_orin_pyproject_diff.md` | upstream vs orin/pyproject.toml 변경 이력 누적 기록 |
| `03_orin_lerobot_diff.md` | upstream vs orin/lerobot/ 코드 변경 이력 누적 기록 |
| `99_lerobot_upstream_Tracking.md` | lerobot 동기화 이력 누적 기록 |

### `logs/`

| 파일 | 역할 |
|---|---|
| `todo.md` | Orin 환경 정비/검증 작업 로그 및 진행 상태 기록 |

### `others/`

PyPI·공식 인덱스에서 구할 수 없어 **수동 배포가 필요한 사전 빌드 wheel**을 보관합니다.

| 파일 | 역할 |
|---|---|
| `torchvision-0.20.0a0+afc54f7-cp310-cp310-linux_aarch64.whl` | Seeed SharePoint 제공 Jetson aarch64 빌드. JetPack 6.1 & 6.2 + CUDA 12.6 + **PyTorch 2.5 전용** torchvision 0.20. Orin에서 `pip install <file> --no-deps`로 수동 설치 (`setup_env.sh`가 PyPI 설치 실패 시 대체). 원본: [reComputer 3.5-Pytorch/README.md L60](docs/reference/reComputer-Jetson-for-Beginners/3-Basic-Tools-and-Getting-Started/3.5-Pytorch/README.md#L60) |

---

## AI 어시스턴트 컨텍스트 파일

| 파일 | 대상 도구 |
|---|---|
| `CLAUDE.md` | Claude Code |
| `AGENTS.md` | OpenAI Codex |
| `.codex` | OpenAI Codex |
| `.github/copilot-instructions.md` | GitHub Copilot |
| `.claude/commands/` | Claude Code 커스텀 슬래시 커맨드 |

---

## 참고

- 장치 스냅샷 수집: `bash docs/storage/devices_snapshot/run_snapshots.sh` (SSH alias `orin` / `dgx` 필요)
- upstream 변경 비교: `bash docs/storage/lerobot_upstream_check/check_update_diff.sh`
- PyTorch 설치 경로 (Orin): `https://pypi.jetson-ai-lab.io/jp6/cu126` (torch 2.11.0, cp310, cu126)
- 구조가 변경되면 이 README도 함께 갱신합니다.
