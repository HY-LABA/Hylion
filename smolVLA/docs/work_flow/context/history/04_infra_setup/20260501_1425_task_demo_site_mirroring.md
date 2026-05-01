# TODO-M1 — 시연장 미러링 가이드 작성 (history)

> 작성: 2026-05-01 14:25 | task-executor | cycle: 1

## 요약

`docs/storage/10_demo_site_mirroring.md` 신규 작성 완료.
시연장 환경을 DataCollector 인근에 재현하기 위한 절차·체크리스트 문서.
사용자 결정 (육안+사진 비교, 자동 검증 BACKLOG) 반영.
BACKLOG 03 #15·#16 연계 명시.

## 산출물

- `docs/storage/10_demo_site_mirroring.md` — 신규 작성 (246줄)
  - §1 시연장 환경 측정 항목 (책상·작업영역·조명·top카메라·wrist카메라·토르소)
  - §2 측정 도구 (줄자·스마트폰·조도계 앱 등)
  - §3 DataCollector 측 재현 체크리스트 (책상/조명/top카메라/wrist카메라/토르소/포트/카메라인덱스)
  - §4 미러링 검증 방법 (육안+사진 비교 절차 + 합격 기준 + 자동 검증 BACKLOG)
  - §5 05_leftarmVLA 진입 전 점검 항목 (환경미러링/하드웨어/소프트웨어 3개 게이트)

## 핵심 결정 반영

- 검증 방식: 육안 + 사진 비교 (사용자 답 E, 2026-05-01 14:25)
- 자동 검증 스크립트: BACKLOG 04 로 명시 (§4 끝)
- 사용자 책임 영역: §1 측정, §2 도구 준비, §3 재현, §4 사진 비교 모두 사용자 직접
- 자동화 가능 영역: §5 lerobot-record dry-run (DataCollector 환경 셋업 후)

## 잔여 리스크

- 시연장 접근 가능성 — 사용자 일정에 따라 측정 시점 조정 필요 (§0 에 명시)
- BACKLOG 03 #15 (카메라 인덱스 발견) · #16 (wrist flip) 미해결 — §3·§5 에 명시하고 TODO-G1/G3 연결
