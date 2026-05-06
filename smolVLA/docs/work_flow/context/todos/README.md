# context/todos/ — todo 별 작업 흔적

각 todo 마다 디렉터리 (`<TODO-XX>/`) 가 만들어지고 그 안에:

- `01_implementation.md` — task-executor 산출
- `02_code-test.md` — code-tester 산출 (verdict 포함)
- `03_prod-test.md` — prod-test-runner 산출 (해당 시)

spec 사이클 종료 시 (`/wrap-spec`) `context/history/<spec명>/todos/` 로 이동.
