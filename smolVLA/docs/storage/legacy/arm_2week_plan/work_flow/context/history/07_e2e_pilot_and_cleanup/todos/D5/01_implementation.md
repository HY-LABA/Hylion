# TODO-D5 — Implementation

> 작성: 2026-05-03 | task-executor | cycle: 1

## 목표

`dgx/scripts/setup_train_env.sh` 의 lerobot editable install extras 에 `hardware,feetech` 추가 — 06_dgx_absorbs_datacollector 결정 후행 누락 영구 fix.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `dgx/scripts/setup_train_env.sh` | M | §3 editable install extras `[smolvla,training]` → `[smolvla,training,hardware,feetech]` + §3-c 주석 갱신 |
| `docs/storage/lerobot_upstream_check/04_dgx_lerobot_diff.md` | M | 2026-05-03 변경 이력 항목 추가 |
| `docs/work_flow/specs/BACKLOG.md` | M | 07 섹션에 항목 #3 (§3-c 중복 정리 후보) 추가 |

## 적용 룰

- CLAUDE.md Hard Constraints Category A: `docs/reference/` 수정 금지 — 읽기만 수행
- CLAUDE.md Hard Constraints Category B: `setup_train_env.sh` 변경 — 사용자 동의 (C 옵션) 받음
- Coupled File Rule: `04_dgx_lerobot_diff.md` 동시 갱신 (DGX 환경 설정 변경 이력)
- 레퍼런스 활용: `docs/reference/lerobot/pyproject.toml` 직접 Read — extras 키 이름 확인
  - 인용: `hardware = ["lerobot[pynput-dep]", "lerobot[pyserial-dep]", "lerobot[deepdiff-dep]"]` (line 110-114)
  - 인용: `feetech = ["feetech-servo-sdk>=1.0.0,<2.0.0", "lerobot[pyserial-dep]", "lerobot[deepdiff-dep]"]` (line 145)
- lerobot-upstream-check 스킬: 옵션 B 원칙 — `dgx/pyproject.toml` 신규 생성 X, `dgx/lerobot/` 변경 X

## Step 1 — 현 setup_train_env.sh 상태 분석

`§3` (line 63-66): `pip install -e "${LEROBOT_SRC}[smolvla,training]"` — smolvla + training 만 있음.

`§3-c` (line 68-96): 06 사이클에서 추가된 별도 pip install 블록:
- torchcodec (cu130 인덱스 별도)
- datasets, pandas, pyarrow, av, jsonlines (dataset extras 에 해당)
- pynput, pyserial, deepdiff, feetech-servo-sdk (hardware + feetech extras 에 해당)

즉, hardware/feetech 관련 패키지가 `§3-c` 에 개별 pip install 로 이미 설치되었으나, editable install extras 에는 포함되지 않은 상태였음. 이로 인해 `lerobot-find-port` 같은 entrypoint 가 runtime 에 `pyserial` import 를 시도할 때 환경에 따라 ImportError 발생 가능.

## Step 2 — extras 갱신 결과

lerobot upstream `pyproject.toml` extras 키 확인 결과:
- `hardware` 키 — 정확히 `hardware` (line 110)
- `feetech` 키 — 정확히 `feetech` (line 145)

변경:
```
# Before
pip install -e "${LEROBOT_SRC}[smolvla,training]" --quiet

# After
pip install -e "${LEROBOT_SRC}[smolvla,training,hardware,feetech]" --quiet
```

갱신 주석에 명시한 내용:
- 06_dgx_absorbs_datacollector 결정 후행 (영구 fix) + 07 TODO-D5
- Option B 원칙 (dgx/pyproject.toml 신규 생성 X) 유지

## Step 3 — Coupled File Rule 검토

CLAUDE.md 의 Coupled File Rule 은 `orin/pyproject.toml` 변경 시 `02_orin_pyproject_diff.md` 갱신을 명시하고 있음. DGX 측에는 `pyproject.toml` 미존재 (Option B 유지). 그러나 `setup_train_env.sh` 는 DGX 환경 구성 스크립트로서 `04_dgx_lerobot_diff.md` 가 DGX 래퍼 변경 이력 문서이므로 이 문서에 기록함.

결론: `04_dgx_lerobot_diff.md` 에 변경 이력 항목 추가 완료.

DGX 전용 `setup_train_env.sh` diff 전용 문서 (예: `06_dgx_setup_env_diff.md`) 는 현재 미존재. 04 에 흡수하는 것이 기존 패턴과 일관됨.

## Step 4 — 검증

```
bash -n dgx/scripts/setup_train_env.sh  → PASS
shellcheck                               → not available (시스템 미설치)
```

정적 검토:
- extras 추가 라인 (`[smolvla,training,hardware,feetech]`) 확인 완료
- §3-c 의 기존 패키지 목록 미삭제 (중복 설치지만 pip no-op — 회귀 없음)
- §3-c 의 torchcodec 별도 인덱스 처리 유지 (lerobot[dataset] extras 의 torchcodec 은 linux/aarch64 에서 skip 조건이 있어 DGX x86_64 에서는 직접 설치 필요)
- 다른 섹션 (§0 사전 점검, §1 venv 생성, §2 PyTorch, §4 환경변수, §5 설치 검증) 회귀 없음 확인

## Step 5 — 즉석 install 결과 인지

메인 D4 진단 시점에서 DGX 에 `pip install pyserial` 즉석 설치 처리 완료 (또는 진행 중).

`setup_train_env.sh` 재실행 시:
- `lerobot[hardware,feetech]` 가 pyserial 을 의존성으로 포함 → pip 가 이미 설치된 버전 확인 후 조건 충족 시 no-op
- 버전 범위 (`pyserial>=3.5,<4.0`) 충족 시 충돌 없음
- 충돌 발생하더라도 pip 가 범위 내 최신 버전으로 자동 갱신

## 변경 내용 요약

`setup_train_env.sh` 의 `§3` editable install extras 를 `[smolvla,training]` 에서 `[smolvla,training,hardware,feetech]` 로 확장했다. 이는 06_dgx_absorbs_datacollector 사이클에서 DGX 가 데이터 수집 책임을 흡수하면서 필요해진 hardware/feetech extras 갱신이 누락된 것을 영구 수정한 것이다. 07 D4 precheck 에서 `lerobot-find-port` 실행 시 pyserial ImportError 가 발생한 원인이 이 누락이었다.

`§3-c` 는 06 사이클 추가 당시의 개별 pip install 방식을 유지하되 주석을 갱신하여 `§3` extras 통합 완료를 명시했다. `§3-c` 의 중복 패키지 라인 제거는 BACKLOG #3 으로 인계하여 차기 cleanup 사이클에서 처리한다.

## code-tester 인계 사항

- `bash -n dgx/scripts/setup_train_env.sh` 재실행 확인 권장
- extras 키 이름 (`hardware`, `feetech`) 이 lerobot upstream `pyproject.toml` line 110, 145 와 일치하는지 확인 — 직접 Read 권장
- `§3` extras 갱신 라인 (line 77): `[smolvla,training,hardware,feetech]` 정합 확인
- `§3-c` 주석 갱신 내용 — §3 extras 통합 사실 명시 여부 확인
- `04_dgx_lerobot_diff.md` 변경 이력 항목 추가 확인
- BACKLOG `07_e2e_pilot_and_cleanup` #3 항목 추가 확인
- `dgx/lerobot/` 변경 없음 (옵션 B 준수) 확인
- `dgx/pyproject.toml` 변경 없음 (06 X4 결정 유지) 확인
- `docs/reference/lerobot/` 변경 없음 (Category A 준수) 확인
