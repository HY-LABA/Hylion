# TODO-X3 — Code Test

> 작성: 2026-05-02 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 0건. Recommended 2건.

---

## 단위 테스트 결과

```
bash -n dgx/scripts/run_teleoperate.sh   → exit 0  (OK)
bash -n dgx/scripts/push_dataset_hub.sh  → exit 0  (OK)
bash -n dgx/scripts/check_hardware.sh    → exit 0  (OK)
```

3파일 모두 bash syntax 통과.

---

## Lint·Type 결과

```
shellcheck: 바이너리 미설치 (apt-cache show shellcheck: 0.8.0-2 available, not installed)
ruff / mypy: .sh 파일 비적용 (bash 스크립트)
```

수동 패턴 점검 결과:

- `run_teleoperate.sh`: `set -euo pipefail` 선언. 모든 변수 쌍따옴표 처리. `case ... *)` 분기 처리. heredoc `<<'EOF'` 단일 따옴표 (변수 확장 차단).
- `push_dataset_hub.sh`: `set -e` 선언 (원본과 동일). `${HF_TOKEN:-}` 안전 처리. heredoc `<<'PYEOF'` 단일 따옴표 보존. `while [ $# -gt 0 ] ... shift` 쌍 정합.
- `check_hardware.sh`: `set -uo pipefail` 선언. `set -e` 미사용 (개별 step 실패 수집 의도). `record_step()` 환경변수 경유 Python 호출 (특수문자 안전). `trap + mktemp` 임시 파일 정리.

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| `run_teleoperate.sh` 신규 — datacollector/scripts/ 이식 + dgx venv 갱신 | ✅ | 원본 대비 venv 경로·주석·usage 만 변경. CLI 인자 100% 보존 확인 |
| `push_dataset_hub.sh` 신규 — heredoc 보안 패턴 그대로 | ✅ | `<<'PYEOF'` 단일 따옴표 보존. `${HF_TOKEN:-}` 보안 개선. 실행 로직 원본 동일 |
| `check_hardware.sh` 신규 — datacollector 이식 또는 preflight 통합 | ✅ | datacollector 원본 미존재 → orin 패턴 기반 신규 작성 (DOD "이식 또는 기존과 통합" 에 부합). 5-step 구성 (venv·dialout·soarm_port·v4l2·cameras) |
| 기존 {preflight_check, smoke_test, save_dummy_checkpoint}.sh 그대로 유지 | ✅ | `git diff HEAD -- dgx/scripts/preflight_check.sh` 등 3파일 출력 없음 (무변경) |
| bash -n + shellcheck 정적 검증 | ✅ (부분) | bash -n 3파일 모두 exit 0. shellcheck 미설치 → 수동 패턴 점검으로 대체 (보고서에 명시) |

---

## Critical 이슈

