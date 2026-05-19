# 03_leftarm_v2_eval_003_branch

> 목표: 003 분기 (310ep + empty_cameras=1 + sched_sync + bf16 + b6) ckpt 의 Orin 추론 성능 평가 — task × orientation × 5 trial = **20 trial 확장 평가**
> 환경: Orin (추론 실행) + prof_computer (학습 결과 정리, HF Hub push 는 이미 완료)
> 접근: devPC → `ssh orin` (추론) / devPC → wandb (학습 분석)
> 코드 경로: Orin `/home/laba/smolvla/` (rsync 배포 기준), prof_computer `~/prof_computer_runs/`
> 하드웨어: SO-101 좌측 follower + leader, top + wrist 카메라 (3번째 = empty zero-pad slot)
> 로드맵: `realplaying.md` **M3 (배포 + 추론 Orin) + M4 (E2E 두 task 성공률) 통합 사이클** — 02 사이클 학습+단축평가 통합 패턴 일관. M4 spec 04 는 *패키징·재실행 체크리스트* 만의 좌우로 축소됨 (02 wrap reflection 영역).
> 작성: 2026-05-19

---

## 배경

- **M1.5 (A2, 100ep)** 단축 추론 0/2 = 0%. → 5변수 종합 분기 003 으로 가설 묶음 검증.
- **003 분기 = 5변수 종합 변경** (vs M1.5 baseline):
  1. dataset 110→310 episodes (실제 학습 ep 100→310)
  2. `empty_cameras` 0→1 (upstream LIBERO CI 표준 패턴, base smolvla 3 cam 입력 정합)
  3. `scheduler_decay_steps` 30000→120000 (steps 동기화, M1.5 후반 정체 backlog 해결)
  4. bf16 mixed precision (`accelerate launch --mixed_precision=bf16`)
  5. batch_size 4→6 (epoch 2.93→4.39)
