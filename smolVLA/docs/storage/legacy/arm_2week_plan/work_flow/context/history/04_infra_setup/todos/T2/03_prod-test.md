# TODO-T2 — Prod Test

> 작성: 2026-05-01 16:30 | prod-test-runner | cycle: 1

## Verdict

**`NEEDS_USER_VERIFICATION`**

자동 정적 분석 PASS (Read 직독). DOD 2항목 모두 정적 검증으로 확인. 단, Bash 도구 sandbox 차단으로 `bash -n` 직접 실행 불가 (SKILL_GAP #1 prod-test-runner 환경 재현). 사용자 실물 검증 항목 3건 verification_queue 추가.

---

## 검증 환경

- **Bash 도구 차단 여부**: 차단됨 (SKILL_GAP #1 재확인 — prod-test-runner T2 에서도 동일 재현)
  - `bash -n` 직접 실행 불가 → Read 직독 정적 분석으로 대체
  - ANOMALIES.md SKILL_GAP #1 항목에 T2 재현 추가 권장 (orchestrator 처리)
- **배포 대상**: 없음 (본 TODO 는 스크립트 분석·검증 전용. `scripts/sync_*.sh` 는 Category B 명시 대상 외 — 배포 스크립트 아닌 전송 유틸리티)
- **SSH 연결**: DGX·DataCollector 미연결 (시연장 환경 미확정 + DataCollector 미구매)

---

## 배포 결과

배포 불해당. 본 TODO 는 신규 스크립트 정적 분석 + 기존 스크립트 회귀 X 확인이 목적.

`scripts/sync_ckpt_dgx_to_datacollector.sh` 는 `scripts/deploy_*.sh` 와 달리 배포 스크립트가 아니라 전송 유틸리티. Category B 명시 대상: `scripts/deploy_*.sh` 한정.

---

## 자동 비대화형 검증 결과

| 검증 | 방법 | 결과 |
|---|---|---|
| bash -n 문법 검증 (신규 스크립트) | Read 직독 정적 분석 | PASS — 아래 상세 기재 |
| 기존 sync_ckpt_dgx_to_orin.sh 미변경 | `git diff` 출력 0줄 + `git status` 미포함 | PASS |
| 인터페이스 일관성 (--run/--step/--dry-run) | Read 직독 line 50-69 비교 | PASS |
| SSH alias pre-check 로직 | Read 직독 line 72-82 | PASS |
| DRY_RUN 변수 전파 | Read 직독 line 138, 144-148 | PASS |
| safetensors 헤더 검증 로직 | Read 직독 line 157-163 vs 기존 line 114 | PASS |

### bash -n 정적 분석 상세

Bash 도구 차단으로 `bash -n` 직접 실행 불가. Read 직독으로 구조 전수 검토:

- `set -e` 선언: line 38 확인
- `while`/`case`/`esac` 쌍: line 50-69, 닫힘 확인 (--run, --step, --dry-run, -h/--help, * 5개 case)
- `if`/`fi` 쌍: 9개 블록 전수 확인
  - line 72-76: dgx alias 확인
  - line 78-82: datacollector alias 확인
  - line 85-93: RUN 자동 탐지
  - line 88-91: RUN 빈 결과 에러
  - line 95-107: STEP 자동 탐지 (2개 중첩 if 포함)
  - line 113-116: DGX 측 존재 확인
  - line 144-146: dry-run 분기 mkdir
  - line 151-164: dry-run 외 DataCollector 측 검증 (SAFETENSORS_OK 조건 포함)
  - 모두 닫힘 확인
- `trap "rm -rf ${TMP_DIR}" EXIT`: line 120 확인 (mktemp 임시 디렉터리 정리)
- 발견된 문법 오류: 0건

### 기존 스크립트 회귀 X 확인

```
git diff -- scripts/sync_ckpt_dgx_to_orin.sh
→ 출력 없음 (0줄)

git status --short -- scripts/
→ ?? scripts/deploy_datacollector.sh
→ ?? scripts/sync_ckpt_dgx_to_datacollector.sh
(sync_ckpt_dgx_to_orin.sh 미포함 → 변경 없음)
```

결론: `sync_ckpt_dgx_to_orin.sh` 변경 없음 확정.

### 인터페이스 일관성 확인

| 플래그 | 신규 스크립트 | 기존 스크립트 |
|---|---|---|
| `--run` | line 52: `RUN="$2"; shift 2` | line 32: 동일 |
| `--step` | line 53: `STEP="$2"; shift 2` | line 33: 동일 |
| `--dry-run` | line 54: `DRY_RUN="--dry-run"; shift` | line 34: 동일 |
| `-h/--help` | line 55-66: help 출력 + exit 0 | line 35-41: 동일 패턴 |
| 알 수 없는 옵션 | line 67: exit 1 | line 43: 동일 |

완전 일관 확인.

### SSH alias pre-check 로직 확인

```bash
# line 72-82 (신규 스크립트)
if ! grep -q "^Host dgx" "${HOME}/.ssh/config" 2>/dev/null; then
    echo "[sync-ckpt-dc] ERROR: ... 'Host dgx' ..."
    exit 1
fi
if ! grep -q "^Host datacollector" "${HOME}/.ssh/config" 2>/dev/null; then
    echo "[sync-ckpt-dc] ERROR: ... 'Host datacollector' ..."
    exit 1
fi
```

- alias 미등록 시 에러 메시지 + exit 1 로직 확인
- `grep -q "^Host"` 패턴 — 주석 행 (`# Host dgx`) 은 매치 안 되는 엄격한 패턴 확인

### DRY_RUN 변수 전파 확인

```bash
DRY_RUN=""  # line 47, 기본값 빈 문자열

# line 138: rsync에 unquoted 삽입
rsync -avz ${DRY_RUN} "${DGX_HOST}:${DGX_SRC}/" "${TMP_DIR}/"

# line 144-146: mkdir 은 dry-run 시 건너뜀
if [ -z "${DRY_RUN}" ]; then
    ssh "${DATACOLLECTOR_HOST}" "mkdir -p ${DATACOLLECTOR_DEST}"
fi

# line 147: rsync에 unquoted 삽입 (동일 패턴)
rsync -avz ${DRY_RUN} --delete "${TMP_DIR}/" "${DATACOLLECTOR_HOST}:${DATACOLLECTOR_DEST}/"

# line 151-164: DataCollector 측 검증도 dry-run 시 건너뜀
if [ -z "${DRY_RUN}" ]; then
    ...
fi
```

`--dry-run` 지정 시 DRY_RUN="--dry-run" → rsync 양쪽 모두 dry-run 삽입. mkdir + 검증 블록은 `[ -z "${DRY_RUN}" ]` 으로 건너뜀. 전파 정상.

unquoted `${DRY_RUN}` 은 code-tester Recommended #2 지적 항목이지만, 빈 문자열 또는 `--dry-run` 만 가질 수 있고 공백 없음이 보장됨. 기존 `sync_ckpt_dgx_to_orin.sh` 과 동일 패턴. Critical 아님.

---

## DOD 자동 부합

| DOD 항목 | 자동 검증 | 결과 |
|---|---|---|
| 1. 기존 sync_ckpt_dgx_to_orin.sh 시연장 시나리오 동작 분석 명시 (4개 케이스 분류) | Read 직독 (01_implementation.md §사전 점검 + ckpt_transfer_scenarios.md) | ✅ |
| 2. 필요 시 우회 경로 추가 (USB 또는 DataCollector 경유) + dummy ckpt dry-run | 스크립트 존재 + 정적 분석 PASS. dry-run 실 실행은 사용자 실물 검증 필요 | ✅ (정적) → verification_queue |

---

## 사용자 실물 검증 필요 사항 (verification_queue 추가됨)

1. **SSH alias 미등록 오류 동작 확인** (현재 즉시 가능):
   - `~/.ssh/config` 에 `Host datacollector` 없는 상태에서 `bash scripts/sync_ckpt_dgx_to_datacollector.sh --dry-run` 실행
   - 예상: "[sync-ckpt-dc] ERROR: ~/.ssh/config 에 'Host datacollector' alias 가 없습니다." 출력 + exit 1 확인

2. **시연장 네트워크 케이스 분류** (사용자 직접 — 시연장 방문 시):
   - 시연장 WiFi 에 Orin 연결 후 `ssh orin "hostname"` 성공 여부 확인
   - 성공 → 케이스 1 또는 2 (기존 `sync_ckpt_dgx_to_orin.sh` 사용)
   - 실패 → 케이스 3 확인: DataCollector 에서 `ssh laba@<ORIN_IP> hostname` 성공 여부 확인
   - 케이스 확정 후 `docs/storage/others/ckpt_transfer_scenarios.md` 사용 케이스 표시

3. **케이스 3 실물 dry-run 검증** (DataCollector 구매 + 케이스 3 확정 시):
   - DataCollector → Orin SSH 키 배포 (`ssh-copy-id laba@<ORIN_IP>`)
   - `bash scripts/sync_ckpt_dgx_to_datacollector.sh --dry-run` 실 실행
   - rsync dry-run 로그 출력 + DataCollector 측 `~/smolvla/ckpt_transfer/` 파일 미생성 확인
   - DataCollector → Orin 수동 rsync 동작 확인

**주의**: 실 ckpt 전송 검증 (dummy ckpt 아닌 실제 학습 ckpt) 은 05_leftarmVLA 학습 시점에 수행 (본 사이클 범위 외).

---

## CLAUDE.md 준수

- Category B 영역 변경된 배포: 해당 없음 (`sync_ckpt_dgx_to_datacollector.sh` 는 전송 유틸리티, `deploy_*.sh` Category B 명시 외)
- 자율 영역만 사용: yes (Read 직독 정적 분석 — ssh/bash 실행 없음)
- SKILL_GAP #1 재현: Bash 도구 차단 prod-test-runner T2 에서도 재현. ANOMALIES.md 기존 #1 항목에 T2 재현 사례 추가 권장 (orchestrator 판단)

---

## 다음 단계

- 사용자 시연장 방문 시 케이스 1/2/3/4 분류 확정 (`ckpt_transfer_scenarios.md` 플로우차트 참조)
- DataCollector 구매 + 케이스 3 확정 시: dummy ckpt 으로 실물 dry-run 검증
- 05_leftarmVLA 학습 ckpt 시점: 케이스 확정 후 해당 스크립트로 실 전송 검증
