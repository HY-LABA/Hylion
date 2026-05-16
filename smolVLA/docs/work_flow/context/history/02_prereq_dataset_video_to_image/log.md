# 오케스트레이터 timeline 로그

> spec 자동화 진행 중 매 dispatch·완료·분기 이벤트마다 한 줄 추가.

2026-05-15 | START | spec=02_prereq_dataset_video_to_image, todos=3, parallel_groups=1 (Group 1 단일 노드 — Group 2-A/3 은 verdict 게이트 후 직렬)
2026-05-15 | DISPATCH | TODO-01 → researcher (산출: context/research/m1.5_video_decode_oom.md)
2026-05-15 | RESEARCHER_RETURN | verdict=NEEDS_INVESTIGATION (실험 A cleanup 강화 먼저 권장; 핵심증거: video_utils.py stream.close() 누락 + streaming_dataset torchcodec 전용)
2026-05-15 | ORCHESTRATOR_RECOVERY | researcher 가 Write 미이행 → 메인이 보고서 파일 직접 Write 복구
2026-05-15 | GATE | verdict ≠ NO_BLOCKER → 사용자 결정 필요. TODO-02·03 dispatch 보류
2026-05-15 | USER_DECISION | 실험 A + 실험 B 모두 시도 채택 → TODO-1a/1b 신설, TODO-02·03 보류 상태로 plan 갱신
2026-05-15 | PLANNER_RECALL | plan.md 갱신 (분기 B confirm, TODO-1a/1b 신설, TODO-02·03 보류, ORCHESTRATOR_GAP 재발 차단 지침)
2026-05-15 | DISPATCH | TODO-1a → task-executor (산출: experiments/cleanup_helper.sh + exp_a_cleanup_attempt3.md + training_log.md 시도 3 양식)
2026-05-15 | TASK_EXECUTOR_RETURN | TODO-1a 3 파일 작성 + dgx/finetune/README.md Coupled Rule §6 갱신
2026-05-15 | CODE_TESTER_VERDICT | TODO-1a = READY_TO_SHIP (Recommended 2건: 90GB 강한 신호 메모, pkill 범위 안내)
2026-05-15 | ORCHESTRATOR_EDIT | Recommended 2건 즉석 수정 (walkthrough 정책 — 단일 파일 1~30줄, 회귀 위험 낮음)
2026-05-15 | DISPATCH | TODO-1a → prod-test-runner (SSH_AUTO dgx 검증)
2026-05-15 | PROD_TEST_VERDICT | TODO-1a = NEEDS_USER_VERIFICATION (deploy OK, SSH 5/5 OK, dry-run exit 0, DGX baseline 112Gi available)
2026-05-15 | TODO_DONE | TODO-1a 자동화 완료, Phase 3 PHYS_REQUIRED 대기 (사용자 실험 A 학습 진입)
2026-05-16 | USER_PHASE3_REPORT | 실험 A 시도 시 학습 시작 단계에서 torchcodec ABI crash (cleanup 단계 영향 X). traceback: undefined symbol torch_dtype_float4_e2m1fn_x2 / libavutil.so.{56-60} 모두 미스매치
2026-05-16 | DIAG | DGX 환경: torch 2.10.0+cu130, torchcodec 0.11.1, ffmpeg 6.1.1 (libavutil.so.58 only), pyav 15.1.0, lerobot 0.5.2 editable. train_config.yaml 에 video_backend 명시 없음 → lerobot default get_safe_default_codec() 가 torchcodec 자동 선택
2026-05-16 | ANOMALIES_ADD | #2 SKILL_GAP (researcher backend 자동 선택 로직·환경 진단 빈틈), #3 CONSTRAINT_AMBIGUITY (시도 1·2 의 실제 backend 미기록)
2026-05-16 | NEW_TODO | TODO-1a-fix 신설 — video_backend=pyav 강제 적용 (train_config.yaml + run_train.py)
2026-05-16 | DISPATCH | TODO-1a-fix → task-executor (산출: train_config.yaml L37, run_train.py L89·L121, training_log.md L232-268)
2026-05-16 | TASK_EXECUTOR_RETURN | 3 파일 수정, YAML+AST 통과, Cat A/B/D 위반 없음
2026-05-16 | CODE_TESTER_VERDICT | TODO-1a-fix = READY_TO_SHIP (라인 정합성 100%, Recommended: pre-existing ruff E731 무관)
2026-05-16 | DISPATCH | TODO-1a-fix → prod-test-runner (deploy + dry-run cmd 검증)
2026-05-16 | PROD_TEST_VERDICT | TODO-1a-fix = NEEDS_USER_VERIFICATION (deploy OK, 자동 검증 7/7, dry-run cmd 에 --dataset.video_backend=pyav 포함, torchcodec traceback 없음)
2026-05-16 | TODO_DONE | TODO-1a-fix 자동화 완료, Phase 3 PHYS_REQUIRED 대기 (사용자 실험 A *재시도*)
2026-05-16 10:58 | USER_PHASE3_START | 시도 3 학습 진입 (pyav backend, cleanup 없음, baseline MemAvailable 59 GiB)
2026-05-16 | WRAP_HOLD | 사용자 /wrap-spec 호출 → verification_queue 미처리 2건 (TODO-1a, TODO-1a-fix) 처리 결정 prompt → "학습 결과 대기" 선택. wrap-spec 보류, 학습 결과 보고 후 재호출 예정
2026-05-16 11:44 | DIAG | 학습 step 337 / 45:40, MemAvailable 9.7 GiB (-49 GiB), 누수율 1.07 GB/min (시도 1·2 와 같은 수준 1.25 GB/min). loss 0.71→0.32 정상. process RSS 안정 (main 2.89GB / workers 1.5-1.6GB). 누수는 process 외부 (libav OS buffer 또는 shmem)
2026-05-16 | DIAG_CONCLUSION | backend 변수 분리 완료 — torchcodec/pyav 둘 다 누수. workers 변수도 process RSS 안정으로 사실상 분리 (실험 B 의 데이터 진단 의미 사라짐). 근본 해법 = image 변환 (researcher §5 옵션 3 confirm)
2026-05-16 | USER_DECISION | "OOM 까지 두고 image 변환 진입" 선택. TODO-1b 폐기, TODO-02·03 활성화
2026-05-16 | TASK_UPDATE | task #5 (TODO-1b) deleted, task #2 (TODO-02) blocked 해제 + in_progress 준비 (사용자 OOM 보고 받은 후 dispatch)
2026-05-16 | PLANNER_RECALL | plan.md 갱신 (Group 2-EXP-B 폐기, Group 2-A·3 활성화, lerobot image dataset 형식 조사 결과 plan 에 반영)
2026-05-16 | DISPATCH | TODO-02 → task-executor (산출: convert_to_image.py + convert_to_image.md + dgx/finetune/README.md)
2026-05-16 | TASK_EXECUTOR_RETURN | TODO-02 cycle 1: 353 lines, ffmpeg subprocess 방식으로 leak 격리 설계
2026-05-16 | CODE_TESTER_VERDICT | TODO-02 cycle 1 = MAJOR_REVISIONS (Critical: parquet image 컬럼 미포함)
2026-05-16 | TASK_EXECUTOR_RETURN | TODO-02 cycle 2: rewrite_data_parquet 전면 재작성 (Dataset.from_dict + Image() + embed_images + to_parquet), total_frames 갱신, source==target 가드
2026-05-16 | CODE_TESTER_VERDICT | TODO-02 cycle 2 = READY_TO_SHIP (Critical + Recommended 2건 해결, 신규 non-blocking 1건)
2026-05-16 | DGX_LEARNING_RECOVERY | 학습 OOM 회복 — 11:56 MemAvailable 151 MiB → 12:11 34 GiB. 누군가 외부 정리 또는 kernel reclaim. step 472 진행 중, ETA 41h
2026-05-16 | PROD_TEST_VERDICT | TODO-02 = NEEDS_USER_VERIFICATION (deploy OK, DGX AST·--help·ffmpeg·디스크 3.3T 가용 모두 통과, dry-run skip — 학습 메모리 압박 28GiB<30GiB 기준선, 실제 변환 학습 종료 후)
2026-05-16 | TODO_DONE | TODO-02 자동화 완료, Phase 3 PHYS_REQUIRED/SSH_AUTO 대기 (사용자 변환 110ep)
2026-05-16 | IDLE_TASK | researcher 호출 (사용자 유휴 시간 활용) → 보고서 `context/research/lerobot_smolvla_training_best_practice.md` (485 lines). 핵심 발견: (1) bfloat16 미명시 → FP32 가능성 즉시 수정 권장, (2) LoRA LR 공식 권장 1e-3 vs 우리 1e-4, (3) n_action_steps Hub config.json 함정 (inference 시 1→50)
2026-05-16 14:21 | DIAG | 학습 상태 확인 — wandb API 직접 호출로 system metric 확보. GPU 0%/5W/38°C, system memory 99.99%, proc.memory.availableMB 12MB. dataloader bottleneck + 메모리 압박으로 GPU idle (학습 사실상 정지). step 808/20000 (4%), step_time 577.70s (9.6분), loss 0.71→0.21 정상. 첫 ckpt 미도달, 16시간+ 추가 필요 추정
2026-05-16 14:24 | USER_PHASE3_END | 사용자 Ctrl+C 로 학습 kill. main+workers 종료, MemAvailable 115 GiB 회수. OOM 자체는 발생 안 함 (kernel reclaim 으로 swap-less UMA 환경에서 무한 thrashing 도달)
2026-05-16 | TRAINING_LOG_UPDATE | dgx/docs/finetune/leftarm_v2/training_log.md 시도 3 entry 자동 채움 (메인 약속 이행) — 시도 1·2 와 변수 비교 표 + 메모리 회복 사이클 분석 + 진단 결론 + 잔여 미해결
