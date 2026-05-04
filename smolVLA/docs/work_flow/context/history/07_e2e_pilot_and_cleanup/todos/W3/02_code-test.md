# TODO-W3 — Code Test

> 작성: 2026-05-03 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈 0건. Recommended 0건. 즉시 prod-test-runner 진입 가능.

---

## 단위 테스트 결과

```
변경 파일:
  - docs/storage/lerobot_upstream_check/02_orin_pyproject_diff.md (신규 섹션 추가, L216~261)
  - docs/work_flow/specs/BACKLOG.md (04 #1 상태 갱신)

대상: 순수 마크다운 문서 변경 — 실행 가능 코드 없음.
pytest 대상 없음. N/A.

entrypoint 목록 정합 검증:
  orin/pyproject.toml [project.scripts] 실제 목록:
    유지 9개: lerobot-calibrate, lerobot-find-cameras, lerobot-find-port,
              lerobot-find-joint-limits, lerobot-record, lerobot-replay,
              lerobot-setup-motors, lerobot-teleoperate, lerobot-info
    제거 (주석): lerobot-eval, lerobot-train

  02_orin_pyproject_diff.md 절차 섹션 표:
    유지 9개: 위 9개 동일 ✅
    제거 2개: lerobot-eval, lerobot-train ✅

→ 목록 완전 일치.
```

---

## Lint·Type 결과

```
ruff check: 마크다운 파일 — ruff 대상 아님. N/A.
mypy: 마크다운 파일 — 대상 아님. N/A.

마크다운 구조 점검:
  - 섹션 헤더 계층 정상 (## / ###)
  - 표 형식 일관
  - 코드 블록 인라인 백틱 정상
  - 기존 파일 흐름과 단절 없음 (재확인 항목 → 신규 절차 섹션 cross-ref 정상)
```

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. 절차 6단계 실행 가능 안내 (모호한 일반론 X) | ✅ | 각 단계가 구체적 행동 기술. 1=Read 확인, 2=유지 표 대조, 3=제거 표 대조, 4=재추가 시 즉시 삭제, 5=신규 entrypoint 판단 기준, 6=후속 이력·Coupled File 연계 |
| 2. 유지/제거 entrypoint 표 현 pyproject.toml 일치 | ✅ | orin/pyproject.toml 직접 Read 대조 — 유지 9개·제거 2개 완전 일치 |
| 3. 04 BACKLOG #1 원문 의도 충족 | ✅ | "동기화 절차에 본 항목 명시 필요" → 02_orin_pyproject_diff.md 에 6단계 절차 섹션 신규 추가로 대응 |
| 4. 재확인 항목 [project.scripts] cross-ref 보강 | ✅ | L212 "(아래 절차 참조)" 추가로 기존 체크리스트와 신규 섹션 연결 |
| 5. BACKLOG 04 #1 마킹 형식·날짜 | ✅ | "완료 (07 W3 명문화 — 02_orin_pyproject_diff.md 에 동기화 절차 섹션 추가, 2026-05-03)" — 형식·날짜 정확 |
| 6. Category A (.claude/skills/SKILL.md) 변경 X | ✅ | 사용자 위임 결정 (a) 준수: SKILL.md 미변경, storage 문서 경로 선택 확인 |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

없음.

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경. `.claude/agents/*.md`, `.claude/skills/**/*.md`, `.claude/settings.json` 미변경. 사용자 위임 결정 (a) — storage 문서 경로 선택 준수 확인 |
| B (자동 재시도 X) | ✅ | `orin/pyproject.toml` 직접 변경 없음 → Coupled File Rule (setup_env.sh·02_*.md 동시 갱신) 트리거 없음. 판단 올바름 |
| Coupled File Rules | ✅ | pyproject.toml 미변경이므로 Rule 1 미적용. Rule 3 (`orin/lerobot/` 코드 수정) 미해당. 위반 없음 |
| bash 명령 예시 룰 | ✅ | CLAUDE.md "docs/storage/ 하위에는 사용자 명시 요청 없으면 bash 명령 예시 추가 X". 본 todo 는 spec W3 DOD 에 "절차 명문화"가 명시됐고 사용자 위임 결정 (a) 로 storage 문서 경로가 선택됨 — 사용자 명시 요청 범위 내. L226 `git submodule update` · L260 `pip install -e orin/[...]` 는 절차 단계의 구체 명령 예시로 DOD 이행에 필수. 위반 없음 |
| Category C·D | ✅ | 신규 디렉터리 생성 없음. 외부 의존성 추가 없음. 금지 명령 없음 |

---

## 배포 권장

READY_TO_SHIP — prod-test-runner 진입 권장.

본 todo 는 순수 문서 절차 명문화 작업으로 prod-test 는 정적 검증 (markdown 파일 존재 확인 + BACKLOG 마킹 grep) 수준이면 충분.
