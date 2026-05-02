# TODO-O1 — Code Test

> 작성: 2026-05-01 | code-tester | cycle: 1

## Verdict

**`MAJOR_REVISIONS`** — Critical 2건

---

## 단위 테스트 결과

```
해당 없음 — study 타입 todo. 코드 변경 없음, 테스트 대상 파일 없음.
```

---

## Lint·Type 결과

```
해당 없음 — docs/storage/13_orin_cli_flow.md 신규 문서만 (Python 파일 없음).
```

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. orin 측 flow 3~ 단계 (추론 책임) 구체 정의 | ✅ | §2 후보 A·B·C 3개 도출 + §6 전체 흐름 요약 |
| 2. ckpt 선택·hil_inference 실행·시연 데모 후보 정리 | ✅ | §3 소스 4가지, §4 호출 구조, §5 시연 데모 비교표 |
| 3. 사용자 합의 명세 (awaits_user-B) 작성 | ✅ (형식) / ⚠️ (내용 오류) | 3가지 결정 사항 명세 작성됨. 단 Category B 분류 오류 포함 (Critical 2 참조) |

---

## Critical 이슈

### 1. `orin/inference/hil_inference.py` 를 Category B (자동 재시도 X 영역)로 잘못 분류

- 위치: `docs/storage/13_orin_cli_flow.md:135~136`, `docs/work_flow/context/todos/O1/01_implementation.md:45`, `01_implementation.md:119`, `01_implementation.md:139~140`
- 사유:
  CLAUDE.md Category B는 `orin/lerobot/`, `dgx/lerobot/`, `pyproject.toml`, `orin/scripts/setup_env.sh`, `scripts/deploy_*.sh`, `.gitignore` 만 해당한다.
  `orin/inference/hil_inference.py` 는 `orin/lerobot/` 하위가 아니며 Category B 조건 어느 항목에도 해당하지 않는다.
  이 잘못된 분류로 인해 awaits_user-B 발송 명세(O2 dispatch 전 "Category B 수정 동의")가 불필요한 사용자 보고 게이트를 요청하게 된다. O2 는 정상적으로 자동 dispatch 가능하다.
- 연계 오류: `01_implementation.md` line 140 의 "수정 동의 시 `03_orin_lerobot_diff.md` 갱신" 요청도 잘못됨.
  `lerobot-upstream-check` 스킬의 Coupled File Rule은 `orin/lerobot/` 코드 수정 시에만 `03_orin_lerobot_diff.md` 갱신을 요구한다.
  `orin/inference/hil_inference.py` 는 `orin/lerobot/` 하위가 아니므로 해당 규칙 적용 대상이 아니다.
- 수정 요청:
  - `13_orin_cli_flow.md §3`, `§7` 의 "Category B" 표기 제거. `orin/inference/hil_inference.py` 수정은 일반 task (Category B 아님) 로 기술.
  - `01_implementation.md` 의 awaits_user-B 발송 명세에서 "Category B 수정 동의" 항목 및 `03_orin_lerobot_diff.md` 갱신 요청 제거. 대신 "O2 에서 `--ckpt-path` 인자 추가 동의 여부 (일반 task 수정)" 로 교체.

### 2. `§1 run_env_check()` 예시에서 `check_hardware.sh` 에 `--gate-json` 인자 전달 — 실제 동작하지 않는 인터페이스

- 위치: `docs/storage/13_orin_cli_flow.md:25~28`
- 사유:
  `check_hardware.sh` (orin/tests/check_hardware.sh line 68~83) 의 인자 파싱은 `--mode`, `--config`, `--quiet`, `--output-json` 만 지원한다. 알 수 없는 인자에 대해 `[ERROR] 알 수 없는 인자` + `usage()` (exit 2) 를 호출한다.
  따라서 `["bash", str(check_script), "--mode", "resume", "--gate-json", str(config_dir)]` 호출은 exit 2 로 실패한다. `run_env_check()` 는 항상 `False` 를 반환하게 되어 flow 2 가 항상 실패한다.
  `12_interactive_cli_framework.md §5` 에 동일한 패턴이 존재하며, task-executor 가 이를 그대로 복사한 것으로 보인다. `check_hardware.sh` 를 직접 Read 했다면 `--gate-json` 미지원을 확인할 수 있었다.
  `--gate-json` 은 `hil_inference.py` 의 인자이며 `check_hardware.sh` 는 별개 인터페이스이다.
