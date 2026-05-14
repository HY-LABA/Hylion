# TODO-T2 — Code Test

> 작성: 2026-05-01 15:45 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 0건. Recommended 2건. 기존 스크립트 회귀 없음. DOD 완전 충족.

---

## 단위 테스트 결과

```
bash -n scripts/sync_ckpt_dgx_to_datacollector.sh
→ sandbox 차단으로 직접 실행 불가 (SKILL_GAP #1 누적)
→ 대신 수동 정적 분석 수행 — 아래 상세 기재
```

bash -n 실행 불가로 인한 SKILL_GAP 처리:
- 구조 전수 검토로 대체 수행
- set -e 선언 확인 (line 38)
- while/case/esac 쌍 일치 확인 (line 50~69)
- if/fi 쌍 전수 확인 (총 9개 조건 블록, 모두 닫힘)
- trap 선언 확인 (line 120, EXIT 핸들러)
- 발견된 문법 오류: 0건
- 결론: 문법 구조 정상 — Critical 아님. 단, 직접 실행 결과가 아니므로 prod-test-runner 가 `bash -n` 을 자율 검증 항목으로 재확인 필요.

---

## Lint·Type 결과

대상: bash 스크립트 2개 신규 (`scripts/sync_ckpt_dgx_to_datacollector.sh`, `docs/storage/others/ckpt_transfer_scenarios.md` 는 문서)

수동 검토 항목:
- 변수 quoting: 대부분 `"${VAR}"` 형태. `${DRY_RUN}` 은 rsync 선택적 플래그 변수로 unquoted 사용 — 기존 `sync_ckpt_dgx_to_orin.sh` 와 동일 패턴. 의도적 처리로 판단.
- `set -e` 선언 있음 (line 38)
- `trap "rm -rf ${TMP_DIR}" EXIT` — TMP_DIR 은 mktemp 결과 변수이므로 정상 임시 파일 정리
- 비-Critical lint 경고 후보 2건 (Recommended 섹션 참조)

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. 기존 `sync_ckpt_dgx_to_orin.sh` 시연장 시나리오 동작 분석 명시 (4개 케이스 분류) | ✅ | `01_implementation.md` §사전 점검 결과 + `ckpt_transfer_scenarios.md` 에 4개 케이스 상세 기술 |
| 2. 필요 시 우회 경로 추가 (USB 또는 DataCollector 경유) | ✅ | 케이스 3: `sync_ckpt_dgx_to_datacollector.sh` 신규. 케이스 4: `ckpt_transfer_scenarios.md §케이스 4` USB 절차 명시 |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `docs/storage/others/ckpt_transfer_scenarios.md` §케이스 2 "증상 (확인 방법)" | "devPC 에서 Orin SSH 단절 →" 이라고 시작하는 첫 줄이 케이스 3 증상처럼 읽힘. 케이스 2 의 핵심은 "다른 서브넷이지만 SSH 가 가능"한 시나리오인데, 확인 방법 설명이 모호함. "devPC 에서 Orin SSH 단절될 수 있으나, 먼저 시도 후 성공 시 케이스 2" 식으로 재서술 권장. |
| 2 | `scripts/sync_ckpt_dgx_to_datacollector.sh` line 154 | `ssh "${DATACOLLECTOR_HOST}" "ls -la ${DATACOLLECTOR_DEST}/"` — `DATACOLLECTOR_DEST` 가 변수 확장된 채로 원격 명령에 삽입. 경로에 공백 없음이 보장되는 환경이라 실용적 문제 없으나, 방어적으로 `"${DATACOLLECTOR_DEST}/"` 를 원격 명령 내에서도 quote 처리 권장 (다른 ssh 호출들과 일관성). |

Recommended 2건으로 READY_TO_SHIP 기준 충족.

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경. `.claude/agents/*.md`, `.claude/skills/**/*.md`, `.claude/settings.json` 미변경 확인 (git status 에 해당 경로 없음) |
| B (자동 재시도 X) | ✅ | `orin/lerobot/`, `dgx/lerobot/` 미변경. `pyproject.toml` 미변경. `orin/scripts/setup_env.sh` 미변경. `scripts/deploy_*.sh` 미변경. `.gitignore` 미변경. `sync_*.sh` 는 Category B 명시 대상 아님 (CLAUDE.md 는 `deploy_*.sh` 만 명시). 보수적 처리 근거 task-executor 가 `01_implementation.md` 에 명시함. |
| Coupled File Rules | ✅ | `orin/pyproject.toml` 미변경 → `02_orin_pyproject_diff.md` 갱신 불필요. `orin/lerobot/` 코드 미변경 → `03_orin_lerobot_diff.md` 갱신 불필요. |
| D (절대 금지 명령) | ✅ | 신규 스크립트 내 `rm -rf ${TMP_DIR}` 은 mktemp 임시 디렉터리 정리용 (trap EXIT). `sudo`, `git push --force`, `chmod 777`, `curl | bash` 미포함. |
| 옛 룰 | ✅ | `docs/storage/` 하위에 bash 명령 예시를 문서 내 추가했으나, 이는 사용자 결정 가이드 문서의 본질적 내용 (케이스별 실행 방법 안내). 단순 예시 추가가 아니라 필수 절차 기술이므로 룰 위반 아님으로 판단. |

