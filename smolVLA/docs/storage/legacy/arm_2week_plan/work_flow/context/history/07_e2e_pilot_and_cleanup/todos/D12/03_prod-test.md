# TODO-D12 — Prod Test

> 작성: 2026-05-04 17:15 | prod-test-runner | cycle: 1

## Verdict

**`NEEDS_USER_VERIFICATION`**

자동 검증 (AUTO_LOCAL + SSH_AUTO) 전 항목 통과. DOD 5항 중 4항 자동 충족. DOD 5항 (사용자 walkthrough 재시도 — cameras.json 검출 결과 사용) 은 PHYS_REQUIRED — verification_queue 추가.

---

## 배포 대상

- DGX (dgx/interactive_cli/flows/record.py + mode.py 변경)

## 배포 결과

- 명령: `bash scripts/deploy_dgx.sh`
- 결과: 성공
- 전송 파일:
  - `interactive_cli/flows/mode.py` (10,794 bytes, 2026-05-04 17:08)
  - `interactive_cli/flows/record.py` (24,533 bytes, 2026-05-04 17:09)
- rsync speedup: 32.63 (기존 파일 변경분만 전송)
- lerobot 서브모듈: 변경 없음 (speedup 440.60 — 바이트 전송 최소)
- Category B 영역 변경 없음 (dgx/lerobot/ 미변경) → 자율 배포 적용

---

## 자동 비대화형 검증 결과

### A. devPC 정적 (AUTO_LOCAL)

| 검증 | 명령 | 결과 |
|---|---|---|
| py_compile record.py | `python3 -m py_compile dgx/interactive_cli/flows/record.py` | OK |
| py_compile mode.py | `python3 -m py_compile dgx/interactive_cli/flows/mode.py` | OK |
| ruff lint | `ruff check dgx/interactive_cli/flows/record.py dgx/interactive_cli/flows/mode.py` | All checks passed! |
| bash -n main.sh | `bash -n dgx/interactive_cli/main.sh` | OK |
| import smoke record | `python3 -c "import flows.record as r; print(r._load_configs_for_record)"` | OK |
| import smoke mode | `python3 -c "import flows.mode as m; print(m._run_collect_flow)"` | OK |

### B. DGX 배포 + sync 검증 (SSH_AUTO)

| 검증 | 결과 |
|---|---|
| deploy_dgx.sh 실행 | 성공 (mode.py + record.py 전송 확인) |
| DGX record.py 존재 확인 | `/home/laba/smolvla/dgx/interactive_cli/flows/record.py` 24533B, 2026-05-04 17:09 |
| DGX mode.py 존재 확인 | `/home/laba/smolvla/dgx/interactive_cli/flows/mode.py` 10794B, 2026-05-04 17:08 |
| DGX import smoke | `_load_configs_for_record`, `flow6_record`, `_validate_camera_indices`, `_run_collect_flow` ALL OK |
| DGX configs_dir 패치 확인 | mode.py L104 `configs_dir = script_dir / "configs"`, L109 `configs_dir=configs_dir` 전달 확인 |

### C. cameras.json·ports.json 로드 시뮬 (DGX)

| 시뮬 | 결과 |
|---|---|
| 현재 DGX configs 상태 | `ports.json`: follower/leader null placeholder. `cameras.json`: wrist_left/overview null placeholder |
| null placeholder → fallback | `_load_configs_for_record()` 로드 → cameras `{'wrist_left': {'index': None}, 'overview': {'index': None}}`, ports `{'follower_port': None, 'leader_port': None}` |
| None 가드 → hardcoded fallback | `wrist_idx=None` → `cam_wrist_left_index=0` 유지. 경고 출력: "⚠ 미설정 항목 — v4l2 메타 device 차단 가능. precheck 옵션 1 (새 학습) 권장." 정상 출력 |
| 실 값 시뮬 (임시 configs) | `/dev/video0`·`/dev/video2`·`/dev/ttyACM1`·`/dev/ttyACM0` 주입 → 반영 확인. cameras_source="cameras.json 검출 결과" 정상 |

