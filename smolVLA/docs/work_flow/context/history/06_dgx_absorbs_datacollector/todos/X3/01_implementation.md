# TODO-X3 — Implementation

> 작성: 2026-05-02 | task-executor | cycle: 1

## 목표

`dgx/scripts/` 에 데이터 수집용 스크립트 3개 신규 (datacollector/scripts/ 이식 + dgx 환경 맞춤).

---

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `dgx/scripts/run_teleoperate.sh` | N (신규) | datacollector/scripts/run_teleoperate.sh 이식 + dgx venv 경로 갱신 |
| `dgx/scripts/push_dataset_hub.sh` | N (신규) | datacollector/scripts/push_dataset_hub.sh 이식 + dgx data_root·venv 경로 갱신 |
| `dgx/scripts/check_hardware.sh` | N (신규) | orin/tests/check_hardware.sh 패턴 기반, DGX 수집 환경 5-step 체크 신규 작성 |

---

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 (Category A 준수)
- Coupled File Rule: `orin/lerobot/`, `dgx/lerobot/`, `pyproject.toml` 미변경 → Coupled File Rule 비해당
- Category B 비해당: `dgx/scripts/setup_env.sh` 가 아닌 신규 스크립트, `scripts/deploy_*.sh` 패턴 아님
- 기존 `dgx/scripts/preflight_check.sh` · `smoke_test.sh` · `save_dummy_checkpoint.sh` 미접촉 (학습 책임 보존)
- 레퍼런스 직접 Read:
  - `docs/storage/legacy/02_datacollector_separate_node/datacollector/scripts/run_teleoperate.sh` (전체 — L1~L97)
  - `docs/storage/legacy/02_datacollector_separate_node/datacollector/scripts/push_dataset_hub.sh` (전체 — L1~L222)
  - datacollector/scripts/ 에 `check_hardware.sh` 미존재 확인 (scripts/ 에는 run_teleoperate.sh, push_dataset_hub.sh, setup_env.sh 3개만 존재)
  - `orin/tests/check_hardware.sh` (04 G1 산출물 — L1~L553, 전체 Read)
  - `dgx/scripts/preflight_check.sh` (책임 분담 결정 근거 — 전체 Read)

---

## §1 신규 3 스크립트 목록 + 원본 인용 라인

### run_teleoperate.sh

원본: `datacollector/scripts/run_teleoperate.sh` (L1~L97)

핵심 인용:
- `FOLLOWER_PORT="/dev/ttyACM1"`, `LEADER_PORT="/dev/ttyACM0"` (L19~L20) — 원본 그대로
- `lerobot-calibrate --robot.type=so101_follower --robot.port=... --robot.id=...` (L25~L30) — CLI 인자 원본 그대로
- `lerobot-calibrate --teleop.type=so101_leader --teleop.port=... --teleop.id=...` (L32~L37) — CLI 인자 원본 그대로
- `lerobot-teleoperate --robot.type=so101_follower ... --teleop.type=so101_leader ...` (L40~L49) — CLI 인자 원본 그대로
- `Usage: run_teleoperate.sh [all|calibrate-follower|calibrate-leader|teleoperate]` (L53) — 원본 그대로

### push_dataset_hub.sh

원본: `datacollector/scripts/push_dataset_hub.sh` (L1~L222)

핵심 인용:
- 인자 파싱 패턴 `--dataset / --repo-id / --private / --branch / --dry-run` (L48~L74) — 원본 그대로
- heredoc 보안 패턴: `python3 - <<'PYEOF'` (단일 따옴표 닫기 — bash 변수 확장 차단) (L172) — 원본 그대로
- `DATASET_PATH=... REPO_ID=... PRIVATE=... BRANCH=... python3 - <<'PYEOF'` 환경변수 경유 패턴 (L168~L172) — 원본 그대로
- `LeRobotDataset(repo_id=repo_id, root=dataset_path)` → `dataset.push_to_hub(private=private, branch=branch)` (L194~L204) — 원본 그대로

### check_hardware.sh

원본: `datacollector/scripts/check_hardware.sh` — **미존재** (specs/datacollector/scripts/ 에 3개 파일만 있음)

대체 원본: `orin/tests/check_hardware.sh` (04 G1 패턴)

