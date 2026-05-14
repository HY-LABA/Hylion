# TODO-X3 cycle 2 — 자율성 분류 오류 수정

> 작성: 2026-05-01 15:36 | task-executor | cycle: 2

## 개요

TODO-X3 cycle 1 MAJOR_REVISIONS (Critical 2건 + Recommended 2건) 에 대한 수정 이력.

## 수정 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `docs/work_flow/context/todos/X3/01_implementation.md` | M | cycle 2 수정 4건 반영 (Critical 2 + Recommended 2) |

## Critical #1 — save_dummy_checkpoint.sh 자율성 재분류

- **근거**: `dgx/scripts/save_dummy_checkpoint.sh` 직접 Read — 주석 14~16행 "소요: 약 5~15분 (HF Hub 다운로드 + 1 step 학습 + 체크포인트 저장)", 본문 `lerobot-train --policy.device=cuda --steps=1 --save_checkpoint=true` 확인
- **수정**: 단계 8 을 "자율 가능 항목" → "긴 실행 항목 (사용자 동의 가능)" 섹션으로 이동
- **캐시 분기**: 캐시 HIT 시 자율 / MISS 시 사용자 동의 (smoke_test.sh 와 동일 패턴)

## Critical #2 — HF cache 경로 정정

- **근거**: `dgx/scripts/setup_train_env.sh` 19행 `HF_CACHE_DIR="${SMOLVLA_DIR}/.hf_cache"`, `dgx/README.md` 163행 `HF_HOME: /home/laba/smolvla/.hf_cache`, `dgx/scripts/preflight_check.sh` 43행 동일 경로 확인
- **수정**: `~/.cache/huggingface/hub/` → `~/smolvla/.hf_cache/hub/` (단계 6b + 단계 8 캐시 확인 명령)

## Recommended #1 — preflight 설명 정확화

- **근거**: `preflight_check.sh` 직접 Read — [1/5] venv/HF_HOME/CUDA_VISIBLE_DEVICES, [2/5] 메모리, [3/5] Walking RL, [4/5] Ollama, [5/5] 디스크
- **수정**: 단계 6 설명 "메모리 점검만" → "5가지 체크 (venv 격리·메모리·Walking RL·Ollama·디스크)"

## Recommended #2 — 04_dgx_lerobot_diff.md 매핑 추가

- 단계 4b 신규: `grep -E "2026-05-01.*TODO-X2"` devPC 측 coupled file 갱신 확인
- 검증 순서 권장 업데이트

## 다음 단계

code-tester cycle 2 재검증 → READY 시 prod-test-runner X3 진입
