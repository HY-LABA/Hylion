# TODO-T1 cycle 2 수정 이력

> 작성: 2026-05-01 18:00 | task-executor | cycle: 2

## 배경

code-tester MINOR_REVISIONS (Critical 0, Recommended 3) → cycle 2 수정.

## 수정 파일

| 경로 | 변경 종류 | 요약 |
|---|---|---|
| `scripts/sync_dataset_collector_to_dgx.sh` | M | R1: dead exit code 제거 + set -e 주석 명확화 |
| `datacollector/scripts/push_dataset_hub.sh` | M | R2: heredoc 환경변수 전달 방식 전환 / R3: repo_id 의미 주석 추가 |

## 수정 내용

### R1 — sync_dataset_collector_to_dgx.sh

- L124-128 (`RSYNC1_EXIT=$?` 분기) 제거, L142-146 (`RSYNC2_EXIT=$?` 분기) 제거
- 각 rsync 직전에 `# set -e 가 rsync non-zero 반환 시 즉시 abort 보장 (BACKLOG 02 #9 버그 2 대응).` 주석 추가
- 결과: set -e 단독 보호로 충분함을 명시, dead code 제거로 구조 명확화

### R2 — push_dataset_hub.sh heredoc 환경변수 전달

- `python3 - <<PYEOF` → `DATASET_PATH=... REPO_ID=... python3 - <<'PYEOF'`
- Python 내부: bash 변수 직접 삽입 → `os.environ["DATASET_PATH"]`, `os.environ["REPO_ID"]` 등으로 전환
- single-quote `'PYEOF'` 로 heredoc 변수 확장 차단
- 공백·특수문자 포함 경로/repo-id 에 대한 Python syntax error 위험 제거

### R3 — push_dataset_hub.sh repo_id 주석

- `dataset = LeRobotDataset(repo_id=repo_id, root=dataset_path)` 직전에 주석 추가:
  `# repo_id 는 HF Hub push 대상 ID. 로컬 dataset 내부 메타의 repo_id 와 달라도 push_to_hub() 는 이 값(self.repo_id)을 사용.`
