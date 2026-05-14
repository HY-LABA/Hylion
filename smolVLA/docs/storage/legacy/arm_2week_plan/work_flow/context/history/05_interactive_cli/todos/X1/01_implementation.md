# TODO-X1 — Implementation

> 작성: 2026-05-01 14:00 | task-executor | cycle: 1

## 목표

dgx interactive_cli 의 flow 3~ 단계 구체 책임 정의 (preflight·데이터셋 선택·학습 trigger·체크포인트 관리 중 어느 책임을 어떻게 묶을지) — 사용자 합의를 위한 분석 및 awaits_user-C 발송.

---

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `docs/storage/14_dgx_cli_flow.md` | 신규 | dgx flow 2~6 설계 문서 (5개 절 + awaits_user-C 명세) |
| `docs/work_flow/context/todos/X1/01_implementation.md` | 신규 | 본 study 진행 보고서 |

---

## 적용 룰

- CLAUDE.md Hard Constraints Category A: `docs/reference/` 미변경 (read-only 준수)
- CLAUDE.md Hard Constraints Category B: `orin/lerobot/`, `dgx/lerobot/`, `pyproject.toml` 미변경 (해당 없음)
- Coupled File Rule: `orin/lerobot/`, `pyproject.toml` 미변경이므로 03_orin_lerobot_diff.md, 02_orin_pyproject_diff.md 갱신 불필요
- 본 todo 는 `docs/storage/` 신규 파일 작성만 — Category 비해당
- 레퍼런스 직접 Read 및 인용:
  - `dgx/scripts/preflight_check.sh` line 1~36 (5체크 항목) — 인용 완료
  - `dgx/scripts/smoke_test.sh` line 24~45, 68~81 (preflight 호출 + 학습 실행) — 인용 완료
  - `dgx/scripts/save_dummy_checkpoint.sh` line 25, 62~63 (저장 경로 + --save_checkpoint=true) — 인용 완료
  - `scripts/sync_ckpt_dgx_to_datacollector.sh` line 6~36 (케이스 분류 + 동작) — 인용 완료
  - `docs/storage/09_dgx_structure.md` §2·§4-3·§4-5 (책임 매트릭스 + 인터페이스) — Read 완료
  - `docs/storage/12_interactive_cli_framework.md` §5 (env_check.py 패턴) — Read 완료

---

## 변경 내용 요약

`docs/storage/14_dgx_cli_flow.md` 를 신규 작성했다. 총 7개 절로 구성:

- §1: flow 2 (env_check.py 가 preflight_check.sh subprocess 래퍼로 동작) 패턴 확정. F1 §5 orin 패턴을 dgx 에 맞게 변형. 5체크 항목 표로 정리.
- §2: flow 3~ 3개 후보 도출. preflight·데이터셋 선택·학습 trigger·ckpt 관리의 단계 조합 방식으로 A(4단계 순차) / B(2단계 통합) / C(3단계 권고) 비교표 제공.
- §3: 데이터셋 선택 메커니즘 3가지 소스 (HF Hub / 로컬 rsync 결과 / T1 dummy push) + smoke_test.sh 하드코드 데이터셋 (`lerobot/svla_so100_pickplace`) 인용 + config/dataset_repos.json 연동 설계.
- §4: smoke_test.sh 내부 동의 메시지 (line 44~45) 직접 인용 + CLAUDE.md 자율성 정책 (>100MB 다운로드 동의 필요) 근거로 interactive_cli 내부 동의 게이트 포함 권고. 학습 단계 분기 구조 제안.
- §5: save_dummy_checkpoint.sh 체크포인트 저장 경로 (line 25) + sync_ckpt_dgx_to_datacollector.sh 케이스 분류 (line 6~24) 직접 인용. DGX 에서 실행 불가한 devPC 스크립트이므로 interactive_cli 는 안내 출력만 수행하는 구조로 설계.
- §6: awaits_user-C 발송 명세 (옵션 A·B·C + 추가 결정 3가지 + X2 영향 정리).
- §7: 확정 항목 vs awaits_user 항목 표로 정리.

---

## awaits_user-C 발송 내용

dgx interactive_cli 의 flow 3~ 단계 구체 책임을 선택해주세요.

`dgx/scripts/{setup_train_env, preflight_check, smoke_test, save_dummy_checkpoint}.sh` 직접 Read + `docs/storage/09_dgx_structure.md` 분석 결과 다음 후보를 도출했습니다:

