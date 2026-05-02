# docs/storage/legacy/ — 이전 워크플로우 자산 보관소

본 디렉터리는 **더 이상 활성 운영되지 않는 노드·워크플로우 자산**을 보관한다. 각 하위 폴더는 독립적인 "보관 단위"이며, 후속 사이클에서 참조 가능하도록 이력을 보존한다.

---

## 하위 폴더 색인

### `01_pre_subagent_workflow/`

- **사유**: 2026-05-01 워크플로우 재구성 이전의 3-AI 분업 (Claude / Copilot / Codex) 자산. 서브에이전트 팀 도입으로 옛 정책 파일들이 비활성화됨.
- **이관 일자**: 2026-05-01
- **후속**: 새 워크플로우는 `.claude/agents/`, `.claude/skills/`, `docs/work_flow/specs/` 기반으로 운영 중. 본 폴더는 **읽기 전용 참조** 용.
- **색인**: 해당 폴더의 `README.md` 참조.

---

### `02_datacollector_separate_node/`

- **사유**: 2026-05-02 `06_dgx_absorbs_datacollector` 사이클 결정 — DataCollector 별도 노드 (smallgaint, Ubuntu 22.04) 운영 종료. DGX 가 데이터 수집 + 학습 두 책임을 흡수하면서 DataCollector 노드 자산 전체를 legacy 이관.
- **이관 일자**: 2026-05-02 (TODO-L2 처리)
- **후속**: DGX 측 흡수 자산은 `dgx/interactive_cli/flows/` + `dgx/scripts/` 에 신규 배치. 본 폴더는 **읽기 전용 참조** 용.
- **색인**: `02_datacollector_separate_node/README.md` 참조 (TODO-L2 에서 작성).

---

## 복구 정책

이 하위 폴더들은 **읽기 전용 참조**. 다시 활성 영역으로 끌어올 일이 있으면, **새로운 이름으로 활성 위치에 복사**하고 본 폴더는 그대로 둘 것 (이력 보존).

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-01 | `01_pre_subagent_workflow/` 초기 보관 — 3-AI 분업 자산 8건 archive |
| 2026-05-02 | `01_pre_subagent_workflow/` 하위로 git mv 이동 (TODO-L1) + 본 색인 README 신규 작성 |
| 2026-05-02 | `02_datacollector_separate_node/` placeholder 추가 — 실제 이관은 TODO-L2 처리 |
