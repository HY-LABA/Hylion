# Phase 3 검증 대기 큐 — placeholder

> Phase 2 진행 중 prod-test-runner 가 완료한 항목 + 사용자 실물 검증이 필요한 항목을 누적. 모든 todo 자동화 종료 시 메인이 본 큐를 사용자에게 일괄 제시.

## 형식

각 항목:

```markdown
### [TODO-XX] (제목)

- **상태**: 자동 검증 통과 / 실패 / N.A.
- **사용자 검증 필요 사항**:
  1. (구체 절차)
  2. ...
- **prod-test-runner 결과 요약**: ...
- **참고 파일**: `context/todos/XX/03_prod-test.md`
```

---

## 활성 spec: 03_leftarm_v2_eval_003_branch

### TODO-01 — 003 학습 결과 정리

- **상태**: `AUTOMATED_PASS` (AUTO_LOCAL 검증 완료)
- **사용자 검증 필요 사항**: 없음
  - wandb metric 후속 채움 (`[wandb run 40kzxlmq 확인]` 마커 항목 갱신) 은 TODO-04 단계 사용자 작업으로 위임. 본 verdict 와 무관.
- **prod-test-runner 결과 요약**: learning_log.md §003 entry well-formed (H2/H3/H4 깊이 일관). HF Hub siblings 10개 정합, `config.json.empty_cameras=1` / `n_action_steps=50` / `adapter_config.json.r=16` 직접 curl 재검증 통과. Hard Constraints 4 카테고리 모두 통과.
- **참고 파일**: `context/todos/TODO-01/03_prod-test.md`

### TODO-02 — Orin 환경 준비 + 평가 시트 골격

- **상태**: ✅ **PASSED (2026-05-19 사용자 검증 통과)** — ssh orin 작동 (~/.ssh/config ad-hoc fix), ckpt 46.2MB download, dry-run smoke 통과:
  - LoRA + base smolvla_base load OK
  - `empty_cameras 0 ≠ ckpt config.json 1 → 학습 분포 정합 위해 1 강제 적용` 로그 (002 사이클 L508-525 패치가 003 ckpt 에서도 정상 작동)
  - n_action_steps=50 적용, top 480×640 rot=-90 / wrist 640×480 rot=0 카메라 정합
  - forward pass 6-joint action OK, bf16→fp32 dtype 호환
- **상태 (이전)**: `NEEDS_USER_VERIFICATION` (devPC AUTO_LOCAL 9/9 통과 + Orin 시연장 사용자 위임)
- **환경 레벨**: PHYS_REQUIRED (devPC ↔ Orin 시연장 LAN 분리 — SSH 차단 상태)
- **사용자 검증 필요 사항**:

  시연장 Orin 콘솔에서 아래 순서 실행:

  ```bash
  cd ~/smolvla && source orin/.hylion_arm/bin/activate

  # (1) 환경 사전 확인
  cat orin/config/ports.json
  cat orin/config/cameras.json
  # → null 이면 아래 override 변수 준비 (실측값으로 채움)

  # (2) 003 ckpt 다운로드 (~44 MB adapter + config files)
  export CKPT_REPO_ID=BaboGaeguri/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6
  export CKPT_LOCAL_DIR=~/smolvla/orin/checkpoints/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6
  bash orin/scripts/run_inference_leftarm_v2.sh download

  # (3) dry-run smoke (로봇 미연결 가능 — policy 로드 + forward pass 1 step)
  bash orin/scripts/run_inference_leftarm_v2.sh dry-run task1 2>&1 | tail -50
  # 기대: empty_cameras=1 강제 적용 로그 + forward pass 성공 (robot connect 에러는 정상)
  ```

  검증 기준:
  - `download` 완료 (adapter_model.safetensors 44MB 존재 확인)
  - `dry-run`: policy load 성공 + `empty_cameras=1` 강제 적용 로그 출력 + forward pass 1 step 정상
  - `ports.json` / `cameras.json` 실측값 확인 (null 이면 환경 변수 override 준비)

  (4) live trial 은 **TODO-03 PHYS_REQUIRED 와 단일 세션 합산** 진행 (아래 TODO-03 항목 참조)

- **prod-test-runner 결과 요약**: `003_eval_2026-05-19.md` 구조 (헤더, 마커 2곳, trial 20행, 집계/정성 골격) 전부 자동 검증 통과. HF Hub siblings 10 / `empty_cameras=1` / `n_action_steps=50` curl 재검증 통과. wrapper 코드 수정 없음 (git status clean). Category B 미발동 확정.
- **참고 파일**: `context/todos/TODO-02/03_prod-test.md`

### TODO-03 — Orin 추론 20 trial (PHYS_REQUIRED — TODO-02 와 단일 세션)

- **상태**: ✅ **PASSED (2026-05-19 사용자 검증 통과 + 추가 trial)** — 단축 평가 (실시 8 / 계획 20) → **8/8 = 100%**:
  - task1 front 1/1, task1 back 2/2 (학습 분포 + 학습 분포 외 1)
  - task2 front 2/2 (학습 분포 + 캔 mass 변화 1), task2 back 3/3 (학습 분포 + 로봇 각도 1 + 다중 perturbation 1)
  - 학습 분포 외 perturbation 4 trial 모두 견딤: 로봇 각도 마늘랩 방향 (2) + 캔 mass 변화 (1) + **다중 perturbation 로봇 각도 + 조명 50% 감소 (1)**
  - 사용자 단축 종료 결정 (M1.5/002 0/2 대비 100% 신호 명확)
  - 상세 결과: `orin/docs/leftarm_v2/003_eval_2026-05-19.md`
- **상태 (이전)**: 대기 (prod-test 미완료 — PHYS_REQUIRED 항목이므로 Phase 3 사용자 진행)
- **환경 레벨**: PHYS_REQUIRED (시연장 SO-101 좌측 아암 + 카메라 실제 하드웨어 필요)
- **사용자 검증 필요 사항**:

  TODO-02 dry-run 통과 후 연속 진행:

  ```bash
  # task1 5 front + 5 back
  bash orin/scripts/run_inference_leftarm_v2.sh live task1

  # task2 5 front + 5 back
  bash orin/scripts/run_inference_leftarm_v2.sh live task2
  ```

  - USB enumeration 변동 대비: trial 시작 전 `003_eval_2026-05-19.md` §trial 시작 전 체크리스트 실행
  - trial 간 그리퍼 살짝 열고 종료 (overload 방지 정책)
  - 결과를 `orin/docs/leftarm_v2/003_eval_2026-05-19.md` Trial 기록 표에 직접 기입
  - 완료 후 `/verify-result <자연어 결과>` 로 orchestrator 에 보고
  - 단축 종료 조건: 첫 trial 결과가 명백히 0% 면 사용자 결정 가능 (사이클 비고에 단축 사유 명시)

- **prod-test-runner 결과 요약**: PHYS_REQUIRED — 자동 검증 불가. 시연장 SO-101 + 카메라 실 하드웨어 의존. 사용자 Phase 3 진행 필요.
- **참고 파일**: `context/todos/TODO-02/03_prod-test.md` (TODO-03 별도 prod-test 는 PHYS_REQUIRED 특성상 미작성 — TODO-02 와 통합)
