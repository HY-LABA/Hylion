# TODO-D3 — DataCollector 환경 셋업 검증 시나리오

> 작성: 2026-05-01 14:30 | task-executor | cycle: 1

## 사전 점검 결과

### D2 산출물 인벤토리 (code-tester READY_TO_SHIP 확인 완료)

| 파일 | 종류 | 상태 |
|---|---|---|
| `datacollector/pyproject.toml` | 신규 | 존재 확인 — record+hardware+feetech extras, entrypoint 9개 |
| `datacollector/scripts/setup_env.sh` | 신규 | 존재 확인 — .hylion_collector venv, 표준 PyPI torch |
| `datacollector/scripts/run_teleoperate.sh` | 이관 | 존재 확인 — archive 에서 최종 이관 |
| `datacollector/README.md` | 신규 | 존재 확인 |
| `datacollector/tests/README.md` | 신규 | 존재 확인 |
| `datacollector/config/README.md` | 신규 | 존재 확인 |
| `datacollector/data/README.md` | 신규 | 존재 확인 |
| `docs/storage/lerobot_upstream_check/05_datacollector_lerobot_diff.md` | 신규 (coupled file) | 존재 확인 |
| `smolVLA/.gitignore` | 신규 | 존재 확인 — datacollector/.hylion_collector/ + datacollector/data/ 포함 |
| `datacollector/lerobot/` | symlink (devPC) / rsync 배포 (DC 머신) | setup_env.sh §0-b 로 처리 |

### DataCollector 머신 미존재

본 검증 시점에 DataCollector 머신 (별도 PC 신규 구매) 이 존재하지 않는다.
모든 prod 검증은 사용자가 하드웨어 구매·셋업 후 수행해야 한다.

## 산출물

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `docs/work_flow/context/todos/D3/01_implementation.md` | N | 본 파일 — 시나리오 정의 보고서 |
| `docs/work_flow/context/verification_queue.md` | M | [TODO-D3] 섹션 추가 |
| `docs/work_flow/context/history/04_infra_setup/20260501_1430_task_d3_setup_verify_scenarios.md` | N | 히스토리 기록 |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 ✓, 코드 변경 없음 (type=test) ✓
- 본 todo 는 시나리오 정의 전용 — Category B 영역 변경 없음 ✓
- orin-deploy-procedure 스킬: DataCollector SSH 검증 패턴을 orin 패턴 미러로 적용 ✓

## 핵심 결정

### prod-test-runner 자율 가능 영역

`deploy_datacollector.sh --dry-run` 은 prod-test-runner 자율 범위. 단, `Host datacollector` alias 미등록 상태에서는 friendly error 가 발생하는 정상 동작을 확인하는 것이 목적. `datacollector` alias 등록 자체는 사용자 책임.

### 단계 6~13 모두 사용자 실물

- 단계 6 (setup_env.sh) — 첫 실행 5~15분 소요 가능 (PyTorch 다운로드). CLAUDE.md § prod-test-runner 자율성 "긴 실행 (>5분) ⚠️ 동의" 해당 → 사용자 실물로 위임.
- 단계 8 (which entrypoints) — DataCollector 머신 SSH 접속 필요 → 사용자 실물.
- 단계 10~13 (SO-ARM + 카메라) — 하드웨어 임시 연결 필요 → 사용자 실물. `lerobot-find-port` 가 대화형 stdin 이므로 사용자 콘솔 필수.

### entrypoint 등록 해제 검증 설계

- `which lerobot-eval lerobot-train` → exit 1 + 빈 출력 기대. SSH 비대화형으로 자동 검증 가능한 유일한 항목이지만 DataCollector 머신 미존재로 사용자 실물 범위에 포함.

## 변경 내용 요약

TODO-D3 는 type=test 이므로 코드 변경이 없다. 본 task-executor 의 책임은 D2 산출물 인벤토리 점검, prod 검증 시나리오 설계, verification_queue.md 에 [TODO-D3] 섹션 추가이다.

시나리오는 A~F 6단계로 구성된다: 머신 사전 준비 (사용자) → 코드 배포 (devPC) → venv 셋업 (DataCollector SSH) → lerobot import 검증 → SO-ARM·카메라 임시 연결 검증 → 결과 기록. prod-test-runner 가 자율적으로 수행 가능한 항목은 단계 4 (deploy_datacollector.sh --dry-run) 뿐이다. 나머지 14개 단계는 DataCollector 머신 + 하드웨어 실물이 필요하여 모두 사용자 실물 범위다.

## 잔여 리스크

- DataCollector 머신 구매·셋업 일정 — 사용자 책임. 구매 전까지 TODO-D3 는 실 검증 불가.
- SO-ARM + 카메라 임시 연결 가용성 — 사용자 책임. G3·G4 와 동일 하드웨어 사용 가능.
- `lerobot-find-port` 대화형 stdin — SSH 비대화형 스크립팅 불가. D3 검증 시 사용자 콘솔 직접 필요. (TODO-G1 의 비대화형 wrapping 은 Orin 측 구현으로, D3 는 해당 wrapping 미사용.)
- `datacollector/lerobot/` symlink 방식 — devPC 개발 환경에서만 적용. DataCollector 머신에서는 rsync 배포 후 실 디렉토리 존재 필요. setup_env.sh §0-b 경고로 안내.
- numpy `>=2.0.0,<2.3.0` + torch 호환성 — DataCollector 실 환경에서 첫 설치 시 검증 필요.

## 검증 필요 (다음 단계)

- code-tester: 시나리오 일관성·자율 가능 영역 분류·D2 DOD 항목 반영 여부 확인
- prod-test-runner: 단계 4 자율 실행 + 단계 6~13 verification_queue 추가 확인
- 사용자: DataCollector 머신 구매·셋업 후 verification_queue [TODO-D3] 항목 순서대로 실물 검증
