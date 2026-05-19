# 오케스트레이터 timeline 로그 — 03_leftarm_v2_eval_003_branch

> spec 자동화 진행 중 매 dispatch·완료·분기 이벤트마다 한 줄 추가.

2026-05-19 17:30:00 | START    | spec=03_leftarm_v2_eval_003_branch, todos=5, parallel_groups=3, awaits_user=1 (TODO-05)
2026-05-19 17:30:30 | PLAN     | planner verdict: TODO-01·02 병렬 (Group 1) → TODO-03 직렬 (Group 2, PHYS_REQUIRED) → TODO-04 직렬 (Group 3). TODO-05 awaits_user 해소 후 단독 dispatch
2026-05-19 17:31:00 | TASKREG  | TaskCreate ×5 등록 완료 (TODO-01 ~ TODO-05)
2026-05-19 17:31:30 | USER     | TODO-05 선택지 답 보류 + 사용자 우선순위 코멘트: "Orin 모터 점검부터 시작" → TODO-02 우선 dispatch 사용자 의도 확인
2026-05-19 17:32:00 | USER     | 사용자 = 시연장 현장. TODO-02 (SSH_AUTO) + TODO-03 (PHYS_REQUIRED) 단일 세션 연속 진행 결정. TODO-05 후속 (TODO-03 종료 후) 결정
2026-05-19 17:32:30 | DISPATCH | Group 1 병렬 진입 — task-executor ×2 (TODO-01 prof_computer + TODO-02 Orin) 동시 호출
2026-05-19 17:37:20 | DONE     | TODO-01 task-executor 완료 — learning_log §003 entry + M1.5/002/003 비교 표. wandb 일부 metric `[wandb run 40kzxlmq 확인]` 마커 (devPC wandb 미설치) → code-tester 진입
2026-05-19 17:37:30 | DISPATCH | TODO-01 code-tester 호출
2026-05-19 17:38:30 | DONE     | TODO-02 task-executor 완료 — devPC 측 모두 완료 (HF 원격 검증 + wrapper 분석 + 003_eval 시트 신설). Orin SSH 차단 (devPC ↔ Orin 도달 X, 시연장 LAN 분리) → ckpt 다운로드·smoke 는 사용자 시연장 위임
2026-05-19 17:38:40 | NOTE     | TODO-02 의 SSH_AUTO 영역이 *환경 차단으로 PHYS_REQUIRED 와 합쳐짐* — verification_queue 등록 + 사용자 안내
2026-05-19 17:39:00 | DISPATCH | TODO-02 code-tester 호출 (devPC 측 산출물 검증만, SSH smoke 는 사용자 위임)
2026-05-19 17:39:40 | DONE     | TODO-01 code-tester 완료 — Verdict: READY_TO_SHIP. wandb 마커 처리 합리적, HF Hub 독립 재검증 통과, Hard Constraints 4 카테고리 통과
2026-05-19 17:39:50 | DISPATCH | TODO-01 prod-test-runner 호출 (AUTO_LOCAL — learning_log §003 형식·HF Hub repo sanity)
2026-05-19 17:42:30 | DONE     | TODO-02 code-tester 완료 — Verdict: READY_TO_SHIP. Critical 0, Recommended 1 (trial 헤더 일관성, 영향 없음). 4축 모두 통과
2026-05-19 17:42:40 | DISPATCH | TODO-02 prod-test-runner 호출 (AUTO_LOCAL devPC 산출 + NEEDS_USER_VERIFICATION Orin 시연장 위임 복합)
2026-05-19 17:45:00 | DONE     | TODO-01 prod-test-runner 완료 — Verdict: AUTOMATED_PASS. HF Hub 재검증 (siblings 10, empty_cameras=1, n_action_steps=50, r=16, steps=120000, batch=6) 전항목 통과
2026-05-19 17:45:10 | COMPLETE | TODO-01 자동화 완료 — TaskUpdate #1 completed, spec 본문 마킹
2026-05-19 17:47:30 | DONE     | TODO-02 prod-test-runner 완료 — Verdict: NEEDS_USER_VERIFICATION. AUTO_LOCAL 9/9 통과. verification_queue 에 TODO-02 + TODO-03 등록
2026-05-19 17:47:40 | DISPATCH | Group 2 진입 — TODO-03 PHYS_REQUIRED 사용자 시연장 위임 (TaskUpdate #3 in_progress, 사용자 명령 시퀀스 안내)
2026-05-19 19:15:00 | AD_HOC   | ~/.ssh/config 갱신 — SSID 기반 → ping 도달성 기반 자동 분기 (사용자 환경 SSID ↔ Orin IP 매핑 깨짐 해결). ssh orin / orin-hy / orin-edu 3종 alias 작동
2026-05-19 19:17:40 | DONE     | TODO-02 사용자 검증 통과 — ssh orin 작동, ckpt 46.2MB download, dry-run smoke (empty_cameras 패치 자동 적용 로그 + 6-joint action) 정상. spec [x] 최종 마킹
2026-05-19 19:30:00 | DONE     | TODO-03 사용자 검증 통과 — 단축 7 trial / 7 success = 100% (M1.5·002 의 0/2 = 0% 대비 +100%p 도약). 학습 분포 외 perturbation (로봇 각도·캔 mass) 도 견딤. spec [x] 최종 마킹
2026-05-19 19:30:30 | DONE     | TODO-04 진행 — 003_eval_2026-05-19.md 결과 채움 + learning_log §003 추론 평가 결과 메모 갱신 완료
2026-05-19 19:31:00 | USER     | TODO-05 사용자 결정 = 선택지 1 (현 상태 + 정책 문서). awaits_user 해소
2026-05-19 19:31:30 | DONE     | TODO-05 완료 — docs/storage/09_orin_config_policy.md 신설. 코드 변경 0
2026-05-19 19:32:00 | PHASE2_DONE | 모든 todo verdict ∈ {AUTOMATED_PASS, PASSED} — End-A 성공. /wrap-spec 진입 안내
2026-05-19 19:38:00 | UPDATE   | TODO-03 추가 trial 1회 (사용자 보고) — task2 back, 로봇 각도 + 조명 50% 감소 (다중 perturbation), 성공. 7/7 → 8/8 = 100%. 003_eval / learning_log / verification_queue / spec 모두 갱신
