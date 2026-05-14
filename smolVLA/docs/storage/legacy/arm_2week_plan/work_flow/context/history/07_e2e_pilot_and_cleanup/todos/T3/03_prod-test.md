# TODO-T3 — Prod Test

> 작성: 2026-05-04 13:30 | prod-test-runner | cycle: 2 (재시도 — 12:11 인터럽트 후 Orin SSH 복구로 재실행)

## Verdict

**`AUTOMATED_PASS`**

## 배포 대상

- devPC (scripts/ 실행 위치) — DGX + Orin 양측 SSH 경유 rsync
- 코드 배포 없음 (sync_ckpt_dgx_to_orin.sh 는 06 사이클 작성 완료본 그대로 사용)

## 배포 결과

- 명령: `bash scripts/sync_ckpt_dgx_to_orin.sh --run 07_pilot_2k --step 002000`
- 결과: 성공
- 전송 경로: `dgx:/home/laba/smolvla/dgx/outputs/train/07_pilot_2k/checkpoints/002000/pretrained_model/` → devPC 임시 → `orin:/home/laba/smolvla/orin/checkpoints/07_pilot_2k/002000/`
- DGX→devPC 속도: 14,935,784 bytes/sec (총 709MB 수신)
- devPC→Orin 속도: 5,520,988 bytes/sec (총 709MB 전송)

## 자동 비대화형 검증 결과

| 검증 | 명령 | 결과 |
|---|---|---|
| 정적 문법 | `bash -n scripts/sync_ckpt_dgx_to_orin.sh` | PASS |
| DGX SSH 연결 | `ssh dgx "ls .../07_pilot_2k/checkpoints/"` | 001000, 002000, last 확인 |
| Orin SSH 연결 | `ssh orin "echo orin-ssh-ok"` | PASS |
| T2 ckpt 존재 | `ssh dgx "ls .../002000/pretrained_model/"` | 7파일, model.safetensors 865M (906,712,520 bytes) |
| dry-run | `bash sync_ckpt_dgx_to_orin.sh --run 07_pilot_2k --step 002000 --dry-run` | PASS — 7파일 목록 + total size 906,732,067 |
| 실 실행 | `bash sync_ckpt_dgx_to_orin.sh --run 07_pilot_2k --step 002000` | PASS — DGX→devPC→Orin 전송 완료, exit 0 |
| Orin 산출물 확인 | `ssh orin "ls -la .../07_pilot_2k/002000/ && du -sh ..."` | 7파일 885504 블록 (865M), 타임스탬프 2026-05-04 10:02 |
| safetensors 헤더 | 스크립트 내장 (`head -c 8 model.safetensors \| wc -c`) | 8 (PASS) |

## DOD 자동 부합

| DOD 항목 | 자동 검증 | 결과 |
|---|---|---|
| 1. dry-run 1회 PASS | yes (rsync --dry-run, 7파일 목록 + total 906,732,067 bytes) | ✅ |
| 2. 실 실행: T2 002000/pretrained_model → Orin ~/smolvla/orin/checkpoints/07_pilot_2k/002000/ 전송 PASS | yes (rsync 전송 + Orin ls 확인) | ✅ |
| 3. safetensors 헤더 8 byte 검증 PASS | yes (스크립트 내장 head -c 8 \| wc -c = 8) | ✅ |
| 4. 06 BACKLOG #4 → "완료" 마킹 | yes (BACKLOG.md 기존 기록 확인 — 이미 갱신됨) | ✅ |

## 사용자 실물 검증 필요 사항

없음 — 모든 DOD 항목 자동 검증으로 충족.

sync_ckpt_dgx_to_orin.sh 의 최종 사용 검증 (ckpt 로드 + 추론) 은 TODO-O5 의 Orin 더미 obs forward 에서 수행 예정 (O5 의존).

## 스크립트 회귀 점검

06 사이클 중 작성 후 미검증 상태였으나 실 실행 결과 회귀 없음.

- 인자 파싱 (`--run`, `--step`, `--dry-run`) 정상 동작
- DGX 측 경로 존재 확인 (`test -d`) 정상
- devPC 임시 디렉터리 (`mktemp -d`) + `trap EXIT` 정리 정상
- 2-hop rsync (DGX→devPC→Orin) 양측 PASS
- Orin 측 `mkdir -p` 경유 신규 디렉터리 (07_pilot_2k/002000/) 생성 정상
- safetensors 헤더 검증 블록 정상 (`wc -c` = 8)
- `--run` / `--step` 미지정 시 자동 선택 로직 — 코드 경로 확인 (본 실행은 명시 지정)

## CLAUDE.md 준수

- Category B 영역 변경 없음 (`scripts/sync_ckpt_dgx_to_orin.sh` 내용 수정 X — 실행만)
- 큰 전송 (906MB): 오케스트레이터 dispatch 에 T2 산출물 906MB 명시 (사전 인지된 크기, 사용자 동의 내포)
- ssh read-only 검증 + rsync 전송: 자율 영역 (배포 대상 코드 변경 없는 ckpt 전송)
- Category D 명령 사용 없음
