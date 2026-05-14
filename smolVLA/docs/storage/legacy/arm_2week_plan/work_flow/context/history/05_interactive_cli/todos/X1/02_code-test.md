# TODO-X1 — Code Test

> 작성: 2026-05-01 15:00 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈: 0건. Recommended 개선 사항: 2건.

---

## 단위 테스트 결과

```
해당 없음. 본 todo 는 docs/storage/ 신규 문서 작성 (코드 없음).
pytest 실행 대상 없음.
```

---

## Lint·Type 결과

```
해당 없음. .py 파일 변경 없음.
ruff / mypy 실행 대상 없음.

단, 14_dgx_cli_flow.md §1-3 에 삽입된 Python 코드 스니펫 (env_check.py 예시)
은 문서 참고용 pseudocode 로 분류. X2 구현 시 task-executor 가 ruff/mypy 검증.
```

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. dgx 측 flow 3~ 단계 구체 정의 | ✅ | §2 에 A(4단계)/B(2단계)/C(3단계) 3개 후보 + 비교표 제공. flow 3~6 각 책임 명확히 분리됨 |
| 2. preflight 후보 정리 | ✅ | §1 에 preflight_check.sh subprocess 래퍼 패턴 확정. env_check.py 구현 예시 포함 |
| 3. 데이터셋 선택 후보 정리 | ✅ | §3 에 HF Hub / 로컬 rsync / T1 dummy push 3가지 소스 + smoke 하드코드 데이터셋 인용 |
| 4. 학습 trigger 후보 정리 | ✅ | §4 에 smoke_test.sh 직접 인용 + 동의 게이트 포함/미포함 양쪽 후보 제시 |
| 5. 체크포인트 관리 후보 정리 | ✅ | §5 에 저장 경로 + sync_ckpt_dgx_to_datacollector 케이스 분류 인용 + devPC 실행 스크립트라는 제약 명시 |
| 6. 사용자 합의 명세 (awaits_user-C) 작성 | ✅ | §6 에 발송 명세 (A/B/C + 추가 결정 3가지) 작성. 01_implementation.md 에도 동일 내용 포함 |
| 7. X2 영향 연결 | ✅ | §6 말미 + 01_implementation.md §다음 단계 에서 X2 training.py 구조와의 연결 명시 |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `14_dgx_cli_flow.md` §4-1 | `smoke_test.sh` "line 44~45" 표기 — 실제 다운로드 경고 메시지는 line 44 단 한 줄 (`echo "  최초 실행 시 모델·데이터셋 다운로드로 5~15분 소요됩니다."`). line 45 는 구분선(`========...`). 내용은 정확하나 라인 범위를 "line 44" 로 정정하면 더 엄밀함. |
| 2 | `14_dgx_cli_flow.md` §4-1 | `smoke_test.sh` "line 24~32: preflight → 1-step 학습" 주석 — 실제 line 24~26 은 venv activate 블록이고 preflight 호출은 line 30~32. 범위 표기가 venv activate 를 포함하여 설명이 느슨. "line 24~32: venv 보장 + preflight 호출" 로 표기하면 정확도 향상. 인용 코드 자체는 올바름. |

---

## 레퍼런스 인용 정확성 검증

