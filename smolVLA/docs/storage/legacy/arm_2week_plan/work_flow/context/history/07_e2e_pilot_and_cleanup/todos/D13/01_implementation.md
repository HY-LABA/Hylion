# TODO-D13 — Implementation

> 작성: 2026-05-03 | task-executor | cycle: 1

## 목표

precheck 옵션 2 cameras.json null 시 streamable fallback (Part A) + deploy_dgx.sh configs exclude (Part B) + BACKLOG 07 #15 완료 마킹 (Part C)

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `dgx/interactive_cli/flows/precheck.py` | M | 옵션 2 분기: cameras.json null 검출 + streamable fallback + ports.json null 안내 추가 |
| `scripts/deploy_dgx.sh` | M | rsync `--exclude 'interactive_cli/configs/*.json'` 추가 |
| `docs/work_flow/specs/BACKLOG.md` | M | 07 #15 완료 마킹 |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경. `orin/lerobot/`, `dgx/lerobot/` 미변경 (옵션 B 원칙). 이 변경은 Category B 영역 (`scripts/deploy_dgx.sh`) — 사용자 동의 (d) 이미 수령.
- Coupled File Rule: `deploy_dgx.sh` 는 `pyproject.toml` / `setup_env.sh` 와 무관 — 별도 coupled file 없음. 변경 이력은 본 implementation.md 에 기록.
- 레퍼런스 활용: `_get_streamable_video_devices()` 는 이미 `precheck.py` 에 구현됨 (D8 e). 본 TODO 는 옵션 2 분기에서 해당 함수를 *호출*하는 것이므로 신규 자산 없음. 레퍼런스 SKILL_GAP 해당 없음.

## 변경 내용 요약

### Part A — precheck.py 옵션 2 streamable fallback

기존 옵션 2 분기는 cameras.json 상태 무관하게 즉시 "proceed" 를 반환했다. deploy_dgx.sh 가 매 deploy 마다 cameras.json 을 null 초기값으로 덮어써서 옵션 2 진입 시 record 가 하드코딩 fallback (`wrist:0, overview:1`) 을 사용하고, linux v4l2 video1 이 메타 device 여서 `OpenCVCamera(1)` 열기가 차단되는 문제였다.

수정 내용:
- `_load_json_or_default` 로 cameras_path 를 읽어 wrist_left / overview 인덱스 null 여부 확인
- null 인 경우 이미 구현된 `_get_streamable_video_devices()` 호출 (D8 e 자산 재사용)
- streamable device 2개 이상이면 첫 번째 → wrist_left, 두 번째 → overview 로 cameras.json 자동 갱신 + 정합 확인 권고 출력
- streamable device 부족 시 사용자에게 명시 안내 (hardcoded fallback 경고)
- ports.json null 시에도 안내 출력 추가 (자동 fallback 없음 — follower/leader 구분 불가)
- _save_json 실패 시 예외 처리 포함 (기존 _save_json 이 False 반환)

### Part B — deploy_dgx.sh exclude

rsync 명령에 `--exclude 'interactive_cli/configs/*.json'` 추가. rsync 의 source 기준 상대 경로 (`dgx/` 기준 → `interactive_cli/configs/*.json`). devPC 의 placeholder cameras.json / ports.json 이 DGX 에 배포되어 사용자 검출 결과를 덮어쓰는 문제를 영구 차단.

orin/config 의 W4 정책 (git 추적 유지 + 사용자 환경 override) 과 같은 패턴. DGX 측 configs/*.json 은 시연장 셋업 후 precheck 옵션 1 검출 결과이므로 devPC 파일로 덮어쓰면 안 됨.

### Part C — BACKLOG #15 완료 마킹

BACKLOG.md 07 #15 항목에 "완료 (07 D13 Part B, 2026-05-03)" 마킹 + 변경 요약 추가.

BACKLOG.md 07 #4 (cameras.json 단절) 확인: D12 에서 이미 "완료 (D12, 2026-05-03)" 마킹 — 추가 조치 불요.

## 정적 검증 결과

- `python3 -m py_compile dgx/interactive_cli/flows/precheck.py`: PASS
- `ruff check dgx/interactive_cli/flows/precheck.py`: PASS (F541 2건 수정 후)
- `bash -n scripts/deploy_dgx.sh`: PASS

## code-tester 입장에서 검증 권장 사항

- 단위: `python3 -c "from dgx.interactive_cli.flows.precheck import teleop_precheck; print('import OK')"` (dgx/ 가 PYTHONPATH 에 있으면)
- 시뮬 Part A:
  - cameras.json null 인 상태에서 옵션 2 선택 → streamable device 감지 후 cameras.json 자동 갱신 확인
  - cameras.json 이미 채워진 상태에서 옵션 2 선택 → 갱신 없이 즉시 "다음 흐름:" 출력 확인
- 시뮬 Part B:
  - `rsync --dry-run` 에서 `interactive_cli/configs/*.json` 이 전송 목록에서 제외되는지 확인
  - 패턴: `rsync -avz --dry-run --exclude 'interactive_cli/configs/*.json' dgx/ /tmp/test-deploy/` 후 /tmp/test-deploy/interactive_cli/configs/ 내용 확인
- DOD 항목 확인:
  - precheck.py 옵션 2 streamable fallback + cameras.json 자동 갱신: ✓ (구현)
  - deploy_dgx.sh exclude 추가 (Category B, 사용자 동의 받음): ✓ (구현)
  - BACKLOG 07 #15 완료 마킹: ✓ (구현)
  - py_compile + ruff + bash -n PASS: ✓ (실행 확인)
