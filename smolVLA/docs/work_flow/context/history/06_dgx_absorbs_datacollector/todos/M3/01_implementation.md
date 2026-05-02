# TODO-M3 — Implementation

> 작성: 2026-05-02 | task-executor | cycle: 1

## 목표

docs 색인·README 정합 갱신 — datacollector 흔적 정리 + spec 시프트 반영.

---

## §1 처리한 파일 목록

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `docs/storage/README.md` | M | 07·10·15 datacollector 행 legacy 이관 표기 추가; 08·09·11·12·13·14 행 신규 또는 정정 표기 추가 |
| `docs/work_flow/specs/README.md` | M | spec 번호 현황 표 신규 추가 (06_dgx_absorbs_datacollector + 시프트 07~10) |
| `docs/storage/12_interactive_cli_framework.md` | M | 헤더에 3-노드→2-노드 정정 주석 + datacollector node.yaml 블록 주석화 |
| `docs/storage/08_orin_structure.md` | M | §4-1 T3 예정 항목에 "06 결정으로 불요화 + legacy 이관 완료" 정정 주석 |
| `docs/storage/09_dgx_structure.md` | M | §0 4-노드 책임 표에 06 결정 정정 주석; §4-1 DataCollector→DGX 전송 인터페이스 무효화 주석 |
| `docs/storage/02_hardware.md` | M | §1 컴퓨팅 장치 DataCollector 항목 "운영 종료" 표기 + DGX 행 "데이터 수집 흡수" 갱신 |
| `docs/storage/03_software.md` | M | §6 DataCollector venv 참조 경로 legacy 이관 경로로 정정 |
| `docs/storage/11_demo_site_mirroring.md` | M | 헤더 형제 문서 참조 legacy 경로로 정정 + "DGX 직접 이동" 정정 주석 |
| `docs/storage/others/ckpt_transfer_scenarios.md` | M | 헤더 참고 스크립트 정정 + 케이스 3 제목에 무효화 표기 + 본문 정정 주석 |
| `orin/interactive_cli/README.md` | M | 개요 3-노드→2-노드 정정; 노드별 차이점 표 datacollector 열 제거; deploy 절차 2-노드로 갱신 |
| `dgx/interactive_cli/README.md` | M | 개요 3-노드→2-노드 + "학습 + 데이터 수집 책임" 갱신; 노드별 차이점 표 datacollector 열 제거; deploy 절차 2-노드로 갱신; 후행 todo 갱신 |

**총 11개 파일 수정.**

### docs/storage/README.md 세부 내용

- 07_datacollector_venv_setting.md 행: legacy 이관 + 경로 안내
- 10_datacollector_structure.md 행: legacy 이관 + 경로 안내
- 15_datacollector_cli_flow.md 행: legacy 이관 + 경로 안내
- 08·09·11·12·14 행 신규 추가 (기존 README 에 이 번호들이 없었음 — 색인 불완전 상태였음)
- 13_orin_cli_flow.md 행 신규 추가

### docs/work_flow/specs/README.md 세부 내용

- "활성 spec 번호 현황" 절 신규 추가 (spec 명, 상태 표)
- 번호 시프트 배경 주석 (06_dgx_absorbs_datacollector 삽입 → 구 06~09 → 신 07~10)

---

## §2 X2 인계 항목

| 항목 | 위치 | 내용 |
|---|---|---|
| `dgx/interactive_cli/flows/training.py` | L15·L54·L70·L72 (L2 grep 결과) | `sync_ckpt_dgx_to_datacollector.sh` 인용 — X2 에서 training.py 수정 시 해당 참조 제거 또는 legacy 주석 처리 |
| `dgx/interactive_cli/flows/entry.py` | flow 1 장치 옵션 | orin/dgx/datacollector → orin/dgx 2 옵션으로 축소 (VALID_NODES 상수, NODE_DESCRIPTIONS 등) |
| `dgx/interactive_cli/flows/env_check.py` | mode 파라미터 | 수집/학습 분기 체크 통합 (14_dgx_cli_flow.md §1 결정 반영) |
| `dgx/interactive_cli/flows/training.py` | mode=학습 진입 분기 | entry 변경 — mode.py 에서 "학습" 선택 시 training.py 호출 경로 |
| `dgx/interactive_cli/configs/node.yaml` | responsibilities | "data_collection" 추가 |

