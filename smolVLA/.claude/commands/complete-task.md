# /complete-task

Copilot이 업데이트한 current_task.md를 읽고 spec에 반영한 뒤 history로 보관한다.

## 실행 순서

1. `docs/work_flow/context/current_task.md` 를 읽는다.
   - `## 업데이트` > `### 변경한 내용` 아래에 실제 내용이 없으면 개발자에게 알리고 종료한다.

2. current_task.md 헤더에서 연결된 스펙 파일 경로와 TODO 번호를 확인한다.

3. 해당 스펙 파일의 TODO 항목을 업데이트한다:
   - 업데이트 내용이 DOD를 충족하면 `[ ]` → `[x]` 로 변경
   - 부분 완료이면 todo 아래에 진행 상황 메모 추가
   - test/prod 검증이 필요하다고 명시된 경우 해당 todo의 타입을 `both`로 업데이트하고 메모 추가

4. `docs/work_flow/specs/BACKLOG.md` 를 읽고 업데이트한다:
   - 현재 스펙에 해당하는 섹션을 찾는다. 섹션이 없으면 하단에 새 섹션을 추가한다.
   - 이번 작업으로 해소된 백로그 항목이 있으면 상태를 `완료`로 업데이트한다.
   - 작업 중 새로 발견된 잔여 리스크·기술 부채·설계 개선 필요 사항이 있으면 해당 스펙 섹션 하단에 새 항목으로 추가한다.
   - 우선순위 `높음` 미완 항목 목록을 파악해 둔다 (보고에 활용).

5. 현재 날짜+시간을 확인한다. `date +%Y%m%d_%H%M`

6. 개발자에게 Orin 배포 여부를 묻는다:
   - "Orin에 배포할까요? (`bash smolVLA/scripts/deploy_orin.sh` 실행)" 라고 물어본다.
   - OK가 나오면 Hylion 레포 루트에서 `bash smolVLA/scripts/deploy_orin.sh` 를 실행한다.
   - 거절하면 배포 없이 다음 단계로 진행한다.

7. `docs/work_flow/context/current_task.md` 하단에 배포 결과를 추가한다:
   ```
   ## 배포
   - 일시: YYYY-MM-DD HH:MM
   - 결과: 완료 / 미실행 (사유)
   ```

8. `docs/work_flow/context/current_task.md` 를
   `docs/work_flow/context/history/YYYYMMDD_HHMM_task_<요약>.md` 로 복사한다.

9. `docs/work_flow/context/current_task.md` 를 비운다:
   ```
   # Current Task
   <!-- 마지막 완료: YYYYMMDD_HHMM — history 참조 -->
   ```

10. 업데이트된 스펙 파일을 분석한다:
    - 남은 미완료 todo 목록 확인
    - 전체 진행률 계산

11. 완료 후 보고:
    - 반영한 스펙 파일 및 TODO 번호와 상태 변경 내용
    - 배포 실행 여부 및 결과
    - history에 보관된 파일 경로
    - 남은 미완료 todo 목록 및 진행률
    - BACKLOG.md 변경 내용 (추가된 항목 / 완료 처리된 항목)
    - 우선순위 `높음` 미완 백로그 항목 목록
    - 개발자에게 다음 액션 제안 (다음 task handoff / test handoff / spec 업데이트 필요 여부)
