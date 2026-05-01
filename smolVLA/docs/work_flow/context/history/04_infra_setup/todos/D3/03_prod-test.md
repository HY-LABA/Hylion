# TODO-D3 — Prod Test

> 작성: 2026-05-01 | prod-test-runner | cycle: 1

## 검증 환경

- 실행 환경: devPC (babogaeguri@babogaeguri-950QED)
- Bash 도구 차단 여부: **부분 차단** — `echo` 등 단순 명령은 통과, `bash <스크립트>` 형태 실행은 sandbox 차단 확인. SKILL_GAP #1 D3 재현 (T3 prod-test 와 동일 패턴).
- DataCollector 머신: 미존재 (사용자 별도 PC 구매 후 셋업 예정 — TODO-D1 § 사용자 결정 사항)

## 배포 대상

- devPC (D2 산출물 신규 작성 완료 상태)
- DataCollector 머신 미존재 → 실 배포 불가 (사용자 실물 범위)

## 배포 결과

- 명령: `bash scripts/deploy_datacollector.sh` (실 배포) — DataCollector 머신 미존재로 미실행
- `scripts/deploy_datacollector.sh` — task-executor (TODO-T3) 가 devPC 로컬에 이미 작성 완료, code-tester READY_TO_SHIP 확인됨
- D2 산출물 (`datacollector/` 전체 디렉터리) — task-executor (TODO-D2) 작성 완료, code-tester READY_TO_SHIP 확인됨

## 자동 비대화형 검증 결과

| 검증 | 명령 | 결과 | 비고 |
|---|---|---|---|
| `deploy_datacollector.sh --dry-run` 실 실행 | `bash scripts/deploy_datacollector.sh --dry-run` | **차단** | Bash 도구 sandbox 차단 — SKILL_GAP #1 D3 재현 |
| `bash -n` 정적 분석 | `bash -n scripts/deploy_datacollector.sh` | **차단** | 동일 차단 |
| Read 직독 정적 분석 | Read 도구 직독 전문 | PASS | 아래 상세 분석 |
| D2 산출물 인벤토리 확인 | code-tester 02_code-test.md 교차 참조 | PASS | 9개 파일 모두 존재 확인됨 (code-tester READY_TO_SHIP) |

### deploy_datacollector.sh Read 직독 정적 분석 결과

| 항목 | line | 결과 |
|---|---|---|
| shebang `#!/bin/bash` | 1 | PASS |
| `set -e` 최상단 | 2 | PASS |
| `--dry-run` 플래그 파싱 | 28-33 | PASS — `DRY_RUN=true`, `RSYNC_DRY_RUN_FLAG="-n"`, 안내 메시지 출력 |
| SSH alias pre-check — `grep -q "^Host datacollector" ~/.ssh/config 2>/dev/null` | 38 | PASS — `2>/dev/null` 로 `.ssh/config` 미존재 시에도 오류 없이 처리 |
| alias 미등록 시 friendly error 메시지 | 39-40 | PASS — "ERROR: ~/.ssh/config 에 'Host datacollector' alias 가 없습니다. docs/storage/09_datacollector_setup.md §5-1 을 참조..." |
| alias 미등록 시 exit 1 | 41 | PASS — `exit 1` 명시 |
| `--dry-run` + alias 미등록 실행 순서 분석 | 28-42 | PASS — `--dry-run` 안내 메시지 출력(28-33) 후 pre-check(38-42). `--dry-run` 여부와 무관하게 alias 미등록 시 exit 1 발생 (예상 동작 정확히 일치) |
| dry-run 시 원격 mkdir skip | 48 | PASS — `if [[ "${DRY_RUN}" == false ]]` 조건부 |
| rsync 3건 `|| { exit 1; }` | 70, 87, 97 | PASS — BACKLOG 02 #9 버그2 답습 없음 |
| dry-run 완료 메시지 | 104-106 | PASS — "--dry-run 완료. 실제 배포는 --dry-run 플래그 없이 재실행하세요." |
| Category D 금지 명령 (rm -rf, sudo 등) | 전체 | PASS — 미포함 |
| rsync 동기화 대상 3건 | 60-97 | PASS — `datacollector/` + `docs/reference/lerobot/` + `docs/storage/09_datacollector_setup.md` |
| `data/` 동기화 제외 | 64 | PASS — `--exclude 'data/'` 명시 (TODO-T1 책임 분리) |

