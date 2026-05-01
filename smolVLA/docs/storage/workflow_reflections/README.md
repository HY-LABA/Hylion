# docs/storage/workflow_reflections/

reflection 에이전트가 **spec 사이클 종료 시 (`/wrap-spec`)** 작성하는 회고 보고서 보관.

## 파일명 규칙

```
<YYYY-MM-DD>_<spec명>.md
```

예: `2026-05-15_04_infra_setup.md`

## 보고서 역할

- 사이클 동안 누적된 `specs/ANOMALIES.md` 의 활성 섹션 분석
- 발견된 패턴 추출 (`HOOK_BLOCK`, `MAJOR_RETRY`, `SKILL_GAP` 등)
- skill·hook·CLAUDE.md·에이전트 정의 갱신 제안 도출
- 사용자 승인 결과 기록 (적용 / 거부 / 보류)

## 입력 자료 (reflector 가 참조)

1. **활성 사이클 자료**: `context/{plan, log, verification_queue}.md`, `context/todos/<XX>/*.md`
2. **시스템 누적 자료**: `specs/ANOMALIES.md` 활성 섹션
3. **현재 룰**: `/CLAUDE.md`, `.claude/skills/**/SKILL.md`, `.claude/settings.json`, `.claude/agents/*.md`
4. **과거 reflection** (제한적): 본 디렉터리의 직전 1~2개 보고서

## 갱신 적용 정책

- skill·hook·CLAUDE.md·에이전트 정의 변경은 **모두 사용자 승인 필요**
- 승인된 변경 → 메인 Claude 가 직접 활성 파일 수정
- 변경 이유는 본 보고서 + git commit message 양쪽 기록

자세한 정책: `/CLAUDE.md` § 가시화 레이어 / Hard Constraints / Coupled File Rules

---

(아직 보고서 없음 — 첫 spec 사이클 종료 시 첫 보고서 생성)
