# /complete-test

Codex가 기록한 current_test.md의 테스트 결과를 읽고 spec에 반영한 뒤 history로 보관한다.

## 실행 순서

1. `docs/work_flow/context/current_test.md` 를 읽는다.
   - 테스트 결과 테이블(test 코드 / prod 코드)에 결과가 없으면 개발자에게 알리고 종료한다.

2. current_test.md 헤더에서 연결된 스펙 파일 경로와 TODO 번호를 확인한다.

3. 테스트 결과를 분석한다:
   - 전체 단계 중 pass / fail / blocked 비율
   - fail 원인 분석 (DOD와 대조)
   - blocked 항목은 하드웨어 미확보 또는 환경 문제인지 구분

4. 해당 스펙 파일의 TODO 항목을 업데이트한다:
   - 모든 단계 pass + DOD 충족 → `[ ]` → `[x]`
   - fail 항목 있음 → todo 아래에 실패 내역 메모, `[ ]` 유지
   - blocked → todo 아래에 blocked 사유 메모

5. `docs/work_flow/specs/BACKLOG.md` 를 읽고 업데이트한다:
   - 현재 스펙에 해당하는 섹션을 찾는다. 섹션이 없으면 하단에 새 섹션을 추가한다.
   - 이번 테스트로 해소된 백로그 항목이 있으면 상태를 `완료`로 업데이트한다.
   - 테스트 중 새로 발견된 잔여 리스크·설계 개선 필요 사항·기술 부채가 있으면 해당 스펙 섹션 하단에 새 항목으로 추가한다.
   - 우선순위 `높음` 미완 항목 목록을 파악해 둔다 (보고에 활용).

6. 현재 날짜+시간을 확인한다. `date +%Y%m%d_%H%M`

7. `docs/work_flow/context/current_test.md` 를
   `docs/work_flow/context/history/YYYYMMDD_HHMM_test_<요약>.md` 로 복사한다.

8. `docs/work_flow/context/current_test.md` 를 완료 상태로 초기화한다:
   ```
   # Current Test Target
   <!-- 마지막 완료: YYYYMMDD_HHMM — history 참조 -->
   ```

9. 업데이트된 스펙 파일을 분석한다:
   - 남은 미완료 todo 목록 확인
   - 전체 진행률 계산

10. 완료 후 보고:
    - 테스트 결과 요약 (pass/fail/blocked 수)
    - fail 원인 및 다음 조치 (재테스트 / 코드 수정 요청 / 하드웨어 대기)
    - 반영한 스펙 파일 및 TODO 번호와 상태
    - history에 보관된 파일 경로
    - 남은 미완료 todo 목록 및 진행률
    - BACKLOG.md 변경 내용 (추가된 항목 / 완료 처리된 항목)
    - 우선순위 `높음` 미완 백로그 항목 목록
    - 개발자에게 다음 액션 제안
