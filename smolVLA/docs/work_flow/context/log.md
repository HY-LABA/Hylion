# Orchestrator Log

> 오케스트레이터의 매 dispatch·완료·분기 이벤트 timeline. 한 줄 한 이벤트.

## 형식

```
YYYY-MM-DD HH:MM:SS | [이벤트 타입] | 상세
```

이벤트 타입 예:
- `START` — spec 자동화 시작
- `DISPATCH` — 워커 호출
- `COMPLETE` — 워커 완료
- `VERDICT` — code-tester 판정
- `BLOCK` — 가정 위반 또는 Critical 이슈
- `USER_INPUT` — 사용자 답 받음
- `PHASE2_DONE` — Phase 2 자동화 종료

(아직 활성 spec 없음)
