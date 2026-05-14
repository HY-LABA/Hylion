# 99. lerobot Upstream Tracking

이 문서는 lerobot upstream 변화를 추적하고 Orin 환경과의 동기화 이력을 누적 기록한다.

---

## 디렉터리 파일 색인

`docs/storage/lerobot_upstream_check/` 하위 파일 목록 및 각 파일의 역할.

| 파일 | 생성 시점 | 역할 요약 |
|---|---|---|
| `01_compatibility_check.md` | 2026-04-22 (03_smolvla_test_on_orin) | lerobot upstream 의존성 충돌 점검 기록. Python 3.10 / CUDA 12.6 / aarch64 Orin 환경 고정값 대비 upstream 요구사항 비교. `check_update_diff.sh` 연계. |
| `02_orin_pyproject_diff.md` | 2026-04-22 (03_smolvla_test_on_orin) | `orin/pyproject.toml` vs upstream 차이 이력. `requires-python` 완화 (`>=3.12` → `>=3.10`), torch/torchvision 의존성 제거 등 Coupled File Rule 의무 기록 대상. |
| `03_orin_lerobot_diff.md` | 2026-04-23 (03_smolvla_test_on_orin) | `orin/lerobot/` vs upstream 코드 변경 이력. Python 3.10 호환 backport 패치 (PEP 695 generic→TypeVar, type alias→Union 등) 기록. Coupled File Rule 의무 기록 대상. |
| `04_dgx_lerobot_diff.md` | 2026-04-28 (02_dgx_setting) | ⚠️ **이름 주의** — lerobot 코드 diff 가 아닌 **DGX wrapper 스크립트 변경 이력**. DGX 는 `docs/reference/lerobot/` editable install 이라 lerobot 코드 diff 0; `dgx/scripts/*.sh` (setup_train_env·smoke_test·preflight_check 등) 보정만 기록. (rename 안 한 이유: history/ 30+ 참조 깨짐 회피) |
| `check_update_diff.sh` | 2026-04-22 (03_smolvla_test_on_orin) | upstream lerobot diff 점검 보조 스크립트. `01_compatibility_check.md` 연계. |
| `99_lerobot_upstream_Tracking.md` (본 파일) | 2026-04-22 (03_smolvla_test_on_orin) | 색인 역할 대행 + upstream 동기화 이력 누적. |

> **이관됨**: `05_datacollector_lerobot_diff.md` (구 색인) → `docs/storage/legacy/arm_2week_plan/others/02_datacollector_separate_node/lerobot_upstream_check_05_datacollector_lerobot_diff.md` (2026-05-06). DataCollector 노드 legacy 이관 (06 결정) 으로 본 디렉터리 활성 색인에서 제외. 역사 기록은 legacy 위치에 보존.

### 등록 현황 노트

- **`04_dgx_lerobot_diff.md`**: 06_dgx_absorbs_datacollector M3 code-tester 에서 색인 누락 지적 (06 BACKLOG #7). 07_e2e_pilot_and_cleanup TODO-W2 에서 등록 완료 (2026-05-03). 2026-05-06 — 파일명·실체 mismatch 명시 노트 추가 (rename 미실시, 본문 상단 disambiguation 만).

---

## Upstream Tracking Log

upstream 변화를 점검할 때 아래 항목을 누적 기록한다.

| Date (KST) | lerobot commit | Describe | Recent cadence (30/90/180d) | Impact note | Action |
|---|---|---|---|---|---|
| 2026-04-22 | `ba27aab79c731a6b503b2dbdd4c601e78e285048` | `v0.5.1-42-gba27aab7` | `70 / 185 / 314` | upstream 변경 빈도 높음. Orin 의존성 drift 리스크 존재 | `orin/pyproject.toml` 기준 유지, 다음 동기화 시 설치/실행 재검증 |

### Snapshot Notes (2026-04-22)

- Latest commit subject: `fix(robotwin): pin compatible curobo in benchmark image (#3427)`
- Current smolVLA pointer state: `-ba27aab79c731a6b503b2dbdd4c601e78e285048 lerobot`
- 해석: `-` 접두는 submodule이 현재 워킹트리에서 미초기화/불일치 상태일 수 있음을 의미하므로, 실제 동기화 작업 전 상태 확인이 필요하다.