---

## 검증 항목별 상세

### 기존 스크립트 회귀 X

- `git status --short` 결과에 `scripts/sync_ckpt_dgx_to_orin.sh` 미포함 → 변경 없음 확인
- 인터페이스 비교: 기존 `--run`, `--step`, `--dry-run` 플래그 동일하게 신규 스크립트에 구현됨

### 신규 스크립트 인터페이스 일관성

- `--run`, `--step`, `--dry-run`, `-h/--help` — 기존 스크립트와 완전 동일 패턴
- SSH alias pre-check: `dgx` + `datacollector` 양쪽. 미등록 시 "[sync-ckpt-dc] ERROR: ~/.ssh/config 에 'Host datacollector' alias 가 없습니다." + exit 1 출력
- safetensors 헤더 8 byte 검증 패턴 — 기존 `sync_ckpt_dgx_to_orin.sh` line 114 과 동일 로직 (line 157~163)

### 케이스 3 우회 경로 합리성

- `09_datacollector_setup.md §1-2` 네트워크 표: DataCollector 와 Orin 모두 "시연장 WiFi (DHCP)" → 동일 서브넷 근거 확인
- `09_datacollector_setup.md §5` DataCollector SSH alias `datacollector` 확정 → 스크립트 내 `DATACOLLECTOR_HOST="datacollector"` 일치
- DataCollector 측 도착 경로 `~/smolvla/ckpt_transfer/` — `~/smolvla/orin/checkpoints/` 와 구분됨 (DataCollector 는 임시 경유, Orin 역할 X)
- 완료 후 DataCollector → Orin 2단계 안내 (단계 A: rsync / 단계 B: USB) 출력 — 합리적

### 케이스 4 USB 절차

- `ckpt_transfer_scenarios.md §케이스 4`: DGX 에서 USB 마운트 → cp + sync → USB 이동 → Orin 에서 마운트 → cp 순서 모두 명시
- 무결성 확인 (`ls -la` 로 model.safetensors 존재 확인) 명시됨

### 4개 케이스 분류 가이드

- 사용자 결정 플로우차트 (`ckpt_transfer_scenarios.md §사용자 결정 플로우차트`): devPC → Orin SSH 가능 여부 → DataCollector → Orin SSH 가능 여부 순서로 케이스 1/2/3/4 분류 가능
- 시연장 배치 전 확인 체크리스트 (`§확인 체크리스트`) 명시
- 잔여 리스크 (시연장 Orin 인터넷 가용성 미확인) `§잔여 리스크` 표에 명시

### prod-test-runner 인계 시나리오

- 자율 가능 시나리오 4건 (`01_implementation.md §자율 가능`) — devPC 에서 bash 문법 검증, alias pre-check 로직 검증, --dry-run 플래그 검증, 기존 스크립트 hash 비교
- 사용자 실물 필요 4건 (`01_implementation.md §사용자 실물 필요`) — verification_queue 항목으로 분류됨
- prod-test-runner 가 verification_queue 에 시연장 네트워크 케이스 분류 항목 추가 요청 명시됨

---

## ANOMALIES 누적

### SKILL_GAP #1 (기존 누적 항목 확인 필요)

- 유형: `SKILL_GAP`
- 내용: `bash -n <스크립트>` sandbox 차단으로 직접 실행 불가. 수동 정적 분석으로 대체 수행.
- 영향: Critical 판단에는 영향 없으나, bash 문법 검증 자동화 불가 → prod-test-runner 자율 검증 항목에서 `bash -n` 재확인 필요.
- 권장 조치: ANOMALIES.md 에 SKILL_GAP 항목으로 누적 (bash -n 차단 — prod-test-runner 에서 대신 수행).

---

## 배포 권장

**READY_TO_SHIP** — prod-test-runner 진입 권장.

자율 검증 항목:
1. `bash -n scripts/sync_ckpt_dgx_to_datacollector.sh` exit=0 확인
2. SSH alias 미설정 시 에러 메시지 + exit=1 확인
3. `--dry-run` 플래그 전파 확인 (DataCollector 측 파일 미생성)
4. 기존 `sync_ckpt_dgx_to_orin.sh` hash 변경 없음 확인

verification_queue 추가 항목:
1. 시연장 네트워크 케이스 분류 (사용자 직접)
2. 케이스 3 확정 시 실물 dry-run 검증
3. 케이스 1·2 확정 시 기존 스크립트 dry-run 검증
