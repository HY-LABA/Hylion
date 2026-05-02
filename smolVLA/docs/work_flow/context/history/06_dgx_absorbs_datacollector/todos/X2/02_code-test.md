# TODO-X2 — Code Test

> 작성: 2026-05-02 15:30 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 0건, Recommended 1건.

---

## 단위 테스트 결과

```
py_compile ALL OK
  대상: dgx/interactive_cli/flows/{mode,teleop,data_kind,record,transfer,entry,env_check,training}.py
        orin/interactive_cli/flows/entry.py
  결과: 9/9 OK
```

---

## Lint·Type 결과

```
ruff check [9개 파일] → All checks passed!
  대상: dgx/interactive_cli/flows/mode.py
        dgx/interactive_cli/flows/teleop.py
        dgx/interactive_cli/flows/data_kind.py
        dgx/interactive_cli/flows/record.py
        dgx/interactive_cli/flows/transfer.py
        dgx/interactive_cli/flows/entry.py
        dgx/interactive_cli/flows/env_check.py
        dgx/interactive_cli/flows/training.py
        orin/interactive_cli/flows/entry.py
```

task-executor 보고서 §6 와 일치: Path 미사용 import 1건 자체 발견·수정 후 All checks passed.

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. `mode.py` 신규 — flow 3 mode 분기 (G-4 적용) | ✅ | 메뉴 (1)수집/(2)학습/(3)종료 + 수집 완주 후 학습 전환 prompt 정확 구현 |
| 2. `teleop.py` 신규 — datacollector 이식 + scripts 경로 변경 | ✅ | `script_dir.parent.parent` → `script_dir.parent` 정확 변경 |
| 3. `data_kind.py` 신규 — 변경 없이 이식 | ✅ | DATA_KIND_OPTIONS 5개 동일, 로직 동일 |
| 4. `record.py` 신규 — data_root 2곳 변경 | ✅ | line 206·line 384 모두 `~/smolvla/dgx/data/` 로 변경 확인 |
| 5. `transfer.py` 신규 — H-(b) 재정의, rsync 완전 제거 | ✅ | `_guide_rsync_to_dgx` 함수 완전 삭제, 2분기 메뉴 정확 구현 |
| 6. `entry.py` 수정 — VALID_NODES datacollector 제거, mode.py 호출 | ✅ | VALID_NODES=("orin","dgx"), dgx 분기에서 flow3_mode_entry 호출 |
| 7. `env_check.py` 수정 — mode 파라미터 추가 | ✅ | mode="train"/"collect" selective check 구현 |
| 8. `training.py` 수정 — sync_ckpt 7라인 정정 + run_training_flow_with_dataset 추가 | ✅ | grep 결과: 실행 코드에서 sync_ckpt_dgx_to_datacollector.sh 0건, 함수 시그니처 확인 |
| 9. `configs/node.yaml` 수정 — data_collection 추가 | ✅ | responsibilities: [training, data_collection] 확인 |
| 10. README.md 갱신 — 수집 mode flow 도식 + X2 완료 표기 | ✅ | flow 도식 + 후행 todo 목록 정확 |
| 11. `orin/interactive_cli/flows/entry.py` — VALID_NODES datacollector 제거 | ✅ | VALID_NODES=("orin","dgx"), flow 0 datacollector 분기 제거 |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `orin/interactive_cli/flows/entry.py:212,262` | 주석에 `dgx / datacollector: 후행 todo 에서 구현` (line 212), `# flow 0: 환경 확인 (datacollector 전용)` (line 262) 잔존. orin entry.py 는 실제로는 orin 분기만 동작하므로 무해하지만 `_run_node_flows` docstring의 `datacollector` 언급 (line 212)과 `flow 0` 주석 (line 262) 이 내용상 구버전 흔적. MINOR 스타일 개선 후보. |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경, `.claude/` 미변경 — git status 확인 |
| B (자동 재시도 X) | ✅ | `dgx/lerobot/`, `dgx/pyproject.toml`, `dgx/scripts/setup_env.sh`, `scripts/deploy_*.sh` 미접촉 확인 |
| Coupled File Rules | ✅ 비해당 | `orin/lerobot/`, `dgx/lerobot/`, `pyproject.toml` 미변경 — diff 파일 갱신 불필요 |
| 옛 룰 | ✅ | `docs/storage/` 하위 bash 명령 예시 미추가 |

