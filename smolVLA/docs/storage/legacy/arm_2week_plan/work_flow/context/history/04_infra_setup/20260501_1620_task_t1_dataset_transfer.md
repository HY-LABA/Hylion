# task-executor — TODO-T1 dataset transfer scripts

> 2026-05-01 16:20 | task-executor | cycle: 1

## 작업 요약

DataCollector → DGX 데이터 전송 2종 스크립트 신규 작성:
1. `scripts/sync_dataset_collector_to_dgx.sh` — rsync 방식 (devPC 2-hop 경유)
2. `datacollector/scripts/push_dataset_hub.sh` — HF Hub 방식

사용자 결정 (답 D, 2026-05-01 14:18): **HF Hub + rsync 둘 다 지원** 확정 반영.

## 산출물

| 파일 | 종류 | 요약 |
|---|---|---|
| `scripts/sync_dataset_collector_to_dgx.sh` | 신규 | DataCollector data/ → DGX data/ rsync, devPC 2-hop, exit code 명시 |
| `datacollector/scripts/push_dataset_hub.sh` | 신규 | HF Hub push, LeRobotDataset.push_to_hub() 활용, --private 지원 |

## 레퍼런스 활용

- `sync_ckpt_dgx_to_orin.sh`, `sync_ckpt_dgx_to_datacollector.sh` — rsync 2-hop 패턴 동일 미러
- `docs/reference/lerobot/src/lerobot/datasets/lerobot_dataset.py:501` — `push_to_hub()` 구현체 확인: `HfApi.create_repo` + `upload_folder` + `card.push_to_hub` 패턴 직접 활용
- `docs/storage/09_datacollector_setup.md §5-3` — 네트워크 토폴로지 (devPC 2-hop) + SSH alias 이름 확인

## BACKLOG 02 #9 버그 답습 방지

BACKLOG 02 #9 두 버그 (deploy_dgx.sh):
1. DGX 측 대상 디렉터리 사전 생성 없음 → rsync error 11 → `ssh dgx "mkdir -p"` 선행 추가
2. rsync 실패 후 exit 0 반환 (마지막 echo 덮어씀) → 명시적 `RSYNC_EXIT=$?` + `exit "${RSYNC_EXIT}"` 적용

`sync_dataset_collector_to_dgx.sh` 반영:
- L115: `ssh "${DGX_HOST}" "mkdir -p ${DGX_DEST}"` (dry-run 아닐 때만)
- L105-108: `RSYNC1_EXIT=$?` + exit 명시
- L122-125: `RSYNC2_EXIT=$?` + exit 명시
- 스크립트 최상단 `set -e` 도 병행

## 핵심 결정

- rsync 경로: devPC 경유 2-hop (`sync_ckpt_dgx_to_orin.sh` 동일 패턴) — DataCollector (시연장) ↔ DGX (연구실) 다른 서브넷 가정
- HF Hub: Python `lerobot.datasets.lerobot_dataset.LeRobotDataset(root=).push_to_hub()` 호출
- private 지원: `--private` flag → `push_to_hub(private=True)`
- dry-run: rsync 는 `--dry-run` 그대로 전달; HF Hub 는 Python 실행 없이 경로/인증 확인만
