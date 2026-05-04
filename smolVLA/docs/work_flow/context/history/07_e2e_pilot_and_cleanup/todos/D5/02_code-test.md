# TODO-D5 — Code Test

> 작성: 2026-05-03 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈 0건. Recommended 이슈 0건.

---

## 단위 테스트 결과

```
bash -n dgx/scripts/setup_train_env.sh → PASS (직접 실행 확인)
pytest 적용 범위 없음 — shell script 변경 + 문서 변경만. 정적 검증으로 대체.
```

## Lint·Type 결과

```
ruff: 해당 없음 (Python 파일 미변경)
mypy: 해당 없음 (Python 파일 미변경)
shellcheck: 시스템 미설치 (task-executor 보고와 일치) — bash -n 으로 대체
bash -n: PASS
```

---

## DOD 정합성

D5 는 활성 spec (07_e2e_pilot_and_cleanup) 의 D 그룹 외 ANOMALIES 07-#3 후행 처리. task-executor 가 정의한 목표 기준으로 평가.

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. §3 extras `[smolvla,training,hardware,feetech]` 로 갱신 | ✅ | line 77: `pip install -e "${LEROBOT_SRC}[smolvla,training,hardware,feetech]" --quiet` 확인 |
| 2. extras 키 이름이 lerobot upstream pyproject.toml 과 일치 | ✅ | `hardware` = line 110, `feetech` = line 145 — 직접 Read 확인 |
| 3. §3-c 주석 갱신 — §3 extras 통합 완료 명시 | ✅ | line 81: "07 TODO-D5 이후: hardware·feetech extras 는 §3 의 editable install extras 로 통합 완료" 명시 |
| 4. §3-c 기존 패키지 미삭제 (pip no-op 보장) | ✅ | pynput·pyserial·deepdiff·feetech-servo-sdk 라인 유지 확인 |
| 5. `04_dgx_lerobot_diff.md` 변경 이력 항목 추가 | ✅ | 2026-05-03 항목 — before/after 표·이유·upstream 인용·Option B 선언 포함 |
| 6. BACKLOG 07 #3 항목 추가 | ✅ | `§3-c 정리 — D5 extras 통합 후 중복 라인 제거` 항목 확인 |
| 7. `dgx/lerobot/` 변경 X (Option B) | ✅ | `dgx/lerobot/` 디렉터리 미존재 — Option B 유지 |
| 8. `dgx/pyproject.toml` 변경 X (06 X4 결정) | ✅ | 파일 미존재 확인. git diff 미반영 |
| 9. `docs/reference/lerobot/` 변경 X (Category A) | ✅ | git status clean. docs/reference/ diff 없음 |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

없음.

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/`, `.claude/agents/*.md`, `.claude/skills/**/*.md`, `.claude/settings.json` 미변경. D5 변경 파일 3건 모두 Category A 외부 |
| B (자동 재시도 X) | ✅ | `dgx/scripts/setup_train_env.sh` 는 Category B 영역. 사용자 동의 (결정 C 옵션) 수령 후 진행. Coupled File Rule 준수 (04_dgx_lerobot_diff.md 동시 갱신). MAJOR 가 아니므로 자동 재시도 X 정책 무관 |
| Coupled File Rules | ✅ | `lerobot-upstream-check` SKILL 기준: `dgx/scripts/setup_train_env.sh` 변경 → `04_dgx_lerobot_diff.md` 동시 갱신 완료. `dgx/pyproject.toml` 미변경 (Option B 유지) 이므로 `02_orin_pyproject_diff.md` 적용 불요 |
| 옛 룰 | ✅ | `docs/storage/` 에 사용자 요청 없이 bash 명령 예시 추가 없음. 04_dgx_lerobot_diff.md 에 `bash -n` 결과 텍스트만 언급 (bash 명령 예시 추가가 아님) |

---

## 추가 검증 — lerobot upstream extras 정합

`docs/reference/lerobot/pyproject.toml` 직접 Read 결과:

```
# line 110-114
hardware = [
    "lerobot[pynput-dep]",
    "lerobot[pyserial-dep]",
    "lerobot[deepdiff-dep]",
]
# line 145
feetech = ["feetech-servo-sdk>=1.0.0,<2.0.0", "lerobot[pyserial-dep]", "lerobot[deepdiff-dep]"]
```

- `hardware` 와 `feetech` 는 별개 extras. `hardware` 는 `pynput+pyserial+deepdiff`, `feetech` 는 `feetech-servo-sdk+pyserial+deepdiff`.
- `pyserial-dep` 가 양쪽에 중복 포함되나 pip 가 중복 처리하므로 무해.
- `§3-c` 의 개별 `pyserial>=3.5,<4.0` install 과 `hardware/feetech` extras 의 `pyserial-dep = ["pyserial>=3.5,<4.0"]` 버전 범위 동일 → pip no-op 보장 정확.
- DGX 즉석 설치된 pyserial 3.5 는 `pyserial>=3.5,<4.0` 범위 내 → 충돌 없음.
- `training` extras 가 `dataset` 을 체인 → `datasets/pandas/pyarrow/jsonlines/av` 자동 포함. `§3-c` 의 해당 패키지 pip install 역시 no-op.
- task-executor 가 인용한 lerobot upstream line 번호 (110, 145) 정확히 일치.

---

## §3-c no-op 유효성 검증

§3-c 에 남아있는 패키지:

| 패키지 | §3 extras 커버 여부 |
|---|---|
| datasets, pandas, pyarrow, av, jsonlines | `training → dataset` 체인으로 커버 ✅ |
| pynput | `hardware → pynput-dep` 으로 커버 ✅ |
| pyserial | `hardware → pyserial-dep` + `feetech → pyserial-dep` 으로 커버 ✅ |
| deepdiff | `hardware → deepdiff-dep` + `feetech → deepdiff-dep` 으로 커버 ✅ |
| feetech-servo-sdk | `feetech` extras 로 커버 ✅ |
| torchcodec (cu130 인덱스) | lerobot extras 로 처리 불가 (sys_platform 조건 + cu130 인덱스) — §3-c 유지 필수 ✅ |

§3-c 제거하지 않고 BACKLOG #3 으로 인계한 결정 적정 — 안전 최우선 scope 최소화 원칙 부합.

---

## 배포 권장

READY_TO_SHIP — prod-test-runner 진입 권장.

prod-test 범위 (AUTO_LOCAL): `bash -n` 이미 PASS. 추가 정적 검증 불요.
DGX 실 실행 (`setup_train_env.sh` 재실행) 은 사용자 Phase 3 검증 대상 (SSH_AUTO 수준, 단 환경 재구성 의도 없으면 불요).
