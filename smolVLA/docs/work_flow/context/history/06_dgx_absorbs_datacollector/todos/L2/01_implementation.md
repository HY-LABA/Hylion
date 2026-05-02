# TODO-L2 — Implementation

> 작성: 2026-05-02 | task-executor | cycle: 1

## 목표

datacollector 노드 자산 전체 + 관련 docs/storage 3 파일 + scripts 3 파일을
`docs/storage/legacy/02_datacollector_separate_node/` 하위로 git mv 이관.
사유·일자·후속을 담은 README 신규 작성.

---

## §1 변경 자산 목록 (git mv 7건 + README 신규 1건)

| 원래 경로 | 이관 후 경로 | 변경 종류 |
|---|---|---|
| `datacollector/` (디렉터리 전체) | `docs/storage/legacy/02_datacollector_separate_node/datacollector/` | git mv (rename) |
| `docs/storage/07_datacollector_venv_setting.md` | `docs/storage/legacy/02_datacollector_separate_node/docs_storage_07_datacollector_venv_setting.md` | git mv (rename) |
| `docs/storage/10_datacollector_structure.md` | `docs/storage/legacy/02_datacollector_separate_node/docs_storage_10_datacollector_structure.md` | git mv (rename) |
| `docs/storage/15_datacollector_cli_flow.md` | `docs/storage/legacy/02_datacollector_separate_node/docs_storage_15_datacollector_cli_flow.md` | git mv (rename) |
| `scripts/sync_dataset_collector_to_dgx.sh` | `docs/storage/legacy/02_datacollector_separate_node/scripts_sync_dataset_collector_to_dgx.sh` | git mv (rename) |
| `scripts/sync_ckpt_dgx_to_datacollector.sh` | `docs/storage/legacy/02_datacollector_separate_node/scripts_sync_ckpt_dgx_to_datacollector.sh` | git mv (rename) |
| `scripts/deploy_datacollector.sh` | `docs/storage/legacy/02_datacollector_separate_node/scripts_deploy_datacollector.sh` | git mv (rename) |
| (신규) `docs/storage/legacy/02_datacollector_separate_node/README.md` | — | 신규 작성 |

### datacollector/ 내부 구조 (git mv 로 통째 이동)

git status 에서 rename 으로 인식된 내부 파일 목록 (주요):

```
R  datacollector/README.md -> docs/storage/legacy/02_datacollector_separate_node/datacollector/README.md
R  datacollector/config/README.md -> ...
R  datacollector/interactive_cli/README.md -> ...
R  datacollector/interactive_cli/configs/node.yaml -> ...
R  datacollector/interactive_cli/flows/__init__.py -> ...
R  datacollector/interactive_cli/flows/data_kind.py -> ...
R  datacollector/interactive_cli/flows/entry.py -> ...
R  datacollector/interactive_cli/flows/env_check.py -> ...
R  datacollector/interactive_cli/flows/record.py -> ...
R  datacollector/interactive_cli/flows/teleop.py -> ...
R  datacollector/interactive_cli/flows/transfer.py -> ...
R  datacollector/interactive_cli/main.sh -> ...
R  datacollector/pyproject.toml -> ...
R  datacollector/scripts/push_dataset_hub.sh -> ...
R  datacollector/scripts/run_teleoperate.sh -> ...
R  datacollector/scripts/setup_env.sh -> ...
R  datacollector/tests/README.md -> ...
```

`datacollector/data/` 는 git untracked (`.gitignore` 제외 대상) — 이동 확인 별도 필요.

---

## §2 grep 검증 결과

### 검증 대상 경로 패턴

1. `smolVLA/datacollector/` 또는 `/datacollector/`
2. `docs/storage/07_datacollector` / `docs/storage/10_datacollector` / `docs/storage/15_datacollector`
3. `scripts/sync_dataset_collector_to_dgx` / `scripts/sync_ckpt_dgx_to_datacollector` / `scripts/deploy_datacollector`

### 결과 요약

하드코딩 잔재가 발견된 **현행 (non-legacy, non-history) 파일** 목록:

| 파일 | 하드코딩 내용 | 처리 주체 |
|---|---|---|
| `docs/storage/12_interactive_cli_framework.md` | `venv: ~/smolvla/datacollector/.hylion_collector` (line 100, 137) | M3 또는 X 그룹 (datacollector 행 legacy 표기) |
| `docs/storage/14_dgx_cli_flow.md` | `scripts/sync_ckpt_dgx_to_datacollector.sh` 인용 (line 83, 263) | M3 또는 X1 (flow study 시 legacy 경로로 정정) |
| `docs/storage/08_orin_structure.md` | `scripts/deploy_datacollector.sh`, `scripts/sync_dataset_collector_to_dgx.sh` (line 170~171) | M3 (08 orin 구조 문서 — datacollector 행 legacy 표기) |
| `docs/storage/09_dgx_structure.md` | `scripts/sync_dataset_collector_to_dgx.sh` (line 139) | M3 (09 dgx 구조 문서) |
| `docs/storage/02_hardware.md` | `~/smolvla/datacollector/data/` (line 131) | M3 |
| `docs/storage/03_software.md` | `docs/storage/07_datacollector_venv_setting.md` 참조 (line 109) | M3 (legacy 경로로 정정 또는 삭제) |
| `docs/storage/11_demo_site_mirroring.md` | `docs/storage/10_datacollector_structure.md` 참조 (line 8) | M3 |
| `docs/storage/others/ckpt_transfer_scenarios.md` | `scripts/sync_ckpt_dgx_to_datacollector.sh` (line 9, 93, 95) | M3 |
| `orin/interactive_cli/README.md` | `bash scripts/deploy_datacollector.sh` (line 50) | M3 또는 X2 (orin entry.py 수정 시 README 동반 갱신) |
| `dgx/interactive_cli/README.md` | `bash scripts/deploy_datacollector.sh` (line 50) | M3 또는 X2 |
| `dgx/interactive_cli/flows/training.py` | `scripts/sync_ckpt_dgx_to_datacollector.sh` 인용 (line 15, 70, 72) | X2 (training.py 수정 — DGX sync 흡수 시 제거 또는 legacy 표기) |

