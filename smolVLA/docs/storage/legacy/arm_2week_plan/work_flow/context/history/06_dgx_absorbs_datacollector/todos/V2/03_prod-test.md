# TODO-V2 — Prod Test

> 작성: 2026-05-02 | prod-test-runner | cycle: 1

## Verdict

**`NEEDS_USER_VERIFICATION`**

devPC 로컬 정적 검증 전항목 통과. DGX SSH 불가 (사용자 명시 환경 제약) — calibrate·record·HF Hub push 모두 사용자 실물 의존. DOD의 DGX 실물 flow 0~7 완주 자동 검증 불가.

---

## 배포 대상

- DGX (rsync from devPC)
- Orin: orin/interactive_cli/flows/entry.py 변경 포함 — Orin 배포도 필요

## 배포 결과

- **상태**: SSH 불가 — 실물 배포 Phase 3 사용자 수행 필요
- 배포 명령:
  - `bash scripts/deploy_dgx.sh` — dgx/ 변경 동기화
  - `bash scripts/deploy_orin.sh` — orin/interactive_cli/flows/entry.py 변경 동기화
- 자율성 분류: deploy_*.sh 는 Category B 영역이나 **변경 내용 자체가 Category B 외 (dgx/interactive_cli/, dgx/scripts/ 신규 파일, orin/interactive_cli/flows/entry.py)** — 자율 배포 해당. 단 SSH 불가로 현재 실행 불가 → Phase 3 사용자 수행.

---

## 자동 비대화형 검증 결과 (devPC 정적 검증)

### X2 산출물 — py_compile (9/9 파일)

| 파일 | 명령 | 결과 |
|---|---|---|
| dgx/interactive_cli/flows/mode.py | `python3 -m py_compile` | OK |
| dgx/interactive_cli/flows/teleop.py | `python3 -m py_compile` | OK |
| dgx/interactive_cli/flows/data_kind.py | `python3 -m py_compile` | OK |
| dgx/interactive_cli/flows/record.py | `python3 -m py_compile` | OK |
| dgx/interactive_cli/flows/transfer.py | `python3 -m py_compile` | OK |
| dgx/interactive_cli/flows/entry.py | `python3 -m py_compile` | OK |
| dgx/interactive_cli/flows/env_check.py | `python3 -m py_compile` | OK |
| dgx/interactive_cli/flows/training.py | `python3 -m py_compile` | OK |
| orin/interactive_cli/flows/entry.py | `python3 -m py_compile` | OK |

### X2 산출물 — ruff check (9/9 파일)

| 대상 | 명령 | 결과 |
|---|---|---|
| 위 9 파일 일괄 | `python3 -m ruff check [파일 목록]` | All checks passed! |

### X3 산출물 — bash -n (3/3 스크립트)

| 파일 | 명령 | 결과 |
|---|---|---|
| dgx/scripts/run_teleoperate.sh | `bash -n` | EXIT:0 |
| dgx/scripts/push_dataset_hub.sh | `bash -n` | EXIT:0 |
| dgx/scripts/check_hardware.sh | `bash -n` | EXIT:0 |

### G-4 분기 로직 정합 — 직접 Read 확인

`mode.py::_run_collect_flow()` → `(returncode, dataset_name)` 반환  
→ `mode.py::_prompt_transition_to_train(script_dir, dataset_name)` 호출  
→ Y 응답 시 `training.py::run_training_flow_with_dataset(script_dir, dataset_name=dataset_name)` 호출

체인 4단계 모두 확인:
- `_run_collect_flow()`: `repo_id.split("/")[-1]` 로 `dataset_name` 추출 → `return 0, dataset_name`
- `flow3_mode_entry()` line 211~219: `rc, dataset_name = _run_collect_flow(script_dir)` → `return _prompt_transition_to_train(script_dir, dataset_name)`
- `_prompt_transition_to_train()` line 163~164: `from flows.training import run_training_flow_with_dataset` + `return run_training_flow_with_dataset(script_dir, dataset_name=dataset_name)`
- `run_training_flow_with_dataset()`: `dataset_name` 이 주어지면 `~/smolvla/dgx/data/{dataset_name}` 자동 매핑 + 학습 진행

**정합 확인: 완전.**

