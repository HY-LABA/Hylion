# 20260501_1530 — TODO-T3 devPC sync hub 갱신

> 작성: 2026-05-01 15:30 | task-executor | spec: 04_infra_setup

## 요약

`scripts/deploy_datacollector.sh` 신규 작성. devPC → DataCollector 배포 스크립트. `deploy_orin.sh` / `deploy_dgx.sh` 의 형제 패턴.

## 작업 내역

### 신규 파일

- `scripts/deploy_datacollector.sh`
  - 동기화 대상 3개: `datacollector/`, `docs/reference/lerobot/`, `docs/storage/09_datacollector_setup.md`
  - SSH alias `datacollector` pre-check
  - 원격 디렉터리 `mkdir -p` 선행 (BACKLOG 02 #9 버그 1 방지)
  - `set -e` + `rsync ... || exit 1` (BACKLOG 02 #9 버그 2 방지)
  - `--dry-run` 플래그 지원 (rsync `-n` 옵션)

## 참조

- `09_datacollector_setup.md §5` — SSH alias 패턴, rsync 대상·exclude 정의
- `scripts/deploy_orin.sh`, `scripts/deploy_dgx.sh` — 기존 형제 패턴
- BACKLOG 02 #9 — deploy_dgx.sh 두 버그 기록
- `docs/work_flow/context/todos/T3/01_implementation.md` — 상세 구현 보고서
