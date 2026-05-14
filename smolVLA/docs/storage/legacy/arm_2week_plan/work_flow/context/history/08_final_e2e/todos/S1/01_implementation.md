# TODO-S1 — Implementation

> 작성: 2026-05-04 | task-executor | cycle: 1

## 목표

`arm_2week_plan.md` 에서 04~07 `[x]` 마킹 + 신규 `08_final_e2e` 항목 삽입 + 기존 08~11 → 09~12 시프트

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `arm_2week_plan.md` | M | `[x]` 마킹 4건 + 신규 08_final_e2e 삽입 + 09~12 시프트 |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 ✓. `.claude/` 미변경 ✓
- Coupled File Rule: `orin/lerobot/`, `pyproject.toml`, `setup_env.sh` 미변경 → Coupled File Rules 해당 없음 ✓
- 레퍼런스 활용: 본 todo 는 문서 마킹·시프트 작업으로 코드 레퍼런스 참조 불필요. SKILL_GAP 해당 없음.

## 변경 내용 요약

### [x] 마킹 4건

git history 기준 wrap 완료된 4개 spec 을 완료 상태로 변경:

- `### [ ] 04_infra_setup` → `### [x] 04_infra_setup`
- `### [ ] 05_interactive_cli` → `### [x] 05_interactive_cli`
- `### [ ] 06_dgx_absorbs_datacollector` → `### [x] 06_dgx_absorbs_datacollector`
- `### [ ] 07_e2e_pilot_and_cleanup` → `### [x] 07_e2e_pilot_and_cleanup`

### 신규 08_final_e2e 항목 삽입

07_e2e_pilot_and_cleanup 섹션 직후에 `### [ ] 08_final_e2e` 신규 항목 추가.
- spec 목표·결정사항 A~I·주요 작업 그룹별 요약·종착점·spec 파일 경로 포함
- 시프트 주석: `<!-- 신규 삽입 (2026-05-04). 기존 08~11 → 09~12 시프트. -->`

### 기존 08~11 → 09~12 시프트 (4건)

| 구 번호 | 신 번호 | 시프트 주석 누적 방식 |
|---|---|---|
| `08_leftarmVLA` | `09_leftarmVLA` | 기존 주석 보존 + 08_final_e2e 삽입 사유 선행 추가 |
| `09_biarm_teleop_on_dgx` | `10_biarm_teleop_on_dgx` | 동일 패턴 |
| `10_biarm_VLA` | `11_biarm_VLA` | 동일 패턴 |
| `11_biarm_deploy` | `12_biarm_deploy` | 동일 패턴 |

모든 시프트 주석은 기존 주석 완전 보존 + 신규 시프트 이력을 최상단에 prepend.

### 09_leftarmVLA 본문 책임 재명시

08_leftarmVLA → 09_leftarmVLA 전환 시 본문에서 "팔 배치 차이만" 담당함을 명시:
- "데이터 수집·학습·배포 한 사이클 완주" 책임은 08_final_e2e 로 이전
- `전제:` 항목 신규 추가 — 08_final_e2e 완료 후 진입, 토르소 좌표계 차이만 담당
- 기존 내용(표준 책상 mount 대비 좌표계·관절 한계 고려사항 등)은 그대로 보존

## code-tester 입장에서 검증 권장 사항

```bash
# 완료 마킹 8건 확인 (00~07)
grep -c "^### \[x\]" arm_2week_plan.md
# 기대값: 8

# 마일스톤 헤더 목록 확인 (순번·번호 정합)
grep -n "^### \[.\] " arm_2week_plan.md

# 신규 08_final_e2e 항목 존재
grep -c "### \[ \] 08_final_e2e" arm_2week_plan.md
# 기대값: 1

# 시프트 후 번호 범위 확인 (09~12 존재)
grep -E "^### \[ \] (09|10|11|12)_" arm_2week_plan.md

# 구 번호(08_leftarmVLA 등) 가 헤더에 없음을 확인
grep -E "^### \[.\] 08_leftarmVLA|^### \[.\] 09_biarm|^### \[.\] 10_biarm|^### \[.\] 11_biarm" arm_2week_plan.md
# 기대값: 0건

# 시프트 주석 누적 확인 (기존 주석 보존)
grep -c "06_dgx_absorbs_datacollector (2026-05-02)" arm_2week_plan.md
# 기대값: 4 이상 (각 시프트 주석에 누적)
```

## 잔여 리스크

없음. 본 todo 는 문서 마킹·시프트 전용이며 코드 변경 없음.