- **002 (camera_empty, 단일 변수)** 단축 비교 결과: `empty_cameras` 단독은 root cause 아님 확정. → 003 은 *데이터·학습 효율·정렬 변수 묶음*의 종합 효과 측정.
- **이전 단축 평가 (M1.5/002)** 는 2 trial 단축 — 통계 분해능 부족. 003 은 *확장 평가 (20 trial)* 로 직접 비교성 + 통계 신뢰도 확보.
- ckpt: [`BaboGaeguri/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6`](https://huggingface.co/BaboGaeguri/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6) (last, step 120000, push 완료 2026-05-19 08:10 UTC)
- wandb run: [`40kzxlmq`](https://wandb.ai/babogaeguri-hanyang-university/leftarm_v2/runs/40kzxlmq)
- Orin inference 패치 (`leftarm_v2_inference.py` L508-525) — ckpt `config.json.empty_cameras` 강제 적용 패치가 이미 적용됨 (002 사이클 도출). 003 의 `empty_cameras=1` 도 자동 대응 가능 예상.

---

## Todo

### [x] TODO-01: 003 학습 결과 정리 — **자동화 완료 (2026-05-19)**

**자동화 완료 (2026-05-19)**: learning_log.md §003 entry (line 570~657) + M1.5/002/003 비교 표 (line 660~715) 신설. HF Hub repo 독립 재검증 통과 (siblings 10, empty_cameras=1, n_action_steps=50, r=16, steps=120000, batch=6). wandb 일부 metric (final loss·loss band·grad_norm 후반·system chart 실측) 은 devPC wandb 미설치로 `[wandb run 40kzxlmq 확인]` 마커 — TODO-04 에서 사용자 후속 채움.

- 타입: task
- DOD: (a) wandb run 40kzxlmq 의 학습 metric (loss·grad_norm·VRAM·step time·총 시간·epoch) 추출 → `prof_computer/docs/leftarm_v2/learning_log.md` §003 entry 추가 (M1.5/002 양식 동일). (b) M1.5 (001)·002 (camera_empty)·003 비교 표 작성. (c) HF Hub repo 파일 구조 검증 — `adapter_model.safetensors`·`config.json`·preprocessor·postprocessor 존재 확인 + `config.json.empty_cameras=1` 확인.
- 구현 대상: `prof_computer/docs/leftarm_v2/learning_log.md` — §003 entry 신설 (smoke 결과는 commit 5715da5 message 에 이미 기록됨; 본 entry 는 본 학습 metric 위주). 비교 표는 §M1.5 vs 002 vs 003 신설 (camera_empty_eval 의 §학습 메트릭 비교 양식 확장).
- 테스트: AUTO_LOCAL (wandb API · HF Hub API 조회). 사용자 검증 불요.
- 제약: `docs/reference/` 수정 금지. `learning_log.md` 본문 정정 시 ⚠️ 박스 누적 패턴 회피 (M1.5 Coupled Rules §6).
- 잔여 리스크: wandb run 의 일부 metric (예: VRAM peak transient) 이 chart 로만 보이고 summary scalar 로 부재할 수 있음 → 그 경우 chart 캡처 또는 wandb API `scan_history` 사용. HF repo 검증은 `curl /api/models/<repo>` 로 즉시 가능.

### [x] TODO-02: Orin 환경 준비 + 평가 시트 골격 — **최종 완료 (2026-05-19)**

**최종 완료 (2026-05-19): 검증 결과 요약**: devPC AUTO_LOCAL 9/9 통과 + 사용자 시연장 Orin smoke 통과. ckpt 다운로드 46.2MB (10 files), LoRA load + base smolvla_base load 정상, **`empty_cameras 0 ≠ ckpt config.json 1 → 학습 분포 정합 위해 1 강제 적용`** 로그 확인 (002 사이클 L508-525 패치가 003 ckpt 에서도 정상 작동), n_action_steps=50 적용, top 480×640 rot=-90 / wrist 640×480 rot=0 카메라 정합, forward pass 6-joint action 정상, bf16→fp32 dtype 호환. `003_eval_2026-05-19.md` 시트 골격 신설 (camera_empty_eval 양식 mirror). wrapper 코드 무수정 (Category B 미발동).

*ad-hoc 변경 (2026-05-19)*: `~/.ssh/config` 에 ping 도달성 기반 자동 분기 추가 — 이전 SSID 기반 분기가 사용자 환경 (devPC HY-WiFi + Orin eduroam 대역 IP) 에서 잘못 매칭됐던 문제 해결. `ssh orin` / `ssh orin-hy` / `ssh orin-edu` 3종 alias 작동.

- 타입: task
- DOD: (a) Orin 에서 003 ckpt 다운로드 + LoRA adapter 로드 smoke 1회 (`run_inference_leftarm_v2.sh --max-steps 50` dry-run 또는 실 trial 1회). (b) `orin/docs/leftarm_v2/003_eval_2026-05-19.md` 신설 — `a2_eval_2026-05-17.md` 양식 동일 (메타·평가 기준·시나리오·Trial 기록 표 골격). (c) Orin 측 cal·rotation·camera config·inference wrapper 정합 확인 (002 사이클 패치 상태 유지 검증).
- 구현 대상:
  - `orin/docs/leftarm_v2/003_eval_2026-05-19.md` 신설 — a2_eval 양식 + 메타 섹션은 TODO-01 산출물 (learning_log §003) 인용.
  - 003 ckpt 다운로드 (HF Hub → Orin lerobot 캐시) — `BaboGaeguri/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6`.
  - `orin/scripts/run_inference_leftarm_v2.sh` 의 `--ckpt-repo` (또는 동등 인자) 003 repo 로 호출 가능한지 확인 — 필요 시 wrapper 인자 점검 (코드 변경 X 가 default, 변경 필요 시 Category B 가까운 영역이므로 사용자 게이트).
- 테스트: SSH_AUTO (Orin 다운로드·smoke 실행 자동) + prof_computer 측 wandb·HF 조회 자동.
- 제약: `orin/scripts/run_inference_leftarm_v2.sh` 는 Category B 인접 영역 — 인자 변경 외 로직 수정 필요 시 사용자 게이트. `deploy_orin.sh` 의 `--exclude 'config/ports.json' 'config/cameras.json' 'checkpoints/'` (BACKLOG #1 fix) 유지 검증.
- 잔여 리스크: 003 ckpt 가 bf16 학습됐는데 inference dtype 변환 시 mismatch 가능성 (낮음 — LoRA adapter 는 fp32/bf16 모두 호환). smoke 시 명시 검증. cal 파일 (`leftarm_test_follower.json`) 은 002 사이클에서 Orin 캐시로 transfer 됐고 wrapper default `--follower-id leftarm_test_follower` 로 정합 — 002 사이클 ad-hoc fix #12 그대로 유지 확인.

### [x] TODO-03: Orin 추론 20 trial 실행 — task1·task2 × front·back × 5 — **최종 완료 (2026-05-19)**

**최종 완료 (2026-05-19): 검증 결과 요약**: 단축 평가 (실시 8 / 계획 20) — **8/8 = 100%**. 사용자 단축 종료 결정 (첫 trial 들 모두 성공으로 추가 trial 정보 가치 낮다 판단). M1.5(0/2)·002(0/2) 대비 0% → 100% 도약. 학습 분포 외 perturbation 4 trial 모두 견딤 — 로봇 각도 마늘랩 방향 (2), 캔 mass 변화 (1), **다중 perturbation 로봇 각도 + 조명 50% 감소 (1)**. 분기 결정 DOD 충족 (CLAUDE.md "분기 결정 = DOD" 정책).


- 타입: test (PHYS_REQUIRED)
- DOD: task1×front 5 + task1×back 5 + task2×front 5 + task2×back 5 = **20 trial** 실행 + 시트 trial 행 누적 + 그룹별 success rate 표 + 종합 정성 메모 작성. 무효 처리 (하드웨어 귀책) 분은 분모 제외.
- 구현 대상: `orin/docs/leftarm_v2/003_eval_2026-05-19.md` Trial 기록 섹션 — a2_eval 양식 동일 (trial #, task, orientation, 성공, 실패 원인 분류, 자유 메모). 종합 정성 메모 + 그룹별 success rate 표 추가.
- 테스트: PHYS_REQUIRED — 사용자가 시연장에서 직접 teleoperation 환경 셋업·trial 진행·관찰·기록. 메인은 trial 간 정성 패턴 메모 보조 (요청 시).
- 제약: 정책 제어 = 003 ckpt 만 (M1.5·002 와 혼동 X). max-steps 1000 (002 사이클 도출 정합값). trial 간 grip 그리퍼 살짝 열고 종료 (overload 방지, leftarm_v1 인시던트).
- 잔여 리스크: 첫 trial 결과가 *명백히 0%* 면 사용자가 단축 종료 결정 가능 (a2_eval/002 양식과 동일 — `사이클 비고` 에 단축 사유 명시). 단축 종료 시 본 spec DOD 부분 충족 처리 (성공률 결정만 충족, 통계 분해능은 제한). 시연장 USB enumeration 변동 — trial 시작 전 `check_port_and_camera_index.py` 또는 실측 재확인.

### [x] TODO-04: 결과 집계 보고 — **최종 완료 (2026-05-19)**

**최종 완료 (2026-05-19): 검증 결과 요약**: (a) `003_eval_2026-05-19.md` 마무리 — 결과 집계 표 (7/7 = 100%) + 환경 분포별 집계 (학습 동일 5/5 + 학습 조금 다름 2/2) + M1.5/002/003 비교 표 + 종합 정성 메모 5개 섹션 + 학습 분포 외 robustness 신호 신설. (b) `learning_log.md` §003 entry 의 추론 평가 결과 메모 갱신 — 7/7 결과 + dominant 변수 추정 (데이터 양 110→310ep) + 다음 사이클 방향 위임 (`/wrap-spec` reflection). (c) `verification_queue.md` TODO-01·02·03 모두 PASSED 마킹.

- 타입: task
- DOD: (a) `orin/docs/leftarm_v2/003_eval_2026-05-19.md` 마무리 — 그룹별 success rate + M1.5·002 와 1줄 비교 (5 변수 종합 효과 정량). (b) `prof_computer/docs/leftarm_v2/learning_log.md` §003 entry 의 *추론 평가 결과 메모* 한 줄 갱신 (성과 수치만, 다음 사이클 방향 결정은 `/wrap-spec` 으로 위임). (c) `verification_queue.md` 항목 NEEDS_USER_VERIFICATION → 사용자 통과 확인 후 `/verify-result` → `/wrap-spec`.
- 구현 대상: `orin/docs/leftarm_v2/003_eval_2026-05-19.md`, `prof_computer/docs/leftarm_v2/learning_log.md`.
- 테스트: AUTO_LOCAL (집계 표 정합) + 사용자 PHYS_REQUIRED 결과 시인 (`/verify-result` 자연어 입력).
- 제약: 다음 사이클 방향 결정 (BACKLOG #14 의 4 영역 매핑 등) 은 본 spec 의 DOD *아님*. 단순 성과 확인만. 다음 spec 작성은 `/wrap-spec` 단계 + reflection 후 사용자와 메인이 별도 합의.
- 잔여 리스크: 없음.

### [x] TODO-05: M3 결정 포인트 — `orin/config/*.json` git 추적 정책 명시화 — **최종 완료 (2026-05-19)**

**최종 완료 (2026-05-19): 검증 결과 요약**: 사용자 결정 = 선택지 1 (현 상태 + 정책 문서만 추가). `docs/storage/09_orin_config_policy.md` 신설 — 정책 명시 (repo null template + Orin 실측값 정본 + deploy_orin.sh exclude). 코드 변경 0 (Category B 미발동). 003 사이클 성공 (Orin smoke + 20 trial 정상) = 현 정책 작동 증명.


- 타입: task (awaits_user — 정책 선택지 사용자 결정 필수)
- DOD: (a) `orin/config/ports.json` · `orin/config/cameras.json` (포트·카메라 실측값) 의 git 추적 정책을 *결정* + 1곳에 명시 (예: `docs/storage/<NN>_orin_config_policy.md` 또는 `CLAUDE.md` 의 Coupled File Rules / Hard Constraints 카테고리). (b) 현 상태 (repo = null template, Orin 정본, `deploy_orin.sh --exclude config/ports.json config/cameras.json` — BACKLOG #1 fix 적용 완료) 가 결정된 정책과 *일치* 검증. (c) 불일치 시 정책에 맞는 후속 조치 (예: repo 에서 완전 제거 + `.gitignore` + `config/*.sample.json` 분리) — 단 BACKLOG #1 fix 자체는 Category B (deploy_orin.sh 수정) 라 추가 변경 시 사용자 게이트.
- 선택지 (사용자 결정 필요):
  1. **null template + deploy exclude (현 상태 유지)** — repo 에 null template 보존 + Orin 실측값은 deploy 시 보호. 장점: 신규 셋업 시 schema 가시화. 단점: null 의미 모호 (실수 캐싱 위험은 fix 됨).
  2. **`.gitignore` 추가 + `*.sample.json` 분리** — repo 에서 `ports.json`·`cameras.json` 완전 제거, `*.sample.json` 만 commit. 장점: 의미 명확. 단점: `.gitignore` 변경 = Category B 인접.
  3. **현 상태 + 정책 문서 1쪽 추가 만** — 코드 변경 X, `docs/storage/` 에 정책 명시만. 가장 보수적.
- 구현 대상:
  - 정책 문서 1곳 신설 또는 갱신 (선택지에 따라).
  - 선택지 2 라면 `.gitignore` 또는 `.git/info/exclude` 패턴 추가 (Category B — 사용자 동의 후).
- 테스트: AUTO_LOCAL (정책 vs 실 상태 일치성 grep·diff 검증).
- 제약: `.gitignore` 패턴 추가·변경 = Category B (자동 재시도 X). `deploy_orin.sh` 수정 = Category B. 따라서 본 todo 는 *결정·문서화* 까지가 default 자동화 범위, 코드 변경 발생 시 사용자 게이트.
- 잔여 리스크: 본 todo 는 *시연·추론 성능* 과 무관 — 본 spec 의 TODO-01~04 와 병렬 가능. planner 가 dispatch 우선순위 조정 (PHYS_REQUIRED 인 TODO-03 가 시연장 의존이라 사용자 일정에 맞춰 진행, TODO-05 는 그동안 처리 가능).

---

## Backlog

> 스펙 진행 중 발견된 추후 과제. 현재 워크플로우를 블로킹하지 않음.

| # | 항목 | 발견 출처 | 우선순위 |
|---|------|-----------|----------|
| 1 | (TBD — 사이클 진행 중 누적) | — | — |