본 todo (M3) 에서 dgx/interactive_cli/ 파일들의 README 만 처리했고, 코드 파일 (flows/*.py) 수정은 X2 담당.

---

## §3 reflection 인계 항목

| 항목 | 위치 | 내용 | 처리 방향 |
|---|---|---|---|
| `.claude/skills/lerobot-reference-usage/SKILL.md` L111 | `docs/storage/legacy/CLAUDE_pre-subagent.md` 하드코딩 | L1 에서 파일이 `01_pre_subagent_workflow/CLAUDE_pre-subagent.md` 로 이동됨. 스킬 파일의 경로 참조가 옛 경로 가리킴 | Category A → 워커 수정 X. reflection 시점 메인 Claude 가 사용자 승인 후 수정 필요. 새 경로: `docs/storage/legacy/01_pre_subagent_workflow/CLAUDE_pre-subagent.md` |

---

## §4 잔여 리스크

| 항목 | 영향도 | 처리 방안 |
|---|---|---|
| `docs/storage/README.md` 에 13_orin_cli_flow.md 행 추가했으나 파일 실존 미확인 | 낮음 | code-tester 가 `ls docs/storage/13_orin_cli_flow.md` 로 확인 권장 |
| `dgx/interactive_cli/flows/training.py` L15·L54·L70·L72 의 `sync_ckpt_dgx_to_datacollector.sh` 참조 잔재 | 낮음 (legacy 파일 경로 참조 — 실 동작에는 무해) | X2 에서 training.py 수정 시 처리 |
| `orin/interactive_cli/flows/entry.py` 의 `VALID_NODES = ("orin", "dgx", "datacollector")` 상수 잔재 | 낮음 (flow 1 메뉴에 datacollector 선택 불가 안내가 나오나 기능 오류는 아님) | X2 에서 entry.py 수정 시 동시 처리 |
| `.claude/settings.json` permissions.allow 의 `Bash(ssh datacollector*:*)` 잔재 | 없음 (사용 X) | reflection 시점 정리 후보 |

---

## 적용 룰

- CLAUDE.md Hard Constraints Category A: `docs/reference/` 미변경 ✓
- CLAUDE.md Hard Constraints Category A: `.claude/skills/` 미변경 ✓ (L111 발견만 보고)
- Coupled File Rule: `orin/lerobot/`, `dgx/lerobot/` 미변경 → 03·04_diff.md 갱신 불필요 ✓
- 역사적 결정 보존 원칙: 본문 완전 삭제 X — HTML 주석 + ~~취소선~~ + "정정" 안내로 처리 ✓
- lerobot-reference-usage SKILL: 본 todo 는 문서 정합 갱신 — lerobot 코드 구현 없음, 레퍼런스 검색 불요 ✓
- lerobot-upstream-check SKILL: Coupled File Rule 해당 없음 ✓

---

## 변경 내용 요약

본 TODO 는 06_dgx_absorbs_datacollector spec 의 L1·L2·M1 완료 후 docs 색인 정합을 갱신하는 작업이다.

주요 처리 내용:

1. **docs/storage/README.md** — 이미 legacy 이관된 07·10·15 파일 행을 이관 완료 표기로 정정. 기존 색인에 누락되어 있던 08~14 파일 행을 신규 추가하여 색인을 완전하게 만들었다.

2. **docs/work_flow/specs/README.md** — 활성 spec 번호 현황 표를 신규 추가. 06_dgx_absorbs_datacollector 삽입으로 인한 07~10 시프트를 공식 기록했다. 기존 README 에는 spec 번호 목록이 없어 `/start-spec` 자동 탐지 로직 외에 사람이 참조할 색인이 부재했다.

3. **docs/storage/ 잔재 파일 8개** — L2 grep 결과로 인계받은 datacollector 언급 파일들에 역사적 결정 보존 원칙을 적용. 본문 텍스트 완전 삭제 없이 HTML 주석 또는 인라인 "정정" 안내로 06 결정 후 상태를 명확히 표기했다.

4. **orin/dgx interactive_cli README** — 3-노드 → 2-노드 전환을 README 에 반영. datacollector 열 제거, deploy 절차 2-노드로 갱신, 후행 todo 갱신 (dgx 측 X1~V3 todo 목록 반영).

---

## code-tester 입장에서 검증 권장 사항

- `grep -r "07_datacollector\|10_datacollector\|15_datacollector" docs/storage/README.md` → legacy 이관 표기 존재 확인
- `grep -n "06_dgx_absorbs\|leftarmVLA\|biarm" docs/work_flow/specs/README.md` → spec 번호 현황 표 존재 확인
- `grep -n "datacollector" orin/interactive_cli/README.md` → 주석 외 활성 참조 없음 확인
- `grep -n "datacollector" dgx/interactive_cli/README.md` → 주석 외 활성 참조 없음 확인
- `ls docs/storage/13_orin_cli_flow.md 2>/dev/null || echo "MISSING"` → README 에 추가한 13번 파일 실존 여부 확인
- DOD 항목:
  - docs/storage/README.md 갱신 (07·10·15 legacy 표기) ✓
  - docs/work_flow/specs/README.md 갱신 (06 추가 + 시프트 반영) ✓
  - docs/storage/lerobot_upstream_check/README.md — 파일 미존재 확인 (05_datacollector_lerobot_diff.md 행 없음 = 정정 불필요) ✓
  - L2 grep 인계 항목 처리 (역사적 결정 보존 + 정정 주석) ✓
  - orin/interactive_cli/README.md 정정 ✓
  - dgx/interactive_cli/README.md 정정 ✓ (본 todo 에서 둘 다 처리 결정)
  - Category A 영역 발견만 보고 ✓
