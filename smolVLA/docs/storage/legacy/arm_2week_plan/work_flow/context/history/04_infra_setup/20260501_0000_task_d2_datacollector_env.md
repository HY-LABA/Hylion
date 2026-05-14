# TODO-D2 — DataCollector venv·lerobot 셋업 history

> 날짜: 2026-05-01 | 에이전트: task-executor | cycle: 1

## 요약

DataCollector 전용 환경 셋업 자산을 `smolVLA/datacollector/` 에 구성.
TODO-D1 산출물 (`docs/storage/09_datacollector_setup.md`) 의 §2·§3 결정을 그대로 구현.

## 신규 파일 목록

| 파일 | 분류 |
|---|---|
| `datacollector/pyproject.toml` | 신규 |
| `datacollector/scripts/setup_env.sh` | 신규 |
| `datacollector/scripts/run_teleoperate.sh` | 이관 (archive → 본 위치) |
| `datacollector/README.md` | 신규 |
| `datacollector/tests/README.md` | 신규 |
| `datacollector/config/README.md` | 신규 |
| `datacollector/data/README.md` | 신규 |
| `docs/storage/lerobot_upstream_check/05_datacollector_lerobot_diff.md` | 신규 (coupled file) |
| `.gitignore` | 신규 (Category B 최소) |

## 갱신 파일 목록

| 파일 | 내용 |
|---|---|
| `docs/work_flow/specs/BACKLOG.md` | 04 #2 "완료" 갱신 |
| `docs/storage/others/run_teleoperate.sh.archive` | 이관 완료 표시 |

## 핵심 결정 메모

- `record` extras: upstream `dataset` 에 대응, torchcodec x86_64 Linux 조건부 포함
- numpy: Python 3.12 환경이므로 `>=2.0.0,<2.3.0` (orin 의 `<2.0.0` 제약 불필요)
- `datacollector/lerobot/`: 옵션 B — setup_env.sh §0-b 에서 symlink 자동 생성 (devPC 개발환경) 또는 rsync 배포로 실 디렉토리 전송 (DataCollector 머신)

## 다음 단계

code-tester → TODO-D2 검증
prod-test-runner → TODO-D3 (DataCollector 머신 실 환경 검증)
