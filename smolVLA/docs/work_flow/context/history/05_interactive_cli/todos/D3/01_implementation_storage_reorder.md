# docs/storage 재정렬 — Implementation Report

> 작성: 2026-05-02 | task-executor | cycle: 1

## 목표

docs/storage/ 루트를 의미적 그룹 (공통 / 노드별 venv / 노드별 structure / 시연 / CLI) 으로 재정렬 (orin → dgx → datacollector 순). 09_datacollector_setup.md 분해 흡수 후 삭제. 전체 참조 일괄 갱신.

---

## 1) mv 8건 결과

| 이전 번호 | 새 번호 | 파일명 (공통 부분) | 결과 |
|---|---|---|---|
| 08_dgx_structure | 09_dgx_structure | dgx_structure.md | DONE |
| 07_orin_structure | 08_orin_structure | orin_structure.md | DONE |
| 15_datacollector_venv_setting | 07_datacollector_venv_setting | datacollector_venv_setting.md | DONE |
| 12_datacollector_cli_flow | 15_datacollector_cli_flow | datacollector_cli_flow.md | DONE |
| 11_interactive_cli_framework | 12_interactive_cli_framework | interactive_cli_framework.md | DONE |
| 10_demo_site_mirroring | 11_demo_site_mirroring | demo_site_mirroring.md | DONE |
| 16_datacollector_structure | 10_datacollector_structure | datacollector_structure.md | DONE |
| 09_datacollector_setup | (삭제) | 분해 흡수 후 rm | DONE |

충돌 방지 순서: 08→09, 07→08 (orin/dgx 충돌 방지), 나머지는 독립 실행.

### 최종 번호 매핑 (의미적 그룹)

```
01 smolvla_arm_env_requirements  — 공통
02 hardware                      — 공통
03 software                      — 공통
04 devnetwork                    — 공통
05 orin_venv_setting             — 노드별 venv
06 dgx_venv_setting              — 노드별 venv
07 datacollector_venv_setting    — 노드별 venv
08 orin_structure                — 노드별 structure
09 dgx_structure                 — 노드별 structure
10 datacollector_structure       — 노드별 structure
11 demo_site_mirroring           — 시연
12 interactive_cli_framework     — CLI
13 orin_cli_flow                 — CLI
14 dgx_cli_flow                  — CLI
15 datacollector_cli_flow        — CLI
```

---

## 2) 09_datacollector_setup.md 분해 흡수 매핑 (절별)

| 09 절 | 처리 | 흡수처 |
|---|---|---|
| §0 본 문서 위치 | 폐기 | 메타 정보 — 흡수 불필요 |
| §1 노드 정체 (하드웨어·OS·네트워크) | 폐기 | 이미 02·03·04 에 흡수됨 |
| §2 venv·lerobot 의존성 | 폐기 | 이미 07_datacollector_venv_setting.md 에 흡수됨 |
| §3 디렉터리 구조 | 폐기 | 이미 10_datacollector_structure.md 에 흡수됨 |
| §4-1 DHCP 변동 리스크 | **흡수** | `04_devnetwork.md §10` 신규 소절 추가 |
| §4-2 인터넷 격리 vs HF Hub | **흡수** | `11_demo_site_mirroring.md §6-1` 신규 절 추가 |
| §4-3 전원·배선·물리 보안 | **흡수** | `11_demo_site_mirroring.md §6-2` 신규 절 추가 |
| §4-4 시연장 이동 체크리스트 | 폐기 | 이미 `04_devnetwork.md §8` 에 DataCollector 항목 포함됨 |
| §5-1 SSH 설정 | 폐기 | 이미 `04_devnetwork.md §5` 에 흡수됨 |
| §5-2 devPC→DataCollector rsync | **흡수** | `10_datacollector_structure.md §4-1` devPC sync hub 구성에 포함 |
| §5-3 DataCollector→DGX 데이터 전송 | **흡수** | `10_datacollector_structure.md §4-3` 에 흡수 명시 |
| §5-4 DataCollector→DGX 네트워크 토폴로지 | **흡수** | `10_datacollector_structure.md §4-4` 신규 소절 추가 |
| §5-5 devPC sync hub 전체 구성 | **흡수** | `10_datacollector_structure.md §4-1` 에 전체 구성 추가 |
| §6 향후 작업 | 폐기 | 각 흡수처에 TODO 트리거 이미 존재 |
| §7 변경 이력 | 폐기 | 역사적 기록 — 각 흡수처 변경 이력에 2026-05-02 항목 추가 |