## DOD 자동 부합

| DOD 항목 (spec § D3) | 자동 검증 가능 | 결과 |
|---|---|---|
| 1. setup_env.sh DataCollector 머신 동작 시나리오 정의 | yes (Read 직독 — 01_implementation.md + verification_queue C 블록) | ✅ 단계 6 (setup_env.sh 첫 실행 절차) 명시 확인 |
| 2. lerobot import OK 검증 시나리오 정의 | yes (Read 직독 — verification_queue D 블록) | ✅ 단계 7~9 (import + entrypoint 9개) 명시 확인 |
| 3. SO-ARM 1대 + 카메라 1대 임시 연결 + find-port·find-cameras PASS 시나리오 정의 | yes (Read 직독 — verification_queue E 블록) | ✅ 단계 10~13 명시 확인 |
| 실 setup_env.sh 동작 확인 | no (DataCollector 미존재) | → verification_queue C |
| 실 lerobot import 동작 확인 | no (DataCollector 미존재) | → verification_queue D |
| 실 SO-ARM + 카메라 연결 확인 | no (하드웨어 + DataCollector 미존재) | → verification_queue E |

## SKILL_GAP #1 재확인

- `bash scripts/deploy_datacollector.sh --dry-run` — Bash 도구 sandbox 차단 확인
- T3 prod-test-runner 와 동일 패턴 재현 (더 광범위: `bash <스크립트>` 형태 전체 차단)
- Read 직독 정적 분석으로 대체. 구문·로직·분기 이상 없음 확인.
- ANOMALIES.md SKILL_GAP #1 에 D3 prod-test-runner 재현 사실 기록 (본 파일 작성 후 verification_queue 갱신 시 반영).

## 사용자 실물 검증 필요 사항 (verification_queue [TODO-D3] A~F)

task-executor 가 정의한 A~F 블록 그대로 유지. 자율 단계 4 정적 분석 결과를 항목 상태에 반영:

- **단계 4 (deploy --dry-run)**: 실 실행 차단 (SKILL_GAP #1) → Read 직독으로 friendly error + exit 1 분기 정확성 확인 완료 (정적 PASS). 실 동작 확인은 사용자 실물 범위.
- **단계 5~13 (A-E 나머지 전체)**: DataCollector 머신 미존재 + 하드웨어 필요 → 사용자 실물 범위 그대로.

## Verdict

**`NEEDS_USER_VERIFICATION`**

### 근거

1. Read 직독 정적 분석에서 `deploy_datacollector.sh` 구문·로직·분기 이상 없음 확인 (DOD 시나리오 정의 3항목 모두 충족).
2. Bash 도구 sandbox 차단으로 `--dry-run` 실 실행 불가 (SKILL_GAP #1 D3 재현).
3. DataCollector 머신 미존재 + 하드웨어 미확보 → A~F 실물 검증 불가.
4. 사용자 실물 검증 항목 ≥ 1 (A~F 전 단계) → 보수적 판단: `NEEDS_USER_VERIFICATION`.

`AUTOMATED_PASS` 는 아님: 사용자 실물 검증 항목이 다수 존재하며 DataCollector 머신 자체가 미존재.

## CLAUDE.md 준수

| 항목 | 결과 |
|---|---|
| Category B 영역 (`scripts/deploy_*.sh`) 내용 수정 | 없음 — prod-test-runner 는 검증만 수행 |
| Category A 영역 미변경 | ✅ Read 직독 + 문서 작성만 |
| prod-test-runner 자율성 — 자율 실행 영역 | deploy_datacollector.sh --dry-run 은 자율 분류 정확. Bash 차단으로 실행 불가 → Read 직독 대체 |
| prod-test-runner 자율성 — 동의 필요 영역 | 해당 없음 (실 배포·setup_env.sh 실행 없음) |
| DataCollector 실 SSH 연결 시도 | 없음 — DataCollector 미존재 상황 |

## 다음 단계

- `verification_queue.md [TODO-D3]` 상태 갱신 — 자율 단계 4 정적 PASS 반영
- Phase 3 진입 시 사용자가 DataCollector 머신 구매·셋업 후 A~F 블록 순서대로 처리
- 단계 4 실 동작 확인은 현재 즉시 가능 (사용자가 devPC 에서 직접 실행)
- ANOMALIES.md SKILL_GAP #1 — D3 prod-test-runner 재현 사실 추가 (orchestrator 처리)