- 수정 요청:
  - `§1 run_env_check()` 예시에서 `"--gate-json", str(config_dir)` 줄 제거.
  - `check_hardware.sh` 는 `--mode resume` 만으로 충분함 (경로 상수는 스크립트 내부에서 자동 결정됨, line 41~46 확인).
  - 올바른 호출: `["bash", str(check_script), "--mode", "resume"]`
  - 참고: `12_interactive_cli_framework.md §5` 의 동일 오류는 해당 문서 담당 todo 범위에서 별도 처리 필요 (ANOMALIES 또는 BACKLOG 등록 권고).

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `13_orin_cli_flow.md §3` 소스 (2) | `~/smolvla/orin/checkpoints/` 경로 예시가 sync_ckpt_dgx_to_datacollector.sh 의 DataCollector 목적지 경로 (`ckpt_transfer/<run>/<step>/`) 와 다름. Orin 의 실제 경로는 `sync_ckpt_dgx_to_orin.sh` 또는 DataCollector → Orin rsync 결과로 `orin/checkpoints/<run>/<step>/pretrained_model/` 이 되어야 함. 08_orin_structure.md line 235 인용이 올바르나, 본문 예시 주석에 DataCollector 경로와 혼용 가능성 있음 — 명확화 권장. |
| 2 | `01_implementation.md:140` awaits_user-B | Critical 1 수정 후 남는 문항: ckpt 선택 소스 조합 (4가지 조합 확인 요청) 이 세분화됨. 사용자 결정 사항을 단순하게 "어느 소스를 지원할지" 로 압축하면 합의 효율 높아짐. |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/`, `.claude/` 미변경 |
| B (자동 재시도 X) | ⚠️ | `orin/inference/hil_inference.py` 를 Category B 로 잘못 분류 — Critical 1 사유. 실제 변경 파일은 `docs/storage/13_orin_cli_flow.md` 신규만으로 Category 미해당. |
| Coupled File Rules | ⚠️ | `orin/lerobot/` 미변경으로 03_orin_lerobot_diff.md 갱신 불필요. 단 awaits_user-B 명세에서 갱신 요청이 잘못 포함됨 — Critical 1 연계. |
| 옛 룰 | ⚠️ | `docs/storage/13_orin_cli_flow.md` 에 bash 명령 예시 포함 (`§1 check_hardware.sh` 경로 상수 블록, `§6 전체 흐름 요약`). CLAUDE.md 옛 룰: "docs/storage/ 하위에는 사용자 명시 요청 없으면 bash 명령 예시 추가 X". 그러나 이 예시들은 레퍼런스 인용·설계 분석 맥락 (실행 명령이 아닌 참조용 코드 인용)이므로 CONSTRAINT_AMBIGUITY 해당. 심각도 Recommended. |

### ANOMALY: CONSTRAINT_AMBIGUITY

CLAUDE.md "옛 룰"의 "bash 명령 예시" 범위가 명확하지 않음.
- 운용 가이드의 실행 명령 블록 (예: `bash sync_ckpt_dgx_to_orin.sh --dry-run`) vs. 설계 분석 문서의 코드 인용 블록 (예: check_hardware.sh 경로 상수 발췌) 이 구분 안 됨.
- 본 검증에서는 후자 (분석 맥락 코드 인용) 는 "bash 명령 예시" 아님으로 해석하여 Recommended 처리.
- 추후 reflection 시 룰 명확화 권장.

---

## 배포 권장

MAJOR_REVISIONS — task-executor 재호출 권장.

수정 대상:
1. `docs/storage/13_orin_cli_flow.md` — `§3`, `§7` Category B 표기 제거 + `§1 run_env_check()` 예시 `--gate-json` 제거
2. `docs/work_flow/context/todos/O1/01_implementation.md` — awaits_user-B 발송 명세에서 "Category B 수정 동의" 항목 및 `03_orin_lerobot_diff.md` 갱신 요청 제거

수정 후 재검증 불필요 (code-tester 사이클 정책: max 2 cycle 중 1 cycle 사용).
재수정 후 prod-test 없이 READY_TO_SHIP 조건(Critical 0건, Recommended 2건 이하)이면 즉시 종료.

참고: `orin/inference/hil_inference.py` Category B 아닌 일반 코드이므로 O2 dispatch 는 사용자 동의 없이 자동 진행 가능. awaits_user-B 는 flow 구조 선택 (A/B/C), ckpt 선택 소스 조합, 시연 데모 포함 여부 3가지로만 구성하면 충분.
