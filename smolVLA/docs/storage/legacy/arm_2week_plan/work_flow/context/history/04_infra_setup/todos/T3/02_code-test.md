# TODO-T3 — Code Test

> 작성: 2026-05-01 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈: 0건 / Recommended 개선 사항: 2건 (임계 2건 이하 → READY_TO_SHIP)

---

## 단위 테스트 결과

```
bash -n scripts/deploy_datacollector.sh: 실행 차단 (sandbox deny)
→ SKILL_GAP #1 (bash -n 차단) — 하기 수동 정적 분석으로 대체 검증.
   코드 전체를 Read 도구로 직독, 구문 오류 없음 확인.
```

수동 정적 분석 결과:
- shebang `#!/bin/bash` 정상
- `set -e` 최상단 위치, 스크립트 전체 early-exit 보호 동작
- 모든 변수 substitution 의 quoting 점검 (아래 세부 항목 참조)
- 제어 흐름 (`if/then/fi`, `[[ ]]`, `|| { ...; exit 1; }`) 문법적 오류 없음
- 미사용 변수 없음
- 도달 불가 코드 없음

판정: **SYNTAX PASS** (수동 리뷰 기반, bash -n 미실행 SKILL_GAP 기록)

---

## Lint·Type 결과

```
shellcheck: 실행 차단 (sandbox deny) — 수동 리뷰로 대체
ruff / mypy: 해당 없음 (bash 스크립트)
```

수동 shellcheck 상당 항목 점검:

| 항목 | 결과 | 비고 |
|---|---|---|
| SC2086 (unquoted variable) | 주의 1건 | `${RSYNC_DRY_RUN_FLAG}` unquoted (라인 60, 79, 94). 빈 문자열일 때 bash word splitting 으로 인자 0개 → 실행 상 정상 동작. SC2086 경고 해당하나 Critical 아님 |
| SC2034 (unused variable) | 0건 | 전 변수 사용됨 |
| SC2164 (cd 실패) | 해당 없음 | `cd ... && pwd` 패턴 정상 |
| `${1:-}` default empty | 정상 | unset parameter 접근 안전 처리 |
| `/dev/null` redirect | 정상 | `grep ... 2>/dev/null` |

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. devPC `scripts/` 에 deploy_datacollector.sh 추가 | ✅ | `scripts/deploy_datacollector.sh` 신규 작성 확인 |
| 2. deploy_orin.sh / deploy_dgx.sh 형제 패턴 | ✅ | 변수명 (DATACOLLECTOR_HOST/DEST), rsync 옵션 (-avz --delete), exclude 패턴 모두 형제 일관성 유지. `set -e` 는 deploy_dgx.sh 채택 |
| 3. dry-run 지원 | ✅ | `--dry-run` → `RSYNC_DRY_RUN_FLAG="-n"` 전달, 모든 rsync 3건에 적용 확인 |

---

## Critical 이슈 — 0건 (MAJOR_REVISIONS 없음)

없음.

---

## BACKLOG 02 #9 버그 답습 검증 (CRITICAL 판정 기준)

### 버그 1 — 대상 디렉터리 미사전 생성

- 대응 코드 위치: `scripts/deploy_datacollector.sh` 라인 48-54
- 구현: `DRY_RUN == false` 조건 하에 `ssh "${DATACOLLECTOR_HOST}" "mkdir -p ${DATACOLLECTOR_DEST}/datacollector ${DATACOLLECTOR_DEST}/docs/reference/lerobot ${DATACOLLECTOR_DEST}/docs/storage"` 선행 실행
- dry-run 시 skip — 원격 미존재 환경에서 dry-run 가능하도록 의도적 설계 (01_implementation.md 명시)
- 판정: **버그 1 답습 없음 (PASS)**

### 버그 2 — rsync 실패 후 exit 0 덮어씀

- 대응 코드:
  - 라인 2: `set -e` (스크립트 최상단, 전체 early-exit 보호)
  - 라인 70: `|| { echo "[deploy-datacollector] ERROR: datacollector/ rsync 실패"; exit 1; }`
  - 라인 87: `|| { echo "[deploy-datacollector] ERROR: docs/reference/lerobot/ rsync 실패"; exit 1; }`
  - 라인 97: `|| { echo "[deploy-datacollector] ERROR: 09_datacollector_setup.md rsync 실패"; exit 1; }`
