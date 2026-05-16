# TODO-02 — Prod Test

> 작성: 2026-05-16 12:10 | prod-test-runner | cycle: 1

## Verdict

**`NEEDS_USER_VERIFICATION`**

자동 검증 (deploy + AST + --help + 파일 존재 + ffmpeg + 디스크) 전체 통과. 단 dry-run 은 학습 도중 메모리 가용 28 GiB (기준선 30 GiB 미달) → skip 결정. 변환 실제 실행 (dry-run 포함 full path) 은 학습 종료 후 사용자 직접 수행 필요.

---

## 배포 대상

- dgx

## 배포 결과

- 명령: `bash scripts/deploy_dgx.sh`
- 결과: 성공
- 로그 요약:
  - `dgx/finetune/leftarm_v2/convert_to_image.py` — 31,035 bytes 전송
  - `dgx/docs/finetune/leftarm_v2/convert_to_image.md` — 9,588 bytes 전송
  - `dgx/finetune/README.md` — 전송 (convert_to_image 등록 포함)
  - `docs/reference/lerobot/` — incremental (변경 없음, 27,063 bytes 메타 sync)
  - sent 15,226 bytes / received 138 bytes, speedup 23.74

---

## 자동 비대화형 검증 결과

| 검증 | 명령 | 결과 |
|---|---|---|
| devPC AST | `python3 -c "import ast; ast.parse(...)"` | OK |
| devPC --help | `python3 convert_to_image.py --help` | 정상 출력. 모든 인자 표시 |
| DGX 파일 존재 | `ls -la ~/smolvla/dgx/finetune/leftarm_v2/convert_to_image.py ~/smolvla/dgx/docs/finetune/leftarm_v2/convert_to_image.md` | 양쪽 존재 확인 (31,035 / 9,588 bytes) |
| DGX AST | `python3 -c "import ast; ast.parse(...)"` | DGX AST OK |
| DGX venv --help | `source .arm_finetune/bin/activate && python convert_to_image.py --help` | 정상 출력. lazy import 동작 확인 — lerobot 없이 --help 완료 |
| DGX README 등록 | `grep -n "convert_to_image" ~/smolvla/dgx/finetune/README.md` | L18 에 `convert_to_image.py` 등록 확인 (`# ⑤ video dataset → image dataset 변환 (M1.5 OOM 대응)`) |
| DGX 절차 문서 존재 | `head -30 ~/smolvla/dgx/docs/finetune/leftarm_v2/convert_to_image.md` | 정상 출력. 배경·사전조건 포함 |
| ffmpeg 존재 | `which ffmpeg && ffmpeg -version` | `/usr/bin/ffmpeg`, version 6.1.1-3ubuntu5+esm7 |
| DGX 디스크 여유 | `df -h ~/smolvla` | 총 3.7T, 사용 256G, **가용 3.3T** — 변환 예상 20-50 GB 충분 |
| DGX 메모리 baseline | `free -h` | 총 121Gi, 사용 93Gi, **가용 28Gi** — 기준선 30 GiB 미달 |
| dry-run | (skip — 메모리 가용 < 30 GiB) | 학습 종료 후 사용자 수행 필요 |

---

## DOD 자동 부합

| DOD 항목 | 자동 검증 | 결과 |
|---|---|---|
| (a) `convert_to_image.py` 신규 작성 | yes (파일 존재 + AST) | ✅ |
| (a) 원본 무손상 (source_root 에 write 없음) | yes (code-tester 코드 추적 확인) | ✅ (code-test 위임) |
| (a) lerobot 형식 정확 (DEFAULT_IMAGE_PATH, image 컬럼 embed) | yes (code-tester cycle 2 확인) | ✅ (code-test 위임) |
| (a) video leak 회피 (ffmpeg subprocess 격리) | yes (code-tester 확인) | ✅ (code-test 위임) |
| (a) resumable (--skip-existing) | yes (--help 출력 확인) | ✅ |
| (a) incremental (--episodes) | yes (--help 출력 확인) | ✅ |
| (b) DGX 실제 실행 (원본→신규 110ep 전체) | no — 사용자 수행 필요 | → verification_queue |
| (c) 디스크 사용량 측정·기록 | no — 실제 변환 후 확인 | → verification_queue |
| Coupled Rule §6: README 갱신 | yes (DGX grep 확인) | ✅ |
| ffmpeg DGX 존재 | yes (which + version) | ✅ |

---

## 사용자 실물 검증 필요 사항 (verification_queue 추가됨)

1. **학습 종료 후 dry-run** — 변환 계획 (episode 수, frame 수, 디스크 추정) 출력 확인. 실제 ffmpeg 호출 없음.
2. **소규모 변환 (episodes 0-1) 검증** — 실제 ffmpeg 실행 + LeRobotDataset 로드 자동 검증 (스크립트 L748-763). PNG 생성 + parquet image 컬럼 embed 정상 동작 확인.
3. **전체 변환 (110 episodes)** — 완료 후 디스크 사용량 기록 + 학습 진입 (학습 스크립트는 별도 todo).

---

## 학습 종료 후 사용자 수행 절차

```bash
# 1. DGX SSH 진입
ssh dgx

# 2. 메모리 확인 (가용 30 GiB 이상 확보 필요)
free -h

# 3. 가상환경 활성화
source ~/smolvla/dgx/.arm_finetune/bin/activate
cd ~/smolvla/dgx

# 4. dry-run 먼저 (변환 계획 확인, 파일 쓰기 없음)
python finetune/leftarm_v2/convert_to_image.py \
    --source-root ~/smolvla/.hf_cache/lerobot/BaboGaeguri/leftarm_v2 \
    --target-root ~/smolvla/.hf_cache/lerobot/BaboGaeguri/leftarm_v2_image \
    --episodes 0-1 \
    --dry-run 2>&1 | head -50

# 5. 소규모 변환 (episodes 0-1, 실제 실행)
python finetune/leftarm_v2/convert_to_image.py \
    --source-root ~/smolvla/.hf_cache/lerobot/BaboGaeguri/leftarm_v2 \
    --target-root ~/smolvla/.hf_cache/lerobot/BaboGaeguri/leftarm_v2_image_test \
    --episodes 0-1 \
    --skip-existing

# 6. 소규모 결과 LeRobotDataset 로드 확인 (스크립트 내 자동 검증 L748-763 포함)
# → 변환 로그에서 "LeRobotDataset 로드 OK" 또는 warning 확인

# 7. 전체 변환 (110 episodes, 20-50 GB 예상, 수 시간 소요)
python finetune/leftarm_v2/convert_to_image.py \
    --source-root ~/smolvla/.hf_cache/lerobot/BaboGaeguri/leftarm_v2 \
    --target-root ~/smolvla/.hf_cache/lerobot/BaboGaeguri/leftarm_v2_image \
    --skip-existing
```

---

## CLAUDE.md 준수

- Category B 영역 (`orin/lerobot/`, `pyproject.toml`, `deploy_*.sh`) 변경된 배포: 없음 → 자율 배포 해당
- 자율 영역만 사용: yes (deploy_dgx.sh 자율, ssh read-only 검증 자율)
- 변환 실제 실행 금지 준수: yes (임무 제약 준수 — dry-run skip)
- DGX 환경 변경 (pip install 등) 없음: yes
