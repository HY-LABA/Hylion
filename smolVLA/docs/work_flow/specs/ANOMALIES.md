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
