# TODO-D9 — Prod Test

> 작성: 2026-05-03 15:28 | prod-test-runner | cycle: 1

## Verdict

**`NEEDS_USER_VERIFICATION`**

AUTO_LOCAL + SSH_AUTO 전 항목 PASS. PHYS_REQUIRED 1건 (실 walkthrough — find-port 완료 후 calibrate prompt 검증) 사용자 게이트 4 통합 대기.

---

## 배포 대상

- DGX

## 배포 결과

- 명령: `bash scripts/deploy_dgx.sh`
- 결과: 성공
- 전송 파일: `interactive_cli/configs/cameras.json`, `interactive_cli/configs/ports.json`, `interactive_cli/flows/precheck.py` (3파일)
- 증분 전송량: 2,920 bytes sent / 527 bytes received (speedup 66.62) — 수백 MB 아님 (이전 배포 이후 증분)
- docs/reference/lerobot/ 동기화: 26,840 bytes (speedup 440.60 — 대부분 기존 일치)

---

## 자동 비대화형 검증 결과

### A. devPC 정적 검증 (AUTO_LOCAL)

| 검증 | 명령 | 결과 |
|---|---|---|
| py_compile | `python -m py_compile dgx/interactive_cli/flows/precheck.py` | PASS |
| ruff lint | `ruff check dgx/interactive_cli/flows/precheck.py` | All checks passed! |
| import smoke | `python3 -c 'from flows.precheck import _run_calibrate, _PORTS_FILENAME, _PORTS_DEFAULT; import inspect; print(inspect.signature(_run_calibrate))'` | PASS — signature: `(configs_dir: pathlib._local.Path) -> bool` |

### B. DGX 배포 후 동기화 확인 (SSH_AUTO)

| 검증 | 명령 | 결과 |
|---|---|---|
| DGX SSH 연결 | `ssh -o ConnectTimeout=5 dgx "echo SSH_OK"` | SSH_OK |
| precheck.py 타임스탬프 | `ssh dgx "ls -la ~/smolvla/dgx/interactive_cli/flows/precheck.py"` | `-rw-rw-r-- laba laba 50491 5월 4 15:28` (배포 후 갱신) |
| ports.json 존재·내용 | `ssh dgx "cat ~/smolvla/dgx/interactive_cli/configs/ports.json"` | 존재 — 현재 `{"follower_port": null, "leader_port": null}` (find-port walkthrough 미완료 상태) |

### C. DGX import smoke (SSH_AUTO)

| 검증 | 명령 | 결과 |
|---|---|---|
| DGX import + 시그니처 | `ssh dgx "cd ~/smolvla/dgx/interactive_cli && python3 -c 'from flows.precheck import _run_calibrate, _PORTS_FILENAME, _PORTS_DEFAULT; import inspect; print(...)'` | import OK, `_PORTS_FILENAME: ports.json`, signature: `(configs_dir: pathlib.Path) -> bool` |

### D. ports.json 로드 시뮬 (SSH_AUTO)

| 검증 | 시나리오 | 결과 |
|---|---|---|
| ports_path 존재 확인 | DGX 측 `configs/ports.json` exists | True — 파일 존재 |
| null 상태 로드 | follower_port=null, leader_port=null → hardcoded fallback | PASS — `/dev/ttyACM1` fallback 정상 |
| 실 값 시뮬 (walkthrough 완료 후) | `follower_port=/dev/ttyACM0` → prompt default `ttyACM0, source: ports.json 검출 결과` | PASS — D9 fix 핵심 경로 정상 |

**비고**: 현재 DGX ports.json 이 null 인 이유는 find-port walkthrough 가 D4 당시 SO-ARM 직결 환경에서만 가능하기 때문. 실 walkthrough 완료 시 ports.json 에 follower/leader 실 포트가 저장되고, 이후 _run_calibrate 가 해당 값을 prompt default 로 사용하는 경로를 시뮬로 PASS 확인.

---

## DOD 자동 부합

| DOD 항목 | 자동 검증 | 결과 |
|---|---|---|
| 1. `_run_calibrate` 시그니처 `(configs_dir: Path) -> bool` | devPC + DGX import smoke (inspect.signature) | ✅ |
| 2. `ports_path = configs_dir / _PORTS_FILENAME` + `exists()` 가드 | code-tester L980~984 확인 + DGX 로드 시뮬 | ✅ |
| 3. `json.load` → `follower_port` / `leader_port` 키 읽기 + prompt default 적용 | DGX 실 값 시뮬 PASS | ✅ |
| 4. `JSONDecodeError | OSError` 예외 처리 + 경고 + hardcoded fallback | code-tester 시나리오 3 PASS (devPC) | ✅ |
| 5. 호출 위치 L1156 → `_run_calibrate(configs_dir)` 수정 | code-tester DOD #5 확인 | ✅ |
| 6. `configs_dir` 변수 scope 정합 (`teleop_precheck` L1081 정의) | code-tester DOD #6 확인 | ✅ |
| 7. 키 정합 (`follower_port` / `leader_port`) | DGX 로드 시뮬 + code-tester DOD #7 | ✅ |
| 8. py_compile + ruff PASS | devPC + DGX 양측 | ✅ |
| 9. walkthrough 실 calibrate SerialException 해소 | PHYS_REQUIRED → verification_queue | → Phase 3 |

---

## 사용자 실물 검증 필요 사항 (verification_queue 추가됨)

1. **[D9-1] find-port 완료 후 calibrate prompt default 확인 (PHYS_REQUIRED, D4 게이트 4 통합)**
   - SO-ARM + DGX USB 직결 환경에서:
     ```bash
     cd ~/smolvla && bash dgx/interactive_cli/main.sh
     ```
     흐름: flow3 mode (1) 수집 → precheck (1) 새 수집 시작 → `_run_find_port_self` (follower·leader USB 분리/재연결 각각) → ports.json 저장 → calibrate prompt:
     - follower calibrate prompt — `(Enter=/dev/ttyACM0, source: ports.json 검출 결과)` 표시 확인
     - leader calibrate prompt — `(Enter=/dev/ttyACM1, source: ports.json 검출 결과)` 표시 확인
     - Enter (default 수락) → follower 캘리브레이션이 `/dev/ttyACM0` (실 follower 포트) 로 진행 → `SerialException` 미발생 확인

---

## CLAUDE.md 준수

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경. `.claude/` 미변경 |
| B (자동 재시도 X) | ✅ | 변경 파일 `dgx/interactive_cli/flows/precheck.py` — Category B 외. `deploy_dgx.sh` 는 스크립트 내용 변경 X (실행만) |
| Category B deploy 자율성 | ✅ | deploy_dgx.sh 내용 Read 확인 — rsync + docs/reference/lerobot/ 동기화 (증분, 수백 MB 아님). GPU 학습·패키지 설치 트리거 X. 자율 실행 범위 |
| Coupled File Rules | ✅ | `orin/lerobot/` / `orin/pyproject.toml` 미변경 — coupled file 갱신 의무 없음 |
| 동의 영역 | N/A | 가상환경 재생성·패키지 업그레이드·큰 다운로드 없음 |
