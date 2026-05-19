# Anomalies — 하네스 발전 단서

> 하네스 차단·이상 패턴 누적. spec 별 섹션. 사이클 종료 시 reflection 에이전트가 본 파일을 분석하여 skill·hook·CLAUDE.md 갱신 제안 도출.
>
> **`BACKLOG.md` 와의 차이**: BACKLOG = 구현 차원 잔여. ANOMALIES = 시스템(하네스) 차원 잔여.
>
> 자세한 정책은 `/CLAUDE.md` § Hard Constraints / 가시화 레이어 참조.

> **2026-05-14 fresh start**: 구 `arm_2week_plan` era 의 ANOMALIES 기록은 → [`docs/storage/legacy/arm_2week_plan/ANOMALIES.md`](../../storage/legacy/arm_2week_plan/ANOMALIES.md) 로 이관. 본 파일은 `realplaying.md` 로드맵 기준으로 새로 누적한다. 워커가 풀리지 않는 하네스 문제를 만났을 때 옛 era 의 유사 이상 패턴을 참조할 필요가 있으면 위 legacy 파일 확인. (아래 TYPE·처리상태·형식·누적정책은 워크플로우 참조 스키마 — era 무관하게 유지.)

## TYPE 정의

| TYPE | 의미 |
|---|---|
| `HOOK_BLOCK` | PreToolUse hook 이 워커 도구 호출 차단 (Category A 영역 수정 시도) |
| `MAJOR_RETRY` | code-tester 가 같은 todo 에 MAJOR_REVISIONS 반복 발급 |
| `AWAITS_USER_DELAY` | awaits_user 항목이 N 분 이상 정지 |
| `PROD_TEST_FAIL` | prod-test-runner FAIL verdict 발급 |
| `USER_OVERRIDE` | 사용자가 자연어로 자동화 흐름 수정 (planner·orchestrator 결정 무효화) |
| `SKILL_GAP` | code-tester / planner 가 "관련 skill 없음, 추측 진행" 판단 |
| `CONSTRAINT_AMBIGUITY` | Hard Constraints 가 모호하여 워커가 판단 보류 |
| `DEPLOY_ROLLBACK` | prod-test 후 사용자 검증에서 롤백 결정 |
| `ORCHESTRATOR_GAP` | orchestrator 가 plan 의 dispatch 또는 후처리 (spec 본문 갱신·verdict 추적) 를 누락 |
| `GPU_IDLE_THRASHING` | 학습 중 GPU utilization 0% + system_memory ≥ 99% 동시 발생 → kernel reclaim thrashing. swap-less UMA 환경 (DGX Spark 등) 에서 OOM kill 전 발생하는 무한 대기 상태. wandb system metric (`system.gpu.0.gpu`, `system.memory_percent`) 에서 조기 감지 가능. M1.5 (2026-05-16) 신규 정의. |

## 처리 상태 정의

- `미처리` — 사이클 진행 중
- `reflection 분석됨` — 사이클 종료 후 reflector 가 봤음
- `갱신 적용` — 사용자 승인하여 skill/hook/CLAUDE.md 갱신됨
- `무시됨` — 사용자가 처리 안 하기로 결정

## 형식

각 spec 섹션:

```
| # | 시각 | TYPE | source | details | 처리 상태 |
|---|------|------|--------|---------|-----------|
```

- `시각`: `YYYY-MM-DD HH:MM`
- `source`: 신호 발생 주체 (예: `task-executor:O3`, `hook:PreToolUse`)
- `details`: 한 줄 요약 (구체 파일·verdict 등)

## 누적 정책

| 누가 | 언제 |
|---|---|
| PreToolUse hook | Category A 차단 시 즉시 |
| orchestrator | MAJOR_RETRY, AWAITS_USER_DELAY, USER_OVERRIDE, DEPLOY_ROLLBACK, ORCHESTRATOR_GAP 발생 시 (자기 발견 또는 사용자 지적) |
| prod-test-runner | PROD_TEST_FAIL verdict 발급 시 |
| code-tester / planner | SKILL_GAP, CONSTRAINT_AMBIGUITY 판단 시 |

