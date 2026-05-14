# TODO-W3 — Implementation

> 작성: 2026-05-03 | task-executor | cycle: 1

## 목표

04 BACKLOG #1 — upstream 동기화 시 `orin/pyproject.toml [project.scripts]` 의 entrypoint 정리 (lerobot-eval / lerobot-train 제거) 가 덮어씌워지지 않도록 동기화 절차를 `docs/storage/lerobot_upstream_check/02_orin_pyproject_diff.md` 에 명문화.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `docs/storage/lerobot_upstream_check/02_orin_pyproject_diff.md` | M | "upstream 동기화 시 entrypoint 정리 절차" 섹션 신규 추가 + "upstream 동기화 시 재확인 항목" 마지막 항목에 "(아래 절차 참조)" 보강 |
| `docs/work_flow/specs/BACKLOG.md` | M | 04 BACKLOG #1 → 완료 마킹 |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 ✓, `.claude/` 미변경 ✓
- 사용자 위임 결정 (a): storage 문서 변경 — Category A 회피 ✓ (SKILL.md 변경 X)
- Coupled File Rule: `orin/pyproject.toml` 미변경이므로 `setup_env.sh` / `02_orin_pyproject_diff.md` 동시 갱신 트리거 없음 ✓
- 레퍼런스 활용: 본 todo 는 절차 문서화 작업 — 코드 신규 작성 없음. SKILL_GAP 해당 없음.

## Step 1 — 현 상태 확인 결과

### `02_orin_pyproject_diff.md` 기존 구조

- 섹션 1~7: 현재 차이 요약 (requires-python, torch 제거, 메타데이터, extras, scripts, setuptools, 도구 설정)
- 섹션 5: `[project.scripts]` — 04_infra_setup TODO-O2 시점 (2026-04-30) 에 lerobot-eval / lerobot-train 제거 이력이 표로 기록됨
- 변경 이력 섹션: [2026-04-30] 에 제거 2줄 + 주석 대체 + 영향 범위 상세 기록됨
- "upstream 동기화 시 재확인 항목" 섹션: 5개 체크리스트 항목 중 `[project.scripts]` 변경 확인 항목 있으나 **구체적인 제거 목록 및 절차는 없었음**

### `orin/pyproject.toml [project.scripts]` 현재 상태

유지 중인 entrypoint 9개:
- `lerobot-calibrate`, `lerobot-find-cameras`, `lerobot-find-port`, `lerobot-find-joint-limits`
- `lerobot-record`, `lerobot-replay`, `lerobot-setup-motors`, `lerobot-teleoperate`, `lerobot-info`

제거된 entrypoint 2개 (주석으로 이력 명시):
- `lerobot-eval` (04 TODO-O2 제거)
- `lerobot-train` (04 TODO-O2 제거)

### entrypoint 정리 절차 기록 유무

- 제거 **이력**은 이미 기록됨 (why + what)
- 동기화 시 **재발 방지 절차** (어떻게 확인하고 대응할지) 는 미명문화 — 본 todo 의 핵심

## Step 2 — 변경 내용 요약

`02_orin_pyproject_diff.md` 에 "upstream 동기화 시 entrypoint 정리 절차 (07 W3 추가, 2026-05-03)" 섹션을 신규 추가했다.

추가된 내용:
- **배경**: 04 TODO-O2 결정 (2026-04-30) 으로 lerobot-eval / lerobot-train 제거 이유 재요약
- **유지 대상 entrypoint 9개 표**: 동기화 시 보존해야 할 목록
- **제거 대상 entrypoint 2개 표**: 제거 이유와 함께 명시
- **6단계 절차**:
  1. 동기화 후 `[project.scripts]` 직접 Read 확인
  2. 유지/제거 판단
  3. 제거된 항목이 재추가됐으면 즉시 삭제 (파일 자체는 upstream 보존 원칙대로 유지)
  4. 신규 entrypoint 추가 시 Orin 책임 범위 해당 여부 판단 절차
  5. 변경 후 본 문서 이력 기록
  6. Coupled File Rule 1 (`setup_env.sh`) 연계 갱신 안내

"upstream 동기화 시 재확인 항목" 의 `[project.scripts]` 항목 끝에 "(아래 절차 참조)" 보강으로 새 섹션과 연결.

## Step 3 — 04 BACKLOG #1 마킹

`docs/work_flow/specs/BACKLOG.md` 04 섹션 #1 항목:
- 이전: `미완`
- 이후: `완료 (07 W3 명문화 — 02_orin_pyproject_diff.md 에 동기화 절차 섹션 추가, 2026-05-03)`

## code-tester 입장에서 검증 권장 사항

- **텍스트 정합성**: `02_orin_pyproject_diff.md` 의 신규 절차 섹션 내 entrypoint 목록이 현재 `orin/pyproject.toml [project.scripts]` 와 일치하는지 확인
  - 유지 9개 목록 vs `orin/pyproject.toml` 실제 9개 일치 여부
  - 제거 2개 (`lerobot-eval`, `lerobot-train`) 가 실제로 없는지 확인
- **BACKLOG 마킹**: `BACKLOG.md` 04 #1 상태가 완료로 갱신됐는지 grep 확인
- **Category 준수**: `docs/reference/` 미변경, `.claude/` 미변경 확인
- **Coupled File Rule**: `orin/pyproject.toml` 을 직접 변경하지 않았으므로 `setup_env.sh` 동시 갱신 불요 — 이 판단이 올바른지 확인