- 3개 rsync 호출 모두에 `|| { exit 1; }` 명시 + `set -e` 이중 보호
- 판정: **버그 2 답습 없음 (PASS)**

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| R1 | 라인 60, 79, 94 — `${RSYNC_DRY_RUN_FLAG}` unquoted | `"${RSYNC_DRY_RUN_FLAG}"` 로 quoting 권장. 현재는 빈 문자열 시 bash word splitting 으로 인자 0개 → 정상 동작하나, shellcheck SC2086 경고 대상. 기능 영향 없음 |
| R2 | 라인 50-53 — `ssh "${DATACOLLECTOR_HOST}" "mkdir -p ${DATACOLLECTOR_DEST}/..."` 에서 원격 명령 내 `${DATACOLLECTOR_DEST}` unquoted | 경로에 공백 없으므로 실질 문제 없음. 엄밀히는 큰따옴표 중첩 이슈로 `'mkdir -p ...'` 또는 변수 export 방식 권장. 기능 영향 없음 |

Recommended 2건 이하 → READY_TO_SHIP 기준 충족.

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경 확인 (`git diff HEAD -- docs/reference/` 출력 없음). `.claude/` 미변경 확인 |
| B (자동 재시도 X 영역) | ✅ 의도적 변경 | `scripts/deploy_datacollector.sh` 신규 — Category B (`scripts/deploy_*.sh`) 패턴. 본 TODO 의 의도적 작업. MAJOR 발급 없음이므로 게이트 불발동 |
| Coupled File Rules | ✅ 해당 없음 | `orin/pyproject.toml` 미변경, `orin/lerobot/` 미변경 → Coupled File 규칙 트리거 없음 |
| D (절대 금지 명령) | ✅ | `rm -rf`, `sudo`, `git push --force`, `chmod 777`, `curl \| bash` 모두 미포함 (`grep` 0건 확인) |
| 형제 스크립트 변경 X | ✅ | `deploy_orin.sh`, `deploy_dgx.sh` untracked 상태 변화 없음 (`git status` 확인) |
| 옛 룰 (`docs/storage/` bash 예시) | ✅ | `docs/storage/` 하위 bash 명령 예시 추가 없음 |

---

## ANOMALIES 누적 항목

| 타입 | 내용 |
|---|---|
| SKILL_GAP #1 (기존 동일 항목) | `bash -n` 및 `shellcheck` sandbox 차단 — bash 스크립트 문법 자동 검증 불가. 수동 리뷰로 대체. 하네스 보강 필요 (허용 명령 목록에 `bash -n <file>`, `shellcheck <file>` 추가 권고) |

---

## 검증 요약

| 검증 항목 | 결과 |
|---|---|
| bash -n 문법 체크 | SKILL_GAP — 수동 리뷰 PASS |
| shellcheck | SKILL_GAP — 수동 리뷰 (R1·R2 Recommended 2건) |
| DOD 1 (파일 신규) | PASS |
| DOD 2 (형제 패턴) | PASS |
| DOD 3 (dry-run) | PASS |
| BACKLOG 02 #9 버그 1 (디렉터리 선행 생성) | PASS |
| BACKLOG 02 #9 버그 2 (rsync exit code 보호) | PASS |
| SSH alias 사전 확인 | PASS (grep -q "^Host datacollector") |
| Category A 미변경 | PASS |
| Category D 금지 명령 X | PASS |
| 형제 deploy 미변경 | PASS |

---

## 배포 권장

**yes — prod-test-runner 진입 권장**

READY_TO_SHIP. Critical 0건, Recommended 2건 이하.

prod-test-runner 진입 시 주의:
- DataCollector 머신 미물리적 존재 → SSH 연결 실패 예상 (정상)
- `--dry-run` 플래그로 스크립트 진입·SSH alias 체크·rsync dry-run 출력까지만 검증 가능
- alias `datacollector` 미등록 시 exit 1 오류 메시지 확인 → 정상 동작 판정

## 다음 단계

- **READY → prod-test-runner 진입**
  - `bash scripts/deploy_datacollector.sh --dry-run` dry-run 실행
  - SSH alias 미등록 시 오류 메시지 + exit 1 확인
  - alias 등록 시 rsync dry-run 출력 확인 (DataCollector 미존재면 SSH 연결 실패 — 정상)
