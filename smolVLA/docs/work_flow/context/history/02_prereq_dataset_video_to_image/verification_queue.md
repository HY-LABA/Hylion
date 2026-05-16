# Phase 3 검증 대기 큐

> Phase 2 진행 중 prod-test-runner 가 완료한 항목 + 사용자 실물 검증이 필요한 항목을 누적. 모든 todo 자동화 종료 시 메인이 본 큐를 사용자에게 일괄 제시.

---

## wrap-spec 처리 결정 (2026-05-16)

| 항목 | 결정 | 비고 |
|---|---|---|
| TODO-1a | **✅ 통과** | 학습 데이터로 backend 변수 분리 + cleanup 시간벌기 수준 확정. cleanup 자체는 미수행이나 목적 (researcher §5 1단계 검증) 달성 |
| TODO-1a-fix | **✅ 통과** | pyav 우회 작동 + 학습 진입 성공 + 동일 누수 패턴 → backend 무관 확정 |
| TODO-02 | **⏸ 연기 → BACKLOG** | 자동화 (스크립트 작성) 통과, 실제 110ep 변환은 사용자가 진행 중 또는 시작 전. 트리거: "DGX 110ep 변환 완료 후 결과 보고" |
| TODO-03 | **⏸ 연기 → BACKLOG** | 본 사이클 시작 안 함. 트리거: "TODO-02 변환 결과 보고 후" |

---

### [TODO-1a] 실험 A — cleanup 강화 + 시도 3

- **상태**: 자동 검증 통과 (NEEDS_USER_VERIFICATION)
- **환경 레벨**: `PHYS_REQUIRED`
- **사용자 검증 필요 사항**:
  1. DGX 에서 `cleanup_helper.sh` 실제 실행 (VSCode·Claude·Firefox kill 발생) → 메모리 100GB+ 확보 확인
  2. 실험 A 학습 진입 (시도 3): `python -m lerobot.scripts.train ...` 실행 → OOM 발생 여부 모니터링
  3. OOM 발생 시 → 실험 B (num_workers=0) 로 전환 결정
  4. OOM 미발생 시 → 학습 완료 후 체크포인트 정상 저장 확인
- **prod-test-runner 결과 요약**:
  - deploy 성공 (dgx/ rsync, sent 9,001 bytes)
  - SSH 검증 5/5 통과 (experiments/ 파일 존재, bash -n 문법 OK, training_log 시도 3 섹션, README.md experiments/ 등록)
  - dry-run exit 0 — 전체 cleanup 단계 정상 작동 확인
  - DGX 메모리 baseline: 총 121Gi / 가용 112Gi (실험 A 직전 기준)
- **참고 파일**: `context/todos/01a/03_prod-test.md`
- **실험 A 핵심 절차**:
  ```bash
  ssh dgx
  bash ~/smolvla/dgx/finetune/leftarm_v2/experiments/cleanup_helper.sh
  # (선택) sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'
  source ~/smolvla/dgx/.arm_finetune/bin/activate
  cd ~/smolvla/dgx
  # exp_a_cleanup_attempt3.md 절차 참고하여 학습 실행
  ```

---

### [TODO-1a-fix] video_backend=pyav 강제 적용

- **상태**: 자동 검증 통과 (NEEDS_USER_VERIFICATION)
- **환경 레벨**: `PHYS_REQUIRED`
- **사용자 검증 필요 사항**:
  1. 실험 A 학습 재시도 (시도 3) — `python run_train.py train --pass 2a` 실행 후 dataloader 첫 배치 fetch 시 `torchcodec RuntimeError` 미발생 확인. `pyav` 로 정상 video decode 되어야 함.
- **prod-test-runner 결과 요약**:
  - deploy 성공 (dgx/ rsync, sent 4,814 bytes — train_config.yaml, run_train.py, training_log.md 3개 파일)
  - devPC YAML 파싱: `dataset_video_backend: pyav` 확인
  - DGX grep 3개 라인 확인: train_config.yaml L37, run_train.py L89 (required), run_train.py L121 (cmd)
  - DGX dry-run 성공: `--dataset.video_backend=pyav` cmd 포함 확인, torchcodec traceback 없음, exit 0
