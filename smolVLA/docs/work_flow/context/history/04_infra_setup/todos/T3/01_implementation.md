# TODO-T3 — devPC sync hub 갱신

> 작성: 2026-05-01 | task-executor | cycle: 1

## 사전 점검 결과

### 09_datacollector_setup.md §5 추출 (SSH alias, rsync 패턴)

- SSH alias: `Host datacollector` (`~/.ssh/config`)
- 원격 경로: `/home/laba/smolvla/` (orin: `/home/laba/smolvla/orin/`, dgx: `/home/laba/smolvla/` 와 형제)
- rsync 동기화 대상 (§5-2 명시):
  - `datacollector/` → `datacollector:/home/laba/smolvla/datacollector/`
  - `docs/reference/lerobot/` → `datacollector:/home/laba/smolvla/docs/reference/lerobot/` (editable install 대상)
  - `docs/storage/09_datacollector_setup.md` → 참고용
- exclude: `.hylion_collector`, `data/`, `__pycache__`, `*.pyc`

### deploy_orin.sh / deploy_dgx.sh 패턴 추출

| 항목 | deploy_orin.sh | deploy_dgx.sh | deploy_datacollector.sh |
|---|---|---|---|
| set -e | X | O | O (dgx 패턴 채택) |
| HOST 변수 | ORIN_HOST | DGX_HOST | DATACOLLECTOR_HOST |
| 원격 DEST | /home/laba/smolvla/orin | /home/laba/smolvla | /home/laba/smolvla |
| rsync 소스 | orin/ | dgx/ + docs/reference/lerobot/ | datacollector/ + docs/reference/lerobot/ + 09_datacollector_setup.md |
| pre-check 디렉터리 생성 | X (버그) | O (ssh mkdir -p) | O (ssh mkdir -p) |
| dry-run 지원 | X | X | O (신규 — --dry-run 플래그) |
| exclude .venv | .hylion_arm | .arm_finetune | .hylion_collector |
| exclude data | X (orin 에 data/ 없음) | outputs/ | data/ (수집 dataset 제외) |

### BACKLOG 02 #9 두 버그 답습 방지 매핑

| 버그 | 원인 | deploy_datacollector.sh 대응 |
|---|---|---|
| 버그 1: 대상 디렉터리 미생성 | rsync 원격 경로 없으면 실패 | `ssh datacollector "mkdir -p ..."` 를 rsync 전에 실행 (dry-run 시 생략) |
| 버그 2: rsync 실패 후 exit 0 | 이후 명령이 exit code 덮어씀 | `set -e` + `rsync ... || { ...; exit 1; }` 명시 적용 |

## 산출물

### scripts/deploy_datacollector.sh (신규)

**파일 경로**: `scripts/deploy_datacollector.sh`
**변경 종류**: N (신규)

**인자**:
- `--dry-run`: rsync `-n` 옵션으로 실 배포 없이 동작 확인. pre-check SSH alias 확인은 수행. 원격 mkdir 은 skip.

**동기화 대상 (순서대로)**:
1. `smolVLA/datacollector/` → `datacollector:/home/laba/smolvla/datacollector/`
2. `smolVLA/docs/reference/lerobot/` → `datacollector:/home/laba/smolvla/docs/reference/lerobot/`
3. `smolVLA/docs/storage/09_datacollector_setup.md` → `datacollector:/home/laba/smolvla/docs/storage/`

**각 rsync 의 exit code 처리**:
- `set -e` (스크립트 상단)
- 각 rsync 뒤 `|| { echo "ERROR: ... rsync 실패"; exit 1; }` 명시 추가 (이중 안전망)

## 핵심 결정

### exclude 패턴

| 패턴 | 대상 | 이유 |
|---|---|---|
| `.hylion_collector` | datacollector/ venv | 런타임 생성, orin 의 `.hylion_arm` 패턴 미러 |
| `data/` | 수집된 dataset | 수백 MB~GB 규모 — 데이터 전송은 TODO-T1 책임 |
| `__pycache__/` | Python 캐시 | 이식성 없음 |
| `*.pyc` | 컴파일된 bytecode | 이식성 없음 |
| `*.egg-info` | editable install 메타 | 원격에서 pip install -e 시 재생성 |
| `.git` | git 메타 | 원격에 불필요 |
| `.gitignore` | git 설정 | 원격에 불필요 |
| `tests/outputs` | lerobot 테스트 산출물 | dgx 패턴 미러 (docs/reference/lerobot/ 동기화 시 적용) |

### pre-check: SSH alias 확인

`grep -q "^Host datacollector" ~/.ssh/config` 로 alias 존재 여부 확인. 없으면 오류 메시지 + exit 1.
DataCollector 가 미배치 상태에서도 이 체크로 즉시 명확한 오류 메시지 확인 가능.