**unique 정보 흡수 완료 자기 검증**: §4-1·§4-2·§4-3·§5-2·§5-3·§5-4·§5-5 모두 흡수처에 명시적으로 기록. 나머지 절은 기존 파일에 이미 내용이 존재하여 중복 흡수 불필요.

---

## 3) grep 일괄 갱신 결과

### 처리된 파일 수

- sed 배치 처리: 51개 파일 (07_orin_structure·08_dgx_structure·10_demo_site_mirroring·11_interactive_cli_framework·12_datacollector_cli_flow·15_datacollector_venv_setting·16_datacollector_structure 7개 패턴)
- 09_datacollector_setup 활성 파일 추가 갱신: 9개 파일 (specs/05, context/verification_queue, storage/04·11·10·15, datacollector/README, todos/D3/*)
- 수동 Edit: 03_software.md §6, 04_devnetwork.md §10, 07_datacollector_venv_setting.md 내부 참조, 11_demo_site_mirroring.md §0·§6, 10_datacollector_structure.md 헤더·§4, verification_queue.md 라인 51

### 처리 원칙

- **history 파일** (`docs/work_flow/context/history/04_infra_setup/**`): 과거 기록 보존 우선. 07_orin_structure → 08_orin_structure 등 파일명 갱신은 적용. 09_datacollector_setup 참조는 "(삭제됨)" 처리 없이 그대로 — 역사적 컨텍스트 보존.
- **활성 파일**: 모든 구 패턴 → 새 패턴 갱신 완료.

---

## 4) 잔여 옛 참조 검증 결과

```bash
# 검증 명령 1 — 주요 패턴 (10·11·12·15·16 구 번호)
grep -rn "10_demo_site_mirroring|11_interactive_cli_framework|12_datacollector_cli_flow|
          15_datacollector_venv_setting|16_datacollector_structure" ... --exclude-dir="reference"
# 결과: 0건 (exit code 1)

# 검증 명령 2 — orin/dgx structure 구 번호
grep -rn "07_orin_structure|08_dgx_structure" ... --exclude-dir="reference"
# 결과: 0건 (exit code 1)
```

주요 6개 갱신 패턴 모두 잔여 참조 0건 확인.

09_datacollector_setup.md 참조는 history 파일에 다수 잔존하나, 이는 04 사이클의 역사적 기록이므로 의도된 잔재. history 외 활성 파일의 09 참조는 모두 흡수처 참조로 교체 완료.

---

## 5) self-check 결과

| 항목 | 결과 |
|---|---|
| 15·16·09 파일 없음 | `ls` 기준 확인 — 3개 파일 모두 없음 (No such file) |
| 07·10 새 파일 존재 | 07_datacollector_venv_setting.md / 10_datacollector_structure.md 존재 확인 |
| 새 번호 매핑 정확 (08·09 포함) | 01~15 순서 갭 없음, 13·14 원래 번호 유지 확인 |
| 09 §4·§5 unique 정보 흡수 | 04_devnetwork.md §10 + 11_demo_site_mirroring.md §6 + 10_datacollector_structure.md §4 신규 추가 확인 |
| 03_software.md §6 참조 갱신 | "15_datacollector_venv_setting.md" → "07_datacollector_venv_setting.md" 확인 |
| 05_interactive_cli.md 참조 갱신 | 12_datacollector_cli_flow → 15_*, 09_datacollector_setup → 10_datacollector_structure 갱신 확인 |
| 새 07·10 본문 자기 참조 갱신 | 형제 문서 참조 (08_orin_structure, 09_dgx_structure) 갱신 확인 |
| Category A (docs/reference/) 미수정 | --exclude-dir="reference" 로 완전 제외 확인 |
| Category B (pyproject.toml 등) 미수정 | 해당 없음 — docs 재정렬 작업 |

---

## 적용 룰

- CLAUDE.md Hard Constraints: docs/reference/ 미변경 (Category A 준수)
- Category B 비해당: pyproject.toml·setup_env.sh·deploy_*.sh 미수정
- Category C 비해당: 기존 디렉터리 내 파일 mv/삭제 — 신규 디렉터리 X
- Category D 비해당: `rm 09_datacollector_setup.md` (단일 파일 — `rm -rf` X)
- lerobot-reference-usage: 코드 구현 없음 — docs 재정렬 작업이므로 레퍼런스 인용 의무 약함
