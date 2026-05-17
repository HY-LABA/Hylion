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

## [02_prereq_dataset_video_to_image — wrap 시 연기 항목]

> 본 spec 의 verification_queue 항목 중 사용자 결정 (2026-05-16 /wrap-spec) 으로 *연기* 처리된 항목. 다음 사이클에서 트리거 도래 시 재진입.

| # | 항목 | 트리거 | 우선순위 | 상태 |
|---|------|--------|----------|------|
| 7 | TODO-02 — DGX 110ep 변환 실행 + 디스크 사용량 측정 + LeRobotDataset 로드 smoke. 변환 자동화 (스크립트 작성·deploy·dry-run skip) 까지는 완료. 사용자가 학습 종료 후 `nohup python finetune/leftarm_v2/convert_to_image.py ... &` 백그라운드 실행 시작 (또는 시작 예정). 결과 보고 대기. | DGX 110ep 변환 완료 후 사용자 결과 보고 (성공/실패, 디스크 사용량, smoke 결과) | 중간 (다음 사이클 진입 시 즉시 처리) | 미완 (사용자 PHYS_REQUIRED 진행 중) |
| 8 | TODO-03 — image dataset 으로 train_config 갱신 + 시도 4 학습 진입 (첫 1000 step ckpt 도달 + OOM 없음 + wandb 기록). best practice 보고서 §7 권장 (bfloat16 명시) 적용 검토 포함. | TODO-02 완료 보고 후 (#7 트리거 도래) | 중간 | 미완 |

## [02_leftarm_v2_finetune (TODO-03 사이클) — code-tester Recommended 항목]

> 2026-05-17 code-tester 가 READY_TO_SHIP verdict 와 함께 발견. 본 사이클 강제 의무 아님 — 기존 *README 트리 drift* 의 연장. M1.5 Coupled Rules §6 일관 적용 대상.

| # | 항목 | 발견 출처 | 우선순위 | 상태 |
|---|------|-----------|----------|------|
| 9 | `prof_computer/README.md` 트리에 신규 `docs/orin_a2_eval_2026-05-17.md` 미등록 (기존 docs 인덱스 부재 연장 — M1.5 reflection §6 본문 정정 의무 일관 적용). 추후 `prof_computer/docs/README.md` 신설 또는 `prof_computer/README.md` 의 docs/ 섹션 정정. | 2026-05-17 code-tester TODO-03-A | 낮음 | 미완 |
| 10 | `orin/README.md` 트리에 신규 `scripts/run_inference_leftarm_v2.sh` 미등록 (기존 scripts/ 섹션 drift 연장 — `orin/scripts/README.md` 는 신설했으나 `orin/README.md` 본문은 미갱신). | 2026-05-17 code-tester TODO-03-B | 낮음 | 미완 |
| 11 | [ad-hoc] rotation 정합 복원 — `orin/inference/leftarm_v2_inference.py` 의 `OpenCVCameraConfig` 생성 시 rotation/width/height 누락 → 추론이 수집 분포와 불일치 (top: 640x480 NO_ROTATION ≠ 480x640 CCW90). `cameras.json` schema 확장 (rotation/width/height/fps/fourcc 추가) + `apply_gate_config` 파라미터 추출 + `OpenCVCameraConfig` 생성부 slot별 파라미터 적용으로 수정 완료 (TODO-03-H 2026-05-18). | 2026-05-18 시연장 직전 ad-hoc 발견 → 즉시 fix | 높음 | 완료 |
| 12 | [ad-hoc] DGX cal 파일 (`leftarm_test_follower.json`) → Orin lerobot 캐시로 transfer + `leftarm_v2_inference.py` line 387 의 `--follower-id` default `hylion_follower` → `leftarm_test_follower` 로 수정 (수집 시 base_config.yaml robot.id 와 정합). 시연장에서 사용자가 발견 (cal 프롬프트 무한 hang). 메인이 SSH 로 즉시 transfer + Edit + scp 재배포. devPC ↔ Orin 정합 유지. | 2026-05-18 시연장 ad-hoc | 중간 | 완료 |
| 13 | [ad-hoc] `orin/scripts/run_inference_leftarm_v2.sh` line 254 `--max-steps 50` 을 Orin 에서 *직접 sed* 로 500 → 1000 으로 임시 변경 (시연장 단축 trial). devPC 의 wrapper 는 *기존 500 그대로* — Orin ↔ devPC 비동기 상태. 다음 사이클에서 *학습 방법 점검 후 적정 max-steps 결정* 시 정식 동기화 (env 패턴 또는 default 값 정합). | 2026-05-18 시연장 ad-hoc | 중간 | 미완 (다음 사이클 정식 처리) |
| 14 | task1·task2 *단축 결과 (0/2 = 0%)* → 본 사이클 인프라 검증 (Orin SSH·deploy·lerobot trim·LoRA 로드·cal·rotation·camera config) 모두 *작동* 확인. **다음 사이클은 데이터·학습 방법 만 결정**. 4개 영역: (1) 학습 방법 (LoRA r·target·dropout / VLM trainable / epoch / lr·scheduler·batch), (2) 데이터셋 확장 (M1 잔여 100ep + 다른 사람 + orientation 5:5 균형 + 위치 분포), (3) 학습 노드 (prof_computer vs DGX 재시도), (4) 검증 시점 패턴 (정성 + 정량). | 2026-05-18 Phase 3 결과 | 높음 | 다음 사이클 Phase 1 의 핵심 입력 |