- **참고 파일**: `context/todos/01a_fix/03_prod-test.md`
- **학습 진입 절차**:
  ```bash
  ssh dgx
  # cleanup_helper.sh 먼저 실행 (메모리 확보)
  bash ~/smolvla/dgx/finetune/leftarm_v2/experiments/cleanup_helper.sh
  source ~/smolvla/dgx/.arm_finetune/bin/activate
  cd ~/smolvla/dgx/finetune/leftarm_v2
  python run_train.py train --pass 2a
  # 학습 시작 후 첫 배치 fetch 시 torchcodec RuntimeError 없으면 pyav 정상 적용 확인
  ```

---

### [TODO-02] convert_to_image.py — video → image dataset 변환 스크립트

- **상태**: 자동 검증 통과 (NEEDS_USER_VERIFICATION)
- **환경 레벨**: `SSH_AUTO` (dry-run·소규모 변환) + `PHYS_REQUIRED` (전체 110 episode 변환)
- **skip 사유**: prod-test 시점 DGX 학습 도중 — 메모리 가용 28 GiB (기준선 30 GiB 미달) → dry-run 포함 변환 실행 전체 skip
- **사용자 검증 필요 사항**:
  1. **dry-run 확인** — 변환 계획 (episode 수, frame 수, 디스크 추정) 출력 확인. 실제 파일 쓰기 없음.
  2. **소규모 변환 (episodes 0-1)** — PNG 생성 + parquet image 컬럼 embed 정상 동작. 스크립트 L748-763 LeRobotDataset 자동 로드 검증 포함.
  3. **전체 변환 (110 episodes)** — 완료 후 디스크 사용량 기록. 예상 20-50 GB.
- **prod-test-runner 결과 요약**:
  - deploy 성공 (dgx/ rsync, sent 15,226 bytes — convert_to_image.py 31,035 bytes + convert_to_image.md 9,588 bytes + README.md)
  - devPC AST OK, devPC --help 정상
  - DGX 파일 존재 확인 (31,035 / 9,588 bytes), DGX AST OK
  - DGX venv --help 정상 (lazy import 동작 — lerobot 없이 --help 완료)
  - DGX README L18 등록 확인 (`convert_to_image.py # ⑤ video dataset → image dataset 변환`)
  - ffmpeg /usr/bin/ffmpeg version 6.1.1-3ubuntu5+esm7 존재
  - DGX 디스크 가용 3.3T (변환 예상 20-50 GB 충분)
  - DGX 메모리 baseline: 총 121Gi, 가용 28Gi (학습 도중 — dry-run skip)
- **참고 파일**: `context/todos/02/03_prod-test.md`
- **학습 종료 후 변환 절차**:
  ```bash
  ssh dgx
  free -h   # 가용 30 GiB 이상 확인

  source ~/smolvla/dgx/.arm_finetune/bin/activate
  cd ~/smolvla/dgx

  # Step 1: dry-run (변환 계획 출력)
  python finetune/leftarm_v2/convert_to_image.py \
      --source-root ~/smolvla/.hf_cache/lerobot/BaboGaeguri/leftarm_v2 \
      --target-root ~/smolvla/.hf_cache/lerobot/BaboGaeguri/leftarm_v2_image \
      --episodes 0-1 \
      --dry-run 2>&1 | head -50

  # Step 2: 소규모 변환 (episodes 0-1)
  python finetune/leftarm_v2/convert_to_image.py \
      --source-root ~/smolvla/.hf_cache/lerobot/BaboGaeguri/leftarm_v2 \
      --target-root ~/smolvla/.hf_cache/lerobot/BaboGaeguri/leftarm_v2_image_test \
      --episodes 0-1 \
      --skip-existing

  # Step 3: 전체 변환 (110 episodes, 수 시간 소요)
  python finetune/leftarm_v2/convert_to_image.py \
      --source-root ~/smolvla/.hf_cache/lerobot/BaboGaeguri/leftarm_v2 \
      --target-root ~/smolvla/.hf_cache/lerobot/BaboGaeguri/leftarm_v2_image \
      --skip-existing
  ```
