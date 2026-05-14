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
