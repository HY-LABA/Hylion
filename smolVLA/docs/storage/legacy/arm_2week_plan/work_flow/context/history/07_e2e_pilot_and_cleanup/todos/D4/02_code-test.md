# TODO-D4 — Code Test

> 작성: 2026-05-03 14:00 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈 0건. Recommended 개선 사항 2건 (2건 이하 → READY).

---

## 단위 테스트 결과

```
python3 -m py_compile \
  dgx/interactive_cli/flows/entry.py \
  dgx/interactive_cli/flows/env_check.py \
  dgx/interactive_cli/flows/mode.py \
  dgx/interactive_cli/flows/teleop.py \
  dgx/interactive_cli/flows/data_kind.py \
  dgx/interactive_cli/flows/record.py \
  dgx/interactive_cli/flows/transfer.py \
  dgx/interactive_cli/flows/training.py \
  dgx/interactive_cli/flows/precheck.py
→ ALL_OK (exit 0)

python3 -c "
import sys; sys.path.insert(0, 'dgx/interactive_cli')
from flows import mode; print('mode OK')
from flows import precheck; print('precheck OK')
from flows.precheck import teleop_precheck, _get_calib_dir
calib = _get_calib_dir()
print(f'calib_dir: {calib}')
"
→ mode OK
→ precheck OK
→ calib_dir: /home/babogaeguri/.cache/huggingface/lerobot/calibration

bash -n dgx/interactive_cli/main.sh
→ OK (exit 0)
```

---

## Lint·Type 결과

```
python3 -m ruff check dgx/interactive_cli/flows/
→ All checks passed!
```

mypy: 본 프로젝트 dgx/interactive_cli 에 mypy 설정 없음 — 생략 (SKILL_GAP 아님, 정책 外).

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| mode.py + precheck.py py_compile PASS | ✅ | ALL_OK (9파일) |
| ruff PASS | ✅ | All checks passed! |
| main.sh bash -n PASS | ✅ | exit 0 |
| 흐름: 수집 mode → env_check → precheck(신규) → _run_collect_flow 순서 | ✅ | mode.py L223-240 확인 — env_check PASS 직후 L233-238 precheck 삽입, precheck 후 L240 _run_collect_flow 호출 |
| 표시 정보 (모터 포트·카메라 인덱스·캘리브 위치) 실 저장 위치 인용 | ✅ | _get_calib_dir() 가 constants.py L66-75 로직 완전 미러. 환경변수 우선순위 3단계 정확. import smoke calib_dir 정상 |
| 메뉴 분기 3개 (1·2·3) 코드 정합 | ✅ | precheck.py L429/470/475 분기 확인. while-loop + invalid 입력 재시도 |
| 옵션 (1) find-port + find-cameras 자동 재실행 + 캘리브 별도 묻기 | ✅ | precheck.py L436 _run_find_port → L442 _run_find_cameras → L453 캘리브 [y/N] 묻기 → _run_calibrate 조건부 |
| DGX SSH walkthrough smoke (precheck 도달까지) | ⚠️ PHYS_REQUIRED | env_check(mode="collect") SO-ARM 미연결 시 FAIL → precheck 도달 X (정상 동작). 시연장 SO-ARM 직결 환경에서만 검증 가능 |

