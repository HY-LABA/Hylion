# TODO-X2 — Implementation

> 작성: 2026-05-02 14:00 | task-executor | cycle: 1

## 목표

`dgx/interactive_cli/flows/` 에 mode.py 신규 + 수집 flow 4 파일 이식 + 기존 파일 수정. 사용자 결정 G-4·H-(b) 적용.

---

## §1 신규 5 파일 + 수정 5 파일 목록

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `dgx/interactive_cli/flows/mode.py` | A | flow 3 mode 분기 — G-4: 수집/학습/종료 + 수집 후 학습 전환 prompt |
| `dgx/interactive_cli/flows/teleop.py` | A | datacollector/teleop.py 이식 — scripts 경로 `.parent` 1단계로 수정 |
| `dgx/interactive_cli/flows/data_kind.py` | A | datacollector/data_kind.py 이식 — 변경 없음 (DATA_KIND_OPTIONS 독립) |
| `dgx/interactive_cli/flows/record.py` | A | datacollector/record.py 이식 — data_root `~/smolvla/dgx/data/` 로 변경 |
| `dgx/interactive_cli/flows/transfer.py` | A | H-(b) 재정의 — `(1) 로컬만 / (2) HF Hub + 로컬`, rsync 옵션 폐지 |
| `dgx/interactive_cli/flows/entry.py` | M | VALID_NODES datacollector 제거, dgx 분기 mode.py 호출로 교체 |
| `dgx/interactive_cli/flows/env_check.py` | M | mode 파라미터 추가 — "collect" 시 USB·dialout·v4l2·SO-ARM 항목 6~9 추가 |
| `dgx/interactive_cli/flows/training.py` | M | sync_ckpt_dgx_to_datacollector.sh 7 라인 정정 + run_training_flow_with_dataset 시그니처 추가 |
| `dgx/interactive_cli/configs/node.yaml` | M | responsibilities: training + data_collection 추가 |
| `dgx/interactive_cli/README.md` | M | 수집 mode flow 도식 + X2 완료 표기 |
| `orin/interactive_cli/flows/entry.py` | M | VALID_NODES datacollector 제거, flow 0 datacollector 분기 제거 |

---

## §2 G-4 mode.py 분기 로직 도식

```
flow3_mode_entry(script_dir)
  │
  ├─ 메뉴 (1) 수집 선택
  │    └─ _run_collect_flow(script_dir) → (rc, dataset_name)
  │         ├─ flow3_teleoperate()
  │         ├─ flow4_confirm_teleop()
  │         ├─ flow5_select_data_kind()
  │         ├─ flow6_record(...) → (success, local_path, repo_id)
  │         └─ flow7_select_transfer(...)
  │    └─ _prompt_transition_to_train(script_dir, dataset_name)
  │         ├─ [Y] run_training_flow_with_dataset(script_dir, dataset_name)
  │         │       └─ flow3_select_scenario → flow4(자동선택) → flow5_train_and_manage_ckpt
  │         └─ [n] 저장 안내 + return 0
  │
  ├─ 메뉴 (2) 학습 선택
  │    └─ run_training_flow(script_dir)
  │         └─ flow3_select_scenario → flow4_select_dataset → flow5_train_and_manage_ckpt
  │
  └─ 메뉴 (3) 종료
       └─ return 0
```

**G-4 하이브리드 특성**: 단발 종료 (G-1) + 수집 끝 학습 전환 prompt. 루프 없음. 학습 전환 prompt 가 루프 역할 대체.

---

## §3 H-(b) transfer.py 메뉴 + push 호출 패턴

**H-(b) 확정 메뉴 (2 옵션)**:

```
  (1) 로컬 저장만 (DGX 에 이미 저장됨)
  (2) HF Hub 백업도 같이 (인터넷 필요 + 로컬 보관 유지)
```

**rsync 옵션 완전 폐지**: DGX 가 자기 자신에게 rsync 하는 (2) 옵션 및 Orin rsync 안내 모두 제거.

**push_dataset_hub.sh 호출 패턴** (원본 _transfer_to_hub 그대로):
```python
push_script = script_dir.parent / "scripts" / "push_dataset_hub.sh"
cmd = ["bash", str(push_script), "--dataset", local_dataset_path, "--repo-id", repo_id]
```
`script_dir.parent` = `dgx/interactive_cli/` → `dgx/scripts/` (X3 이식 대상).