### D. _validate_camera_indices 4 케이스 시뮬 (devPC + DGX)

| 케이스 | 입력 | 기대 | 결과 |
|---|---|---|---|
| int 정상 | `(0, 1)` | True | PASS |
| int 음수 | `(-1, 0)` | False | PASS |
| str 정상 | `("/dev/video0", "/dev/video2")` | True | PASS |
| str 비정규 | `("video0", "/dev/video2")` | False | PASS |
| str 빈 문자열 | `("", "/dev/video2")` | False | PASS |

devPC + DGX 양측 동일 결과 확인.

### E. BACKLOG.md 변경 확인

| 항목 | 결과 |
|---|---|
| 07 #4 완료 마킹 | "완료 (D12, 2026-05-03): _load_configs_for_record() helper 신설 + ..." — 확인 |
| 07 #15 신규 등록 | "deploy_dgx.sh 가 dgx/interactive_cli/configs/ports.json·cameras.json placeholder 덮어쓰는 문제 — ... rsync exclude 또는 별도 정책 필요." — 확인 |

---

## DOD 자동 부합

| DOD 항목 | 자동 검증 방법 | 결과 |
|---|---|---|
| 1. record.py 가 cameras.json + ports.json 로드 + hardcoded fallback | DGX 로드 시뮬 (null placeholder + 실 값) | ✅ |
| 2. 사용자 안내 출력 (config source 명시) | DGX null placeholder 시뮬 — 출처 안내 + 경고 출력 확인 | ✅ |
| 3. BACKLOG 07 #15 추가 | BACKLOG.md grep 확인 | ✅ |
| 4. py_compile + ruff PASS | devPC AUTO_LOCAL 전 항목 PASS | ✅ |
| 5. 사용자 walkthrough 재시도 시 cameras.json 검출 결과 사용 | PHYS_REQUIRED — 시연장 SO-ARM + 카메라 직결 환경 필요 | → verification_queue |

---

## 사용자 실물 검증 필요 사항 (verification_queue 추가됨)

1. **[D12-F1] 게이트 4 walkthrough 재시도 — cameras.json 검출 결과 record 반영 확인**
   - 시연장 SO-ARM + 카메라 USB 직결 DGX 환경에서 `bash dgx/interactive_cli/main.sh`
   - 흐름: flow1 DGX 선택 → precheck 옵션 1 (새 수집 시작) → `_run_find_cameras_split` 완료 → cameras.json 갱신 (`/dev/videoN`·`/dev/videoM`) → record 진입 시 "[record] config 출처: cameras: wrist_left=/dev/videoN, overview=/dev/videoM (cameras.json 검출 결과)" 출력 확인
   - `lerobot-record` 인자에 `index_or_path: /dev/videoN` 경로 포함 확인 (hardcoded `0`·`1` 미사용)
   - OpenCVCamera 차단 X 확인 (D4 게이트 4 + D6·D7·D8·D9·D10·D11 통합 walkthrough 내 자연 검증 권장)

---

## CLAUDE.md 준수

- Category B 영역 (dgx/lerobot/) 변경 없음 → 자율 배포 적용
- Category A 영역 (docs/reference/, .claude/) 변경 없음
- Category D 명령 미사용
- deploy_dgx.sh 스크립트 내용 변경 없음 (실행만)
- 자율 영역 (rsync 배포 + SSH import smoke + python -c 시뮬) 만 실행

## BACKLOG 신규 항목 참고

- 07 #15: deploy_dgx.sh 가 `dgx/interactive_cli/configs/` 를 rsync --delete 로 덮어쓰는 문제 — precheck 옵션 1 재실행으로 우회 가능. 영구 fix: rsync exclude 패턴에 `configs/` 추가 권장. (D12 walkthrough 에서 발견, BACKLOG.md 등록 완료)
