# TODO-T1 — DataCollector → DGX 데이터 전송

> 작성: 2026-05-01 16:20 | task-executor | cycle: 1

## 목표

DataCollector 수집 dataset 을 DGX 학습 환경으로 전송하는 2종 스크립트 작성.
사용자 답 D (2026-05-01 14:18): **HF Hub + rsync 직접 둘 다 지원** 확정.

## 사전 점검 결과

- 사용자 답 D (HF Hub + rsync 둘 다) 확정: `docs/storage/09_datacollector_setup.md §5-3` 에 이미 반영됨 ("사용자 답 (2026-05-01): HF Hub + rsync 직접 둘 다 지원")
- lerobot upstream push_to_hub 패턴 추출: `docs/reference/lerobot/src/lerobot/datasets/lerobot_dataset.py:501-575` — `HfApi.create_repo(repo_id, private, exist_ok=True)` → `upload_folder(folder_path=root)` → `card.push_to_hub()` 시퀀스 확인
- D1 §5 네트워크 경로 정보 추출: DataCollector (시연장 WiFi) ↔ DGX (연구실 WiFi) — 다른 서브넷 가능성 높음 → devPC 경유 2-hop 선택 (`09_datacollector_setup.md §5-4` 토폴로지 참조)
- BACKLOG 02 #9 두 버그 답습 X 매핑:
  - 버그 1 (mkdir 없음): `ssh dgx "mkdir -p ${DGX_DEST}"` 선행 추가 (sync_dataset_collector_to_dgx.sh L115)
  - 버그 2 (exit code 0 덮어씀): `RSYNC1_EXIT=$?` + `RSYNC2_EXIT=$?` 명시 + `exit "${RSYNC_EXIT}"` 적용 (L105-108, L122-125)
- Category A 확인: `scripts/sync_*.sh` 는 `docs/reference/` 미변경 ✓
- Category B 확인: `scripts/sync_*.sh` 는 `deploy_*.sh` 아님 — 일반 작업 (Category B 명시 외)

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `scripts/sync_dataset_collector_to_dgx.sh` | 신규 | DataCollector→DGX rsync, devPC 2-hop, exit code 명시, SSH alias pre-check |
| `datacollector/scripts/push_dataset_hub.sh` | 신규 | HF Hub push, LeRobotDataset.push_to_hub() 활용, --private/--dry-run 지원 |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 ✓, Category D 금지 명령 미사용 ✓
- Category B 비해당: `scripts/sync_*.sh` 는 `deploy_*.sh` 명시 영역 아님. 일반 작업으로 처리.
- `datacollector/scripts/push_dataset_hub.sh` 도 일반 작업 (Category B 미해당)
- Coupled File Rules 비해당: `orin/lerobot/`, `dgx/lerobot/`, `pyproject.toml` 변경 없음
- 레퍼런스 활용: `docs/reference/lerobot/src/lerobot/datasets/lerobot_dataset.py:501` 의 `push_to_hub()` 패턴 직접 차용
- rsync 패턴: `scripts/sync_ckpt_dgx_to_orin.sh` 및 `scripts/sync_ckpt_dgx_to_datacollector.sh` 와 동일 2-hop 구조 미러

## 변경 내용 요약

`sync_dataset_collector_to_dgx.sh` 는 기존 `sync_ckpt_dgx_to_orin.sh` 패턴을 그대로 적용하여 DataCollector 의 `~/smolvla/datacollector/data/<name>/` 를 devPC 임시 디렉터리 경유 DGX 의 `~/smolvla/dgx/data/<name>/` 로 전송한다. `--dataset all` 로 전체 동기화, `--dataset <name>` 으로 특정 dataset 만 전송 가능. SSH alias pre-check (datacollector, dgx) 와 DGX 측 `mkdir -p` 선행 실행, 명시적 exit code 전파로 BACKLOG 02 #9 버그 패턴을 방지했다.

