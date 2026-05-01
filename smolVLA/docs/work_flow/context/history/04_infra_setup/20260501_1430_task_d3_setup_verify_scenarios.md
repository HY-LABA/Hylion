# TODO-D3 — DataCollector 환경 셋업 검증 시나리오 정의

> 날짜: 2026-05-01 14:30 | 에이전트: task-executor | cycle: 1

## 요약

TODO-D3 (type=test) 의 검증 시나리오를 정의하고 verification_queue.md 에 [TODO-D3] 섹션을 추가.
코드 변경 없음. DataCollector 머신 미존재로 실 prod 검증은 사용자 실물 위임.

## 산출물 목록

| 파일 | 종류 |
|---|---|
| `docs/work_flow/context/todos/D3/01_implementation.md` | 신규 |
| `docs/work_flow/context/verification_queue.md` | 갱신 ([TODO-D3] 섹션 추가) |
| `docs/work_flow/context/history/04_infra_setup/20260501_1430_task_d3_setup_verify_scenarios.md` | 신규 (본 파일) |

## 시나리오 구조

A. DataCollector 머신 사전 준비 (사용자 책임)
B. 코드 배포 — deploy_datacollector.sh (devPC)
C. venv 셋업 — setup_env.sh (DataCollector 콘솔)
D. lerobot import 검증 — python -c + which entrypoints (SSH)
E. SO-ARM + 카메라 임시 연결 검증 (사용자 직접)
F. 결과 기록

## prod-test-runner 자율 / 사용자 분류

| 단계 | 분류 | 사유 |
|---|---|---|
| 4 (deploy --dry-run) | prod-test-runner 자율 | 안전, alias 미등록 시 friendly error 확인 목적 |
| 5~13 | 사용자 실물 | DataCollector 머신 미존재 / 하드웨어 연결 필요 / 긴 실행 (>5분) |

## 전제 조건 체인

```
DataCollector 머신 구매·OS 설치
    → ~/.ssh/config 에 datacollector alias 등록
        → deploy_datacollector.sh 실 배포 (단계 5)
            → setup_env.sh 실행 (단계 6)
                → lerobot import 검증 (단계 7~9)
                    → SO-ARM + 카메라 연결 검증 (단계 10~13)
```
