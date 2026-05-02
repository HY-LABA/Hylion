# /wrap-spec

Phase 3 통과 후 spec 사이클 마무리 + reflection 호출 + 다음 spec Phase 1 진입.

## 사전 조건

- `context/verification_queue.md` 의 모든 항목 처리 완료 (통과 / 무시 / 연기 / 실패 처리 중 하나)
- 미처리 항목 있으면 **메인이 항목별 명시적 처리 결정 prompt 제시** (CLAUDE.md § Phase 3 § /wrap-spec 미처리 verification_queue 처리 정책 — 06 reflection 도출):
  - **무시 (BACKLOG 이관)**: verification_queue 마킹 + BACKLOG.md 활성 spec 섹션 + ANOMALIES `USER_OVERRIDE`
  - **연기 (다음 사이클 재시도)**: 무시와 동일 + BACKLOG 우선순위 "중간" + 트리거 명시
  - **실패 처리**: `/verify-result <항목> 실패` 분기 → todo 추가 → planner 재호출 → Phase 2 재진입
- 사용자 답 받기 전 본 명령 진행 X

## 실행 순서

### 1. 활성 spec 식별

- `docs/work_flow/specs/` 에서 `NN_*.md` 식별 (`history/` 등 제외)
- `SPEC_NAME` 변수 추출 (예: `04_infra_setup`)

### 2. context/ 의 활성 자료를 history 로 이동

이동 대상:
- `context/plan.md`
- `context/log.md`
- `context/verification_queue.md`
- `context/todos/` (디렉터리 통째)

이동 위치: `context/history/<SPEC_NAME>/`

```bash
mkdir -p docs/work_flow/context/history/<SPEC_NAME>/
mv docs/work_flow/context/plan.md docs/work_flow/context/log.md \
   docs/work_flow/context/verification_queue.md \
   docs/work_flow/context/history/<SPEC_NAME>/
mv docs/work_flow/context/todos docs/work_flow/context/history/<SPEC_NAME>/
```

### 3. context/ placeholder 재초기화

- `context/plan.md`, `log.md`, `verification_queue.md` → 빈 placeholder (다음 spec 준비 상태)
  - 각 파일 내용은 `context/README.md` 에 정의된 양식의 빈 버전
- `context/todos/` → 디렉터리 새로 만들고 `README.md` 만 두기 (todo 별 자료 다음 사이클에 누적)

### 4. spec 파일 history 로 이동

```bash
mv docs/work_flow/specs/<SPEC_NAME>.md docs/work_flow/specs/history/<SPEC_NAME>.md
```

### 5. reflection 에이전트 호출

입력 자료:
- `context/history/<SPEC_NAME>/` (사이클 자료)
- `docs/work_flow/specs/ANOMALIES.md` 의 `<SPEC_NAME>` 섹션
- `docs/work_flow/specs/BACKLOG.md` 의 `<SPEC_NAME>` 섹션 (변경분 — git diff 또는 가장 최근 항목들)
- 현재 룰:
  - `/CLAUDE.md`
  - `.claude/skills/**/SKILL.md`
  - `.claude/settings.json`
  - `.claude/agents/*.md`
- 직전 reflection 1~2개: `docs/storage/workflow_reflections/` 에서 가장 최근 1~2개

산출: `docs/storage/workflow_reflections/<YYYY-MM-DD>_<SPEC_NAME>.md`

산출물 형식 (reflection 에이전트가 알아서 채움):
- 사이클 요약 (총 todo, 자동 성공·재시도·사용자 결정 비율, 토큰 소비)
- 발견 패턴 (몇 건)
- 갱신 제안 (대상·변경 내용·위험도)
- 사용자 승인 결과 섹션 (이 시점엔 비어있음)

### 6. reflection 보고서를 사용자에게 제시

- 보고서 핵심 요약 (요약 + 패턴 + 갱신 제안 표)
- **갱신 제안 항목별** 사용자에게 묻기:
  - "1번: skill `lerobot-upstream-check` 에 X 추가. 적용?"
  - 답: 적용 / 거부 / 보류

### 7. 승인된 갱신 적용

**중요**: Hard Constraints Category A 에 따라 워커 사용 X. **메인 Claude (오케스트레이터) 가 직접 활성 파일 수정**.

- `Edit` 도구로 해당 파일 수정 (skill SKILL.md, hook settings.json, CLAUDE.md, 에이전트 정의)
- reflection 보고서의 "사용자 승인 결과" 섹션에 항목별 결정 (적용 / 거부 / 보류) 기록
- `docs/work_flow/specs/ANOMALIES.md` 의 해당 항목 처리 상태 갱신:
  - 갱신 적용된 anomaly → "갱신 적용"
  - 거부된 anomaly → "무시됨"
  - 보류 → "reflection 분석됨" (다음 사이클에서 재고)

### 8. git 커밋 (사용자 OK 시)

- 변경된 활성 파일들 + reflection 보고서 + ANOMALIES 갱신 + spec history 이동 + context/ 이동
- 커밋 메시지: `wrap(spec): <SPEC_NAME> 사이클 종료 — reflection 갱신 N건 적용`
- 메시지 본문에 변경 이유 명시 (Coupled File Rules)

### 9. 다음 spec 작성 시작 묻기

- 사용자에게: "다음 spec 작성 시작?"
- **OK** → Phase 1 진입 (사용자와 자연어 대화로 새 milestone·spec 합의)
- **나중에** → 메인 세션 대기 종료 (사용자가 다음에 재진입 시 이어가기)

## 종료 조건

- spec history 이동 완료
- reflection 보고서 작성 + 사용자 승인 완료
- ANOMALIES 처리 상태 갱신 완료
- 다음 spec 진입 또는 세션 종료
