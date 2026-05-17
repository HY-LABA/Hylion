# TODO-03-E — Implementation

> 작성: 2026-05-17 | task-executor | cycle: 2 (prod-test FAIL F1·F2·F3 후 재수정)

## 목표

F1 (reachy2_camera ImportError) + F2 (set -u LD_LIBRARY_PATH 충돌) + F3 (huggingface-cli deprecated) 묶음 fix — lerobot-record CLI 복원 + wrapper 스크립트 정상화.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `orin/lerobot/scripts/lerobot_record.py` | M | reachy2_camera import → try/except ImportError wrap (F1) |
| `orin/scripts/run_inference_leftarm_v2.sh` | M | LD_LIBRARY_PATH 초기화(F2) + hf/huggingface-cli fallback(F3) |
| `docs/storage/lerobot_upstream_check/03_orin_lerobot_diff.md` | M | F1 패치 entry 신규 추가 (Coupled Rule §3 의무) |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 ✓, `.claude/` 미변경 ✓
- Category B 사용자 승인: `orin/lerobot/scripts/lerobot_record.py` F1 패치 — 사용자 2026-05-17 23:45 승인 (옵션 A) ✓
- Coupled File Rule §3: `orin/lerobot/` 코드 수정 → `03_orin_lerobot_diff.md` 동시 갱신 ✓
- 레퍼런스 직접 Read: `docs/reference/lerobot/src/lerobot/scripts/lerobot_record.py` line 83 확인
  - upstream 원본 동일: `from lerobot.cameras.reachy2_camera import Reachy2CameraConfig  # noqa: F401`
  - orin 버전: 동일 plain import 였으나 `orin/lerobot/cameras/reachy2_camera` 폴더 없어 ImportError
- lerobot-upstream-check: 옵션 B 원칙 — upstream 파일 삭제/디렉터리 이동 X. import 보호(try/except)만 추가하여 upstream 흐름 최대 보존 ✓

## 변경 내용 요약

### F1 — lerobot_record.py reachy2_camera try/except

`orin/lerobot/cameras/` trim 에 `reachy2_camera/` 서브모듈이 없어 `lerobot-record` CLI 전체가 `ModuleNotFoundError` 로 실패하는 상황이었다. 사용자 승인 옵션 A: upstream 코드 흐름 최대 보존 원칙에 따라 import 시도 자체는 보존하되 `ImportError` 시 silent pass 처리. 주석으로 "orin trim — Reachy2 카메라 미포함 (inference-only, SO-ARM 작업 무관)" 명시. 인접 plain import (`OpenCVCameraConfig`, `RealSenseCameraConfig`, `ZMQCameraConfig`) 는 orin trim 에 해당 모듈 존재 — 동일 try/except 불필요, reachy2_camera 만 예외 처리.

### F2 — LD_LIBRARY_PATH 초기화

스크립트 상단 `set -euo pipefail` 직후 `export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}"` 한 줄 추가. Orin 시스템에 LD_LIBRARY_PATH 미설정 시 venv activate 내부 `export LD_LIBRARY_PATH=...:$LD_LIBRARY_PATH` 가 `-u` nounset 모드에서 unbound variable 에러를 내는 문제를 해결. 빈 문자열 초기화이므로 실제 LD_LIBRARY_PATH 에 영향 없음.

### F3 — hf/huggingface-cli fallback

`cmd_download` 함수의 `huggingface-cli download` → `command -v hf` 존재 시 `hf download`, 없으면 `huggingface-cli download` fallback 구조로 변경. Orin 에 설치된 `huggingface_hub 1.12.0` 에서 `huggingface-cli` deprecated → `hf` 대체. 동시에 구형 환경 호환성 유지.

## code-tester 입장에서 검증 권장 사항

- syntax: `bash -n orin/scripts/run_inference_leftarm_v2.sh` → SYNTAX_OK (확인 완료)
- AST: `python3 -c "import ast; ast.parse(open('orin/lerobot/scripts/lerobot_record.py').read())"` → AST_OK (확인 완료)
- Orin SSH: `lerobot-record --help` — F1 패치 후 ImportError 없이 도움말 출력 여부
- Orin SSH: `bash run_inference_leftarm_v2.sh download` — F2+F3 수정 후 set -u 에러 없이 hf download 실행 여부
- diff 정합성: `03_orin_lerobot_diff.md` F1 entry 형식 확인 (날짜·이유·before/after·영향 범위·inference-only 여부)

## 직전 피드백 반영 (prod-test FAIL F1·F2·F3)

| FAIL 사유 | 수정 |
|---|---|
| F1: `orin/lerobot/scripts/lerobot_record.py` line 83 `reachy2_camera` ImportError | try/except ImportError wrap 추가 (사용자 승인 옵션 A) |
| F2: `run_inference_leftarm_v2.sh` `set -u` + venv activate LD_LIBRARY_PATH unbound | 스크립트 상단 `export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}"` 추가 |
| F3: `cmd_download` 내 `huggingface-cli` deprecated | `command -v hf` 분기 — hf 우선, huggingface-cli fallback |

## 잔여 리스크

- **다른 누락 카메라 import**: `orin/lerobot/scripts/lerobot_record.py` 의 다른 import (`OpenCVCameraConfig`, `RealSenseCameraConfig`, `ZMQCameraConfig`) 는 orin trim 에 해당 모듈 존재 (`orin/lerobot/cameras/opencv/`, `realsense/`, `zmq/`) — 추가 try/except 불필요. prod-test-runner 가 `lerobot-record --help` 로 최종 확인 필요.
- **upstream 추가 trim 불일치**: lerobot_record.py 의 robots/teleoperators import 가 upstream 대비 이미 일부 trim되어 있음 (`reachy2`, `bi_openarm_follower` 등 미포함). 현재 동작에는 문제 없으나, upstream 재동기화 시 재점검 필요.
- **hf CLI 존재 여부**: Orin venv 에 `hf` 명령이 있는지 prod-test-runner 가 `which hf` 로 확인 필요. fallback 존재하므로 `huggingface-cli` 만 있어도 동작.