핵심 인용:
- JSON 임시 파일 방식 결과 관리: `TMP_RESULT_JSON="$(mktemp /tmp/check_hardware_XXXXXX.json)"` + `trap 'rm -f ...' EXIT` (orin L51~L53) — 패턴 미러
- `record_step()` 함수: STEP_NAME/STEP_STATUS/STEP_DETAIL 환경변수 경유 Python json.dump 패턴 (orin L115~L145) — 패턴 미러
- SO-ARM 포트 발견: `Path("/dev").glob("ttyACM*")` + `Path("/dev").glob("ttyUSB*")` (orin L236~L238) — 패턴 미러
- 카메라 발견: `OpenCVCamera.find_cameras()` (orin L342~L365) — 패턴 미러
- `finalize_output()` JSON summary 패턴 (orin L491~L527) — 패턴 미러

---

## §2 변경 항목 (venv 경로 등) 정정 결과

### run_teleoperate.sh

| 항목 | 원본 (datacollector) | 변경 후 (dgx) |
|---|---|---|
| venv 경로 (주석) | `~/smolvla/datacollector/.hylion_collector` | `~/smolvla/dgx/.arm_finetune` |
| usage Prerequisites | `source ~/smolvla/datacollector/.hylion_collector/bin/activate` | `source ~/smolvla/dgx/.arm_finetune/bin/activate` |
| lerobot CLI 인자 | 원본 그대로 | 변경 없음 |
| FOLLOWER_PORT / LEADER_PORT | `/dev/ttyACM1` / `/dev/ttyACM0` | 변경 없음 (물리 구성 동일) |

### push_dataset_hub.sh

| 항목 | 원본 (datacollector) | 변경 후 (dgx) |
|---|---|---|
| venv 경로 (Python error 메시지) | `source ~/smolvla/datacollector/.hylion_collector/bin/activate` | `source ~/smolvla/dgx/.arm_finetune/bin/activate` |
| data_root 예시 | `~/smolvla/datacollector/data/<name>` | `~/smolvla/dgx/data/<name>` |
| 완료 메시지 footer | `ssh dgx` + `source ~/smolvla/dgx/.arm_finetune/...` | DGX 자체 실행이므로 ssh dgx 제거, source 경로 통일 |
| HF_TOKEN 참조 | `${HF_TOKEN}` (set -e 환경에서 unbound 가능) | `${HF_TOKEN:-}` (unset 안전 처리) |
| heredoc 보안 패턴 | `<<'PYEOF'` 단일 따옴표 | 원본 그대로 보존 |
| LeRobotDataset.push_to_hub 인자 | 원본 그대로 | 변경 없음 |

### check_hardware.sh

신규 작성 (원본 없음) — orin/tests/check_hardware.sh 패턴 기반, DGX 수집 환경 맞춤:

| 항목 | orin 패턴 | DGX 적용 |
|---|---|---|
| venv 경로 | `~/smolvla/orin/.hylion_arm` | `~/smolvla/dgx/.arm_finetune` |
| mode 인자 | `first-time / resume` | 미적용 (단순 점검 스크립트) |
| cusparseLt fallback | 있음 (Orin 전용) | 제거 (DGX 불필요) |
| step 구성 | venv · cuda · soarm_port · cameras | venv · dialout · soarm_port · v4l2 · cameras |
| dialout 체크 | 없음 | 추가 (DGX USB 접근 권한 체크) |
| v4l2 체크 | 없음 | 추가 (카메라 직결 전 선행 확인) |
| CUDA 체크 | 있음 | 제거 (수집 환경 무관) |
| config 파일 | YAML 기반 (`--config`) | 불필요 (단순 환경 점검) |
| JSON 결과 관리 | 있음 | 동일 패턴 적용 |

---

## §3 check_hardware.sh 책임 분담 결정 사유

**결정: preflight_check.sh (학습) + check_hardware.sh (수집) 분리**

**근거:**

1. `preflight_check.sh` 는 학습 시나리오별 메모리 임계치 (smoke 20GB / s1 35GB / s3 65GB / lora 28GB) 논리를 담고 있음. 수집 환경 체크 (USB·dialout·v4l2·카메라) 와 본질적으로 책임이 다름.

