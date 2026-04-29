# /handoff-task

최신 스펙의 미완료 todo에서 구현 작업을 선택해 Copilot용 current_task.md를 작성한다.
copilot-instructions.md 는 수정하지 않는다.

## 실행 순서

1. `docs/work_flow/specs/` 에서 파일명(NN_ 순번 접두사) 기준 **가장 높은 번호 파일**을 찾는다.
   - 스펙 파일이 없으면 개발자에게 알리고 종료한다.

2. 스펙 파일에서 **미완료 todo** (`[ ]`) 중 `타입: task` 또는 `타입: both`인 항목을 추출한다.
   - 미완료 task 항목을 목록으로 출력하고 개발자에게 어떤 todo를 작업할지 선택하게 한다.

3. 현재 날짜+시간을 확인한다. `date +%Y%m%d_%H%M`

4. 선택한 todo의 내용을 기반으로 `docs/work_flow/context/current_task.md` 를 아래 형식으로 덮어쓴다:

   ```
   # Current Task
   <!-- /handoff-task 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

   > YYYY-MM-DD HH:MM | 스펙: `docs/work_flow/specs/[파일명]` | TODO: [번호]

   ## 작업 목표
   [todo 제목 및 목표]

   이 작업은 팀원과 함께 대화형 터미널에서 진행해야 한다.

   ## DOD (완료 조건)
   [todo의 DOD]

   ## 구현 대상
   - `path/to/file.py` — 변경/확인 내용

   ## 건드리지 말 것
   - `docs/reference/` 하위 전체 (read-only)
   - [스펙의 제약 사항]

   ## 업데이트
   *Copilot이 작업 완료 후 아래 항목을 채운다.*

   ### 변경한 내용

   ### 검증 방법 및 결과

   ### 실 실행 검증 필요 여부
   ```

5. 완료 후 보고:
   - 읽은 스펙 파일 및 선택한 TODO 번호
   - current_task.md 핵심 내용
   - Copilot에게 전달할 다음 지시 요약
