# todos/ — todo 별 작업 흔적 누적

활성 spec 의 자동화가 진행되는 동안 todo ID (예: `O3`, `D1`, `T1`) 별 디렉터리가 생성된다.

## 구조

```
todos/<TODO-XX>/
├── 01_implementation.md    # task-executor 산출
├── 02_code-test.md         # code-tester 산출 (verdict 포함)
└── 03_prod-test.md         # prod-test-runner 산출 (해당 시)
```

`/wrap-spec` 시 본 디렉터리 통째로 `context/history/<spec명>/todos/` 로 이동.

(빈 상태 — 다음 사이클 진입 시 누적 시작)