**(A) 4단계 순차**
- flow 3: preflight 재확인 + 시나리오 선택 (smoke/s1/s3/lora)
- flow 4: 데이터셋 선택 (HF Hub repo_id 입력 / 로컬 dgx/datasets/ 선택 / smoke 기본값)
- flow 5: 학습 trigger — smoke test 또는 실 학습 분기. **동의 게이트 포함** (smoke: 5~15분 + 다운로드 경고 / 실 학습: steps·wandb 선택)
- flow 6: ckpt 관리 — 저장 경로 출력 + 전송 케이스 선택 (케이스 1·2 vs 케이스 3 안내)

**(B) 2단계 통합**
- flow 3: preflight + 학습 trigger 통합 (smoke 또는 실 학습 1회 선택, 동의 1회)
- flow 4: ckpt 관리 (로컬 확인 + 전송 안내)
- 데이터셋·ckpt 는 CLI 외부 인자로 직접 지정

**(C) 3단계 (권고)**
- flow 3: preflight 재확인 + 시나리오 선택
- flow 4: 데이터셋 선택
- flow 5: 학습 (smoke/실 학습 분기 + **동의 게이트**) + ckpt 관리 통합

**추가 결정 사항**:

1. smoke_test (5~15분 + svla_so100_pickplace >100MB 다운로드 가능) 의 **interactive_cli 내부 동의 게이트 포함 여부**
   - 포함 권고: CLAUDE.md 자율성 정책 ("큰 다운로드 >100MB 사용자 동의 필요") 충족
   - 미포함: smoke_test.sh 기존 경고 출력에 의존

2. **데이터셋 선택 UI 포함 여부**
   - 포함 (A·C): HF Hub repo_id 입력 + 로컬 선택 대화형 메뉴
   - 미포함 (B): 인자 직접 지정

3. **ckpt 전송 케이스 안내 방식**
   - 케이스 목록 출력 + 사용자 선택 → 해당 명령 출력
   - 케이스 자동 감지 (DGX에서 Orin SSH 시도 → 실패 시 케이스 3 안내) — 구현 복잡

**영향**: X2 의 `dgx/interactive_cli/flows/training.py` 구조가 결정됩니다.
- 옵션 A·C: 데이터셋 선택 UI + smoke 동의 게이트 + ckpt 전송 케이스 안내
- 옵션 B: 최소 구조 (preflight 연동 + 결과 출력)

---

## 다음 단계 권고

X2 task 가 받을 입력 (사용자 답 후 결정될 flow 구조):

사용자가 옵션 A/B/C 중 하나를 선택하면 X2 는 다음을 구현:

| 결정 항목 | X2 입력 |
|---|---|
| flow 구조 옵션 | A: `training.py` 에 4개 함수 / B: 2개 함수 / C: 3개 함수 |
| smoke 동의 게이트 포함 | 포함: `flow_training()` 진입 전 Y/n prompt 추가 |
| 데이터셋 선택 UI | 포함: `flow_dataset_select()` 함수 신규 / 미포함: `--dataset` 인자 직접 |
| ckpt 전송 안내 | 케이스 목록 출력 함수 `flow_ckpt_guide()` — 어느 옵션에서도 공통 |

X2 는 반드시 F2 (boilerplate 복사) 완료 후 진입. F2 가 `dgx/interactive_cli/flows/training.py` 의 빈 stub 을 생성하므로, X2 는 stub 에 본 문서 §2~§5 를 기반으로 구현.

---

## code-tester 입장에서 검증 권장 사항

- 본 todo 는 docs/storage/ 신규 문서 작성 (코드 없음) → lint 검증 불필요
- 레퍼런스 인용 정확성 확인:
  - `dgx/scripts/preflight_check.sh` line 참조가 실제 파일과 일치하는지
  - `dgx/scripts/smoke_test.sh` line 44~45, 68~69 인용이 실제 내용과 일치하는지
  - `scripts/sync_ckpt_dgx_to_datacollector.sh` 케이스 분류 인용 일치 여부
- DOD 충족 확인:
  - preflight·데이터셋 선택·학습 trigger·체크포인트 관리 네 영역 모두 §§1·3·4·5 에서 다루고 있는지
  - 3개 옵션 비교표 (§2-5) 가 사용자 합의에 충분한 정보를 제공하는지
  - awaits_user-C 발송 명세 (`01_implementation.md §awaits_user-C`) 의 결정 항목이 X2 영향으로 이어지는지
