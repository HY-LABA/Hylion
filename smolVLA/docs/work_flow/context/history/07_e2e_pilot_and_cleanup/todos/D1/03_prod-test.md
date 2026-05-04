# TODO-D1 — Prod Test

> 작성: 2026-05-03 | prod-test-runner | cycle: 1

## Verdict

**`NEEDS_USER_VERIFICATION`**

AUTO_LOCAL + SSH_AUTO 전 항목 통과. PHYS_REQUIRED 항목 4건 (D-1~D-4) verification_queue D 그룹에 추가.

---

## 배포 대상

- dgx

## 배포 결과

- 명령: `bash scripts/deploy_dgx.sh`
- 결과: 성공
- 로그:
  - `dgx/interactive_cli/flows/` 8개 파일 전송 (mode.py·teleop.py·data_kind.py·record.py·transfer.py 신규 포함)
  - `docs/reference/lerobot/` rsync incremental (변경 없음 — 26,840 bytes sent, speedup 440.60)
  - `interactive_cli/configs/node.yaml` 정상 동기화
  - 배포 전 DGX 측 flows/ 에 mode.py 등 누락 → 배포로 해소

---

## 자동 비대화형 검증 결과

### AUTO_LOCAL (devPC 정적 검증)

| 검증 | 명령 | 결과 |
|---|---|---|
| py_compile × 8 | `python3 -m py_compile dgx/interactive_cli/flows/*.py` | 8/8 OK |
| ruff check | `ruff check dgx/interactive_cli/flows/*.py` | All checks passed! |
| main.sh bash -n | `bash -n dgx/interactive_cli/main.sh` | OK |

### SSH_AUTO (ssh dgx 비대화형)

| 검증 | 명령 | 결과 |
|---|---|---|
| DGX 가용성 | `ssh dgx "hostname && uname -a"` | spark-8434, Linux aarch64 |
| venv 존재 | `test -f ~/smolvla/dgx/.arm_finetune/bin/activate` | OK |
| node.yaml 존재 | `cat ~/smolvla/dgx/interactive_cli/configs/node.yaml` | node: dgx, responsibilities: training+data_collection |
| py_compile × 8 (DGX) | `python3 -m py_compile dgx/interactive_cli/flows/*.py` | 8/8 OK |
| main.sh bash -n (DGX) | `bash -n ~/smolvla/dgx/interactive_cli/main.sh` | OK |
| flow 0 — VALID_NODES | `from flows.entry import VALID_NODES; flow0_confirm_environment(...)` | ('orin', 'dgx'), dgx: True, orin: True |
| flow 1 — NODE_DESCRIPTIONS | `from flows.entry import NODE_DESCRIPTIONS` | dgx·orin 설명 정상, datacollector 없음: True |
| flow 2 — env_check 함수 임포트 | `from flows.env_check import flow2_env_check, _check_hardware_collect, run_env_check` | OK |
| flow 2 — preflight_check.sh | `Path.home() / 'smolvla/dgx/scripts/preflight_check.sh'` | 존재: True |
| flow 2 — 시그니처 | `inspect.signature(flow2_env_check)` | `(script_dir: Path, scenario: str = 'smoke', mode: str = 'train') -> bool` — 기대치 일치 |
| flow 2 — fallback (SO-ARM 미연결) | `_check_hardware_collect()` | FAIL 안내 출력 + `False` 반환 — 크래시 X |
| mode.py 패치 정합 | `inspect.getsource(flow3_mode_entry)` | `_flow2_env_check_collect` + `mode="collect"` 호출 존재 확인 |

---

## flow 2 SO-ARM 미연결 실 출력 (SSH_AUTO)

```
  [항목 6] USB 포트 확인
    FAIL  leader  (/dev/ttyACM0) 미발견 — SO-ARM leader 연결 확인
    FAIL  follower (/dev/ttyACM1) 미발견 — SO-ARM follower 연결 확인

  [항목 7] dialout 그룹 멤버십
    PASS  laba 는 dialout 그룹 멤버

  [항목 8] v4l2 카메라 확인
    FAIL  /dev/video* 디바이스 없음 — 카메라 USB 연결 확인

  [항목 9] SO-ARM 포트 응답
    SKIP  /dev/ttyACM1 미존재 — 항목 6 FAIL 로 이미 확인됨
결과 (SO-ARM 미연결): False
```

항목 6·8 FAIL 안내 정상 출력, 항목 9 SKIP (항목 6 FAIL 연계) 정상 처리, 크래시 없이 `False` 반환 — fallback 동작 PASS.

---

## DOD 자동 부합

| DOD 항목 | 자동 검증 | 결과 |
|---|---|---|
| 1. SSH_AUTO PASS: flow 0 (entry), flow 1 (장치 선택), flow 2 (env_check fallback) | yes (SSH_AUTO) | ✅ |
| 2. flow 3~7 py_compile·ruff·bash -n PASS | yes (AUTO_LOCAL + SSH_AUTO) | ✅ |
| 3. PHYS_REQUIRED 항목 verification_queue D 그룹 마킹 | no (사용자 실물 환경) | → verification_queue D 그룹 추가됨 |
| 4. 04 BACKLOG #14 진단·수정 (DGX env_check.py NoneType) | yes (정적 분석) | ✅ (port_handler 패턴 0건, serial.Serial context manager 확인) |
| 5. prod-test-runner 인계 검증 명령 시퀀스 작성 (SSH 자율) | yes (본 문서 실행) | ✅ |

---

## 사용자 실물 검증 필요 사항 (verification_queue D 그룹 추가됨)

1. **[D-1]** flow 2 env_check 항목 6~9 실물 PASS — SO-ARM + 카메라 USB 직결 환경에서 `/dev/ttyACM0` (leader), `/dev/ttyACM1` (follower) 인식, dialout 그룹, `/dev/video*` 인식, `serial.Serial` open PASS 확인
2. **[D-2]** flow 3 텔레오퍼레이션 (`run_teleoperate.sh all`) — SO-ARM leader+follower 직결, 동작 추종 육안 확인
3. **[D-3]** flow 6 `lerobot-record` (dummy 1~3 에피소드) — SO-ARM + 카메라 2대 직결. `cam_wrist_left=0`, `cam_overview=1` 실 인덱스 정합 확인
4. **[D-4]** 04 BACKLOG #14 실물 확인 — SO-ARM 직결 환경에서 env_check.py 항목 9 (`serial.Serial` context manager) `NoneType` 에러 미발생 확인

→ 모두 PHYS_REQUIRED (SO-ARM·카메라 USB 직결 필수) — "시연장 이동 시" 처리.

---

## CLAUDE.md 준수

| 항목 | 결과 |
|---|---|
| Category B 영역 변경 여부 (deploy 전 확인) | 변경 파일 `dgx/interactive_cli/flows/mode.py` — Category B 외. `dgx/lerobot/`·`pyproject.toml`·`setup_env.sh`·`deploy_*.sh` 미변경 → 자율 배포 OK |
| 자율 영역만 사용 | ✅ (SSH read-only 검증 + py_compile/ruff + 자율 deploy) |
| Category D 명령 미사용 | ✅ |
| Category A 영역 수정 X | ✅ (배포·검증만) |