DOD 미충족: 없음. PHYS_REQUIRED 항목은 spec 합의 내용.

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `dgx/interactive_cli/configs/` vs `dgx/config/` 분산 | 현재 `dgx/config/`(기존, dataset_repos.json·README) 와 `dgx/interactive_cli/configs/`(신규, ports·cameras) 두 곳 분산. `dgx/interactive_cli/configs/` 가 interactive_cli 전용이므로 모듈 응집 관점에서 OK. 단 15_orin_config_policy.md 는 `orin/config/` 기준 정책 문서 — dgx 측 동일 정책(git 추적·null placeholder) 은 적용됐으나 W4 정책 문서가 orin 전용 명칭. 다음 사이클 wrap 시 dgx 측 config 정책 통합 검토 권고 (Critical X). |
| 2 | `_run_calibrate()` 내 포트 로드 | `_run_calibrate()` 가 configs_dir/ports.json 에서 포트를 자동 로드하지 않고 사용자 입력을 다시 받음 (L304-315). _run_find_port 이후 저장된 값을 자동으로 읽어 기본값으로 제안하면 UX 개선 가능. 현재 동작에는 문제 없음. |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경. `.claude/agents/*.md`, `.claude/skills/**/*.md`, `.claude/settings.json` 미변경 |
| B (자동 재시도 X 영역) | ✅ | `dgx/lerobot/` 미변경. `dgx/pyproject.toml` 미변경. `scripts/deploy_*.sh` 미변경. `.gitignore` 미변경 |
| Coupled File Rules | ✅ | `dgx/lerobot/` 미변경 → 03_orin_lerobot_diff.md 트리거 X. `dgx/pyproject.toml` 미변경 → 의존성 Coupled File Rules 트리거 X |
| C (새 디렉터리) | ✅ | `dgx/interactive_cli/configs/` — `dgx/` 내부 신규 디렉터리. Category C 조건 "orin/·dgx/·docs/ 외" 이므로 미해당. 사용자 동의 불요 |
| 옛 룰 (docs/storage/ bash 예시) | ✅ | 변경 없음 |

### lerobot-reference-usage 준수 상세

| 레퍼런스 | 검증 | 결과 |
|---|---|---|
| `constants.py` L74-75 (HF_LEROBOT_CALIBRATION) | precheck.py docstring + `_get_calib_dir()` 로직이 L66-75 전체 재현 (HF_HOME → HF_LEROBOT_HOME → HF_LEROBOT_CALIBRATION 우선순위). import smoke 일치 | ✅ 정확한 인용 |
| `lerobot_find_cameras.py` argparse `choices=["realsense", "opencv"]` | L297 확인 → `lerobot-find-cameras opencv` 유효한 호출 | ✅ |
| `lerobot_find_port.py` 대화형 패턴 | `find_available_ports()` + 사용자 분리/재연결 안내 패턴 — precheck.py `_run_find_port()` 가 subprocess 래핑으로 구현 | ✅ |
| `lerobot_calibrate.py` `so101_follower`·`so101_leader` | upstream teleoperators/robots 모두 `so101_*` 등록 확인. `run_teleoperate.sh` 도 `so101_*` 사용. `lerobot_calibrate.py` 예시는 `so100_leader` 이나 이는 구형 예시 — 실제 subclass 등록 확인 완료 | ✅ so101_* 유효 |

---

## 배포 권장

READY_TO_SHIP — prod-test-runner 진입 권장.

prod-test-runner 검증 권장 시퀀스 (SSH_AUTO 가능 부분):

```bash
# DGX SSH — py_compile 9파일
ssh dgx "cd ~/smolvla && python3 -m py_compile dgx/interactive_cli/flows/*.py && echo ALL_OK"

# DGX SSH — ruff
ssh dgx "cd ~/smolvla && python3 -m ruff check dgx/interactive_cli/flows/"

# DGX SSH — main.sh bash -n
ssh dgx "bash -n ~/smolvla/dgx/interactive_cli/main.sh"

# DGX SSH — import smoke (precheck + calib_dir)
ssh dgx "cd ~/smolvla && python3 -c \"
import sys; sys.path.insert(0, 'dgx/interactive_cli')
from flows import precheck
from flows.precheck import _get_calib_dir, teleop_precheck
print('import OK')
print('calib_dir:', _get_calib_dir())
\""

# configs 파일 존재 확인
ssh dgx "cat ~/smolvla/dgx/interactive_cli/configs/ports.json && cat ~/smolvla/dgx/interactive_cli/configs/cameras.json"
```

비대화형 precheck UI walkthrough (SO-ARM 미연결 환경): env_check(mode="collect") FAIL로 precheck 미도달 — PHYS_REQUIRED. verification_queue D4 항목으로 등록 권장.