`push_dataset_hub.sh` 는 lerobot upstream 의 `LeRobotDataset.push_to_hub()` 를 Python 인라인 스크립트로 호출한다. HF_TOKEN 환경변수 또는 `huggingface-cli login` 캐시 중 하나로 인증을 확인하고, `--private` flag 로 private repo 생성을 지원한다. `--dry-run` 시에는 Python 을 실행하지 않고 경로·인증 상태만 확인하여 DataCollector 머신 미셋업 상태에서도 안전하게 테스트 가능하다. push 대상은 `lerobot-record` 가 생성한 정규 LeRobotDataset 포맷을 가정하며, 포맷 불일치 시 명확한 오류 메시지를 출력한다.

## 핵심 결정

- rsync 네트워크 경로: devPC 경유 2-hop (`sync_ckpt_dgx_to_orin.sh` 패턴 미러)
  - 근거: DataCollector (시연장 WiFi) ↔ DGX (연구실) 가 다른 서브넷일 가능성이 높고, devPC 가 양쪽 모두 SSH 접근 가능한 sync hub 역할 담당 (`09_datacollector_setup.md §5-4`)
- HF Hub: `lerobot.datasets.lerobot_dataset.LeRobotDataset(root=).push_to_hub()` — upstream 구현 직접 활용
- private repo 지원: `--private` flag → Python `push_to_hub(private=True)`
- 인증: `HF_TOKEN` 환경변수 우선, 없으면 `huggingface_hub.HfFolder.get_token()` 캐시 확인

## 검증 시나리오 정의 (prod-test-runner 입력)

### 자율 가능

1. devPC: `bash smolVLA/scripts/sync_dataset_collector_to_dgx.sh --dataset dummy --dry-run`
   - SSH alias `datacollector` 미등록 → `[sync-dataset] ERROR: ~/.ssh/config 에 'Host datacollector' alias 가 없습니다.` 로 friendly error 출력 + exit 1 확인
2. devPC: `bash smolVLA/scripts/sync_dataset_collector_to_dgx.sh --dry-run` (--dataset 없음)
   - `[sync-dataset] ERROR: --dataset <name|all> 필수 인자 없음.` 확인
3. devPC: `bash smolVLA/datacollector/scripts/push_dataset_hub.sh --dry-run` (필수 인자 없음)
   - `[push-hub] ERROR: --dataset <local_path> 필수 인자 없음.` 확인
4. devPC (가상): `/tmp/dummy_dataset/` 더미 디렉터리 생성 후 `push_dataset_hub.sh --dataset /tmp/dummy_dataset --repo-id testuser/test --dry-run`
   - HF_TOKEN 없으면 인증 에러, 있으면 dry-run 파일 목록 출력 확인
5. bash 문법 검증: `bash -n scripts/sync_dataset_collector_to_dgx.sh` + `bash -n datacollector/scripts/push_dataset_hub.sh`

### 사용자 실물 필요 (verification_queue)

1. TODO-D3 완료 후 DataCollector 머신 셋업 + SSH alias 등록
2. DataCollector 에서 `lerobot-record` 로 dummy dataset 생성 (1-2 에피소드)
3. `bash scripts/sync_dataset_collector_to_dgx.sh --dataset <name> --dry-run` — 경로 확인
4. `bash scripts/sync_dataset_collector_to_dgx.sh --dataset <name>` — 실 rsync 전송 + DGX 파일 수 검증
5. HF Hub push: `export HF_TOKEN=<사용자 토큰>` + `bash datacollector/scripts/push_dataset_hub.sh --dataset ~/smolvla/datacollector/data/<name> --repo-id <HF_USER>/<name> --private` — HF Hub 에 업로드 확인
6. DGX 에서 HF Hub 통해 dataset 다운로드 확인 (`LeRobotDataset(repo_id=...)`)

## 잔여 리스크

