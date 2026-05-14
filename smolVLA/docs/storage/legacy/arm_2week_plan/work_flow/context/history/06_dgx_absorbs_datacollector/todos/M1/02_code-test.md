# TODO-M1 — Code Test

> 작성: 2026-05-02 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 0건, Recommended 1건.

---

## 단위 테스트 결과

```
해당 없음 — arm_2week_plan.md 는 순수 마크다운 문서.
spec 의 TODO-M1 DOD 에도 "테스트: 없음 (문서 정합)" 으로 명시.
```

## Lint·Type 결과

```
해당 없음 — .md 파일. 코드 변경 없음.
마크다운 구조 정합은 육안 + diff 검사로 대체.
```

---

## DOD 정합성

spec (06_dgx_absorbs_datacollector.md) § TODO-M1 DOD:

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 04 마일스톤 본문 — 가정 정정 + "본 결정 이전 가정" 주석 | ✅ | L95: HTML 주석 삽입. 04 본문 텍스트 (목표·배경·주요 작업·결정사항) 원문 완전 보존 확인 |
| 05 마일스톤 본문 — datacollector flow 언급 → DGX 흡수 후 통합 표시 | ✅ | L113: HTML 주석 삽입. 05 본문 (목표·주요 작업·결정사항) 삭제 없이 보존. 위치 절 갱신 (06_leftarmVLA → 07_leftarmVLA 명시) |
| 06 마일스톤 신규 추가 (05 와 07_leftarmVLA 사이) | ✅ | L134~L155: 06_dgx_absorbs_datacollector 신규 삽입. 결정 사항 A~F 모두 인용. 배경·주요 작업·spec 파일 경로 포함 |
| 07 (구 06) leftarmVLA — 시프트 + DataCollector 언급 정정 | ✅ | L157~L171: 제목 07_leftarmVLA. HTML 주석으로 구 번호·시프트 사유 명시. 내부 DataCollector 언급 3곳 → DGX 흡수 표현 정정 확인 |
| 08 (구 07) biarm_teleop_on_dgx — 시프트 + DataCollector 언급 정정 | ✅ | L173~L189: 제목 08_biarm_teleop_on_dgx. HTML 주석 있음. "DataCollector 기준" → "DGX 데이터 수집 흡수 기준". 결정사항 "07 진행 중" → "08 진행 중". 고려사항 "08 학습 시" → "09 학습 시" |
| 09 (구 08) biarm_VLA — 시프트 | ✅ | L190~L203: 제목 09_biarm_VLA. HTML 주석. "07 에서 수집" → "08 에서 수집" 정정 |
| 10 (구 09) biarm_deploy — 시프트 | ✅ | L204~L212: 제목 10_biarm_deploy. HTML 주석 있음 |
| 장비 역할 분담 절 DGX 행에 *데이터 수집 + 시연장 직접 이동 운영* 추가 | ✅ | L21: "학습/튜닝 주력 환경 + **데이터 수집 + 시연장 직접 이동 운영**" 명시. blockquote legacy 경로 + 운영 원칙 갱신 포함 |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `arm_2week_plan.md` L159~L160 (07_leftarmVLA HTML 주석) | 주석 내 "DataCollector" 역할 대체 언급만 있고 "구 06_leftarmVLA" 명시가 있으나, 05 본문 위치 절 (L132) 에서 `07_leftarmVLA` 를 링크 없이 텍스트만 참조 — spec README 갱신(M3) 전까지 구 번호 혼재 가능성. 잔여 리스크 보고서 §4 에서 M3 인계 이미 명시되어 있으므로 minor |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경. `.claude/agents/`, `.claude/skills/`, `.claude/settings.json` 미변경 |
| B (자동 재시도 X) | ✅ | `arm_2week_plan.md` 는 순수 마크다운 문서. `orin/lerobot/`, `dgx/lerobot/`, `pyproject.toml`, `setup_env.sh`, `deploy_*.sh`, `.gitignore` 중 어느 것도 해당 없음 |
| Coupled File Rules | ✅ | Category B 영역 변경 없으므로 Coupled File Rule 비해당 |
| 역사적 결정 보존 원칙 | ✅ | 04·05 본문 텍스트 완전 삭제 없이 HTML 주석 방식으로 정정 경위 추가 |
| 옛 룰 (docs/storage/ bash 예시) | ✅ | docs/storage/ 에 bash 명령 예시 추가 없음 |

---

## 검증 세부 내역

### A~F 결정 사항 인용 정합 확인

spec 원문 (§사용자 결정 사항 표) 대비 arm_2week_plan.md L139~L145 인용:

| 결정 | spec 원문 핵심 | arm_2week_plan.md 인용 | 정합 |
|---|---|---|---|
| A | DGX 시연장 직접 이동 — 04 "DataCollector 별도 노드" 가정 폐기 | "DGX 가 시연장 직접 이동 — 04 의 'DataCollector 별도 노드' 가정 폐기" | ✅ |
| B | SO-ARM·카메라 직결 가능. USB·dialout·v4l2 실 검증은 V1 prod | "DGX SO-ARM·카메라 USB 직결 가능 확인 (USB·dialout·v4l2 실 검증은 V1 prod)" | ✅ |
| C | 옵션 α — 단일 진입점 + flow 3 mode 분기 | "옵션 α 채택 — 단일 진입점 `bash dgx/interactive_cli/main.sh`, flow 3 단계에서 수집/학습/종료 mode 분기" | ✅ |
| D | BACKLOG #11·#12·#13 + 05 항목 "완료(불요)" 마킹 | "04 BACKLOG #11·#12·#13 + 05 미검증 항목 → '완료(불요)' 마킹 (M2 처리)" | ✅ |
| E | CLAUDE.md 4곳 정합 갱신 완료 (Phase 1 메인 직접 수정) | "CLAUDE.md 4곳 정합 갱신 완료 (Phase 1 시점 메인 직접 수정)" | ✅ |
| F | 본 spec = 06, 06_leftarmVLA → 07 시프트 등 | "본 spec 번호 = 06, 기존 06_leftarmVLA → 07 시프트" | ✅ (07~10 시프트 전체는 주요 작업에서 명시) |

### 04·05 본문 보존 확인

- 04 본문 L97~L109: 4-노드 가정 텍스트 (목표·배경·주요 작업·결정사항) 원문 그대로 보존. 삭제 없음.
- 05 본문 L115~L131: 3 노드 공통 CLI, flow 0~7 단계 등 05 결정 시점 텍스트 완전 보존.

### 마일스톤 번호 연속성

00 → 01 → 02 → 03 → 04 → 05 → **06(신규)** → 07 → 08 → 09 → 10 — 연속 확인.

---

## 배포 권장

READY_TO_SHIP — prod-test-runner 진입 권장.

단, 본 TODO 는 타입 `task` (문서 정합), prod-test-runner 의 비대화형 검증 대상 없음. orchestrator 가 바로 spec 본문 `[ ]` → `[x]` 전환 + "자동화 완료" 메모 처리 후 다음 todo (M2, M3) 진행 권장.