| 레퍼런스 | 인용 라인 | 실제 파일 내용 | 일치 여부 |
|---|---|---|---|
| `dgx/scripts/preflight_check.sh` line 1~36 | 헤더 + 5체크 항목 (사용법·통과조건·시나리오별 메모리) | line 1~36: 헤더 주석 (사용법 line 5~16) + case 블록 (line 23~36) | ✅ 일치 |
| `dgx/scripts/smoke_test.sh` line 24~32 | preflight 호출 | line 24~26: venv activate, line 29~32: preflight bash 호출 | ✅ 내용 일치 (범위에 venv activate 포함 — Recommended #2) |
| `dgx/scripts/smoke_test.sh` line 44~45 | 소요 시간 경고 메시지 | line 44: 경고 echo, line 45: 구분선 | ✅ 내용 일치 (범위 1라인 느슨 — Recommended #1) |
| `dgx/scripts/smoke_test.sh` line 68~81 | lerobot-train 인자 전체 | line 68~81: lerobot-train \ ... --wandb.enable=false | ✅ 완전 일치 |
| `dgx/scripts/save_dummy_checkpoint.sh` line 25 | OUTPUT_DIR 정의 | line 25: `OUTPUT_DIR="${DGX_DIR}/outputs/train/${RUN_NAME}"` | ✅ 완전 일치 |
| `dgx/scripts/save_dummy_checkpoint.sh` line 62~63 | --save_freq=1 + --save_checkpoint=true | line 62: `--save_freq=1 \`, line 63: `--save_checkpoint=true \` | ✅ 완전 일치 |
| `scripts/sync_ckpt_dgx_to_datacollector.sh` line 6~24 | 케이스 분류 | line 6~24: 사용 예시 + 케이스 1~4 분류 주석 | ✅ 완전 일치 |
| `scripts/sync_ckpt_dgx_to_datacollector.sh` line 28~36 | 동작 5단계 | line 28~36: 동작 1~5단계 주석 | ✅ 완전 일치 |
| `dgx/scripts/setup_train_env.sh` line 51 | `source "${VENV_DIR}/bin/activate"` | line 51: `source "${VENV_DIR}/bin/activate"` | ✅ 완전 일치 |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/`, `.claude/agents/*.md`, `.claude/skills/**/*.md`, `.claude/settings.json` 미변경. git status 확인: untracked 파일은 `docs/storage/14_dgx_cli_flow.md` + `docs/work_flow/context/todos/X1/` 만 해당 |
| B (자동 재시도 X 영역) | ✅ | `orin/lerobot/`, `dgx/lerobot/`, `pyproject.toml`, `setup_env.sh`, `deploy_*.sh`, `.gitignore` 미변경 |
| Coupled File Rules | ✅ | Category B 영역 변경 없으므로 coupled file 갱신 불필요 |
| 옛 룰 (`docs/storage/` bash 예시) | ✅ | `docs/storage/14_dgx_cli_flow.md` 에 삽입된 bash 스니펫은 레퍼런스 직접 인용 (스크립트 인용)으로, "bash 명령 예시 추가" 가 아닌 기존 스크립트 내용 발췌. 사용자 명시 요청(spec DOD) 에 의한 산출물이므로 룰 적용 범위 외 |

---

## flow 3~ 후보 정합성 검증

| 검증 항목 | 결과 |
|---|---|
| 후보 A/B/C 3가지 모두 도출됐는가 | ✅ §2-2 ~ §2-4 각각 후보 설명 + §2-5 비교표 |
| 각 후보의 호출 스크립트 조합 명확한가 | ✅ A: preflight→dataset→smoke_test/lerobot-train→sync_ckpt / B: preflight+학습 통합 / C: preflight→dataset→학습+ckpt 통합 |
| 권고 후보(C) 근거 제시됐는가 | ✅ §2-4 특징 설명에서 "흐름이 자연스러움" + smoke 동의 게이트 포함 명시 |

## smoke_test 사용자 동의 게이트 검증

| 검증 항목 | 결과 |
|---|---|
| smoke_test.sh 의 5~15분 경고 인용됐는가 | ✅ §3-2 및 §4-2 에서 "5~15분 소요 + svla_so100_pickplace >100MB 다운로드 가능" 명시 |
| CLAUDE.md 자율성 정책 근거 명시됐는가 | ✅ §3-2, §4-2 에서 "CLAUDE.md §prod-test-runner 자율성 '큰 다운로드 (>100MB) 사용자 동의 필요'" 직접 인용 |
| 포함/미포함 양쪽 후보 제시됐는가 | ✅ §4-2 에서 "포함 (권고)" / "미포함" 양쪽 제시 + 결정 필요 명시 |

## awaits_user-C 발송 명세 검증

| 결정 사항 | 명세 포함 여부 |
|---|---|
| flow 구조 옵션 (A/B/C) | ✅ §6 + 01_implementation.md §awaits_user-C 발송 내용 |
| smoke_test 동의 게이트 포함 여부 | ✅ 추가 결정 사항 1번으로 명시 |
| 데이터셋 선택 UI 포함 여부 | ✅ 추가 결정 사항 2번으로 명시 |
| ckpt 전송 안내 방식 | ✅ 추가 결정 사항 3번으로 명시 |
| X2 영향 연결 | ✅ "영향: X2 의 training.py 구조가 결정됩니다" 명시 |

---

## 배포 권장

READY_TO_SHIP — study 타입이므로 prod-test 진입 X.

awaits_user-C 발송 명세가 완비됐으므로 orchestrator 가 사용자에게 §6 내용 전달 후 X2 dispatch 대기로 진입 권장.