### 세부 확인

- `dgx/interactive_cli/flows/` 및 `orin/interactive_cli/flows/entry.py` 만 변경 — 모두 Category B 비해당 영역
- Category A (`docs/reference/`, `.claude/`) 영역 수정 없음 (git status 확인)
- Coupled File Rules: `orin/lerobot/` 미접촉 → `03_orin_lerobot_diff.md` 갱신 불필요

---

## 이식 정합성 검증 상세

### teleop.py 경로 변경

- 원본 (legacy): `script_dir.parent.parent / "scripts" / "run_teleoperate.sh"`
  - datacollector/interactive_cli/flows/ → ../../scripts/ = datacollector/scripts/
- dgx 이식: `script_dir.parent / "scripts" / "run_teleoperate.sh"`
  - dgx/interactive_cli/flows/ → ../scripts/ = dgx/interactive_cli/scripts/ **[주의]**
  - 실제 의도 경로: dgx/scripts/ 이므로 `script_dir.parent.parent`가 맞을 수도 있으나,
    task-executor 보고서 §1 표에서 `script_dir = dgx/interactive_cli/` 로 정의 (flows/ 가 아닌 interactive_cli/ 기준)
  - entry.py 에서 `script_dir = Path(args.node_config).parent.parent` (configs/ 상위 = interactive_cli/)
  - 따라서 `script_dir.parent` = `dgx/` → `dgx/scripts/` — **경로 정확**

### record.py data_root 변경 2곳

- `build_record_args()` line 206: `~/smolvla/dgx/data/{dataset_name}` ✅
- `flow6_record()` line 384: `~/smolvla/dgx/data/{dataset_name}` ✅
- legacy 원본 (`~/smolvla/datacollector/data/`) 실행 코드에 잔존 없음 — 주석·docstring에만 "원본" 표기로 잔존 (의도된 이식 이력 주석)

### transfer.py rsync 완전 제거

- 함수 목록: `_check_hf_token`, `_transfer_to_hub`, `_keep_local_dgx`, `flow7_select_transfer`
- `_guide_rsync_to_dgx` 함수 없음 — 완전 제거 확인 ✅
- 메뉴: (1) 로컬 저장만 / (2) HF Hub 백업도 같이 — H-(b) 정확 ✅

### training.py sync_ckpt_dgx_to_datacollector.sh 7라인 정정

- grep 실행 코드 결과: 주석·docstring에만 잔존 ("인용 제거" 설명용 텍스트 4건)
- 실행 경로에서 해당 스크립트 참조 0건 ✅
- CKPT_CASES 딕셔너리: 케이스 3 = "DataCollector 우회 경로는 현재 무효" 안내로 교체 ✅
- `run_training_flow_with_dataset(script_dir, dataset_name=None)` 시그니처 신규 추가 ✅

### G-4 dataset_name 인계 경로

1. `record.py::flow6_record()` → `(success, local_dataset_path, repo_id)` 반환 ✅
2. `mode.py::_run_collect_flow()` → `repo_id.split("/")[-1]` 로 `dataset_name` 추출 ✅
3. `mode.py::_prompt_transition_to_train()` → `run_training_flow_with_dataset(script_dir, dataset_name=dataset_name)` ✅
4. `training.py::run_training_flow_with_dataset()` → `~/smolvla/dgx/data/{dataset_name}` 자동 매핑 ✅

---

## 배포 권장

**yes — prod-test-runner 진입 권장**

Critical 0건, Recommended 1건 (스타일 개선 후보 — 비blocking). V1·V2·V3 는 Phase 3 사용자 실물 검증 대상. 본 X2 는 코드 정합 검증 완료.

X3 (dgx/scripts/ 이식) 완료 전까지 `run_teleoperate.sh`, `push_dataset_hub.sh` 미존재로 teleop·transfer flow 가 returncode=1 반환하나, 방어적 처리 (파일 미발견 시 명확한 오류 메시지 + returncode=1) 구현됨 — 코드 결함 아님.