**(2) 선택 시 로컬 보관 유지**: HF Hub 업로드 성공·실패 무관, `[flow 7] 로컬 보관 유지: {path}` 출력 후 종료.

---

## §4 record.py data_root 변경 + dataset_name 인계 패턴

**data_root 변경 (원본 line 194 + 367 2곳)**:
```python
# 원본 (datacollector):
data_root = os.path.expanduser(f"~/smolvla/datacollector/data/{dataset_name}")

# dgx 이식 후:
data_root = os.path.expanduser(f"~/smolvla/dgx/data/{dataset_name}")
```

**dataset_name 인계 경로**:
1. `record.py::flow6_record()` → `(success, local_dataset_path, repo_id)` 반환
2. `mode.py::_run_collect_flow()` → `repo_id.split("/")[-1]` 로 `dataset_name` 추출
3. `mode.py::_prompt_transition_to_train()` → `run_training_flow_with_dataset(script_dir, dataset_name=dataset_name)` 인계
4. `training.py::run_training_flow_with_dataset()` → `~/smolvla/dgx/data/{dataset_name}` 로컬 경로 자동 생성

---

## §5 training.py 7 라인 정정 결과

**정정 대상 (L2 grep 인계)**: `sync_ckpt_dgx_to_datacollector.sh` 참조 7건 — DataCollector 노드 운영 종료로 모두 무효.

| 원본 위치 | 정정 내용 |
|---|---|
| L15 (docstring) | `scripts/sync_ckpt_dgx_to_datacollector.sh` 인용 → 갱신 주석으로 교체 |
| L54 (CKPT_CASES 주석) | `sync_ckpt_dgx_to_datacollector.sh line 19~22 인용` → 갱신 주석 |
| L70 (케이스 2 안내 bash 명령) | `sync_ckpt_dgx_to_datacollector.sh` → "차기 사이클 신규 예정" 안내 메시지 |
| L72 (케이스 2 안내 run 지정) | 동일 → 제거 |
| L92 (케이스 4 각주) | `sync_ckpt_dgx_to_datacollector.sh line 22 인용` → 각주 제거 |
| L494 (docstring) | `sync_ckpt_dgx_to_datacollector.sh 실행` → `차기 사이클 신규 예정` |
| L497 (docstring 인용) | `sync_ckpt_dgx_to_datacollector.sh line 19~22 케이스 설명 인용` → 갱신 주석 |

**추가**: `run_training_flow_with_dataset(script_dir, dataset_name=None)` 시그니처 신규 추가 (G-4 수집→학습 dataset 자동 선택).

---

## §6 ruff·py_compile 자체 검증 결과

```
python3 -m py_compile [9개 파일] → 모두 OK
ruff check [9개 파일]            → 1건 발견 (record.py Path 미사용 import) → 즉시 수정 → All checks passed!
```

**최종 검증 결과**: ruff All checks passed + py_compile 9/9 OK.

---

## §7 잔여 리스크

### env_check.py mode 파라미터 selective vs 통합 결정

**결정: selective check 방식 채택.**

사유:
- 학습 mode 진입 시 SO-ARM·카메라 미연결 상태가 일반적 (DGX 가 연구실에서 학습만 하는 경우).
- 항목 6~9 (USB 포트·dialout·v4l2) 체크를 항상 실행하면 학습 mode 에서 불필요한 FAIL 발생.
- `mode="collect"` 시에만 항목 6~9 추가 실행. entry.py 에서 호출 시 `mode="train"` (기본값) 으로 preflight 5단계만.

**현재 entry.py 에서 env_check 호출**:
```python
if not flow2_env_check(script_dir, scenario="smoke"):  # mode 인자 없음 = "train"
    return 1
```
수집 환경 체크는 mode.py 에서 수집 mode 선택 시 별도 호출하는 설계로 가능하나,
현재 구현에서는 mode.py 가 env_check 를 재호출하지 않고 바로 teleop flow 진입.
**V2 prod 검증에서 수집 환경 이상 발견 시 mode.py 에서 collect mode 전환 시 env_check(mode="collect") 재호출 추가 가능** (현재는 단순화).

