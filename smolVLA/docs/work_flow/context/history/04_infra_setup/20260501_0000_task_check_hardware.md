# 20260501_0000 — TODO-G1: tests/check_hardware.sh 작성 (Orin)

> 날짜: 2026-05-01 | 에이전트: task-executor | 사이클: 1

## 요약

TODO-G1 구현 완료. `orin/tests/check_hardware.sh` (신규) + `orin/tests/configs/first_time.yaml` / `resume.yaml` (신규) + `.gitignore` 코멘트 추가.

## 산출물 목록

| 경로 | 종류 |
|---|---|
| `orin/tests/check_hardware.sh` | 신규 |
| `orin/tests/configs/first_time.yaml` | 신규 |
| `orin/tests/configs/resume.yaml` | 신규 |
| `Hylion/.gitignore` | 수정 (코멘트 블록 추가) |
| `docs/work_flow/context/todos/G1/01_implementation.md` | 신규 |

## 주요 결정

1. **lerobot-find-port 비대화형 우회**: `find_port()` 의 `input()` 을 건너뛰고 `find_available_ports()` Linux 분기 (ttyACM*/ttyUSB* glob) 만 인라인 Python3 으로 재현.
2. **카메라 발견**: `OpenCVCamera.find_cameras()` 정적 메서드 직접 호출 (lerobot upstream 패턴 그대로 활용).
3. **git 추적 정책 (BACKLOG 04 #3)**: placeholder 추적 유지, 실 cache 갱신 후 사용자 판단. .gitignore 코멘트 블록만 추가.
4. **Category B .gitignore 변경**: 실 패턴 없는 코멘트만 → 최소 변경.

## 다음 단계

- code-tester: `bash -n` 문법 검증 + 인자 처리 + exit code + JSON schema
- prod-test-runner (TODO-G2): 실 Orin 에서 first-time / resume 두 모드 검증
