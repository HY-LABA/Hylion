# TODO-T1 — Code Test

> 작성: 2026-05-01 17:00 | code-tester | cycle: 1

## Verdict

**`MINOR_REVISIONS`**

Critical 이슈 0건. Recommended 개선 사항 3건 (기준: 3건 이상 → MINOR_REVISIONS).

---

## 단위 테스트 결과

```
bash -n 실행 불가 — Bash 도구 차단 (sandbox deny).
두 스크립트 모두 Read 직독 + 정적 분석으로 대체.
ANOMALIES.md SKILL_GAP #1 누적 필요 (orchestrator 처리).
```

---

## Lint·Type 결과

```
bash -n 차단으로 자동 lint 불가. Read 직독 정적 분석 수행.

sync_dataset_collector_to_dgx.sh:
- set -e 선언: L28 ✓
- while 루프 인자 파싱: L39-57 구문 정상
- 변수 quoting: 주요 변수 "${VAR}" 처리됨 ✓
- trap 'rm -rf "${TMP_DIR}"' EXIT: L101 ✓ (단, TMP_DIR 이 빈 문자열이 될 가능성 없음 — mktemp 실패 시 set -e 가 중단)
- rsync ${DRY_RUN} (unquoted): DRY_RUN 이 공백 포함 가능하면 word split 위험.
  → 현재 값은 "--dry-run" 또는 "" 이므로 실제 위험 없음. 스타일 이슈.

push_dataset_hub.sh:
- set -e 선언: L39 ✓
- DATASET_PATH tilde 확장: L97 DATASET_PATH_EXPANDED="${DATASET_PATH/#\~/$HOME}" ✓
- Python heredoc 내 bash 변수 삽입: ${DATASET_PATH_EXPANDED}, ${REPO_ID} 직접 삽입
  → 경로·repo-id 에 공백·특수문자 포함 시 Python 코드 syntax error 가능성 (Recommended)
- PUSH_EXIT=$? 이후 set -e 환경: python3 heredoc 실패 시 set -e 가 L199 이후로 진행하지 않을 수 있음
  → PUSH_EXIT 처리 (L201-204) 와 set -e 가 중복. 기능 저하 없음. 스타일 이슈.
```

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. `scripts/sync_dataset_collector_to_dgx.sh` 신규 존재 (rsync) | ✅ | 파일 존재 확인 |
| 2. `datacollector/scripts/push_dataset_hub.sh` 신규 존재 (HF Hub) | ✅ | 파일 존재 확인 |
| 3. dry-run dummy dataset 동작 시나리오 정의 | ✅ | `01_implementation.md §검증 시나리오` 에 자율 5건 + 사용자 실물 6건 명시 |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| R1 | `sync_dataset_collector_to_dgx.sh` L117-128 | `set -e` + `RSYNC1_EXIT=$?` 패턴: `set -e` 환경에서 rsync 가 non-zero 반환 시 L118 이전에 스크립트가 abort → `RSYNC1_EXIT=$?` / `RSYNC2_EXIT=$?` 분기는 도달 불가능 코드(dead code). `set -e` 자체가 rsync 실패 전파를 보장하므로 기능 저하는 없음. 단 task-executor 보고서가 "BACKLOG 02 #9 버그 2 명시 exit code 처리로 완전 해소"라고 주장하지만 실제로는 `set -e` 가 처리함 — 주석/문서 설명 수정 권장. 참조 패턴 `sync_ckpt_dgx_to_orin.sh` 도 동일 패턴이므로 기존 일관성은 유지됨. |
| R2 | `push_dataset_hub.sh` L166-199 (Python heredoc) | bash 변수(`${DATASET_PATH_EXPANDED}`, `${REPO_ID}`)를 heredoc 내 Python 코드에 직접 삽입 — 경로나 repo-id 에 공백·큰따옴표·역슬래시 포함 시 Python syntax error 발생 가능. 현재 `DATASET_PATH_EXPANDED` 는 tilde 확장 외 검증 없고, `REPO_ID` 는 `^[^/]+/[^/]+$` regex 만 검증. Python 인자를 환경변수로 전달하는 방식(`DATASET_PATH="${DATASET_PATH_EXPANDED}" python3 - <<PYEOF` + `os.environ`)이 더 안전함. |
| R3 | `push_dataset_hub.sh` L184 | `LeRobotDataset(repo_id=repo_id, root=dataset_path)` — `lerobot-record` 로 수집된 로컬 dataset 의 내부 `repo_id`(meta에 저장된 값)와 스크립트 `--repo-id` 인자가 다를 경우 동작 불확실. `push_to_hub()` 내부는 `self.repo_id`(=생성자 인자)를 push 대상으로 사용하므로 기능은 작동하나, `root` 에 이미 다른 `repo_id` 메타가 있으면 `LeRobotDatasetMetadata` 가 기대값 불일치 경고 또는 HF Hub 접근을 시도할 수 있음. 스크립트 주석에 "생성자 repo_id 는 push 대상 HF repo ID 임 — 로컬 dataset 의 기존 repo_id 와 달라도 됨"을 명시하거나, `push_to_hub()` 에 `repo_id` 오버라이드 인자가 없음을 확인하는 주석 추가 권장. |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경, `.claude/` 미변경 |
| B (자동 재시도 X) | ✅ | `scripts/sync_*.sh` 는 `deploy_*.sh` 명시 영역 아님 — 일반 작업으로 처리 정확. `datacollector/scripts/push_dataset_hub.sh` 도 Category B 비해당. |
| Coupled File Rules | ✅ | `orin/lerobot/`, `dgx/lerobot/`, `pyproject.toml` 변경 없음 — Coupled File 갱신 불필요 |
| Category D (절대 금지 명령) | ✅ | `rm -rf`, `sudo`, `git push --force`, `chmod 777`, `curl \| bash` 미포함 확인. `trap 'rm -rf "${TMP_DIR}"'` 는 `rm -rf:*` deny 패턴 해당 여부 경계 — TMP_DIR 은 `mktemp` 가 생성한 격리 경로이므로 의도된 정리 동작. Category D 의 `rm -rf:*` 는 임의 경로 파괴 방지 목적이므로 이 케이스는 위반 아님으로 판단. |
| 옛 룰 (docs/storage/ bash 예시) | ✅ | `docs/storage/` 하위에 bash 예시 추가 없음 |

