# TODO-D3 — Prod Test

> 작성: 2026-05-01 14:00 | prod-test-runner | cycle: 1

## Verdict

**`NEEDS_USER_VERIFICATION`**

자율 정적 검증 전 항목 통과. DataCollector 머신 미셋업 상태이므로 실물 배포·실행은 사용자 위임. 본 todo 의 DOD (flow 0~7 완주, 3분기 검증) 는 사용자 실물 환경 없이 자동 충족 불가.

---

## 배포 대상

- DataCollector 머신 (Ubuntu 22.04 LTS x86_64)
- 실 deploy 는 DataCollector 머신 셋업 후 사용자가 `bash scripts/deploy_datacollector.sh` 실행

## 배포 결과 (자율 정적 검토 — 실 deploy X)

- 명령: `bash scripts/deploy_datacollector.sh` (DataCollector 머신 셋업 후 실행 가능)
- 실 실행: X (DataCollector SSH alias 미등록, 머신 미셋업)
- 정적 검토 결과:
  - `datacollector/interactive_cli/` 는 `datacollector/` 전체 rsync 대상에 포함 (`${SMOLVLA_ROOT}/datacollector/` → `datacollector:${DATACOLLECTOR_DEST}/datacollector/`)
  - `interactive_cli/` 가 exclude 목록에 없음 → 배포 시 자동 포함
  - Category B 영역 (orin/lerobot, pyproject.toml 실제 변경): 비해당. deploy_datacollector.sh 의 pyproject.toml / setup_env.sh 언급은 주석과 echo 메시지에만 존재 — 실제 수정·배포 대상 아님.

---

## 자동 비대화형 검증 결과

| 검증 | 명령 | 결과 |
|---|---|---|
| py_compile (6개 파일) | `python3 -m py_compile datacollector/interactive_cli/flows/*.py` | ALL OK (구문 오류 없음) |
| main.sh 문법 | `bash -n datacollector/interactive_cli/main.sh` | OK |
| entry.py --help (ImportError 없음) | `python3 datacollector/interactive_cli/flows/entry.py --help` | usage 정상 출력 (cycle 2 Critical #1 정정 확인) |
| transfer.py rsync 안내 전용 확인 | AST 스캔 | subprocess.run 에 sync_dataset_collector_to_dgx.sh 없음 — 안내 메시지만 출력 (DOD 정합) |
| record.py _validate_camera_indices 2-param | AST 파라미터 카운트 | `(cam_wrist_left_index, cam_overview_index)` 2-param 확인 (자기비교 제거됨) |
| record.py _validate_data_kind_choice 단일 호출 | AST call line 확인 | line 317 단일 호출 (이중 호출 제거됨) |
| env_check.py 5단계 순서 | AST call order | venv(228)→USB(242)→camera(256)→lerobot(273)→data_dir(287) — D1 §1 정합 |
| deploy_datacollector.sh interactive_cli 포함 확인 | 정적 Read | datacollector/ 전체 rsync 대상, interactive_cli exclude 없음 |
| entry.py sys.path + 절대 import 패턴 | 정적 Read | _THIS_DIR/_CLI_DIR 주입 + from flows.X import ... (상대 import 없음) |

---

## DOD 자동 부합

| DOD 항목 | 자동 검증 | 결과 |
|---|---|---|
| 1. flow 0~7 모두 구현 | yes (py_compile + entry.py --help + AST) | 코드 존재 확인 ✅ |
| 2. DataCollector 머신 진입 → flow 0~7 완주 | no (사용자 실물) | → verification_queue |
| 3. flow 7 분기 1 HF Hub 동작 | no (사용자 실물) | → verification_queue |
| 4. flow 7 분기 2 rsync 안내 출력 | partial (rsync subprocess 호출 없음 정적 확인) | 안내 메시지 존재 확인 ✅ / 실물 출력은 → verification_queue |
| 5. flow 7 분기 3 로컬 저장 유지 | partial (코드 존재 확인) | → verification_queue |
| 6. 04 BACKLOG #7 DataCollector 머신 셋업 16단계 | no (사용자 실물) | → verification_queue |
| 7. 04 BACKLOG #8 G3 check_hardware 이식 | yes (env_check.py 5단계 AST 확인, 04 G1 패턴 미러) | 코드 구현 확인 ✅ |
| 8. 04 BACKLOG #9 G4 DataCollector prod 검증 | no (사용자 실물) | → verification_queue |

---

## 사용자 실물 검증 필요 사항 (verification_queue 추가됨)

1. **DataCollector 머신 셋업** (04 BACKLOG #7 흡수) — `docs/storage/09_datacollector_setup.md` 16단계 완료 (Ubuntu 22.04 LTS x86_64, .hylion_collector venv, lerobot editable 설치)
2. **SO-ARM follower + leader 임시 연결** — `/dev/ttyACM0` (leader), `/dev/ttyACM1` (follower) 등록 확인
3. **카메라 (wrist + overview) 임시 연결** — OpenCV index 0·1 probe 성공 확인
4. **deploy 실행** — `bash scripts/deploy_datacollector.sh` (SSH alias 'datacollector' 등록 후)
5. **main.sh 실행 + flow 0~7 완주** — `bash ~/smolvla/datacollector/interactive_cli/main.sh` → flow 2 env check 전 항목 PASS → flow 3 teleop → flow 4 teleop 확인 → flow 5 옵션 1 채택 → flow 6 5 episodes dummy dataset 수집
6. **flow 7 분기 3건 모두 검증**:
   - 분기 1 (HF Hub): `export HF_TOKEN=hf_xxx` 설정 후 업로드 (또는 `--private`)
   - 분기 2 (rsync): "devPC 에서 bash smolVLA/scripts/sync_dataset_collector_to_dgx.sh --dataset <name> 실행" 안내 메시지 출력 확인 → devPC 에서 직접 실행
   - 분기 3 (안함): 로컬 저장만 유지 확인 (`~/smolvla/datacollector/data/<dataset>/` 존재)
7. **04 BACKLOG #9 G4 prod 검증** (DataCollector check_hardware prod) — flow 2 env_check 5단계 [PASS] 출력 실물 확인

---

## 04 BACKLOG 통합 처리 현황

| BACKLOG 항목 | 자동 처리 여부 | 상태 |
|---|---|---|
| #7 DataCollector 머신 셋업 16단계 | no | → verification_queue 항목 1 |
| #8 G3 DataCollector check_hardware 이식 | yes (env_check.py 5단계 코드 확인) | 코드 이식 완료 ✅ / 실물 검증 → verification_queue 항목 7 |
| #9 G4 DataCollector check_hardware prod | no | → verification_queue 항목 7 |

---

## CLAUDE.md 준수

- Category B 영역 변경된 배포: no — deploy_datacollector.sh 가 orin/lerobot, dgx/lerobot, pyproject.toml (실제), setup_env.sh (실제) 를 배포 대상으로 포함하지 않음. 스크립트 내 언급은 주석/echo 전용.
- 자율 영역만 사용: yes — devPC 에서 py_compile, bash -n, python3 entry.py --help, AST 정적 검사만 실행. 실 SSH deploy X.
- DataCollector 머신 실 deploy: 사용자 환경 의존 → verification_queue 위임.