### run_teleoperate.sh + push_dataset_hub.sh 미존재

teleop.py·transfer.py 가 `dgx/scripts/run_teleoperate.sh`, `dgx/scripts/push_dataset_hub.sh` 를 참조하나 X3 이식 대상으로 아직 미존재.
스크립트 미발견 시 명확한 오류 메시지 + 경로 안내 출력 후 returncode=1 반환 (방어적 처리 구현됨).

### 카메라 인덱스 기본값

record.py 에서 `cam_wrist_left_index=0, cam_overview_index=1` 기본값 사용.
env_check 가 실제 probe 한 인덱스를 인계받지 않는 상태 — V2 prod 검증에서 실제 인덱스 확인 후 flow 2→flow 6 인계 로직 추가 검토.

---

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경, `dgx/lerobot/` 미접촉 (Category B 비해당)
- Coupled File Rule: `orin/lerobot/` 미변경 — `03_orin_lerobot_diff.md` 갱신 불필요
- 레퍼런스 직접 Read 확인:
  - `docs/storage/legacy/02_datacollector_separate_node/datacollector/interactive_cli/flows/teleop.py` — 함수 시그니처·스크립트 경로 패턴 인용
  - `docs/storage/legacy/02_datacollector_separate_node/datacollector/interactive_cli/flows/data_kind.py` — DATA_KIND_OPTIONS 5개 그대로 적용
  - `docs/storage/legacy/02_datacollector_separate_node/datacollector/interactive_cli/flows/record.py` — build_record_args 패턴 인용, data_root 1 라인 변경
  - `docs/storage/legacy/02_datacollector_separate_node/datacollector/interactive_cli/flows/transfer.py` — _check_hf_token·_transfer_to_hub 패턴 인용, H-(b) 메뉴 재정의
  - `docs/storage/14_dgx_cli_flow.md` §1~§7 전체 준수

---

## 변경 내용 요약

TODO-X2 는 DGX 가 데이터 수집 책임을 흡수하는 06 사이클의 핵심 코드 구현 todo다. datacollector 노드에 있던 수집 flow (teleop·data_kind·record·transfer) 4 파일을 dgx/interactive_cli/flows/ 로 이식하고, mode.py 를 신규 작성하여 flow 3 단계에서 수집/학습/종료 분기를 제공한다.

사용자 결정 G-4 에 따라 단발 종료 구조 + 수집 완료 후 학습 전환 prompt 하이브리드로 mode.py 를 구현했다. 수집 후 Y 응답 시 방금 수집한 dataset_name 을 training flow 에 자동 인계하여 데이터셋 선택 단계를 건너뛰는 연속 흐름을 지원한다. H-(b) 결정에 따라 transfer.py 를 2 옵션 (로컬/HF Hub) 으로 단순화했고 rsync 관련 함수를 완전 제거했다. training.py 의 DataCollector 경유 sync 스크립트 참조 7 라인을 모두 제거하고 "차기 사이클 신규 예정" 안내로 교체했다.

---

## code-tester 입장에서 검증 권장 사항

- `py_compile`: `python3 -m py_compile dgx/interactive_cli/flows/{mode,teleop,data_kind,record,transfer,entry,env_check,training}.py orin/interactive_cli/flows/entry.py`
- `ruff lint`: `ruff check dgx/interactive_cli/flows/ orin/interactive_cli/flows/entry.py`
- **mode.py G-4 분기 정합**: `flow3_mode_entry()` → 수집 후 `_prompt_transition_to_train()` → `run_training_flow_with_dataset()` import 경로 확인
- **record.py data_root 변경**: `grep "smolvla/dgx/data" dgx/interactive_cli/flows/record.py` (2 곳 모두 변경 확인)
- **training.py 정정 완료**: `grep "sync_ckpt_dgx_to_datacollector" dgx/interactive_cli/flows/training.py` → 0 건 확인
- **VALID_NODES 정합**: `grep "datacollector" dgx/interactive_cli/flows/entry.py orin/interactive_cli/flows/entry.py` → 0 건 (상수 제거 확인)
- **node.yaml 책임**: `cat dgx/interactive_cli/configs/node.yaml` → data_collection 확인
