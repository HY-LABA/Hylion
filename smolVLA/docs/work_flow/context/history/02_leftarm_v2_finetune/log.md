# 오케스트레이터 timeline 로그

> spec 자동화 진행 중 매 dispatch·완료·분기 이벤트마다 한 줄 추가.

2026-05-17 23:21:25 | START | spec=02_leftarm_v2_finetune, todos=4 (TODO-03-A/B/C/D), parallel_groups=3 (G1: 03A+03B task-executor 병렬; G2: code-tester + prod-test-runner; G3: 03D PHYS_REQUIRED verification_queue)
2026-05-17 23:21:26 | DISPATCH | task-executor x2 병렬 (TODO-03-A, TODO-03-B) — Group 1
2026-05-17 23:25:00 | DONE-IMPL | TODO-03-A → prof_computer/docs/orin_eval_2026-05-17.md 신규 (20 trial 시트 + 집계 + 정성 메모)
2026-05-17 23:28:30 | DONE-IMPL | TODO-03-B → orin/scripts/run_inference_leftarm_v2.sh 신규 (5 subcommand, lerobot-record 인자 코드 조사 확정) + orin/scripts/README.md 신규 (Coupled Rules §6)
2026-05-17 23:28:35 | DISPATCH | code-tester (TODO-03-A + TODO-03-B 동시 검증)
2026-05-17 23:32:00 | DONE-CODETEST | TODO-03-A verdict=READY_TO_SHIP (Critical 0, Recommended 1 — README 트리 drift BACKLOG)
2026-05-17 23:32:00 | DONE-CODETEST | TODO-03-B verdict=READY_TO_SHIP (Critical 0, Recommended 2 — README 트리 drift / n_action_steps 재확인 무해)
2026-05-17 23:32:10 | DISPATCH | prod-test-runner (TODO-03-C: Orin SSH 점검 + ckpt 다운로드 + dry-run)
2026-05-17 23:40:00 | DONE-PRODTEST | TODO-03-C verdict=FAIL — F1 lerobot_record reachy2_camera import (Category B 게이트), F2 set -u + LD_LIBRARY_PATH 충돌, F3 huggingface-cli deprecated
2026-05-17 23:40:05 | BLOCK | TODO-03-C F1 = Category B (orin/lerobot/) — 자동 재시도 X, 사용자 게이트 분기 prompt
2026-05-17 23:45:00 | USER_DECISION | F1 옵션 A (try/except wrap), F1+F2+F3 묶음 cycle 2 진행 승인
2026-05-17 23:45:05 | DISPATCH | task-executor (TODO-03-E: F1+F2+F3 fix, Category B + orin_lerobot_diff.md 갱신)
2026-05-17 23:48:00 | DONE-IMPL | TODO-03-E → lerobot_record.py (try/except wrap), run_inference_leftarm_v2.sh (LD_LIBRARY_PATH 안전망 + hf 분기), 03_orin_lerobot_diff.md (F1 entry)
2026-05-17 23:48:05 | DISPATCH | code-tester (TODO-03-E 산출물 검증)
2026-05-17 23:50:30 | DONE-CODETEST | TODO-03-E verdict=READY_TO_SHIP (Critical 0, Recommended 0)
2026-05-17 23:50:35 | DISPATCH | prod-test-runner (TODO-03-C cycle 2: 재배포 + Orin SSH 재검증)
2026-05-17 23:55:00 | DONE-PRODTEST | TODO-03-C cycle 2 verdict=FAIL — F2/F3 해소, F1 도 import 자체는 해결 but F4/F5/F6 신규 노출 (lerobot.common.control_utils / lerobot.datasets / lerobot.teleoperators.keyboard — 모두 orin trim 미포함, Category B). max 2 cycle 도달.
2026-05-17 23:55:05 | BLOCK | End-B 후보 — lerobot-record 가 inference-only trim 과 본질적 양립 불가. Phase 1 결정 (lerobot-record 경로) 의 전제 재평가 필요. 사용자 자연어 분기 prompt
2026-05-18 00:05:00 | USER_OVERRIDE | 옵션 W 선택 + 신규 entry 이름 leftarm_v2_inference.py (hil_inference.py 갱신 X, 마일스톤별 분리)
2026-05-18 00:05:05 | DISPATCH | task-executor (TODO-03-F: leftarm_v2_inference.py 신규 작성 + wrapper 재조정)
2026-05-18 00:15:00 | DONE-IMPL | TODO-03-F → leftarm_v2_inference.py 신규 (hil_inference + lego_v1_inference 패턴 + PEFT LoRA 로드 factory.py:537-558 패턴) + wrapper 재조정 (lerobot-record → leftarm_v2_inference.py) + orin/inference/README 갱신
2026-05-18 00:15:05 | BLOCKER_DETECTED | peft 미설치 (Orin SSH 확인) — orin/pyproject.toml 추가는 Category B+C, prod-test 진입 전 사용자 동의 필요
2026-05-18 00:15:10 | DISPATCH | code-tester (TODO-03-F 산출물 검증)
2026-05-18 00:17:30 | DONE-CODETEST | TODO-03-F verdict=READY_TO_SHIP (Critical 0, Recommended 1). peft BLOCKER 잔존 (Category B+C, 사용자 동의 prompt)
2026-05-18 00:20:00 | USER_DECISION | peft 추가 옵션 1 (pyproject + setup_env 정식 갱신) 승인
2026-05-18 00:20:05 | DISPATCH | task-executor (TODO-03-G: peft 의존성 정식 추가 — pyproject + setup_env + pyproject_diff.md)
2026-05-18 00:22:30 | DONE-IMPL | TODO-03-G → 분기 B 확정 (peft 는 upstream smolvla extra 미포함, 별도 peft-dep). orin/pyproject.toml smolvla extra 에 peft>=0.18.0,<1.0.0 추가 + setup_env.sh §6-b peft import 검증 + 02_orin_pyproject_diff.md entry. Coupled Rules §1·§2 충족
2026-05-18 00:22:35 | DISPATCH | code-tester (TODO-03-G 산출물 검증)
2026-05-18 00:25:00 | DONE-CODETEST | TODO-03-G verdict=READY_TO_SHIP (Critical 0). Coupled Rules §1·§2 충족
2026-05-18 00:25:05 | DISPATCH | prod-test-runner (TODO-03-C cycle 3 + 03-F + 03-G 통합 검증: 재배포 + peft install + leftarm_v2_inference 동작)
2026-05-18 00:31:00 | DONE-PRODTEST | TODO-03-C cycle 3 verdict=NEEDS_USER_VERIFICATION — 자동 검증 모두 통과 (peft 0.19.1, LoRA 로드 OK, import smoke OK, dry-run 환경 의존만), PHYS_REQUIRED (cameras/ports null + 20 trial live) Phase 3 위임
2026-05-18 00:31:05 | PHASE2_DONE | spec 02 TODO-03 all sub-steps 완료 (03-A/B/C/E/F/G READY 또는 NEEDS_USER_VERIFICATION) — End-A 도달
2026-05-18 00:45:00 | AD_HOC_DEFECT | 사용자 시연장 진입 직전 발견 — leftarm_v2_inference.py 가 top 카메라의 rotation=-90 (수집 시 적용) 처리 X. cameras.json schema 도 rotation 필드 부재. 학습/추론 정합 깨짐 → 본 사이클 DOD 전제 미충족. 즉시 fix 필요 (사용자 yes)
2026-05-18 00:45:05 | DISPATCH | task-executor (TODO-03-H: rotation 정합 복원 — leftarm_v2_inference.py + cameras.json schema)
2026-05-18 00:48:30 | DONE-IMPL | TODO-03-H → cameras.json schema 확장 + apply_gate_config 파라미터 추출 + OpenCVCameraConfig slot별 적용. base_config.yaml 정확값: top(-90/480x640/MJPG), wrist(0/640x480/MJPG). wrapper 변경 불요
2026-05-18 00:48:35 | DISPATCH | code-tester (TODO-03-H 산출물 검증)
2026-05-18 00:50:30 | DONE-CODETEST | TODO-03-H verdict=READY_TO_SHIP (Critical 0, Recommended 0)
2026-05-18 00:50:35 | DISPATCH | prod-test-runner (TODO-03-H cycle: 빠른 재배포 + import smoke — 사용자 시연장 대기 모드)
2026-05-18 00:53:00 | DONE-PRODTEST | TODO-03-H verdict=NEEDS_USER_VERIFICATION — 재배포 OK, import smoke OK, rotation -90→ROTATE_270 enum 변환 OK. cameras.json index null 유지 (사용자 시연장 채움 대기)
2026-05-18 00:53:05 | PHASE2_DONE_v2 | TODO-03 all sub-steps (03-A/B/C/E/F/G/H) 완료 — rotation 정합 복원 포함. End-A 도달 (재). Phase 3 진입
2026-05-18 01:30:00 | PHASE3_USER_ACTION | 사용자 시연장 진행 — cameras.json/ports.json 채움, DGX cal (leftarm_test_follower.json) transfer (ad-hoc), max-steps 500→1000 (Orin wrapper 한 줄 sed)
2026-05-18 01:35:00 | PHASE3_LIVE | task1 #1 front (500 step): ❌ 잡기 실패 (헛스윙). task2 #1 front (1000 step): ❌ 동작 불완전 (캔 방향 이동만)
2026-05-18 01:40:00 | USER_DECISION | 단축 결정 — 정량 평가 무의미 결론, 학습 방법 + 데이터셋 재정렬 진입. 본 사이클 0-20% 분기 확정 (전체 0/2 = 0%)
2026-05-18 01:45:00 | VERIFY_RESULT | passed=[1,4] partial=[2,3 단축] failed=[] action=PHASE3_COMPLETE (DOD d 충족 — 재정렬 분기 결정이 본 사이클 목표)
2026-05-18 01:45:05 | PHASE3_COMPLETE | spec 02 TODO-03 최종 완료. /wrap-spec 권장
