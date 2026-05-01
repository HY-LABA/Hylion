# TODO-M1 — 시연장 미러링 가이드

> 작성: 2026-05-01 14:25 | task-executor | cycle: 1

## 사전 점검 결과

- **arm_2week_plan.md 미러링 절 추출**: `04_infra_setup` 마일스톤 항목에서 "시연장 환경 미러링
  가이드 (사용자 책임 + 기록 위주)" 와 "시연장 미러링 검증 깊이 (육안+사진 vs 자동 검증)"
  를 확인. `05_leftarmVLA` 항목에서 "DataCollector 의 시연장 미러링 환경에서 데이터 수집
  (학습 정확도의 핵심)" 을 확인 → §5 진입 게이트의 중요성 파악.
- **BACKLOG 03 #15·#16 연계**: #15 (카메라 인덱스 사전 발견) 와 #16 (wrist flip 확정) 를
  §3 재현 체크리스트 3-6·3-7 및 §5 소프트웨어 게이트에 직접 링크.
- **DataCollector D1 산출물 활용**: `09_datacollector_setup.md` §4 (시연장 배치 고려사항)
  의 이동 체크리스트 패턴 참조. DataCollector 가 시연장 인근 노드임을 §3 주체로 명시.
- **레퍼런스 활용**: 본 TODO 는 study 타입 (코드 X). 레퍼런스 (lerobot 코드) 는 해당 없음.
  `lerobot-find-cameras`, `lerobot-record` 커맨드는 `docs/reference/lerobot/` 의 기존 스크립트
  기반이며 신규 코드 작성 없음 — SKILL_GAP 없음.

## 목표

시연장 환경을 DataCollector 인근에 재현하기 위한 절차·체크리스트 문서 작성.
사용자 책임 영역과 자동화 가능 영역 분리. 05_leftarmVLA 진입 전 1차 미러링 셋업 가능.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `docs/storage/10_demo_site_mirroring.md` | A (신규) | 시연장 미러링 가이드 전체 (§0~§7, 246줄) |
| `docs/work_flow/context/history/04_infra_setup/20260501_1425_task_demo_site_mirroring.md` | A (신규) | history 기록 |

## 적용 룰

- CLAUDE.md Hard Constraints Category A: `docs/reference/` 미변경 ✓
- Coupled File Rule: `docs/storage/` 신규 문서 작업, pyproject.toml 미변경 → coupled file 갱신 불필요 ✓
- 레퍼런스 활용: study 타입 (코드 없음). 절 구조는 spec DOD 기반. `09_datacollector_setup.md` §4 패턴 참조. lerobot 커맨드 참조: `docs/reference/lerobot/` 의 `lerobot_record.py`, `lerobot_find_cameras.py`
- Category C 확인: 신규 디렉터리는 `docs/` 하위 (todos/M1) — Category C 해당 없음 ✓

## 변경 내용 요약

`docs/storage/10_demo_site_mirroring.md` 를 신규 작성했다. 본 문서는 시연장을 DataCollector 인근에
재현하기 위한 3단계 구조 (무엇을 측정 → 어떻게 재현 → 어떻게 검증) 로 구성된다.

§1 에서 책상·작업영역·조명·top카메라·wrist카메라·토르소 6개 카테고리에 걸쳐 모든 측정 항목을
표 형식으로 정리했다. §2 에서 줄자·스마트폰 앱(조도계·색온도계·각도계) 을 포함한 측정 도구를
명시했다. §3 에서 7개 단위의 재현 체크리스트를 작성했으며, BACKLOG 03 #15(카메라 인덱스)·#16(wrist
flip) 를 해당 항목에 직접 링크했다. §4 에서 사용자 결정(육안+사진 비교)에 따른 검증 절차와
합격 기준을 기술하고, 자동 검증 스크립트는 BACKLOG 04 로 명시했다. §5 에서 05_leftarmVLA 진입 전
환경미러링·하드웨어·소프트웨어 3개 게이트를 체크리스트로 정리하고, lerobot-record dry-run 을
자동화 가능 영역으로 분리했다.

## code-tester 입장에서 검증 권장 사항

- 단위: 코드 없음 (study 타입) — pytest 불필요
- 문서 구조: spec DOD 의 5개 절 (§1~§5) 모두 존재 확인
- DOD 항목별 충족:
  - §1 시연장 환경 측정 항목 ✓ (책상·조명·카메라·토르소·작업영역 표 형식)
  - §2 측정 도구 ✓ (줄자·조도계·색온도계·사진 — 사용자 책임 명시)
  - §3 DataCollector 재현 절차 ✓ (체크리스트 형태, 7개 단위)
  - §4 검증 방법 ✓ (육안+사진 비교 + 자동 검증 BACKLOG)
  - §5 진입 전 점검 항목 ✓ (3개 게이트)
- 사용자 책임 명확화 확인: §0 알림 + §1~§4 전 영역에 "사용자 책임" 명시
- BACKLOG 03 #15·#16 연계 확인: §3-6, §3-7, §5 wrist 항목

## 잔여 리스크 / SKILL_GAP

- 시연장 접근 가능성 — 사용자 일정에 따라 측정 시점 조정 필요 (§0 에 명시)
- SKILL_GAP: 없음 (study 타입, 신규 코드 없음)
- CONSTRAINT_AMBIGUITY: 없음

---

## cycle 2 수정 (2026-05-01 14:55)

### Critical #1 해소 — BACKLOG.md #6 신규

- 행 추가: `| 6 | 시연장 미러링 자동 검증 스크립트 — DataCollector 측 사진·조도·색온도 자동 측정·비교 (사용자 답 E: 본 사이클은 육안+사진 결정. 05/06 학습 결과로 미러링 부족 진단 시 트리거) | TODO-M1 | 낮음 (05·06 트리거 시 중간) | 미완 |`
- 우선순위: 낮음 (05·06 트리거 시 중간)
- 발견 출처: TODO-M1
- 상태: 미완

### Critical #2 해소 — §5 lerobot-record dry-run 추측 작성 교체

- 옵션 B 채택 (구체 명령어 없이 추상 기술)
- 변경 부분: §5 소프트웨어 게이트 — 4개 체크박스 항목 + draccus 방식 안내 메모
- 추측 플래그 (`--robot-path`, `--cameras top,wrist`, `--num-frames`, `--dry-run` 등) 모두 제거
- 구체 lerobot-record 호출은 TODO-D3 prod 검증 시 사용자가 환경 맞춰 결정으로 이관

### 검증

- BACKLOG.md grep "시연장 미러링" 새 행 존재 확인
- 10_demo_site_mirroring.md §5 grep "draccus" 및 "TODO-D3" 메모 존재 확인
- §1~§4 변경 X 확인

### 잔여 리스크

- 없음 (cycle 2 후 code-tester 재검증 예정)
