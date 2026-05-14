# docs/storage/legacy/ — 이전 워크플로우 자산 보관소

본 디렉터리는 **더 이상 활성 운영되지 않는 노드·워크플로우 자산**을 보관한다. 시대(era) 단위로 묶으며, 각 묶음은 후속 사이클에서 참조 가능하도록 이력을 보존한다.

---

## 보관 묶음 색인

### `arm_2week_plan/` — arm_2week_plan 마일스톤 시대 (2026-04 ~ 2026-05)

- **사유**: 2026-05-14 fresh start — `arm_2week_plan.md` (구 "Bi-arm VLA 최종 프로젝트 로드맵", 마일스톤 00~12) 기반으로 진행하던 시대 전체를 한 묶음으로 아카이브. 새 로드맵을 새로 수립하기 위해 옛 계획·그 계획에서 파생된 워크플로우 자산을 일괄 legacy 이관.
- **이관 일자**: 2026-05-14
- **구성**:
  - `arm_2week_plan.md` — 구 루트 로드맵 문서 (마일스톤 00~08 완료 `[x]`, 09~12 미완 `[ ]`). 새 계획에 미완 마일스톤을 carry forward 하지 않음.
  - `BACKLOG.md` / `ANOMALIES.md` — 구 era 의 사이클 간 누적 잔여 자료 (구현 차원 / 시스템 차원). fresh start 시 이관. 워커가 풀리지 않는 문제·하네스 이상을 만났을 때 유사 사례 참조용.
  - `work_flow/` — 구 era 의 완료된 spec·사이클 흔적 (`specs/history/` 8개 spec + `context/history/` 8개 사이클, 265+ 파일). 원래 `docs/work_flow/` 구조 그대로 보존. 워커가 옛 사이클의 구현·검증 흔적을 참조할 필요가 있을 때.
  - `others/` — 위 분류에 안 들어가는 옛 era 워크플로우 자산 묶음:
    - `01_pre_subagent_workflow/` — 2026-05-01 워크플로우 재구성 이전의 3-AI 분업 (Claude / Copilot / Codex) 자산. 서브에이전트 팀 도입으로 비활성화.
    - `02_datacollector_separate_node/` — `06_dgx_absorbs_datacollector` 결정으로 운영 종료된 DataCollector 별도 노드 (smallgaint, Ubuntu 22.04) 자산. DGX 가 데이터 수집 + 학습 두 책임 흡수.
    - `03_interactive_cli/` — 옛 interactive CLI 프레임워크 (orin/ + dgx/ flows). 후속 워크플로우에서 대체됨.
- **후속**: 현 워크플로우는 `.claude/agents/`, `.claude/skills/`, `docs/work_flow/specs/` 기반. DGX 측 데이터 수집 자산은 `dgx/scripts/` 등에 신규 배치. 본 묶음은 **읽기 전용 참조** 용.
- **색인**: 각 하위 폴더의 `README.md` 참조.

---

## 복구 정책

이 보관 묶음들은 **읽기 전용 참조**. 다시 활성 영역으로 끌어올 일이 있으면, **새로운 이름으로 활성 위치에 복사**하고 본 디렉터리는 그대로 둘 것 (이력 보존).

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-01 | `01_pre_subagent_workflow/` 초기 보관 — 3-AI 분업 자산 8건 archive |
| 2026-05-02 | `01_pre_subagent_workflow/` 하위로 git mv 이동 (TODO-L1) + 색인 README 신규 작성 |
| 2026-05-02 | `02_datacollector_separate_node/` 이관 (TODO-L2) |
| 2026-05-07 | `03_interactive_cli/` 이관 |
| 2026-05-14 | fresh start — `01·02·03` 및 구 루트 `arm_2week_plan.md` 를 `arm_2week_plan/` 묶음으로 그룹핑. 본 README 를 시대(era) 단위 색인으로 재작성. |
| 2026-05-14 | 구 era `BACKLOG.md`·`ANOMALIES.md` (`docs/work_flow/specs/`) 를 `arm_2week_plan/` 으로 이관. `specs/` 에는 fresh placeholder 신규 생성. |
| 2026-05-14 | 구 era `docs/work_flow/{context,specs}/history/` 를 `arm_2week_plan/work_flow/` 아래 동일 구조로 이관 (273 파일). 원위치 `history/` 는 fresh placeholder README 로 재초기화. |
| 2026-05-14 | `arm_2week_plan/` 내 `01·02·03` 을 `others/` 하위로 재그룹핑 (`work_flow/` 와 분리). |