---

## [02_prereq_dataset_video_to_image]

| # | 시각 | TYPE | source | details | 처리 상태 |
|---|------|------|--------|---------|-----------|
| 1 | 2026-05-15 | ORCHESTRATOR_GAP | researcher (agent) | researcher 에이전트가 산출 경로 `docs/work_flow/context/research/m1.5_video_decode_oom.md` 로 Write 하지 않고 텍스트로만 반환. 메인이 사후 직접 Write 복구. 원인 가설: (a) dispatch 프롬프트의 "산출 위치" 표현이 명시 강도 부족, (b) researcher.md §출력 규약 강도 부족. reflection 분석 대상 — agent 정의 또는 dispatch 룰 보강 검토. | 갱신 적용 (researcher.md §6 Write 의무 절 추가) |
| 2 | 2026-05-16 | SKILL_GAP | researcher (agent) + orchestrator | researcher 보고서 §1·§3 가 *lerobot 의 backend 자동 선택 로직* (`get_safe_default_codec` → torchcodec 우선) 과 *config 의 video_backend 미명시 시 default 동작* 을 빠뜨림. §3 의 pyav close 패턴 분석은 실제 환경에서 *호출되지 않는 경로* 분석. 사용자 실험 A 시도 시 torchcodec ABI 미스매치 (`undefined symbol: torch_dtype_float4_e2m1fn_x2`, PyTorch 2.10.0+cu130 vs torchcodec 0.11.1 FFmpeg6 wheel) 로 dataloader 첫 배치 fetch 단계에서 즉시 crash 발견. 추가로 메인의 researcher dispatch 가 *DGX 실 환경 버전 직접 진단* (PyTorch/torchcodec/FFmpeg 버전, libavutil.so 시스템 상태) 을 의무화하지 않음. reflection 분석 대상 — researcher.md 에 "코드 review 시 default·fallback 경로 모두 추적" + "환경 진단 ssh 명령 표준 시퀀스" 추가 검토. | 갱신 적용 (researcher.md §1 호출 경로 검증 의무 + §3 환경 진단 표준 시퀀스 추가) |
| 3 | 2026-05-16 | CONSTRAINT_AMBIGUITY | orchestrator | 시도 1·2 (2026-05-15) 의 실제 video_backend 값이 *기록 없음* (training_log.md 에 명시 없음, config 미명시 → default 적용 가정만). researcher 가설 (pyav leak) 의 *전제* 가 검증 안 됨. 시도 1·2 의 OOM 원인이 torchcodec leak 일 가능성 — image 변환 결정의 *근거 재검토* 필요 시점. 추후 spec 결정 시 환경 변수·default 동작 명시 의무화 검토. | reflection 분석됨 (training_log.md 양식 개선은 별도 spec 또는 TODO-03 진입 시 처리) |
| 4 | 2026-05-16 | DIAG_FINDING | orchestrator (wandb output.log + ps RSS 분석) | 시도 3 (pyav backend) 학습 데이터로 변수 분리 결론 도출 — backend (torchcodec/pyav) 누수율 거의 동일 (1.07 vs 1.25 GB/min), process RSS 안정 (main 2.89 GB / workers 1.5-1.6 GB) → 누수는 process accounting *외부* (libav OS buffer 또는 shmem 의심). workers 가설 (시도 1·2 분석의 "DataLoader workers 주범") 도 RSS 안정으로 사실상 부정. **video decode 자체가 근본 leak 원인** 으로 확정 — researcher §5 옵션 3 (image 변환) confirm. TODO-1b 폐기. | 갱신 적용 (spec 본문 TODO-1b 폐기 마킹 + TODO-02 선결 조건 갱신) |
| 5 | 2026-05-16 | USER_OVERRIDE | orchestrator (/wrap-spec) | wrap-spec 시 verification_queue TODO-02·03 항목을 사용자 결정으로 *연기* 처리 → BACKLOG #7·#8 이관. spec 본문 §"Definition Of Done" 중 "TODO-02 110ep 변환 완료" + "TODO-03 시도 학습 진입 + 첫 ckpt 도달" 부분 *미달성* 상태로 spec 종료. 연기 사유: 변환 1-3h + 학습 진입 PHYS_REQUIRED 라 본 사이클 내 종료 어려움. 다음 사이클에서 트리거 도래 시 BACKLOG #7·#8 처리. | 무시됨 (사용자 결정 정상 분기) |
| 6 | 2026-05-16 | GPU_IDLE_THRASHING | orchestrator (wandb API system metric) | 시도 3 학습 후반 (~14:21) GPU utilization 0%, power 5W, system_memory 99.99%, proc.memory.availableMB 12MB. 학습 step 진행 사실상 정지 (5min/step 이후 9.6min/step). swap 없는 UMA 환경에서 OOM-killer 발동 전 kernel reclaim 이 적극 동작 → leak 누적 속도와 reclaim 속도 비등 → 무한 thrashing 도달. *예상 패턴* (OOM 자연 종료) 과 다른 새 행동. 사용자가 Ctrl+C 수동 kill 로 종료. 본 신호는 향후 DGX 학습 monitoring 에서 *OOM 발생 전 GPU idle* 을 조기 감지 신호로 활용 권장. | 갱신 적용 (TYPE 정의표에 `GPU_IDLE_THRASHING` 추가 + orin-deploy-procedure SKILL.md 에 wandb API 조회 패턴 추가) |

