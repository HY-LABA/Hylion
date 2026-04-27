# docs/work_flow/specs/ — 에이전트 간 인계 스펙

Claude Code + 개발자가 협업하여 작성하는 스펙 파일 보관 디렉토리.
각 파일은 todo + DOD 로 구성되며 `/handoff-*`, `/complete-*` 커맨드의 기준이 된다.

---

## 워크플로우

```
[개발자+Claude] 스펙 작성
       ↓
docs/work_flow/specs/NN_*.md  (todo + DOD)
       ↓
/handoff-task  →  current_task.md  →  Copilot 구현  →  /complete-task  →  스펙 반영
/handoff-test  →  current_test.md  →  Codex 테스트  →  /complete-test  →  스펙 반영

Codex는 current_test.md에만 결과를 기록한다. 스펙 파일은 /complete-test 가 업데이트한다.
```

## 파일 명명 규칙

```
NN_<짧은_설명>.md  (NN = 순번, 예: 01, 02, 03)
예) 02_<진행중인_스펙>.md  ← 활성 스펙 (specs/ 루트)
    00_template.md         ← 템플릿 (실제 스펙 아님)
    history/01_teleoptest.md  ← 완료된 스펙 (specs/history/)
```

- 순번이 높을수록 최신. `/handoff-*`가 `specs/` 루트에서 가장 높은 번호 파일을 자동 선택한다.
- 하나의 스펙 파일이 하나의 구현·테스트 사이클에 대응한다.
- 모든 TODO가 완료된 스펙은 `history/` 로 이동하여 활성 스펙과 분리한다.

## 디렉토리 구조

```
specs/
├── README.md
├── 00_template.md
├── BACKLOG.md              # 각 스펙의 Backlog 항목을 스펙별로 모아 관리하는 중앙 문서 (스펙 파일 자체에는 Backlog 섹션을 두지 않음)
├── NN_<진행중>.md          # 활성 스펙 (현재 사이클)
└── history/
    └── NN_<완료된_스펙>.md  # 완료된 스펙 보관
```

> 완료된 스펙의 task/test 단위 히스토리는 `../context/history/NN_<spec명>/` 하위에 모아둔다.
> `BACKLOG.md` 의 신규 항목 추가·상태 업데이트는 `/complete-task` / `/complete-test` 실행 시 자동 반영된다.

---

## 스펙 파일 구조

| 요소 | 설명 |
|---|---|
| `### [ ] TODO-XX` | 미완료 todo. `/handoff-*`가 이 항목을 읽는다 |
| `### [x] TODO-XX` | 완료된 todo. `/complete-*`가 업데이트한다 |
| `타입: task/test/both` | `/handoff-task`는 task/both, `/handoff-test`는 test/both를 읽는다 |
| `DOD:` | 완료 조건. `/complete-*`가 달성 여부를 판단하는 기준 |
| `테스트: test코드/prod/둘다` | Codex가 어떤 방식으로 검증할지 명시 |

---

## 템플릿

[00_template.md](00_template.md) 참고.
