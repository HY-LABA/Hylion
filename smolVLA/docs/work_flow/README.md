# docs/work_flow/ — 업무 과정 기록

스펙 작성 → 에이전트 인계 → 구현/테스트 → 결과 반영까지 업무 과정 전체를 기록하는 디렉토리.

---

## 구조

```
work_flow/
├── specs/                  # 에이전트 인계 스펙 (NN_*.md — 순번 접두사)
│   ├── README.md
│   ├── 00_template.md
│   └── history/            # 완료된 스펙 보관 (예: 01_teleoptest.md)
└── context/                # 현재 진행 상태 및 히스토리
    ├── current_task.md
    ├── current_test.md
    └── history/
        └── NN_<spec명>/    # 스펙별 task/test 히스토리 (예: 01_teleoptest/)
```

## 디렉토리 역할

| 디렉토리 | 역할 |
|---|---|
| `specs/` | Claude Code + 개발자가 협업하여 작성. todo + DOD 포함. `/handoff-*`가 읽어 에이전트에 전달 |
| `context/` | 현재 진행 중인 task/test 상태 (`current_*.md`) + 날짜별 히스토리 |

## 전체 흐름

```
[개발자+Claude] 스펙 작성
       │
       ▼
specs/YYYYMMDD_*.md  (todo + DOD)
       │
       ├─ /handoff-task → context/current_task.md → Copilot (구현)
       │                                                  │
       │                                         /complete-task
       │                                                  │
       │                                      스펙 반영 + history 보관
       │
       └─ /handoff-test → context/current_test.md → Codex (테스트)
                                                          │
                                                 /complete-test
                                                          │
                                              스펙 반영 + history 보관
```

> 스펙 완료 시 `specs/NN_*.md` → `specs/history/`, 해당 스펙의 task/test 히스토리는 `context/history/NN_<spec명>/` 하위에 모아둔다.
