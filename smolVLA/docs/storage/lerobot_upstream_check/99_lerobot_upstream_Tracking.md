# 99. lerobot Upstream Tracking

이 문서는 lerobot upstream 변화를 추적하고 Orin 환경과의 동기화 이력을 누적 기록한다.

## Upstream Tracking Log

upstream 변화를 점검할 때 아래 항목을 누적 기록한다.

| Date (KST) | lerobot commit | Describe | Recent cadence (30/90/180d) | Impact note | Action |
|---|---|---|---|---|---|
| 2026-04-22 | `ba27aab79c731a6b503b2dbdd4c601e78e285048` | `v0.5.1-42-gba27aab7` | `70 / 185 / 314` | upstream 변경 빈도 높음. Orin 의존성 drift 리스크 존재 | `orin/pyproject.toml` 기준 유지, 다음 동기화 시 설치/실행 재검증 |

### Snapshot Notes (2026-04-22)

- Latest commit subject: `fix(robotwin): pin compatible curobo in benchmark image (#3427)`
- Current smolVLA pointer state: `-ba27aab79c731a6b503b2dbdd4c601e78e285048 lerobot`
- 해석: `-` 접두는 submodule이 현재 워킹트리에서 미초기화/불일치 상태일 수 있음을 의미하므로, 실제 동기화 작업 전 상태 확인이 필요하다.
