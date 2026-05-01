# TODO-G2 cycle 2 — _to_idx Path 타입 수정 + dead catch 제거

> 2026-05-01 | task-executor | MINOR_REVISIONS 반영

## 배경

code-tester cycle 1 verdict: MINOR_REVISIONS (Critical 0, Recommended 3).
MINOR 정책: 1회 수정 + 재검증 없이 prod-test-runner 진입.

## 변경 파일

| 경로 | 변경 종류 | 요약 |
|---|---|---|
| `orin/inference/hil_inference.py` | M | `_to_idx()` str→Path, dead catch 제거, 주석 정정 |
| `docs/work_flow/context/todos/G2/01_implementation.md` | M | cycle 2 절 추가, 시나리오 6번 보강 |

## 수정 내용

### #1 _to_idx() str fallback → Path(v)

`OpenCVCameraConfig.index_or_path: int | Path` (orin/lerobot/cameras/opencv/configuration_opencv.py:61).
str 타입은 타입 어노테이션 위반. `/dev/video0` 같은 디바이스 경로는 `Path("/dev/video0")` 로 반환.
`pathlib.Path` 는 이미 line 37 에서 import 돼 있으므로 추가 import 없음.

### #2 dead catch 제거

`apply_gate_config` 의 외부 `try / except Exception as e` 블록 제거.
`_to_idx()` 내부 `except (ValueError, TypeError)` 가 이미 모든 예외를 처리하므로 외부 catch 에는 도달 불가.
코드 4줄 감소.

### #3 prod-test 시나리오 6번 보강

`--gate-json` 단독 지정 시 ports.json.follower_port=null → parser.error 가 먼저 발생하여
`[gate]` 로그 확인 불가 문제. `--follower-port /dev/ttyACM0` 를 명시하면 gate 코드 경로 통과.
01_implementation.md 의 자율 6번 명령 보강.

## 적용 룰

- Category A/B/C/D 미해당 — `orin/inference/hil_inference.py` 는 Category B 외
- Coupled File Rules 무관 — orin/lerobot/ 미변경, pyproject.toml 미변경
- 레퍼런스 확인: orin/lerobot/cameras/opencv/configuration_opencv.py:61 `index_or_path: int | Path` 직접 확인