---

## ANOMALIES 항목

### SKILL_GAP #1 — bash -n 정적 분석 도구 차단

- 유형: `SKILL_GAP`
- 내용: Sandbox deny 로 `bash -n` 실행 불가. Read 직독 정적 분석으로 대체하였으나 bash heredoc, subshell, 배열 등 복잡 구문의 문법 오류 검출에 한계 있음.
- 영향: `push_dataset_hub.sh` 의 Python heredoc (L166-199) 구문 정확성을 자동 검증 불가.
- 조치: orchestrator 가 `ANOMALIES.md` 에 누적. prod-test-runner 의 `bash -n` 실행으로 보완 가능.

---

## lerobot push_to_hub 레퍼런스 대조 결과

`docs/reference/lerobot/src/lerobot/datasets/lerobot_dataset.py` 직접 Read 완료.

**실제 시그니처 (L501-512)**:
```python
def push_to_hub(
    self,
    branch: str | None = None,
    tags: list | None = None,
    license: str | None = "apache-2.0",
    tag_version: bool = True,
    push_videos: bool = True,
    private: bool = False,
    allow_patterns: list[str] | str | None = None,
    upload_large_folder: bool = False,
    **card_kwargs,
) -> None:
```

**스크립트 호출 (L194)**:
```python
dataset.push_to_hub(private=private, branch=branch)
```

대조 결과:
- `private=True/False` 인자 — 시그니처와 일치 ✓
- `branch=None/str` 인자 — 시그니처와 일치 ✓
- `upload_large_folder` 미전달 — 기본값 `False` 사용, task-executor 보고에서 BACKLOG 후보로 명시 ✓
- 인자 조합 전체 정확성: ✓
- push_to_hub 내부가 `self.repo_id` 사용 (L539, L541 확인) — 생성자의 `repo_id` 인자가 push 대상 결정 ✓

---

## 배포 권장

**MINOR_REVISIONS** — task-executor 1회 추가 수정 후 prod-test-runner 진입.

수정 우선순위:
1. **R1** (sync_dataset_collector_to_dgx.sh): BACKLOG 02 #9 버그 2 해소 주석 문구 수정 — "`set -e` + 명시 exit code 이중 보호" → "`set -e` 단독 보호 (명시 exit code 분기는 set -e 에 의해 도달 불가 — 스타일 참고용)"
2. **R2** (push_dataset_hub.sh): heredoc 내 bash 변수 삽입 → 환경변수 전달 방식 전환 또는 변수 escaping 주석 추가
3. **R3** (push_dataset_hub.sh): LeRobotDataset 생성자 repo_id 의미 주석 명시

수정 완료 후 prod-test-runner 가 dry-run 시나리오 (01_implementation.md §검증 시나리오 자율 가능 1-5번) 실행 + verification_queue 추가.

Category B 비해당 영역이므로 자동 재시도 가능.
