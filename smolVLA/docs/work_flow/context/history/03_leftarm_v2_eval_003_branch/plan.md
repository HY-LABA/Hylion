# Execution Plan — spec 03_leftarm_v2_eval_003_branch

> 작성: 2026-05-19 | planner
> spec: `docs/work_flow/specs/03_leftarm_v2_eval_003_branch.md`
> 활성 todo: TODO-01 ~ TODO-05 (총 5개)

---

## spec 본문 언급 파일·경로 실존 검증

| 파일·경로 | 상태 | 비고 |
|---|---|---|
| `orin/docs/leftarm_v2/a2_eval_2026-05-17.md` | 실존 확인 | 양식 참조 기준 파일 |
| `orin/docs/leftarm_v2/003_eval_2026-05-19.md` | 미존재 (신규) | TODO-02 task-executor 작성 대상 — 정상 |
| `orin/scripts/run_inference_leftarm_v2.sh` | 실존 확인 | 현재 CKPT_REPO_ID default = `BaboGaeguri/leftarm_v2_A2_pc_2026-05-17` (001 기준) — **003 repo 로 변경 필요** |
| `orin/inference/leftarm_v2_inference.py` | 실존 확인 | L508-525 empty_cameras 패치 적용됨 (002 사이클) |
| `orin/config/cameras.json` | 실존 확인 | index=null, rotation=-90/0, width/height 필드 존재. 003 정합 이미 충족 |
| `orin/config/ports.json` | 실존 확인 | devPC 기준 null. Orin 실 환경 값 SSH_AUTO 확인 대상 |
| `prof_computer/docs/leftarm_v2/learning_log.md` | 실존 확인 | §001·§002 비교표 존재, §003 entry 미존재 → TODO-01 신설 대상 |
| `prof_computer/finetune/leftarm_v2/branches/003_a2_310ep_empty1_sched_sync_bf16_b6/train_config.yaml` | 실존 확인 | 학습 파라미터 정본 (empty_cameras=1, steps=120000, batch=6 등) |
| HF Hub `BaboGaeguri/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6` | 외부 — 미검증 | spec 에 push 완료 명시 (2026-05-19 08:10 UTC). prod-test-runner SSH_AUTO 검증 대상 |
| `scripts/deploy_orin.sh` | 실존 확인 | `--exclude 'checkpoints/' 'config/ports.json' 'config/cameras.json'` 패치 적용 완료 (BACKLOG #1 완료) |

### 오기재 정정 메모

- `orin/scripts/run_inference_leftarm_v2.sh` 의 `CKPT_REPO_ID` default 가 `leftarm_v2_A2_pc_2026-05-17` (001 ckpt) 로 하드코딩됨. spec 은 환경 변수 override 가능 (`CKPT_REPO_ID=...` export) 을 전제하므로 코드 변경 X 가 기본 방침 — **환경 변수 override 로 003 repo 호출 가능** (Category B 비해당). task-executor 가 wrapper 호출 시 `CKPT_REPO_ID=BaboGaeguri/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6 CKPT_LOCAL_DIR=~/smolvla/orin/checkpoints/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6` 를 export 하여 사용하도록 smoke/dry-run 절차 명시.
- `orin/docs/leftarm_v2/` 내 `camera_empty_eval_2026-05-18.md` 가 최신 양식 정본 — `a2_eval_2026-05-17.md` 보다 최신. TODO-02 신규 파일 작성 시 `camera_empty_eval_2026-05-18.md` 양식을 기준으로 삼을 것.

---

## Summary

총 todo: 5개 | 병렬 그룹: 3그룹 | awaits_user: 1개 (TODO-05) | 검증 큐 후보: 5개 (AUTO_LOCAL 2 + SSH_AUTO 1 + PHYS_REQUIRED 2)

---

## DAG (의존 관계)

```
TODO-01 (학습 결과 정리 — prof_computer) ─────────────────────┐
TODO-02 (Orin 환경 준비 + 평가 시트 골격 — Orin) ──────────────┤
                                                              ▼
TODO-05 (config git 정책 — awaits_user 해소 후)          TODO-04 (결과 집계 보고) ← TODO-03 (20 trial PHYS_REQUIRED)
```

- TODO-01 → TODO-04: 학습 metric §003 entry 가 TODO-04 보고 내용에 인용됨
- TODO-02 → TODO-03: 평가 시트 골격 + Orin 환경 준비 완료 후 trial 진행 가능
- TODO-02 → TODO-04: 003 eval 문서 파일이 TODO-04 에서 마무리됨
- TODO-03 → TODO-04: 20 trial 결과 집계가 TODO-04 DOD
- TODO-05 → 독립: 본 spec 다른 todo 와 의존 없음. awaits_user 해소 후 단독 처리.

---

## 병렬 그룹

| 그룹 | todo | 의존 | 비고 |
|---|---|---|---|
| **Group 1** (병렬 자율) | TODO-01 | 없음 | prof_computer 측 — wandb/HF API 조회 자율. AUTO_LOCAL |
| **Group 1** (병렬 자율) | TODO-02 | 없음 | Orin 측 — SSH_AUTO + 신규 파일 작성. TODO-01 과 독립 노드 |
| **Group 1** (병렬 자율) | TODO-05 | awaits_user 해소 후 | 본 spec 나머지 todo 와 의존 없음. TODO-03 PHYS_REQUIRED 대기 중 처리 가능 |
| **Group 2** (Group 1 후 직렬) | TODO-03 | TODO-02 완료 필수 | PHYS_REQUIRED — 시연장 사용자 일정 의존 |
| **Group 3** (Group 2 후 직렬) | TODO-04 | TODO-01·02·03 모두 완료 | AUTO_LOCAL + 사용자 `/verify-result` 입력 |

---

## 확신 가정 (병렬 진행 OK)

- **가정 1**: HF Hub push 완료 (spec 명시, 2026-05-19 08:10 UTC). `curl https://huggingface.co/api/models/BaboGaeguri/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6` 로 prod-test-runner SSH_AUTO 검증 가능.
- **가정 2**: `orin/inference/leftarm_v2_inference.py` L508-525 empty_cameras 강제 적용 패치 (002 사이클 도출) 가 003 의 `empty_cameras=1` 도 자동 처리함. ckpt `config.json.empty_cameras` 가 1 이면 policy.config 에 강제 적용 — 별도 코드 수정 불필요.
- **가정 3**: `orin/config/cameras.json` 에 rotation/width/height 필드 이미 존재 확인 (top: rotation=-90, 480×640 / wrist: rotation=0, 640×480). 수집 측 `base_config.yaml` 과 정합 — 별도 수정 불필요.
- **가정 4**: `follower-id` default = `leftarm_test_follower` (002 사이클 ad-hoc fix #12 정합 확인). 수집 측 `base_config.yaml robot.id = leftarm_test_follower` 와 일치. 별도 수정 불필요.
- **가정 5**: `run_inference_leftarm_v2.sh` 의 live/dry-run max-steps = 1000 (002 사이클 정식 동기화 완료, BACKLOG #13 완료). 003 평가 max-steps 1000 유지 확신.
- **가정 6**: `scripts/deploy_orin.sh` 에 `--exclude 'checkpoints/' 'config/ports.json' 'config/cameras.json'` 패치 적용 완료 (BACKLOG #1 완료). deploy 시 Orin 실 환경 보호됨.
- **가정 7**: `orin/scripts/` 에 신규 파일 추가 X (기존 `run_inference_leftarm_v2.sh` 환경 변수 override 사용) — Category B 미해당.
- **가정 8**: `orin/docs/leftarm_v2/` 디렉터리 실존 확인 — 신규 파일 추가 Category C 미해당 (기존 디렉터리 내부).
- **가정 9**: prof_computer 측 wandb API 및 HF Hub API 는 devPC 에서 자율 조회 가능. 별도 SSH 불필요.
- **가정 10**: 003 ckpt bf16 학습 — inference 시 LoRA adapter fp32/bf16 모두 호환. dtype mismatch 위험 낮음 (smoke 1회로 확인).

---

## 확인 필요 가정 (awaits_user 또는 SSH_AUTO 확인 대상)

| TODO | 질문 | 영향 | 분류 |
|---|---|---|---|
| TODO-02 (Orin ports) | Orin 실 `ports.json` 의 `follower_port` 가 null 이면 `FOLLOWER_PORT` 환경 변수 직접 지정 필요. | TODO-03 live trial 명령 완성 여부 | SSH_AUTO 점검 후 null 이면 사용자 확인 |
| TODO-02 (Orin cameras) | Orin 실 `cameras.json` 의 `index` 가 null 이면 `TOP_IDX`/`WRIST_IDX` 환경 변수 직접 지정 필요. | TODO-03 live trial 명령 완성 여부 | SSH_AUTO 점검 후 null 이면 사용자 확인 |
| TODO-03 (일정) | 시연장 이동 일정 (소요 1-2시간). 사용자 일정 확인 필요. | Phase 3 시작 시점 | `awaits_user` (Phase 3 진입 시 사용자 일정 확인) |
| TODO-05 (정책 선택) | 선택지 1/2/3 중 사용자 결정 필수 (spec 본문 명시) | TODO-05 dispatch 여부 | `awaits_user` — 답 받기 전 dispatch X |

---

## awaits_user 항목

### TODO-05 (config git 정책) — 필수 사전 결정

**배경**: `orin/config/ports.json` · `orin/config/cameras.json` 의 git 추적 정책 결정. 현 상태: repo = null template, Orin 실측값 deploy 시 exclude 로 보호.

**선택지**:
1. **null template + deploy exclude (현 상태 유지)** — repo null template 보존 + exclude 유지. 코드 변경 X, 정책 문서 1쪽 추가만. 가장 안전 (Category B 미발생).
2. **`.gitignore` 추가 + `*.sample.json` 분리** — repo 에서 완전 제거, `*.sample.json` 만 commit. `.gitignore` 변경 = **Category B** → 추가 사용자 게이트 발생.
3. **현 상태 + 정책 문서 1쪽 추가만** — 코드 변경 X, `docs/storage/` 에 정책 명시만. 선택지 1 과 유사하나 코드 수정 완전 0.

**Category B 매핑**:
- 선택지 2: `.gitignore` 패턴 추가·변경 = Category B. code-tester MAJOR 시 자동 재시도 X.
- 선택지 1·3: Category B 미해당. 자동 처리 가능.

**해소 후 dispatch 가능 todo**: TODO-05 단독 (다른 todo 와 의존 없음).

---

## 검증 큐 후보 (Phase 3)

| TODO | 환경 레벨 | 검증 방식 | 비고 |
|---|---|---|---|
| TODO-01 (학습 결과 정리) | `AUTO_LOCAL` | wandb API + HF Hub API 조회 자동. `learning_log.md` §003 entry 형식·비교표 구조 확인. Phase 3 검증 불요. | HF Hub curl 검증 포함 |
| TODO-02 (Orin 환경 준비 + 평가 시트) | `SSH_AUTO` | Orin SSH — 003 ckpt 다운로드 (`hf download` 또는 `huggingface-cli`), empty_cameras 강제 적용 동작 확인 (`config.json.empty_cameras` 읽기), dry-run 1 step (`--max-steps 1`). 평가 시트 문서 구조 AUTO_LOCAL code-tester 확인. | Orin SSH_AUTO + devPC code-tester |
| TODO-03 (20 trial 추론) | `PHYS_REQUIRED` | 사용자 시연장 직접 진행. task1×front 5 + task1×back 5 + task2×front 5 + task2×back 5 = 20 trial. 시연장 사용자 일정 의존. 단축 종료 조건: 첫 trial 명백 0% 시 사용자 결정. | 시연장 USB enumeration 변동 → trial 전 `check_port_and_camera_index.py` 또는 실측 재확인 필수 |
| TODO-04 (결과 집계) | `AUTO_LOCAL` + 사용자 확인 | 집계 표 형식 AUTO_LOCAL 확인. 사용자 `/verify-result` 로 Phase 3 최종 통과 확인. | TODO-03 결과 입력 의존 |
| TODO-05 (config git 정책) | `AUTO_LOCAL` | 정책 vs 실 상태 일치성 grep·diff 검증. 선택지 2 이면 `.gitignore` 패치 후 `git status` 확인 포함. | awaits_user 해소 후 처리 |

### PHYS_REQUIRED 상세 절차 (TODO-03)

사용자가 Phase 3 에서 수행:
1. 시연장 Orin SSH 접속 → venv 활성화 (`source ~/smolvla/orin/.hylion_arm/bin/activate`)
2. ckpt 확인: `ls ~/smolvla/orin/checkpoints/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6/`
3. USB enumeration 확인: `check_port_and_camera_index.py` 또는 `v4l2-ctl --list-devices` + `lerobot-find-port`
4. 003 eval 시트 (`orin/docs/leftarm_v2/003_eval_2026-05-19.md`) devPC 에서 보면서 기록
5. `CKPT_REPO_ID=BaboGaeguri/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6 CKPT_LOCAL_DIR=~/smolvla/orin/checkpoints/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6 bash ~/smolvla/orin/scripts/run_inference_leftarm_v2.sh live task1` (front 5회 + back 5회)
6. 동일하게 task2 (front 5회 + back 5회)
7. trial 간 그리퍼 살짝 열고 종료 (overload 방지 — leftarm_v1 인시던트 정책)
8. success rate + 실패 원인 → `/verify-result` 로 결과 보고

---

## dispatch 순서 권고

### Step 1 — 병렬 dispatch (Group 1)

동시 실행 가능 todo:

- **TODO-01** → task-executor: `prof_computer/docs/leftarm_v2/learning_log.md` §003 entry 신설 + 비교표 작성
  - 참조: wandb run `40kzxlmq`, HF Hub `BaboGaeguri/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6`
  - Category B 미해당. code-tester AUTO_LOCAL.

- **TODO-02** → task-executor: `orin/docs/leftarm_v2/003_eval_2026-05-19.md` 신설 + Orin 003 ckpt smoke
  - 환경 변수 override: `CKPT_REPO_ID=BaboGaeguri/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6`
  - `run_inference_leftarm_v2.sh` 코드 변경 X — 환경 변수 override 만 사용 (Category B 미발동)
  - Orin 에서 dry-run 1 step (smoke) + empty_cameras 적용 확인
  - Category B 인접 주의: `run_inference_leftarm_v2.sh` 로직 수정 필요 발생 시 → 즉시 orchestrator 사용자 게이트

- **TODO-05 (awaits_user 해소 후)** → 사용자 답 수신 후 단독 dispatch 가능
  - 선택지 1·3: task-executor (정책 문서 1쪽 신설) → code-tester AUTO_LOCAL
  - 선택지 2: task-executor → code-tester → **Category B 게이트 (`.gitignore` 변경) → 사용자 확인**

### Step 2 — 직렬 dispatch (Group 2, TODO-02 완료 후)

- **TODO-03** → verification_queue 등록 → Phase 3 사용자 위임 (PHYS_REQUIRED)
  - 시연장 일정 확인 후 진행. 다른 todo (TODO-01·TODO-05) 완료 여부와 무관하게 진입 가능.

### Step 3 — 직렬 dispatch (Group 3, TODO-01·02·03 모두 완료 후)

- **TODO-04** → task-executor: 집계 보고 마무리 → code-tester AUTO_LOCAL → 사용자 `/verify-result` → `/wrap-spec`

---

## Hard Constraints 점검 결과

| 영역 | 적용 여부 | 판단 |
|---|---|---|
| Category A (`docs/reference/`, `.claude/`) | 미해당 | 변경 대상 없음 |
| Category B (`orin/lerobot/`, `orin/pyproject.toml`, `orin/scripts/setup_env.sh`, `scripts/deploy_*.sh`, `.gitignore`) | TODO-02 인접, TODO-05 선택지 2 해당 | TODO-02: `run_inference_leftarm_v2.sh` 로직 수정 시 → 즉시 사용자 게이트. TODO-05 선택지 2: `.gitignore` 패치 = Category B → 추가 사용자 확인 필요 |
| Category C (새 디렉터리, 외부 의존성, 환경 변경) | Orin cameras/ports null 시 부분 해당 | SSH_AUTO 점검 후 null 이면 사용자 확인 분기 |
| Category D (rm -rf, sudo 등) | 미해당 | 해당 명령 사용 계획 없음 |

---

## 수집-추론 정합 매트릭스 점검 결과 (§6-b)

| 정합 항목 | 수집 측 | 추론 측 | 정합 상태 |
|---|---|---|---|
| camera rotation (top) | `base_config.yaml cameras.top.rotation: -90` | `orin/config/cameras.json top.rotation: -90` + `leftarm_v2_inference.py` 자동 적용 | 정합 확인 |
| camera dimension (top) | `base_config.yaml cameras.top: width=480, height=640` | `cameras.json top: width=480, height=640` | 정합 확인 |
| camera fourcc | `base_config.yaml fourcc: MJPG` | `cameras.json top/wrist: fourcc: MJPG` | 정합 확인 |
| robot.id (follower-id) | `base_config.yaml robot.id: leftarm_test_follower` | `leftarm_v2_inference.py` `--follower-id` default `leftarm_test_follower` (BACKLOG #12 fix) | 정합 확인 |
| cal 파일 | DGX `~/.cache/lerobot/calibration/.../leftarm_test_follower.json` → Orin transfer | Orin `~/.cache/huggingface/lerobot/calibration/.../leftarm_test_follower.json` | 정합 확인 (BACKLOG #12 완료) |
| max-steps | 학습 config `n_action_steps` 1 (smolvla_base default) → inference 시 ckpt config.json 로 override 가능 | `run_inference_leftarm_v2.sh live` max-steps=1000 | 정합 확인 (BACKLOG #13 완료) |
| empty_cameras | `train_config.yaml empty_cameras: 1` → HF Hub `config.json.empty_cameras=1` 포함 예상 | `leftarm_v2_inference.py` L508-525 ckpt config.json 강제 적용 패치 | 정합 확인 (002 사이클 패치 적용) |

**결론**: 02 사이클 ad-hoc fix (#11·#12·#13) 가 모두 정식 완료됨 — 003 사이클은 동일 이슈 재발 없을 것으로 판단. SSH_AUTO dry-run 1 step 으로 최종 확인.