### history/context 파일 (정정 불필요 — 과거 이력 보존)

`docs/work_flow/context/history/` 하위 및 `docs/work_flow/specs/history/` 하위 파일들에도
다수의 datacollector 경로 하드코딩이 발견되었으나 **과거 이력 파일** 이므로 정정 불필요.
context/plan.md, context/log.md 는 M1~M3 이 갱신 시 자연 처리.

### spec 본문 (06_dgx_absorbs_datacollector.md)

spec 본문 자체에 이관 전 경로 언급 다수 — 본 spec 은 *이관 결정 문서* 이므로 원문 보존. 정정 불필요.

---

## §3 잔여 리스크

### 인계 필요 항목 (M1·M2·M3 책임)

| 항목 | 발견 위치 | 인계 todo |
|---|---|---|
| `docs/storage/12_interactive_cli_framework.md` datacollector venv 행 | line 100, 137 | M3 |
| `docs/storage/14_dgx_cli_flow.md` `sync_ckpt_dgx_to_datacollector.sh` 인용 | line 83, 263 | M3 / X1 |
| `docs/storage/08_orin_structure.md` 스크립트 행 | line 170~171 | M3 |
| `docs/storage/09_dgx_structure.md` 스크립트 행 | line 139 | M3 |
| `docs/storage/02_hardware.md` datacollector/data/ 경로 | line 131 | M3 |
| `docs/storage/03_software.md` 07_datacollector_venv 참조 | line 109 | M3 |
| `docs/storage/11_demo_site_mirroring.md` 10_datacollector 참조 | line 8 | M3 |
| `docs/storage/others/ckpt_transfer_scenarios.md` sync 스크립트 경로 | line 9, 93, 95 | M3 |
| `orin/interactive_cli/README.md` deploy_datacollector 명령 | line 50 | M3 / X2 |
| `dgx/interactive_cli/README.md` deploy_datacollector 명령 | line 50 | M3 / X2 |
| `dgx/interactive_cli/flows/training.py` sync_ckpt_dgx_to_datacollector 인용 | line 15, 70, 72 | X2 |

### datacollector/data/ untracked 이슈

`datacollector/data/` 는 git untracked (`.gitignore` 제외) 상태. git mv 로 이동 시 git 이 추적하지 않아
`docs/storage/legacy/02_datacollector_separate_node/datacollector/data/` 에 파일이 물리적으로 이동했으나
git status 에 `?? docs/storage/legacy/02_datacollector_separate_node/datacollector/data/` 로 표시됨.
실제 로컬 데이터가 있다면 별도 수동 확인 필요 — X 그룹 todo 에서 참조하지 않으므로 영향 없음.

### `.claude/settings.local.json` permissions allow

`Bash(mkdir -p /home/babogaeguri/Desktop/Hylion/smolVLA/datacollector/...)` 등 datacollector 절대경로
권한이 settings.local.json 에 잔재. 운영상 무해 (사용 X) — reflection 시점 정리 후보.

---

## §4 lerobot upstream 영향

없음. 본 todo 는 git mv 이관 및 README 작성만 포함하며, `orin/lerobot/`, `dgx/lerobot/`,
`pyproject.toml`, `setup_env.sh` 등 Coupled File Rules 대상 영역을 변경하지 않음.

---

## 적용 룰

- CLAUDE.md Hard Constraints:
  - `docs/reference/` 미변경 (Category A) ✓
  - `rm -rf` 사용 X — `git mv` 로만 처리 (Category D) ✓
  - Category C "새 디렉터리 생성" — `docs/storage/legacy/` 하위는 `docs/` 내부라 Category C 비해당 ✓
- Coupled File Rule:
  - `orin/lerobot/` 미변경 → 03_orin_lerobot_diff.md 갱신 불필요 ✓
  - `pyproject.toml` 미변경 → 02_orin_pyproject_diff.md 갱신 불필요 ✓
- 레퍼런스 활용: 본 todo 는 파일 이관 + README 작성이므로 lerobot 레퍼런스 코드 참조 불필요.
  SKILL_GAP 없음.
- git mv 사용 (mv 대신) — history 보존 확인 (git status 에 R 로 rename 인식) ✓

## code-tester 입장에서 검증 권장 사항

- `git status` — 모든 이동 자산이 `R` (rename) 으로 인식되는지 확인
- `ls docs/storage/legacy/02_datacollector_separate_node/` — 7 자산 + README 8건 존재 확인
- `ls datacollector/ 2>/dev/null || echo "REMOVED"` — `datacollector/` 디렉터리 완전 제거 확인
- `ls docs/storage/ | grep -E "07_|10_|15_datacollector"` — 원래 위치에 파일 없음 확인
- `ls scripts/ | grep -E "sync_dataset|sync_ckpt_dgx_to_datacollector|deploy_datacollector"` — 원래 위치에 파일 없음 확인
- DOD 항목 충족: (a) datacollector/ 경로 하드코딩 grep 결과 §2 에 기록됨 ✓, (b) datacollector/ 완전 제거 ✓
