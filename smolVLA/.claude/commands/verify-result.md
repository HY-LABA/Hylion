# /verify-result

Phase 3 (사용자 실물 검증) 의 결과를 자연어로 입력받아 통과/추가 todo 분기 처리.

## 인자

자연어 자유 형식. 예:

```
/verify-result O3, O4 통과. X1 은 ImportError 발생
/verify-result 모두 통과
/verify-result O3 통과, 나머지는 내일 다시 볼게
```

## 실행 순서

### 1. 현재 verification_queue 읽기

- `context/verification_queue.md` 의 대기 항목 목록 파악
- 항목별 todo ID, 검증 절차, prod-test 결과 요약 확보

### 2. 사용자 입력 분석

- **통과 항목** 추출 (예: "O3, O4 통과")
- **실패 항목** 추출 (예: "X1 ImportError")
- **미검증 항목** 추출 (예: "나머지는 내일")
- 모호한 부분은 사용자에게 추가 질문:
  - "X1 의 ImportError 가 정확히 뭐였어? 로그 한 줄 줄 수 있어?"
  - "나머지" 가 어느 항목인지 명확화

### 3. 분기 결정

#### A. 모든 항목 통과

- `verification_queue.md` 에 처리 결과 마킹
- `context/log.md` 에 "PHASE3_COMPLETE" 이벤트 기록
- 사용자에게 안내:

  > "spec 종료 가능. `/wrap-spec` 호출하면 reflection 후 다음 spec 으로 진입."

#### B. 일부 실패

- 자연어 대화로 다음 단계 사용자에게 묻기:

  > "TODO-X1 실패. 어떻게 할까?
  > 1. 추가 todo (1a, 1b) 만들어서 자동 재시도
  > 2. 직접 수정한 뒤 다시 `/verify-result` 호출
  > 3. 이 todo 무시하고 종료"

- 사용자 선택에 따라:
  - **1 (자동 재시도)**: orchestrator 가 todo 추가 (예: TODO-X1a "ImportError 원인 분석", TODO-X1b "수정 적용") → planner 재호출 → Phase 2 재진입
  - **2 (직접 수정)**: 사용자 응답 대기. 사용자가 코드 수정 후 다시 `/verify-result` 호출
  - **3 (무시)**: `verification_queue.md` 에서 해당 항목 제외, BACKLOG.md 활성 spec 섹션에 "사용자 무시 결정" 항목 추가, 종료 가능 재평가

#### C. 미검증 항목 있음

- 사용자에게:

  > "남은 항목: [목록]. 검증 후 다시 `/verify-result` 호출해줘."

### 4. anomaly 누적 (해당 시)

- 검증 실패 발견 → `docs/work_flow/specs/ANOMALIES.md` 활성 섹션에 `DEPLOY_ROLLBACK` 항목 추가
- 사용자가 자동화 흐름 무효화 결정 (예: "이 todo 무시") → `USER_OVERRIDE` 추가

### 5. log.md 갱신

- 매 결과 분석 → `context/log.md` 한 줄 추가:
  ```
  YYYY-MM-DD HH:MM:SS | VERIFY_RESULT | passed=[O3,O4] failed=[X1] action=<선택>
  ```

## 종료 조건

- **A 분기**: `/wrap-spec` 호출 권장 안내
- **B-1 분기**: Phase 2 재진입 (planner 재호출)
- **B-2 분기**: 사용자 직접 수정 대기
- **B-3 분기**: 종료 가능 재평가 후 `/wrap-spec` 권장 또는 추가 todo 안내
- **C 분기**: 사용자 검증 마무리 대기
