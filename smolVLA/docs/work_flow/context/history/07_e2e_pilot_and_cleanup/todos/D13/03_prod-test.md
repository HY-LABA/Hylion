# TODO-D13 — Prod Test

> 작성: 2026-05-03 | prod-test-runner | cycle: 1

## Verdict

**`NEEDS_USER_VERIFICATION`**

## 배포 대상

- DGX (`bash scripts/deploy_dgx.sh`)

## 배포 결과

- 명령: `bash scripts/deploy_dgx.sh`
- 결과: 성공
- 로그 요약:
  - `interactive_cli/flows/precheck.py` 1파일 전송 (갱신)
  - `interactive_cli/configs/cameras.json` / `ports.json` 전송 제외 확인 (--exclude 'interactive_cli/configs/*.json' 동작)
  - lerobot/ submodule rsync — 변경 없음 (speedup=440.60)
  - 배포 후 DGX `~/smolvla/dgx/interactive_cli/configs/` 내 cameras.json·ports.json 보존 확인

## 자동 비대화형 검증 결과

| 검증 | 명령 | 결과 |
|---|---|---|
| A1. py_compile devPC | `python3 -m py_compile dgx/interactive_cli/flows/precheck.py` | PASS |
| A2. ruff devPC | `ruff check dgx/interactive_cli/flows/precheck.py` | All checks passed! |
| A3. bash -n deploy | `bash -n scripts/deploy_dgx.sh` | PASS |
| B1. rsync exclude dry-run | exclude 패턴 적용 rsync --dry-run | cameras.json·ports.json 전송 목록 없음 PASS |
| B2. node.yaml 전송 확인 | 동일 dry-run grep node.yaml | 포함됨 (JSON 아닌 yaml 정상) |
| B3. precheck.py 전송 확인 | 동일 dry-run grep precheck.py | 포함됨 (코드 파일 정상) |
| C1. deploy_dgx.sh 실 실행 | `bash scripts/deploy_dgx.sh` | 성공 (precheck.py 전송, json 제외) |
| C2. DGX py_compile | `ssh dgx "python3 -m py_compile .../precheck.py"` | PASS |
| C3. DGX import smoke | `ssh dgx "python3 -c ..."` teleop_precheck + _get_streamable_video_devices | import OK + 함수 2종 확인 |
| D1. DGX cameras.json 보존 | `ssh dgx "cat .../cameras.json"` | null 상태 보존 (devPC placeholder 미전송) |
| D2. DGX ports.json 보존 | `ssh dgx "cat .../ports.json"` | null 상태 보존 |
| E1. Part A null 검출 로직 devPC | python3 시뮬 (_load_json_or_default + null 분기) | null 검출 True, cameras.json 갱신 성공 |
| E2. Part A streamable fallback DGX | `ssh dgx "python3 -c ..."` null 강제 → _get_streamable_video_devices → cameras.json 갱신 | video0·video1·video2·video3 검출 → cameras.json 자동 갱신 PASS |
| E3. cameras.json 출력 확인 | 갱신 후 cat | wrist_left=/dev/video0·overview=/dev/video1 정합 |
| F1. Part F ports null 안내 로직 | python3 시뮬 (ports null → 안내 분기) | ports_null_detected=True 분기 정상 |
| F2. DGX Part F ports null 안내 | `ssh dgx "python3 -c ..."` | "[precheck] ports.json 미설정 — record 가 hardcoded..." 출력 확인 |
| Part C BACKLOG 마킹 | `grep "완료 (07 D13" BACKLOG.md` | L157 완료 마킹 확인 |

## DOD 자동 부합

| DOD 항목 | 자동 검증 | 결과 |
|---|---|---|
| precheck.py 옵션 2 cameras.json null 검출 + streamable fallback | yes (devPC + DGX 시뮬) | ✅ |
| cameras.json 자동 갱신 (_save_json PASS) | yes (DGX 실 실행 + 파일 내용 확인) | ✅ |
| streamable device 부족 시 안내 분기 | yes (코드 정적 확인) | ✅ |
| ports.json null 시 안내 출력 | yes (devPC + DGX 시뮬) | ✅ |
| deploy_dgx.sh --exclude 'interactive_cli/configs/*.json' 추가 | yes (rsync dry-run) | ✅ |
| json 파일 전송 차단 + 비json 파일 정상 전송 | yes (dry-run grep) | ✅ |
| DGX configs/*.json 배포 후 보존 | yes (DGX ssh cat) | ✅ |
| BACKLOG 07 #15 완료 마킹 | yes (grep 확인) | ✅ |
| py_compile + ruff + bash -n PASS | yes (devPC + DGX 양측) | ✅ |
| 사용자 실물 walkthrough — record 정상 진입 | no (PHYS_REQUIRED) | → verification_queue |

## 사용자 실물 검증 필요 사항 (verification_queue 추가됨)

1. **[D13-G1] 게이트 4 walkthrough 재시도 — cameras.json null 시 streamable fallback 효과 + record 정상 진입 확인** (PHYS_REQUIRED)
   - 환경: DGX + SO-ARM + 카메라 2대 USB 직결
   - 절차:
     1. cameras.json null 상태 유지 또는 강제 null 설정
     2. `cd ~/smolvla && bash dgx/interactive_cli/main.sh`
     3. flow1 DGX → precheck 옵션 2 선택
     4. 기대: "[precheck] cameras.json 미설정 검출 — streamable device 자동 fallback 시도" 출력
     5. 기대: "cameras.json 자동 갱신: wrist_left = /dev/videoN ..." 출력 (실 device 기반)
     6. flow6 record 진입 시 "[record] config 출처: cameras: wrist_left=/dev/videoN ..." 출력 확인
     7. OpenCVCamera 차단 미발생 확인 (v4l2 메타 device 경고 없음)

## Category B 처리

- deploy_dgx.sh 변경 포함 → Category B 영역
- implementation.md 에 "사용자 동의 (d) 이미 수령" 명시됨 → 배포 진행 (orchestrator 사용자 동의 수령 확인 기반)

## CLAUDE.md 준수

- Category B 영역 (scripts/deploy_dgx.sh) 변경된 deploy: 동의 이미 수령 (implementation.md 명시)
- Category A 미변경 (docs/reference/·.claude/ 미터치)
- Category D 명령 미사용
- orin/lerobot/·dgx/lerobot/ 미변경 (옵션 B 원칙 준수)
- docs/storage/ bash 예시 추가 없음