- 사용자 HF_TOKEN 미설정 시 `push_dataset_hub.sh` 인증 오류 (의도된 동작, 정상)
- DataCollector 머신 미존재 시 rsync dry-run 도 datacollector SSH 연결 실패 → 자율 dry-run 은 SSH alias 없음 친절 에러로 처리됨
- DataCollector 와 DGX 가 동일 서브넷일 경우 devPC 2-hop 대신 직접 rsync 가 더 빠를 수 있음 — 직접 rsync 는 현재 스크립트 미지원 (필요 시 향후 `--direct` flag 추가 가능)
- `push_dataset_hub.sh` 가 DataCollector 머신의 lerobot venv (`.hylion_collector`) 를 가정 — TODO-D2 venv 셋업 완료 후 동작
- `upload_large_folder` flag 는 현재 미지원 (대용량 dataset 시 필요할 수 있음 — BACKLOG 후보)

## 검증 필요 (다음 단계)

- code-tester: 두 스크립트 bash 문법 (`bash -n`), BACKLOG 02 #9 버그 답습 없음 재확인, HF Hub API 사용 정확성 (LeRobotDataset.push_to_hub 호출부), exclude 패턴 (`__pycache__/`, `*.pyc`, `.git/`) 확인
- prod-test-runner: dummy 인자 오류 시나리오 dry-run + bash -n 문법 검증 + verification_queue 추가

---

## cycle 2 수정 (2026-05-01 18:00)

### Recommended #1 해소 — dead exit code 제거 + set -e 주석 명확화

- 채택 옵션: 코드 1 (dead code 제거)
- 변경 부분: `sync_dataset_collector_to_dgx.sh` L124-128, L142-146
  - `RSYNC1_EXIT=$?` / `if [ "${RSYNC1_EXIT}" -ne 0 ]` 분기 제거
  - `RSYNC2_EXIT=$?` / `if [ "${RSYNC2_EXIT}" -ne 0 ]` 분기 제거
  - 각 rsync 직전 주석: `# set -e 가 rsync non-zero 반환 시 즉시 abort 보장 (BACKLOG 02 #9 버그 2 대응).`
- BACKLOG 02 #9 버그 2 보호: set -e 단독으로 충분. 주석으로 의도 명시.

### Recommended #2 해소 — heredoc 환경변수 전달 방식 전환

- `python3 - <<PYEOF` → `DATASET_PATH=... REPO_ID=... PRIVATE=... BRANCH=... python3 - <<'PYEOF'`
- Python 내부: `${VAR}` 직접 삽입 → `os.environ["VAR"]` 으로 전환
- heredoc 인자 single-quote `'PYEOF'` 로 bash 변수 확장 차단
- 공백·특수문자 포함 경로/repo-id 에서 Python syntax error 위험 제거

### Recommended #3 해소 — LeRobotDataset repo_id 의미 주석

- `dataset = LeRobotDataset(repo_id=repo_id, root=dataset_path)` 직전:
  `# repo_id 는 HF Hub push 대상 ID. 로컬 dataset 내부 메타의 repo_id 와 달라도 push_to_hub() 는 이 값(self.repo_id)을 사용.`
- push_to_hub() 시그니처 (cycle 1 code-tester 검증: private, branch 인자) 유지 확인.

### 다음 단계

- 본 cycle 2 종료 → prod-test-runner T1 진입
- prod-test-runner: 자율 5단계 + verification_queue 6건 (`§검증 시나리오` 참조)

| Recommended 이슈 | 수정 |
|---|---|
| R1: dead exit code (RSYNC*_EXIT 분기) | 분기 제거 + set -e 주석 명확화 |
| R2: heredoc bash 변수 직접 삽입 | `'PYEOF'` single-quote + os.environ 전달 방식 전환 |
| R3: LeRobotDataset repo_id 의미 불명확 | push 대상 HF ID + 로컬 메타와의 관계 명시 주석 추가 |