없음 (MAJOR_REVISIONS 사유 없음).

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `dgx/scripts/push_dataset_hub.sh:47` | `set -e` 만 선언 (원본과 동일). `set -euo pipefail` 으로 강화 가능. 단 원본 패턴 보존 의도적 선택으로 보임 — DOD 위반 아님 |
| 2 | `dgx/scripts/check_hardware.sh:94-98` | 초기 JSON 기록 `python3 -c` 블록 내 `'${TMP_RESULT_JSON}'` 는 bash 변수를 큰따옴표 없는 단일 따옴표로 내삽 — orin 원본과 동일 패턴이므로 Critical 아님. 단, 경로에 공백이 있으면 Python 문자열 리터럴로 처리돼 오류. DGX HOME 경로에 공백 없음 전제 유지 권장 |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` · `.claude/` 미변경. 신규 3파일은 `dgx/scripts/` 하위 |
| B (자동 재시도 X 영역) | ✅ 비해당 | `dgx/lerobot/` · `dgx/pyproject.toml` · `dgx/scripts/setup_env.sh` · `scripts/deploy_*.sh` 미접촉. 신규 스크립트 3개는 Category B 외 |
| Coupled File Rules | ✅ 비해당 | `pyproject.toml` · `orin/lerobot/` · `dgx/lerobot/` 미변경 → Coupled File Rule 발동 없음 |
| 옛 룰 | ✅ | `docs/storage/` 하위 bash 예시 추가 없음 |

---

## 원본 인용 정합 상세

### run_teleoperate.sh

`diff` 결과 (원본 vs dgx):

- 주석 헤더: 노드명(DataCollector → DGX) + 이식 이력 + 변경 항목 설명 추가 — 정보 보강
- `source ~/smolvla/datacollector/.hylion_collector/bin/activate` → `source ~/smolvla/dgx/.arm_finetune/bin/activate` (usage 내 1곳)
- `datacollector/config/ports.json` → `dgx/config/ports.json` (캐시 경로 주석)
- `FOLLOWER_PORT`, `LEADER_PORT`, `FOLLOWER_ID`, `LEADER_ID` 변수값: 원본 그대로
- `lerobot-calibrate`, `lerobot-teleoperate` CLI 인자 전체: 원본 그대로
- `case` 분기 구조: 원본 그대로
- **판정: 정합. venv 경로 외 기능 변경 없음**

### push_dataset_hub.sh

`diff` 결과 (원본 vs dgx):

- 주석 헤더: 노드명(DataCollector → DGX) + 이식 이력 추가
- `~/smolvla/datacollector/data/` → `~/smolvla/dgx/data/` (usage 예시 및 에러 메시지 3곳)
- `${HF_TOKEN}` → `${HF_TOKEN:-}` (L106/L114): unset 시 `set -e` 환경 비정상 종료 방지 → **보안·안전성 개선 (Critical 아님)**
- `print("    source ~/smolvla/datacollector/.hylion_collector/bin/activate")` → dgx 경로 (L189)
- footer 완료 메시지: `"ssh dgx"` + `"DGX 에서 dataset 다운로드:"` → `"DGX 에서 dataset 확인:"` (DGX 자체 실행이므로 ssh 불필요)
- heredoc `<<'PYEOF'` 단일 따옴표: **원본 그대로 보존**
- `LeRobotDataset(repo_id=..., root=...)` + `.push_to_hub(private=..., branch=...)`: **원본 그대로**
- **판정: 정합. 보안 패턴 보존 + data_root 경로 변경 + 불필요한 ssh 안내 제거 — 모두 적절**

### check_hardware.sh

원본 (`datacollector/scripts/check_hardware.sh`) 미존재 확인됨 (task-executor 보고서 §1 명시).
orin/tests/check_hardware.sh 패턴 기반 신규 작성.

비교 (orin 4-step vs dgx 5-step):

| step | orin | dgx |
|---|---|---|
| 1 | venv 활성화 | venv 활성화 |
| 2 | CUDA 라이브러리 | dialout 그룹 멤버십 (신규) |
| 3 | SO-ARM 포트 발견 | SO-ARM 포트 발견 |
| 4 | 카메라 인덱스·flip | v4l2 장치 발견 (신규) |
| 5 | — | 카메라 인덱스 발견 |

- CUDA 체크 제거: DGX 수집 환경에서 CUDA 의존 불필요 (적절)
- cusparseLt fallback 제거: Orin 전용 workaround (적절)
- dialout·v4l2 단계 추가: DGX Ubuntu 22.04 USB 권한 구조 반영 (적절)
- `record_step()` 환경변수 경유 Python json.dump 패턴: orin 원본 그대로 미러
- `TMP_RESULT_JSON mktemp + trap EXIT`: orin 원본 그대로 미러
- `OpenCVCamera.find_cameras()` 호출: orin 원본 동일 (`from lerobot.cameras.opencv import OpenCVCamera`)
- `finalize_output()` JSON summary 패턴: orin 원본 미러
- **판정: 정합. DOD "이식 또는 통합" 옵션에서 신규 작성 경로 선택 — 합리적**

---

## 책임 분담 정합 검증

- `preflight_check.sh` (학습) + `check_hardware.sh` (수집) 분담:
  - `env_check.py` 의 `mode="train"` / `mode="collect"` 분기와 1:1 정합
  - `check_hardware.sh` 헤더에 분담 사유 명시 (단일 책임 + env_check.py 정합)
- `check_hardware.sh --output-json` 플래그: `env_check.py` 파싱용으로 명시 (정합)

---

## 차기 사이클 위임 정합

- `sync_ckpt_dgx_to_orin.sh` 미작성: spec 본문 §scripts/ 측 영향에 "후속(DGX→Orin ckpt sync)는 06 신규 todo 안 만들고, 차기 사이클(07_leftarmVLA) 진입 시 필요 시 신규" 명시 → X3 보고서 §5 및 §3 에서 동일하게 인계
- X2 보고서 §5 와 정합 확인됨

---

## 배포 권장

READY_TO_SHIP — prod-test-runner 진입 권장.

Critical 0건. Recommended 2건 (스타일/방어적 패턴 강화 후보 — 기능 영향 없음).
V1·V2 prod 검증에서 실물 환경 확인 예정 (X4·X5 완료 후 `check_hardware.sh Step 5 cameras` 재실행).
