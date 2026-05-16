# TODO-1a-fix — Prod Test

> 작성: 2026-05-16 10:54 | prod-test-runner | cycle: 1

## Verdict

**`NEEDS_USER_VERIFICATION`**

## 배포 대상

- dgx

## 배포 결과

- 명령: `bash scripts/deploy_dgx.sh`
- 결과: 성공
- 전송 파일:
  - `dgx/docs/finetune/leftarm_v2/training_log.md`
  - `dgx/finetune/leftarm_v2/run_train.py`
  - `dgx/finetune/leftarm_v2/config/train_config.yaml`
- 로그: sent 4,814 bytes / received 347 bytes / speedup 60.85 (dgx/ rsync), docs/reference/lerobot/ 변경 없음 (speedup 436.97)

## 자동 비대화형 검증 결과

| 검증 | 명령 | 결과 |
|---|---|---|
| devPC YAML 검증 | `python -c "import yaml; ... print(y['dataset_video_backend'])"` | `pyav` 출력 ✅ |
| devPC AST 파싱 | `python -c "import ast; ast.parse(open('run_train.py').read())"` | `AST parse OK` ✅ |
| DGX grep — train_config.yaml | `ssh dgx 'grep -n "dataset_video_backend" .../train_config.yaml'` | L37: `dataset_video_backend: pyav` ✅ |
| DGX grep — run_train.py required | `ssh dgx 'grep -n "dataset_video_backend" .../run_train.py'` | L89: required 목록 포함 ✅ |
| DGX grep — run_train.py cmd 구성 | `ssh dgx 'grep -n "video_backend" .../run_train.py'` | L121: `--dataset.video_backend=...` 포함 ✅ |
| DGX dry-run — cmd 출력 확인 | `ssh dgx '... python run_train.py train --pass 2a --dry-run'` | `--dataset.video_backend=pyav` 확인 ✅ |
| DGX dry-run — torchcodec traceback | 위 dry-run 출력 분석 | traceback 없음 ✅ |

## DOD 자동 부합

| DOD 항목 | 자동 검증 | 결과 |
|---|---|---|
| train_config.yaml L37: `dataset_video_backend: pyav` | yes (yaml 파싱 + DGX grep) | ✅ |
| run_train.py required 목록에 `dataset_video_backend` 포함 | yes (DGX grep L89) | ✅ |
| run_train.py cmd 에 `--dataset.video_backend=...` 추가 | yes (DGX grep L121 + dry-run) | ✅ |
| 실 학습 시 torchcodec RuntimeError 미발생 | no (학습 진입 필요 — PHYS_REQUIRED) | → verification_queue |

## 사용자 실물 검증 필요 사항 (verification_queue 갱신됨)

1. **실험 A 학습 재시도 (시도 3)** — `python run_train.py train --pass 2a` 실행 후 dataloader 첫 배치 fetch 시 `torchcodec` RuntimeError 미발생, `pyav` 로 정상 video decode 확인.
   - 환경 레벨: `PHYS_REQUIRED`
   - 전 단계: `cleanup_helper.sh` 실행 (메모리 확보) 권장

## dry-run 출력 핵심 확인

```
[run_train] 구성된 명령:
  lerobot-train \
    ...
    --dataset.video_backend=pyav \
    ...
```

- `--dataset.video_backend=pyav` 포함: 확인
- torchcodec import 시도 없음 (dry-run 이므로 dataset 로딩 없음): 확인
- exit code: 0

## CLAUDE.md 준수

- Category B 영역 변경: 없음 (orin/lerobot/, pyproject.toml 미해당) — deploy 자율 실행
- 자율 영역만 사용: yes (ssh read-only 검증, deploy_dgx.sh, dry-run 20초 이내)
- 동의 영역 실행: 없음