## [02_leftarm_v2_finetune (TODO-03 사이클)]

| # | 시각 | TYPE | source | details | 처리 상태 |
|---|------|------|--------|---------|-----------|
| 1 | 2026-05-17 23:40 | PROD_TEST_FAIL | prod-test-runner:03-C | F1 (Category B): `orin/lerobot/scripts/lerobot_record.py` line 83 가 `lerobot.cameras.reachy2_camera` import → `orin/lerobot/cameras/` trim 에 해당 모듈 없음 (upstream sync gap, scripts trim vs cameras trim 불일치). `lerobot-record --help` 조차 ImportError. F2: `orin/scripts/run_inference_leftarm_v2.sh` 의 `set -euo pipefail` + venv activate (`LD_LIBRARY_PATH` unbound) 충돌. F3: `huggingface-cli` deprecated → `hf` 대체 필요. 보고서: `docs/work_flow/context/todos/03C/03_prod-test.md`. F1 은 Category B 영역이므로 자동 재시도 X — 사용자 게이트 분기 필요. | 갱신 적용 — 2026-05-17 23:45 사용자 결정 옵션 A (line 83 try/except wrap, inference-only trim 일관). F1+F2+F3 묶음 task-executor cycle 2 진입 (TODO-03-E). Coupled Rules §3 (orin_lerobot_diff.md) 갱신 수반. |
| 2 | 2026-05-17 23:40 | DIAG_FINDING | prod-test-runner:03-C | `check` subcommand 결과 — smolvla_base `config.json` 의 `input_features` 에 `camera1/2/3` 3개 존재. 학습 데이터 (top, wrist) 는 2개만 → rename_map 으로 camera1/2 채우고 camera3 는 missing. `empty_cameras=0` 이므로 `modeling_smolvla.py:448-454` logic 에 따라 missing camera 무시 (즉시 break). 추론 동작 예상되나 *성능 영향* 가능 — Phase 3 추론 시 정성 확인 권장. 필요 시 `--empty_cameras=1` 검토. | 무시됨 (Phase 3 정성 관찰 — 동작 부드럽고 영향 미미 확인, 정책 판단력 한계가 핵심) |
| 3 | 2026-05-17 23:55 | PROD_TEST_FAIL | prod-test-runner:03-C cycle 2 | cycle 2 결과 — F2/F3 해소됨 (LD_LIBRARY_PATH + hf 마이그레이션). F1 try/except 도 import 자체는 해결. **그러나** F1 패치 후 *숨어있던* F4/F5/F6 신규 노출: `lerobot.common.control_utils` (line 90), `lerobot.datasets` (line 98), `lerobot.teleoperators.keyboard` (line 133) — 모두 `orin/lerobot/` trim 미포함, Category B. **근본 원인**: `lerobot_record.py` 가 upstream 전체본 그대로 — inference-only trim 정책과 본질적 양립 불가. lerobot-record 가 *데이터 수집* 명령이라 dataset/teleoperator/control_utils dependency 가 *핵심 경로* 에 있음. max 2 cycle 도달 → End-B 후보. Phase 1 결정 (lerobot-record 경로) 의 *전제* 재평가 필요. | 갱신 적용 (2026-05-18) — (a) 사용자 USER_OVERRIDE 옵션 W 로 lerobot-record 폐기 + leftarm_v2_inference.py 신설, (b) reflection 제안 #1 적용 — `lerobot-upstream-check` SKILL §외부 CLI entry trim 호환성 사전 점검 절차 신설로 재발 방지. |
| 5 | 2026-05-18 00:05 | USER_OVERRIDE | orchestrator | End-B 분기에서 사용자가 옵션 W 선택 + 신규 entry 이름 `leftarm_v2_inference.py` 결정 (hil_inference.py 갱신 X — 사전학습 ckpt 책임 보존, 마일스톤별 추론 정책 분리). `orin/inference/README` §"마일스톤별 추론 정책 진화 추적" 패턴 일관. spec 본문 TODO-03 의 entry 변경 (lerobot-record → leftarm_v2_inference.py). | 무시됨 (정상 분기 — End-B USER_OVERRIDE 정책 정합 작동. reflection 제안 #5 로 prod-test cycle 정책 명시 보강). |
| 6 | 2026-05-18 00:45 | DIAG_FINDING | orchestrator (사용자 시연장 진입 직전 발견) | leftarm_v2_inference.py 의 `OpenCVCameraConfig` 생성 (line 491-493) 에 `rotation` 인자 누락. `cameras.json` schema 도 `{index, flip}` 만 있고 rotation 필드 부재. 한편 수집 시 (`dgx/finetune/leftarm_v2/config/base_config.yaml:39`) top 카메라는 `rotation: -90` + `width: 480, height: 640` (세로) 으로 학습 데이터 수집됨. 추론 측은 640×480 가로 + 회전 X → 시야각·방향·dimension 셋 다 학습 분포와 다름. *Phase 1 환경 진단 부족* (수집 config 의 camera rotation 항목을 spec/plan 작성 시 점검 누락). 본 cycle 의 DOD 전제 미충족이므로 즉시 fix 필요 — 사용자 yes (ad-hoc 변경 정책: 단일 코드 파일 ~10줄 + cameras.json schema, 영향 명확). | 갱신 적용 (2026-05-18) — TODO-03-H ad-hoc fix + reflection 제안 #2 (planner.md §6-b 수집-추론 매트릭스) 적용으로 재발 방지. |
| 7 | 2026-05-18 00:45 | CONSTRAINT_AMBIGUITY | orchestrator (Phase 1 회고) | Phase 1 spec 작성 + planner 분석 시 *수집 측 camera 처리 (rotation/flip/dimension/fourcc) 와 추론 측 정합 검증* 이 명시적 의무 아님. 결과로 *학습 분포 일관* 의 1차 정합점이 자동 점검에서 빠짐. ANOMALIES #4 (CONSTRAINT_AMBIGUITY — Phase 1 환경 진단 부족) 의 *구체 예시*. reflection 대상 — planner 또는 task-executor 가 추론 entry 작성 시 *수집 config 와의 camera 매트릭스 비교* 의무 추가 검토. | 갱신 적용 (2026-05-18) — reflection 제안 #2·#3 적용 (planner.md §6-b + §3-a). |
| 4 | 2026-05-17 23:55 | CONSTRAINT_AMBIGUITY | orchestrator (planner·Phase 1 회고) | Phase 1 (사용자 + 메인) 시점에 `orin/lerobot/` trim 상태 + lerobot-record dependency 매트릭스 사전 점검 없이 lerobot-record 경로 결정. *prof_train_setting.md §5-3* 의 단순 명령 형태만 보고 채택. researcher 호출 없이 task-executor 진입 → Orin SSH 검증 단계에서 *연쇄 import 실패* 가 점진 노출 (cycle 1 F1, cycle 2 F4·F5·F6). 다음 사이클 spec 작성 시 *Phase 1 환경 진단 의무* (orin trim 상태 grep) 강화 검토 — reflection 대상. | 갱신 적용 (2026-05-18) — reflection 제안 #1 (lerobot-upstream-check SKILL trim 사전 점검) + #2 (planner.md §6-b 수집-추론 매트릭스) + #3 (planner.md §3-a researcher 선행 트리거) 적용. 02_prereq researcher 갱신 효과 전파 핵심. |
| 8 | 2026-05-18 20:11 | CONSTRAINT_AMBIGUITY | orchestrator (camera_empty 모델 추론 검증 cycle) | `scripts/deploy_orin.sh` 가 Orin 측 `orin/config/ports.json` (`follower_port=/dev/ttyACM0`) 과 `orin/config/cameras.json` (top:0, wrist:2 + rotation/dimension) 의 *실측 하드웨어 값* 을 devPC 의 null template 으로 덮어씀 → 직후 dry-run 재검증이 `parser.error("--follower-port 는 필수")` 로 차단. BACKLOG #1 (2026-05-14 식별, "높음") 가 *실제 발생* 한 케이스. dgx 의 `base_config.yaml` 보호 패턴은 있었지만 orin/config 는 동일 보호 부재 — `orin-deploy-procedure` SKILL.md 의 exclude 명시와 스크립트 실제 구현 간 *불일치* 가 root cause. 사용자 동의 후 즉시 패치 (`checkpoints/` + `config/ports.json` + `config/cameras.json` exclude 추가) + Orin 측 값 복원. reflection 대상 — SKILL.md ↔ 스크립트 정합 자동 점검 패턴 검토. | 갱신 적용 (2026-05-18) — deploy_orin.sh exclude 패치 + BACKLOG #1 완료 처리. SKILL ↔ 스크립트 정합 검증 패턴은 reflection 단계에서 추가 검토. |
| 9 | 2026-05-18 20:11 | DIAG_FINDING | orchestrator (camera_empty 모델 dry-run) | 새 ckpt `BaboGaeguri/leftarm_v2_camera_empty_A2_pc_2026-05-18` 의 `config.json.empty_cameras=1` (학습 시 빈 카메라 슬롯 1개 패딩 학습) 이지만, `leftarm_v2_inference.py` 의 LoRA adapter 로드 경로가 base `lerobot/smolvla_base` 의 default `empty_cameras=0` 을 적용 → 학습 분포 ≠ 추론 환경 mismatch. 기존 ckpt (`leftarm_v2_A2_pc_2026-05-17`) 는 `=0` 이라 문제 없었으나, camera_empty 분기는 *학습 hyperparam 자체가 변경* 됨. 사용자 동의 후 inference script 패치 — ckpt `config.json` 의 `empty_cameras` 를 `policy.config` 에 강제 적용. ANOMALIES #2 (2026-05-17 DIAG_FINDING — `empty_cameras=0` 가정) 의 *분기별 분리 필요성* 확정. | 갱신 적용 (2026-05-18) — leftarm_v2_inference.py L508-525 ckpt config.json 강제 적용 로직 추가. |
| 10 | 2026-05-18 20:15 | ORCHESTRATOR_GAP | orchestrator (메인) | inference script 패치 후 동기화 위해 `deploy_orin.sh` 실행 시 *이미 발견된 BACKLOG #1 (checkpoints/ exclude 부재) 을 먼저 패치하지 않고* deploy 함 → `--delete` 가 Orin 의 ckpt 두 개 (`leftarm_v2_A2_pc_2026-05-17` + `leftarm_v2_camera_empty_A2_pc_2026-05-18`) 모두 삭제. 새 ckpt 는 HF Hub 에서 재다운로드 (~17초) 로 복원, 기존 ckpt 는 사용자 결정으로 스킵. **순서 실수**: 위험 패치를 *deploy 전* 에 적용하지 않은 게 root cause. *coupled action* 패턴 인식 부족 — "BACKLOG 의 위험 항목이 해당 작업 직전에 발견되면 deploy 전 처리 의무". reflection 대상 — orchestrator 의 *위험 항목 우선 차단* 휴리스틱 명문화 검토. | 미처리 — reflection 단계 분석 (orchestrator 휴리스틱 추가) |
| 11 | 2026-05-18 21:50 | CONSTRAINT_AMBIGUITY | orchestrator (DGX↔devPC sync 검증 중 발견) | DGX 측 정본 collection_log·backlog·record_config 를 repo 로 sync 하는 중 `record_config.yaml` 의 `reset_time_s` 가 devPC=7 ↔ DGX=5 (사용자 시연 시 현장 *추가 단축*) 차이 발견. `deploy_dgx.sh` 의 exclude 가 `base_config.yaml` 만 보호 (hardware 섹션) — `record_config.yaml` 은 무방비. 다음 deploy 시 devPC 의 7 이 DGX 의 5 (현장값) 를 덮을 위험. **#8 (deploy_orin 의 동일 패턴) 과 일관 — 양 deploy 스크립트 모두 *세션 현장 갱신 yaml* 보호 패턴 부재**. 사용자 결정 후 즉시 패치 — `deploy_dgx.sh` exclude 에 `finetune/*/config/record_config.yaml` 추가 + deploy 후 echo 안내 신설 (글로벌 필드 변경 시 수동 scp 안내). | 갱신 적용 (2026-05-18) — deploy_dgx.sh 패치 + 사용자 안내 echo 추가. SKILL ↔ 스크립트 정합 검증 패턴은 reflection 단계에서 #8 과 같이 검토. |
| 12 | 2026-05-18 21:50 | DEPLOY_ROLLBACK | orchestrator (사용자 지적) | 본인이 DGX 측 정본 collection_log 의 8차+ entry 를 *추측 (dataset parquet 만 분석)* 으로 갱신 → 사용자가 "DGX 와 동일하게 바꿔야지" 지적. revert + scp 로 정정. **근본 원인**: devPC 의 collection_log 와 DGX 의 collection_log 의 *정본 owner 가 누구인지* 가 명문화 안 됨. 본 사이클에서 DGX 가 정본 (사용자 시연장 현장 작성). 일반적으로 어느 쪽이 정본인지 + sync 방향 명시 부재 — `docs/storage/legacy/arm_2week_plan/` 등에서도 유사 패턴 있을 가능성. reflection 대상 — *문서별 정본 owner 명시* + *DGX → devPC sync 도구 (deploy_dgx.sh 의 역방향)* 신설 검토. | 미처리 — reflection 단계 분석 (정본 owner 명시 + 역방향 sync 도구) |

## [03_leftarm_v2_eval_003_branch]

| # | 시각 | TYPE | source | details | 처리 상태 |
|---|------|------|--------|---------|-----------|
| — | — | — | — | **본 사이클 ANOMALY 등록 0건** — 02 사이클 갱신 6건 적용 효과 (특히 §6-b 수집-추론 매트릭스 점검) 로 시연장 ad-hoc 4건 → 0건 감소. reflection 2026-05-19 §패턴 5 분석. | wrap 종료 (0건) |
