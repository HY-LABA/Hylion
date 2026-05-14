# todos/ — todo 별 작업 흔적

활성 spec 의 각 todo 가 처리될 때, 해당 todo ID 디렉터리가 자동 생성되고 단계별 파일이 누적된다.

## 구조

```
todos/
└── <TODO-XX>/                  # 예: O3, O4, X1, M1
    ├── 01_implementation.md    # task-executor 산출 — 코드 변경 요약
    ├── 02_code-test.md         # code-tester 산출 — 단위 테스트·lint·verdict
    └── 03_prod-test.md         # prod-test-runner 산출 — 배포 후 비대화형 검증
```

## 파일별 작성 규칙

### 01_implementation.md (task-executor)

| 항목 | 내용 |
|---|---|
| 시작 시각 | timestamp |
| 변경 파일 목록 | 경로 + 한 줄 요약 |
| 적용 룰 | CLAUDE.md hard constraints, 옵션B 등 |
| 변경 내용 요약 | 1~2문단 |
| 다음 단계 권장 | code-tester 입장에서 무엇을 검증해야 하는지 |

### 02_code-test.md (code-tester)

| 항목 | 내용 |
|---|---|
| Verdict | `READY_TO_DEPLOY` / `MINOR_REVISIONS` / `MAJOR_REVISIONS` |
| 단위 테스트 결과 | pytest 결과 등 |
| Lint·Type | ruff·mypy 결과 |
| Diff 정합성 | TODO·DOD 부합 여부 |
| Critical 이슈 | (있으면) |
| 배포 권장 | yes/no + 사유 |

### 03_prod-test.md (prod-test-runner)

| 항목 | 내용 |
|---|---|
| 배포 대상 | orin / dgx |
| 배포 결과 | 성공·실패·로그 위치 |
| 비대화형 검증 결과 | 명령·출력·통과 여부 |
| 완료 지점 명확화 | DOD 충족 여부 + 사용자 검증 필요 여부 |
| Verdict | `AUTOMATED_PASS` / `NEEDS_USER_VERIFICATION` / `FAIL` |

## 빈 디렉터리 처리

`todos/` 자체는 spec 사이클 시작 시 비어 있을 수 있음. 본 README.md 만 추적되어 디렉터리 존재 보장.

> ⚠️ 사용자가 본 디렉터리 파일 직접 수정 X. 읽기 전용 관찰만.
