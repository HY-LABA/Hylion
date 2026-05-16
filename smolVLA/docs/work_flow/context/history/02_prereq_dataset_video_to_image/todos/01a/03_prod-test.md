# TODO-1a — Prod Test

> 작성: 2026-05-15 20:50 | prod-test-runner | cycle: 1

## Verdict

**`NEEDS_USER_VERIFICATION`**

---

## 배포 대상

- DGX (dgx/ 변경만 해당. orin/ 변경 없음)

## Category B 변경 여부 점검

변경 파일:
- `dgx/finetune/leftarm_v2/experiments/cleanup_helper.sh` — 신규 생성
- `dgx/finetune/leftarm_v2/experiments/exp_a_cleanup_attempt3.md` — 신규 생성
- `dgx/docs/finetune/leftarm_v2/training_log.md` — 시도 3 섹션 추가
- `dgx/finetune/README.md` — experiments/ 등록 (Coupled Rule §6)

Category B 해당 여부:
- `orin/lerobot/`: 미변경
- `pyproject.toml` 류: 미변경
- `orin/scripts/setup_env.sh`: 미변경
- `scripts/deploy_*.sh`: 미변경 (스크립트 자체 변경 없음)
- `.gitignore`, `.git/info/exclude`: 미변경

결론: **Category B 변경 없음 → 자율 deploy 가능**

## 배포 결과

- 명령: `bash scripts/deploy_dgx.sh`
- 결과: 성공
- 전송 파일 목록:
  - `docs/finetune/leftarm_v2/training_log.md`
  - `finetune/README.md`
  - `finetune/leftarm_v2/experiments/cleanup_helper.sh`
  - `finetune/leftarm_v2/experiments/exp_a_cleanup_attempt3.md`
- 전송량: sent 9,001 bytes / received 337 bytes / speedup 33.37

## 자동 비대화형 검증 결과

| 검증 | 명령 | 결과 |
|---|---|---|
| devPC bash -n | `bash -n cleanup_helper.sh` | SYNTAX OK |
| DGX experiments/ 존재 | `ssh dgx 'ls -la ~/smolvla/dgx/finetune/leftarm_v2/experiments/'` | 2 파일 확인 (cleanup_helper.sh 4924B, exp_a_cleanup_attempt3.md 7493B) |
| DGX bash -n | `ssh dgx 'bash -n cleanup_helper.sh'` | SYNTAX OK |
| DGX exp_a_cleanup_attempt3.md head | `ssh dgx 'head -5 ...'` | 정상 (제목·목적 확인) |
| DGX training_log.md 시도 3 | `ssh dgx 'grep -n "시도 3" ...'` | 3건 매칭 (195, 209, 232행) |
| DGX finetune/README.md experiments/ | `ssh dgx 'grep -n "experiments/" ...'` | 17행 등록 확인 |
| DGX free -h (baseline) | `ssh dgx 'free -h'` | RAM 총 121Gi / 가용 112Gi (학습 전 여유 충분) |
| DGX cleanup dry-run | `ssh dgx 'bash cleanup_helper.sh --dry-run'` | exit 0, 전체 단계 dry-run 출력 정상 |

SSH 검증: **5/5 통과 + dry-run exit 0**

## dry-run 출력 요약

```
[cleanup_helper] ===== DGX 학습 전 환경 cleanup 시작 =====
[cleanup_helper] (--dry-run 모드 — 실제 kill 없음)
[DRY-RUN] pkill -9 -f code 2>/dev/null || true
[DRY-RUN] pkill -9 -f 'claude' 2>/dev/null || true
[DRY-RUN] pkill -9 -f firefox 2>/dev/null || true
[DRY-RUN] sync
[DRY-RUN] free -h
[DRY-RUN] awk '/MemAvailable/ {print $2}' /proc/meminfo  (100GB+ 검증)
[cleanup_helper] (h) page cache drop 안내: sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'
[cleanup_helper] ===== cleanup 완료. 학습을 시작해도 됩니다. =====
```

exit code: 0

## DGX 메모리 Baseline (2026-05-15 실험 A 직전)

| 항목 | 값 |
|---|---|
| 총 RAM | 121 Gi |
| 사용 중 | 9.3 Gi |
| 가용 | 112 Gi |
| 스왑 | 0 B (없음) |

## DOD 자동 부합

| DOD 항목 | 자동 검증 | 결과 |
|---|---|---|
| cleanup_helper.sh 존재 + 문법 오류 없음 | yes (bash -n, DGX/devPC) | ✅ |
| exp_a_cleanup_attempt3.md 존재 + 절차 문서화 | yes (head 확인) | ✅ |
| training_log.md 시도 3 섹션 추가 | yes (grep) | ✅ |
| finetune/README.md experiments/ 등록 | yes (grep) | ✅ |
| cleanup_helper.sh --dry-run 정상 작동 | yes (exit 0) | ✅ |
| 실험 A 실제 학습 진입 (시도 3 실행) | no — PHYS_REQUIRED | → verification_queue |

## 사용자 실물 검증 필요 사항 (verification_queue 추가됨)

1. **실험 A 학습 진입 (PHYS_REQUIRED)** — 사용자가 DGX 에서 직접 실행·관찰
   - cleanup 실행 → 학습 시작 → OOM 발생 여부 모니터링
   - 환경 레벨: `PHYS_REQUIRED` (GPU 학습, >5분, kill 발생)

### 사용자 실험 A 절차 (핵심 명령 시퀀스)

```bash
# 1. DGX SSH 진입
ssh dgx

# 2. 학습 전 cleanup 실행 (실제 kill — VSCode/claude/firefox 종료됨)
bash ~/smolvla/dgx/finetune/leftarm_v2/experiments/cleanup_helper.sh
# sudo 가능하면 추가: sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'
# free -h 로 MemAvailable 100GB+ 확인

# 3. 가상환경 활성화
source ~/smolvla/dgx/.arm_finetune/bin/activate

# 4. 학습 실행 (exp_a_cleanup_attempt3.md 의 설정 따름)
cd ~/smolvla/dgx
bash finetune/leftarm_v2/experiments/exp_a_cleanup_attempt3.md
# 또는 절차 문서 참고하여 수동 실행:
# python -m lerobot.scripts.train \
#   --config-path finetune/leftarm_v2/config \
#   --config-name base_config \
#   training.num_workers=2 training.prefetch_factor=1

# 5. 학습 모니터링 (별도 tmux 창)
watch -n 5 nvidia-smi
watch -n 5 free -h

# 6. OOM 발생 여부 확인
# - 발생: BACKLOG에 실험 B (num_workers=0) 진행
# - 미발생: 시도 3 학습 완료 대기 → eval_freq 체크포인트 확인
```

## CLAUDE.md 준수

- Category B 변경 여부 점검: 완료 — 해당 없음 → 자율 deploy 실행
- deploy_dgx.sh 스크립트 자체 미변경 (Category B 보존)
- 학습 진입 명령 실행 X (PHYS_REQUIRED 준수)
- cleanup_helper.sh 실제 실행 X (kill 발생 — dry-run 만 실행)
