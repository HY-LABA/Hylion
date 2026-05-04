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
| `04_dgx_lerobot_diff.md` | 2026-04-28 (02_dgx_setting) | DGX 측 lerobot 실행 래퍼 변경 이력. upstream 코드 직접 수정 없이 `dgx/scripts/` 래퍼 보정 내역 기록. DGX 는 editable install 방식이므로 파일 레벨 diff 없음; 래퍼·환경 보정만 기록. |
| `05_datacollector_lerobot_diff.md` | 2026-05-01 (04_infra_setup TODO-D2) | `datacollector/lerobot/` vs upstream 코드 변경 이력. 옵션 B 원칙 적용 — 파일 레벨 변경 없음 (upstream 그대로 보존). DataCollector 비활성화는 `pyproject.toml [project.scripts]` entrypoint 미등록만으로 처리. 06_dgx_absorbs_datacollector 종료 후 DataCollector 노드 legacy 이관됨에 따라 향후 갱신 불요. |
| `check_update_diff.sh` | 2026-04-22 (03_smolvla_test_on_orin) | upstream lerobot diff 점검 보조 스크립트. `01_compatibility_check.md` 연계. |
| `99_lerobot_upstream_Tracking.md` (본 파일) | 2026-04-22 (03_smolvla_test_on_orin) | 색인 역할 대행 + upstream 동기화 이력 누적. |

### 등록 현황 노트

- **`04_dgx_lerobot_diff.md`**: 06_dgx_absorbs_datacollector M3 code-tester 에서 색인 누락 지적 (06 BACKLOG #7). 07_e2e_pilot_and_cleanup TODO-W2 에서 등록 완료 (2026-05-03).
- **`05_datacollector_lerobot_diff.md`**: 동일 06 BACKLOG #7 지적 대상. DataCollector 노드가 06_dgx_absorbs_datacollector 결정으로 legacy 이관됐으므로 향후 이 파일은 갱신 없이 역사 기록으로만 보존. 색인 등록은 07_e2e_pilot_and_cleanup TODO-W2 (2026-05-03) 에서 완료.

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