### transfer.py H-(b) 옵션 정합 — 직접 Read 확인

함수 목록: `_check_hf_token`, `_transfer_to_hub`, `_keep_local_dgx`, `flow7_select_transfer`  
`_guide_rsync_to_dgx` 함수: grep 결과 0건 (완전 제거 확인)  
메뉴: (1) 로컬 저장만 / (2) HF Hub 백업도 같이 — H-(b) 정확.

**정합 확인: 완전.**

### record.py data_root 경로 확인

- line 206 (`build_record_args()`): `os.path.expanduser(f"~/smolvla/dgx/data/{dataset_name}")` — 확인
- line 384 (`flow6_record()`): `local_dataset_path = os.path.expanduser(f"~/smolvla/dgx/data/{dataset_name}")` — 확인

**정합 확인: 완전.**

### 04 BACKLOG #14 (env_check.py NoneType) 사전 진단

원인: 04 env_check.py의 `_check_motor_ids()` 함수 내 `port_handler.openPort()` → `port_handler.closePort()` 가 None-safe X 패턴.

DGX X2 env_check.py 구현 방식:
- `_check_hardware_collect()` 내 항목 9 (SO-ARM 포트 응답):
  - `import serial` → `with serial.Serial(follower_port, timeout=0.5): pass`
  - **context manager 패턴** — `with` 블록이 `__exit__` 보장하므로 NoneType `.close()` 패턴 원천 차단
  - `port_handler.openPort()` / `closePort()` 패턴 완전 미사용 — BACKLOG #14 재현 불가 (구조적으로 다른 구현)
  - `except ImportError` + `except Exception` 이중 보호 — 포트 open 실패 시 FAIL 출력 후 `all_pass = False` (크래시 X)

**진단 결과: DGX env_check.py 에서 BACKLOG #14 재현 가능성 없음 — 구현 방식 자체가 다름.**  
Phase 3 사용자 실물 검증에서 SO-ARM 포트 응답 체크 시 동작 확인 권고 (verification_queue 항목에 통합).

---

## DOD 자동 부합

| DOD 항목 | 자동 검증 가능 | 결과 |
|---|---|---|
| flow 0: 환경 확인 prompt 동작 | no (DGX 실물) | → verification_queue |
| flow 1: 장치 선택 메뉴 orin/dgx 2 옵션 확인 | no (DGX 실물) | → verification_queue |
| flow 2: preflight + check_hardware 5-step PASS | no (DGX 실물 + SO-ARM 연결) | → verification_queue |
| flow 3: mode 메뉴 (1)수집/(2)학습/(3)종료 표시 | 부분 (코드 확인, 실행 X) | 코드 정합 ✅ |
| flow 4: lerobot-calibrate follower + leader | no (DGX 실물 + SO-ARM) | → verification_queue |
| flow 5: 학습 종류 선택 5 옵션 | no (DGX 실물) | → verification_queue |
| flow 6: lerobot-record dummy episode 수집 | no (DGX 실물 + SO-ARM + 카메라) | → verification_queue |
| flow 7 (1) 로컬 저장만 분기 | no (DGX 실물) | → verification_queue |
| flow 7 (2) HF Hub 백업 분기 | no (DGX 실물 + 인터넷) | → verification_queue |
| G-4 학습 전환 prompt (Y → training 자동 진입) | 부분 (코드 체인 확인, 실행 X) | 코드 정합 ✅ |
| 04 BACKLOG #14 NoneType 진단 | yes (정적 분석) | 재현 불가 확인 ✅ |

---

## 사용자 실물 검증 필요 사항 (verification_queue 추가됨)

### 사전 준비

**A. DGX 배포** — devPC 에서 `bash scripts/deploy_dgx.sh` + `bash scripts/deploy_orin.sh` 실행  
**B. DGX VSCode remote-ssh 연결** — `bash dgx/interactive_cli/main.sh` 실행

### flow 단계별 검증 항목

1. **flow 0** — 환경 확인 prompt `"DGX 맞나요? [Y/n]"` 표시 + Y 응답 → flow 1 진입 확인

2. **flow 1** — 장치 선택 메뉴에서 `orin / dgx` 2 옵션만 표시 (datacollector 옵션 제거) 확인 → dgx 선택

