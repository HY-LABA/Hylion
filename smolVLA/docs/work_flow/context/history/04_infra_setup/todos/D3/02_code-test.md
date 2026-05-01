# TODO-D3 — Code Test

> 작성: 2026-05-01 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈 0건. Recommended 1건 (2건 이하 — READY 기준 충족). DOD 3항목 모두 충족. CLAUDE.md Hard Constraints 위반 없음.

---

## 단위 테스트 결과

```
type=test — 신규 .py 파일 없음. pytest 해당 없음.
task-executor 산출물 3개 모두 문서 파일 (.md) — 코드 변경 없음.
```

---

## Lint·Type 결과

```
신규 .py 파일 없음 — ruff / mypy 해당 없음.
markdown 문법 시각 검증: 01_implementation.md, verification_queue.md [TODO-D3] 섹션,
history/20260501_1430_task_d3_setup_verify_scenarios.md — 구조 이상 없음.
```

---

## DOD 정합성

| DOD 항목 (spec § D3) | 충족 | 메모 |
|---|---|---|
| 1. setup_env.sh DataCollector 머신 동작 시나리오 정의 | ✅ | verification_queue C 블록 (단계 6) — setup_env.sh 첫 실행 절차 명시 |
| 2. lerobot import OK 검증 시나리오 정의 | ✅ | verification_queue D 블록 (단계 7~9) — python import 확인 + entrypoint 9개 검증 명시 |
| 3. SO-ARM 1대 + 카메라 1대 임시 연결 + lerobot-find-port·find-cameras PASS 시나리오 정의 | ✅ | verification_queue E 블록 (단계 10~13) — /dev/ttyACM* 인식 + find-port 실행 + /dev/video* 인식 + find-cameras 실행 명시 |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `01_implementation.md` § "prod-test-runner 자율 가능 영역" + `verification_queue.md` [TODO-D3] `prod-test-runner 결과 요약` | "단계 4 prod-test-runner 자율 실행" 분류는 CLAUDE.md 정책 (`deploy_*.sh` Category B 외: 자율) 기준으로 정확. 단, T3 prod-test-runner가 동일 Bash 도구 sandbox 차단 (SKILL_GAP #1) 으로 `deploy_datacollector.sh --dry-run` 실 실행 불가였음이 이미 기록된 상황 (T3/03_prod-test.md L39). D3 01_implementation.md 에 "SKILL_GAP #1 로 인해 실제 실행 불가할 수 있음 — verification_queue 단계 4 항목 사용자 실물 확인으로 대체 가능" 보완 언급 권장. verification_queue `prod-test-runner 결과 요약` 의 "단계 4 자율 실행 후" 표현은 미래 지시로 읽힐 수 있어 "자율 실행 가능 분류 (SKILL_GAP #1 로 실행 미완료 시 verification_queue 확인)" 로 표현 다듬기 권장. 기능적 문제 없음. |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경. `.claude/` 미변경. 산출물 3개 모두 `docs/work_flow/context/` 하위 문서 파일 |
| B (자동 재시도 X 영역) | ✅ | type=test — 코드 변경 없음. Category B 영역 (`orin/lerobot/`, `datacollector/lerobot/`, `pyproject.toml`, `setup_env.sh`, `deploy_*.sh`, `.gitignore`) 미변경 |
| Coupled File Rules | ✅ | type=test, Category B 영역 변경 없음 — coupled file 규칙 해당 없음. `05_datacollector_lerobot_diff.md` 는 D2 에서 이미 갱신 완료 |
| C (사용자 동의 필수) | ✅ | 새 디렉터리·외부 의존성·시스템 환경 변경 없음 |
| 옛 룰 (`docs/storage/` bash 명령 예시) | ✅ | `docs/storage/` 하위 신규 bash 명령 예시 추가 없음 |

---

## 자율성 분류 정확성 검증

task-executor 가 정의한 자율성 분류를 CLAUDE.md § prod-test-runner 자율성 정책과 교차 검증.

| 단계 | task-executor 분류 | 정책 근거 | 평가 |
|---|---|---|---|
| 4 (deploy_datacollector.sh --dry-run) | prod-test-runner 자율 | `deploy_*.sh` (Category B 외 변경): 자율. dry-run + SSH alias 미등록 시 friendly error 확인 목적 | ✅ 정책 기준 정확. 단 SKILL_GAP #1 실행 환경 제약 존재 (Recommended #1) |
| 5 (실 배포) | 사용자 실물 | DataCollector 머신 미존재 → SSH 자체 실패. 머신 셋업 후에는 자율 가능이나 현재 미존재 상황 정확 반영 | ✅ 정확 |
| 6 (setup_env.sh — 첫 실행 5~15분) | 사용자 실물 | "긴 실행 (>5분) ⚠️ 동의" + "가상환경 재생성·패키지 업그레이드 ⚠️ 동의" 이중 해당 | ✅ 정확 |
| 7~9 (lerobot import + entrypoint) | 사용자 실물 | DataCollector SSH 불가 (머신 미존재). 머신 셋업 후 SSH read-only 자율 가능하나 현재 상황 정확 반영 | ✅ 정확 |
| 10~13 (SO-ARM + 카메라 + find-port·cameras) | 사용자 실물 | 하드웨어 연결 필요 + `lerobot-find-port` 대화형 stdin (BACKLOG 01 #2) | ✅ 정확 |

X3 cycle 1 의 추측 위반 (save_dummy_checkpoint 미존재 스크립트 추측 작성) 답습 없음 확인: D3 task-executor 는 실제 존재하는 D2 산출물 인벤토리 (`datacollector/pyproject.toml`, `setup_env.sh`, `run_teleoperate.sh`, README 4개, `05_datacollector_lerobot_diff.md`, `.gitignore`) 를 D2/02_code-test.md READY_TO_SHIP 기준으로 점검한 후 시나리오 정의. 없는 자산 추측 없음.

---

## D2 산출물 매핑 완전성

| D2 산출물 | D3 검증 매핑 | 단계 |
|---|---|---|
| `datacollector/pyproject.toml` | ✅ | 단계 6 (`pip install -e .[record,hardware,feetech]`) + 단계 8~9 (entrypoint 9개 등록 확인) |
| `datacollector/scripts/setup_env.sh` | ✅ | 단계 6 (DataCollector 콘솔 setup_env.sh 실행) |
| `datacollector/lerobot/` (symlink/rsync) | ✅ | 단계 7 (lerobot import) + 단계 8 (entrypoint 9개) — DataCollector 머신 rsync 배포 후 확인 |
| `datacollector/scripts/run_teleoperate.sh` | 단계 13 후속 (본 D3 직접 검증 외) | D3 DOD 명시 범위 밖. 별도 TODO 또는 사용자 직접 활용 |
| `05_datacollector_lerobot_diff.md` (coupled file) | D2 검증 완료 — D3 추가 검증 불필요 | D2 code-tester READY_TO_SHIP 에서 확인됨 |
| `smolVLA/.gitignore` | D2 검증 완료 | 동일 |

`run_teleoperate.sh` 가 D3 시나리오에 명시적 단계로 포함되지 않은 것은 spec § D3 DOD에 해당 항목이 없으므로 문제 없음.

---

## BACKLOG 01 #2 연계 확인

| 항목 | 확인 |
|---|---|
| BACKLOG 01 #2 (`lerobot-find-port` 대화형 stdin SSH 비대화형 불가) 인식 | ✅ — `01_implementation.md` § "잔여 리스크" 3번째 항목에 명시 |
| 단계 11 사용자 콘솔 직접 실행 권고 | ✅ — verification_queue E 블록 "(대화형 stdin — 콘솔 직접 필요)" 명시 |
| TODO-G1 비대화형 wrapping이 D3와 별개임을 인식 | ✅ — "D3 는 해당 wrapping 미사용" 명시 |

---

## SKILL_GAP / ANOMALY

| TYPE | 내용 |
|---|---|
| — | 특이사항 없음. SKILL_GAP #1 (Bash 차단) 은 D2 에서 이미 기록됨. D3 type=test 산출물 검증에 새로운 SKILL_GAP 없음 |

---

## 배포 권장

**READY_TO_SHIP — prod-test-runner (D3) 진입 권장.**

prod-test-runner 는 단계 4 (`deploy_datacollector.sh --dry-run`) 자율 실행 시도 + SKILL_GAP #1 재현 시 verification_queue 위임. 단계 5~13 은 모두 verification_queue [TODO-D3] 에 이미 추가됨. Phase 3 사용자 검증으로 진행.
