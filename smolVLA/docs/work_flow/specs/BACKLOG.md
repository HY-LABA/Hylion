# Backlog

> **구현 차원 잔여 자료** — 코드·spec·테스트 미해결 항목. 사이클 간 누적 (spec 마다 별도 섹션 추가).
> orchestrator·prod-test-runner 가 자동 누적. 다음 spec 작성 시 메인 Claude 가 우선순위 검토.
> 정책: `/CLAUDE.md` § 가시화 레이어, `README.md` § BACKLOG·ANOMALIES 관리 정책.

> **2026-05-14 fresh start**: 구 `arm_2week_plan` era 의 BACKLOG 기록은 → [`docs/storage/legacy/arm_2week_plan/BACKLOG.md`](../../storage/legacy/arm_2week_plan/BACKLOG.md) 로 이관. 본 파일은 `realplaying.md` 로드맵 기준으로 새로 누적한다. 워커가 풀리지 않는 문제를 만났을 때 옛 era 의 유사 미해결 항목을 참조할 필요가 있으면 위 legacy 파일 확인.

---

## [pre-spec — devPC↔DGX 동기화 작업 중 발견]

| # | 항목 | 발견 출처 | 우선순위 | 상태 |
|---|------|-----------|----------|------|
| 1 | `scripts/deploy_orin.sh` 의 `--delete` rsync 가 `orin/checkpoints/`·`orin/config/*.json` 을 exclude 하지 않음 — 현재 실행 시 ① Orin 의 실 체크포인트 삭제 (repo 엔 `checkpoints/README.md` 만 존재), ② Orin 의 실 포트·카메라 설정을 repo 의 null placeholder 로 덮어씀. `orin-deploy-procedure` SKILL.md (07 reflection #6) 가 명시한 exclude 가 스크립트에 미반영 (스킬↔스크립트 불일치). 수정안: `--exclude 'checkpoints/' --exclude 'config/*.json'` 추가. 단 `deploy_orin.sh` 는 Category B 영역. (참고: `deploy_dgx.sh` 의 `gestures/*/` 동일 유형 빵꾸는 2026-05-14 즉시 수정 완료) | 2026-05-14 deploy 스크립트 점검 | 높음 | 미완 — 사용자 결정으로 BACKLOG 보류 |

## [M1.5 작성 — 네비게이터·참조 drift 점검]

> 2026-05-15 사용자 지적 → 메인 점검 결과. CLAUDE.md Coupled Rules §6 (M1.5 reflection 도출) 으로 향후 자동 누락 차단 룰 정착됐으나, 기존 drift 는 별도 정리 필요.

| # | 항목 | 발견 출처 | 우선순위 | 상태 |
|---|------|-----------|----------|------|
| 2 | `docs/storage/08_dgx_structure.md` 본문 drift — 04 사이클 시점 본문 그대로 + 상단 ⚠️ 박스로만 정정 누적 (`runs/`·`tests/`·`interactive_cli/`·`config/` 삭제·`outputs/<run>` flat 컨벤션 통일 등). 본문 정정으로 통합 필요. | 2026-05-15 메인 점검 | 중간 | 미완 |
| 3 | `docs/storage/07_orin_structure.md` 본문 drift — 동일 패턴 (확인 필요) | 2026-05-15 메인 점검 | 중간 | 미완 |
| 4 | `dgx/docs/finetune/README.md` 부재 — `camera_and_codec.md`, `backlog.md`, `leftarm_v1/`, `leftarm_v2/` 등 인덱스 없음. 새 사용자가 finetune 운영 문서 trail 모름 | 2026-05-15 메인 점검 | 중간 | 미완 |
| 5 | `dgx/docs/finetune/leftarm_v2/README.md` 부재 — `collection_log.md`, `training_log.md`, `model_config.md` 인덱스 없음. era 안에서 어느 문서가 정본인지 안내 부재 | 2026-05-15 메인 점검 | 중간 | 미완 |
| 6 | `docs/work_flow/specs/README.md` 의 spec 목록이 자동 ls 형식 아님 — 현재 본문은 spec 작성 가이드 + 정책. 새 spec (02_prereq 등) 등록 누락 가능성 — 자동 ls 형식 도입 또는 매 spec 신설 시 본문 갱신 정책 결정 필요 | 2026-05-15 메인 점검 | 낮음 | 미완 |