2. X2 `env_check.py` 의 `mode` 파라미터 정합: `env_check.py` 는 `mode=collect` 시 수집 환경 체크, `mode=train` 시 학습 환경 체크로 분기. bash 스크립트 단위에서도 같은 분리가 명확함.

3. 통합 스크립트로 만들 경우: `preflight_check.sh` 의 set -e + case 분기 구조가 수집 환경 체크의 "경고 허용" 정책 (v4l2 미발견 = WARN, 카메라 1대 = WARN) 과 충돌.

4. `orin/tests/check_hardware.sh` 도 학습(CUDA) + 수집(SO-ARM·카메라)를 **하나**의 스크립트에 담고 있으나, Orin 은 추론 전용 단일 책임이라 통합 가능. DGX 는 학습 + 수집 **이중 책임**이라 분리가 적합.

**sync_ckpt_dgx_to_orin.sh**: 본 spec 외. training.py 가 차기 사이클(07_leftarmVLA) 에서 ckpt 관리 안내 메시지 출력 시 신규 작성 (X2 보고서 §5 정합 — spec 결정 H-(b) 인계).

---

## §4 bash -n + shellcheck 자체 검증 결과

### bash -n 결과

```
bash -n dgx/scripts/run_teleoperate.sh   → OK (exit 0)
bash -n dgx/scripts/push_dataset_hub.sh  → OK (exit 0)
bash -n dgx/scripts/check_hardware.sh    → OK (exit 0)
```

### shellcheck

shellcheck 바이너리 미설치 (apt-cache show shellcheck: 0.8.0-2 available but not installed).

수동 점검 완료:
- `run_teleoperate.sh`: `set -euo pipefail`. 모든 변수 쌍따옴표 처리. `case` 분기 `*)` 처리.
- `push_dataset_hub.sh`: `set -e`. `HF_TOKEN` → `${HF_TOKEN:-}` unset 안전 처리. heredoc `<<'PYEOF'` 단일 따옴표 보안 패턴. `while [ $# -gt 0 ]` + `shift` 쌍 정합.
- `check_hardware.sh`: `set -uo pipefail`. `set -e` 미사용 (개별 step 실패 수집 의도). `record_step()` 환경변수 경유 Python 호출 — 특수문자 안전. `trap` + mktemp 임시 파일 정리.

---

## §5 잔여 리스크

| 항목 | 내용 | 처리 방침 |
|---|---|---|
| sync_ckpt_dgx_to_orin.sh | 미작성 — spec 결정 H-(b) + X2 §5 인계: "차기 사이클 신규 안내" | 차기 사이클(07_leftarmVLA) 위임. BACKLOG 후보 |
| check_hardware.sh Step 5 cameras | lerobot [hardware] extra 미설치 시 ImportError FAIL | X4·X5 완료 후 재실행. 에러 메시지에 설명 포함 |
| push_dataset_hub.sh LeRobotDataset API | upstream 버전에 따라 `push_to_hub(private=, branch=)` 시그니처 변경 가능 | V2 prod 검증 시 확인. HF Hub push 실패 시 사용자 안내 메시지 포함 |
| run_teleoperate.sh 포트 변동 | DGX 시연장 이동 후 USB 순서 변동 시 FOLLOWER_PORT / LEADER_PORT 재확인 필요 | lerobot-find-port 재실행 안내 포함 (코멘트) |
| dialout 그룹 (check_hardware.sh) | DGX 사용자 계정 dialout 미설정 시 FAIL | `sudo usermod -aG dialout $(id -un)` 해결 힌트 포함 |

---

## code-tester 입장에서 검증 권장 사항

- bash -n: `bash -n dgx/scripts/run_teleoperate.sh` · `push_dataset_hub.sh` · `check_hardware.sh` (이미 OK)
- shellcheck (설치 후): `shellcheck dgx/scripts/run_teleoperate.sh push_dataset_hub.sh check_hardware.sh`
- 원본 인용 정합: 레거시 원본 대비 변경 항목 §2 와 실제 파일 diff 비교
- preflight_check.sh 미접촉 확인: `git diff dgx/scripts/preflight_check.sh` → 변경 없음
- 기존 dgx/scripts/ 파일 미접촉: smoke_test.sh · save_dummy_checkpoint.sh · setup_train_env.sh 변경 없음
