# TODO-X3 — dgx/ 마이그레이션 회귀 검증 시나리오 정의

> 작성: 2026-05-01 16:00 | task-executor | cycle: 1

## 개요

TODO-X2 (dgx/ 마이그레이션 실행) + cycle 2 (.gitignore 패턴 추가) 완료 후, DGX prod 환경 회귀 검증을 위한 시나리오를 정의한다. 본 TODO 는 test 타입으로 코드 변경 없이 시나리오 정의 문서만 산출한다.

## 산출물

- `docs/work_flow/context/todos/X3/01_implementation.md` — 검증 시나리오 8단계 정의

## 주요 결정 사항

### smoke_test.sh 자율성 분류

smoke_test.sh 스크립트 내 주석 ("최초 실행 시 5~15분") 확인. CLAUDE.md prod-test-runner 자율성 정책 "긴 실행 (>5분 추정) → 사용자 동의" 적용.

- 캐시 HIT 확인 시 자율 진행 허용 (1~3분 예상)
- 캐시 MISS 시 사용자 동의 요청 정책으로 분류

preflight_check.sh 는 자원 점검만 (학습 X, 수초 이내) → 자율 가능.
save_dummy_checkpoint.sh 는 GPU 학습 불필요한 dummy 저장 → 자율 가능 (5분 미만 예상).

### .gitignore 검증 위치

devPC 측 `.gitignore` (Hylion 루트) 에 `smolVLA/dgx/outputs/` 패턴이 235행에 존재 확인. DGX 측은 git 저장소 설정이 devPC 에만 있으므로 devPC 측 확인으로 충분.

### 검증 단계 8개

1. devPC deploy (자율)
2. 신규 파일 3개 존재 확인 (자율)
3. dataset_repos.json valid JSON (자율)
4. README.md DataCollector 섹션 존재 (자율)
5. 02 산출물 4개 파일 존재 + 실행 권한 (자율)
6. preflight_check.sh smoke 모드 (자율, Walking RL 자원 주의)
7. .gitignore 패턴 확인 (devPC, 자율)
8. save_dummy_checkpoint.sh 동작 (자율)
6b. smoke_test.sh 1 step 학습 (캐시 확인 후 자율 또는 사용자 동의)

## 다음 단계

- code-tester 시나리오 분류 정합성 검토
- prod-test-runner DGX SSH 실행 + verdict
