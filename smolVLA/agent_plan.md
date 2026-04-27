# Agent Plan for smolVLA

## 역할 분담

| AI | 역할 | 핵심 |
|---|---|---|
| **Claude Code** | 기획 / 문서 | 프로젝트 관리, 기록 및 컨텍스트 문서 작성, 시스템 설계 |
| **GitHub Copilot** | 코딩 | Claude가 설계한 구조를 바탕으로 `orin/` 구현 담당 |
| **OpenAI Codex** | 테스트 | 실물 로봇 배포 전 코드 로직과 환경 검증 담당 |

## steering 정책

- 세 ai에게 명령은 개발자가 직점 프롬프트와 skills로 전달
- claude code와 개발자는 직접 프롬프트를 통해 기획하고 spec 문서 작성 작성
- copilot과 codex는 spec 문서에 명시된 todo와 DOD를 기반으로 작업 수행

> copilot과 codex는 새로운 작업 시 개발자가 직접 세션 초기화해야함

## 작업 흐름
1. claude code와 개발자가 협업하여 최신 스펙을 기반으로 설계 문서 작성
- spec 문서는 todo와 각 todo에 대한 DOD가 명시되도록 구성
- 각 todo에 대해 task만 필요한지, test만 필요한지 혹은 둘 다 필요한지 명확히 구분하여 작성
- test는 test 코드 검증과 prod 코드 검증(test/prod 나눠서)으로 구분하여 작성
2. handoff 명령어로 각 ai에게 설계 문서 전달
- claude code가 `/handoff-task` 명령어로 current_task.md를        작성하는데, spec 문서에서 아직 해결되지 않은 todo와 DOD를 기반으로 작성
    1. 개발자가 copilot에게 지시하여 copilot은 current_task.md를 참조하여 `orin/` 코드 구현 (test/prod 나눠서)
    2. 업데이트 사항을 current_task.md에 추가(test/prod 검증이 필요한 경우 current_task.md에서 spec 문서에 반영 요청)
- claude code가 `/handoff-test` 명령어로 current_test.md를 작성하는데, spec 문서에서 아직 해결되지 않은 todo와 DOD를 기반으로 작성
    1. 개발자가 codex에게 지시하여 codex는 current_test.md를 참조하여 test 코드 실행 및 결과 문서화, prod 코드 실제 로봇 환경에서 검증 및 결과 문서화
    2. 테스트 결과에 따라 필요한 경우 current_test.md에서 spec 문서에 반영 요청
3. complete 명령어로 테스트 결과 분석 및 반영
- claude code가 `/complete-task` 명령어로 current_task.md가 handoff시에 작성한 양식에서 업데이트 되었을 경우, 해당 task를 todo에 완료로 업데이트 후, 업데이트 내용을 간단하게 spec 문서에 반영 
    1. 이후 완료된 current_task.md의 내용을 history로 옮기기(history는 현재 docs/work_flow/context/history/ 하위에 YYMMDDHHMM_해당task요약.md로 task별로 관리)
    2. 업데이트된 spec 문서를 분석 한 후 개발자에게 다음 액션 제안 및 필요 시에 개발자와 함께 spec 문서 업데이트
- claude code가 `/complete-test` 명령어로 current_test.md가 handoff시에 작성한 양식에서 업데이트 되었을 경우, 이를 간단하게 spec 문서에 반영하고 todo 최신화
    1. 이후 완료된 current_test.md의 내용을 history로 옮기기(history는 현재 docs/work_flow/context/history/ 하위에 YYMMDDHHMM_해당test요약.md로 test별로 관리)
    2. 업데이트된 spec 문서를 분석 한 후 개발자에게 다음 액션 제안 및 필요 시에 개발자와 함께 spec 문서 업데이트
4. 2., 3.을 반복 수행하여 spec 문서의 todo가 모두 완료될 때까지 작업 진행

> 필요 시에 claude code가 `/update-docs` 명령어로 README.md 및 각종 navigator 문서 최신화

## 필요 skills

- **Claude Code**:
1. README.md 및 각종 navigator 문서 최신화 자동화
2. copilot과의 협업을 위한 명확한 설계 문서 작성
3. codex의 테스트 결과 분석 및 피드백 제공
- **GitHub Copilot**:
1. claude가 작성한 설계 문서를 기반으로 `orin/` 코드 구현(test/prod 나눠서) 및 기존과 달라진 점 문서화
- **OpenAI Codex**:
1. test 코드 실행 및 결과 문서화
2. prod 코드 실제 로봇 환경에서 검증 및 결과 문서화

---

## 스킬 구현 현황

### Claude Code — `.claude/commands/`

| 커맨드 | 파일 | 역할 |
|---|---|---|
| `/handoff-task` | `.claude/commands/handoff-task.md` | 스펙 미완료 todo → current_task.md (Copilot용) |
| `/handoff-test` | `.claude/commands/handoff-test.md` | 스펙 미완료 todo → current_test.md (Codex용) |
| `/complete-task` | `.claude/commands/complete-task.md` | current_task.md 결과 → 스펙 반영 + history 보관 |
| `/complete-test` | `.claude/commands/complete-test.md` | current_test.md 결과 → 스펙 반영 + history 보관 |
| `/update-docs` | `.claude/commands/update-docs.md` | 파일 구조 파악 → README 등 navigator 문서 최신화 |

### GitHub Copilot — 지시문 방식

| 파일 | 역할 |
|---|---|
| `.github/copilot-instructions.md` | 핵심 규칙 (stable) |
| `docs/work_flow/context/current_task.md` | 현재 구현 태스크 (dynamic) |

사용법: VSCode에서 `docs/work_flow/context/current_task.md` 탭으로 열기, 또는 Chat에서 `#file:docs/work_flow/context/current_task.md`

### OpenAI Codex — 지시문 방식

| 파일 | 역할 |
|---|---|
| `AGENTS.md` | 핵심 규칙 (stable) |
| `docs/work_flow/context/current_test.md` | 현재 테스트 기준 (dynamic) |

사용법: Codex 실행 시 AGENTS.md 자동 로드 → `docs/work_flow/context/current_test.md` 자율 탐색

---

## 참조 흐름

```
[개발자+Claude] 스펙 작성
       │
       ▼
docs/work_flow/specs/YYYYMMDD_*.md  (todo + DOD)
       │
       ├─ /handoff-task ─▶ current_task.md ─▶ Copilot 구현
       │                                           │
       │                                    /complete-task
       │                                           │
       │                                    스펙 todo 업데이트
       │                                    history 보관
       │
       └─ /handoff-test ─▶ current_test.md ─▶ Codex 테스트
                                                    │
                                             /complete-test
                                                    │
                                             스펙 todo 업데이트
                                             history 보관

핵심 파일 (stable)         동적 파일 (단계마다 교체)
copilot-instructions.md ──▶ docs/work_flow/context/current_task.md
AGENTS.md               ──▶ docs/work_flow/context/current_test.md
```