### pre-check: 대상 디렉터리 mkdir

```bash
ssh "${DATACOLLECTOR_HOST}" "mkdir -p \
    ${DATACOLLECTOR_DEST}/datacollector \
    ${DATACOLLECTOR_DEST}/docs/reference/lerobot \
    ${DATACOLLECTOR_DEST}/docs/storage"
```

dry-run 시에는 생략 (원격 머신 미존재 시 dry-run 도 SSH 실패 허용 — 정상).

### post-check: rsync exit code 명시

- `set -e` 로 스크립트 전체 보호
- 각 rsync 뒤 `|| { echo "ERROR: ..."; exit 1; }` 명시 — 에러 메시지 명확화

### dry-run flag 지원

`--dry-run` 플래그 → `RSYNC_DRY_RUN_FLAG="-n"` 으로 rsync 에 전달. SSH alias 체크는 수행 (설정 검증). 원격 mkdir 은 skip. 실 배포 없이 동기화 대상·크기 미리 확인 가능.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `scripts/deploy_datacollector.sh` | N | DataCollector 배포 스크립트 신규 — orin/dgx 형제 패턴, dry-run 지원, BACKLOG 02 #9 버그 2종 방지 |

## 적용 룰

- CLAUDE.md Hard Constraints Category B: `scripts/deploy_*.sh` 영역 — code-tester MAJOR 시 사용자 보고 게이트 발동. 자율 1 cycle 작성 완료.
- CLAUDE.md Hard Constraints Category A: `docs/reference/` 미변경 확인 (동기화 대상이지만 소스 파일 자체는 read-only 유지).
- Coupled File Rule: `deploy_datacollector.sh` 는 신규 스크립트 — `pyproject.toml` 변경 없음, `orin/lerobot/` 변경 없음. Coupled file 규칙 해당 없음.
- 레퍼런스 활용: `scripts/deploy_orin.sh` / `scripts/deploy_dgx.sh` 의 기존 패턴 직접 참조 — 새 발명 없음.

## 변경 내용 요약

`scripts/deploy_datacollector.sh` 를 신규 작성했다. 기존 `deploy_orin.sh` 와 `deploy_dgx.sh` 의 패턴을 그대로 따르되, BACKLOG 02 #9 에서 기록된 두 가지 버그(대상 디렉터리 미사전 생성, rsync 실패 후 exit 0 덮어씀)를 명시적으로 방지했다.

동기화 대상은 `datacollector/` (배포 메인), `docs/reference/lerobot/` (editable install 용 upstream), `docs/storage/09_datacollector_setup.md` (참고용) 세 가지다. 수집된 dataset (`data/`) 은 의도적으로 제외했으며, 데이터 전송은 TODO-T1 의 `sync_dataset_collector_to_dgx.sh` 가 담당한다. `--dry-run` 플래그를 추가하여 DataCollector 머신이 아직 미물리적 존재인 현 시점에도 스크립트 구조를 검증할 수 있게 했다.

## 잔여 리스크 / SKILL_GAP

- DataCollector 머신 미물리적 존재 시 `--dry-run` 도 SSH pre-check 에서 alias 는 통과하나 실제 rsync 에서 연결 실패 → 이는 정상 (DataCollector 미배치 상태에서 예상된 동작).
- `datacollector/` 디렉터리가 현재 smolVLA 리포지터리에 아직 없음 — TODO-D2 에서 신규 생성 예정. 본 스크립트는 해당 디렉터리가 존재하는 것을 전제하고 동작 (rsync 실행 시 소스 없으면 rsync 자체 오류).
- SKILL_GAP 없음 — `deploy_orin.sh` / `deploy_dgx.sh` 레퍼런스에 동일 패턴 존재.

## 검증 필요 (다음 단계)

- **code-tester**:
  - bash 문법 (`bash -n scripts/deploy_datacollector.sh`)
  - BACKLOG 02 #9 버그 1 방지 확인: `ssh ... mkdir -p` 선행 여부
  - BACKLOG 02 #9 버그 2 방지 확인: `set -e` + `|| exit 1` 존재 여부
  - exclude 패턴 누락 없음 확인: `data/`, `.hylion_collector`, `__pycache__`, `*.pyc`
  - dry-run flag 처리 로직 확인
  - DOD 항목 ("deploy_orin.sh / deploy_dgx.sh 와 형제 패턴") 충족 확인
- **prod-test-runner**:
  - `bash scripts/deploy_datacollector.sh --dry-run` dry-run 실행 (DataCollector 미존재 시 SSH 연결 실패는 정상 — dry-run flag 동작 자체 + 스크립트 진입·SSH alias 체크 동작 확인)