3. **flow 2** — DGX 환경 체크:
   - preflight_check.sh PASS (학습 환경 5단계)
   - mode="collect" 수집 환경 체크 (항목 6~9 — USB 포트·dialout·v4l2·SO-ARM 포트 응답)
   - check_hardware.sh 5-step 결과 확인

4. **flow 3** — mode 메뉴 `(1) 수집 / (2) 학습 / (3) 종료` 정확 표시 확인 → `(1) 수집` 선택

5. **flow 4 (수집 mode)** — `lerobot-calibrate follower` + `lerobot-calibrate leader` 실 수행:
   - 04 BACKLOG #10 (id_=3 elbow_flex Torque_Enable 실패 간헐) 재발 시 재실행 (1~2회)
   - 포트 인식: `/dev/ttyACM0` (follower), `/dev/ttyACM1` (leader) 확인

6. **flow 5** — 학습 종류 선택 5 옵션 중 `옵션 1 단순 pick-place` 선택 권장

7. **flow 6** — `lerobot-record` dummy 1~3 에피소드 수집:
   - 권장: `--dataset.num_episodes=2`
   - 카메라 인덱스 (wrist_left=0, overview=1) 실제 환경 정합 확인
   - SO-ARM follower 추종 동작 육안 관찰

8. **flow 7 분기 (1) 로컬 저장만** — `"(1) 로컬 저장만"` 선택 시 `~/smolvla/dgx/data/<dataset_name>` 저장 안내 메시지 + 학습 전환 prompt 표시 확인

9. **flow 7 분기 (2) HF Hub 백업** — `"(2) HF Hub 백업도 같이"` 선택 시 `push_dataset_hub.sh` 호출 + HF Hub 업로드 완료 확인:
   - 주의: 학교 WiFi 환경에서 huggingface.co 타임아웃 가능 — 다른 네트워크 권고 (05 ANOMALIES 패턴)
   - private=y 선택 권장 (첫 검증 시)

10. **G-4 학습 전환 prompt** — `"수집 완료. 바로 학습으로 진행할까요? [Y/n]"` 표시 확인:
    - **Y 선택**: flow 3~ 학습 mode 자동 진입 + 방금 수집한 `dataset_name` 자동 선택 확인 (V3 통합 검증 가능)
    - **n 선택**: `"~/smolvla/dgx/data/<dataset_name> 저장 안내"` + 종료 확인

11. **dialout 그룹·USB 연결 검증** — `sudo usermod -aG dialout $USER` 필요 여부 + v4l2 카메라 `/dev/video*` 인식 확인 (flow 2 항목 7·8 PASS 여부)

12. **04 BACKLOG #14 실물 확인** — env_check.py 항목 9 (`SO-ARM 포트 응답`) 실행 시:
    - `serial.Serial` context manager 패턴으로 NoneType 에러 발생 X 확인
    - PASS 또는 `"SKIP pyserial 미설치"` 메시지 확인 (크래시 X 확인 — 정적 분석 결과 재현 불가 예측이나 실물 확인 권고)

---

## CLAUDE.md 준수

| 항목 | 확인 |
|---|---|
| Category B 영역 변경된 deploy (DGX 실물) | SSH 불가 — Phase 3 사용자 수행. deploy_*.sh 자체 변경 없음 (변경 파일 Category B 외) |
| 자율 영역만 사용 | yes — devPC 정적 검증 (py_compile·ruff·bash -n·grep·Read) 만 실행 |
| Category A 영역 수정 X | 코드 수정 없음 (배포·검증만) |
| 큰 다운로드 / 긴 실행 | Phase 3 사용자 수행 (flow 6 lerobot-record, flow 7 HF Hub push) — 동의 필요 항목 verification_queue 에 명시 |

---

## 정적 검증 요약

- py_compile: 9/9 OK
- ruff check: All checks passed (9 파일)
- bash -n: 3/3 OK
- G-4 인계 체인: 코드 직접 Read 확인 (완전)
- H-(b) rsync 제거: grep 결과 0건 (완전)
- record.py data_root: line 206·384 양쪽 `~/smolvla/dgx/data/` 확인
- 04 BACKLOG #14 사전 진단: context manager 패턴으로 NoneType 재현 불가 (구조적 차이)
