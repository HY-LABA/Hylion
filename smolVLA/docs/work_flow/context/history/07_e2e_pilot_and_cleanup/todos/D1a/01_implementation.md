# TODO-D1a — Implementation

> 작성: 2026-05-04 09:57 | task-executor | cycle: 1

## 목표

dgx + orin interactive_cli main.sh 회귀 2건 패치 (ModuleNotFoundError 'flows' + 실행 권한 644)

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `dgx/interactive_cli/main.sh` | M | 회귀1: exec python3 → cd + python3 -m flows.entry / 회귀2: chmod 755 + git +x |
| `orin/interactive_cli/main.sh` | M | 동일 패턴 확인 후 동일 수정 적용 |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 ✓, `orin/lerobot/` · `dgx/lerobot/` 미변경 ✓
- Coupled File Rule: `orin/lerobot/` 미변경이므로 `03_orin_lerobot_diff.md` 갱신 불요 ✓
- 레퍼런스 활용: 본 변경은 bash 관용구 수정 (shell 레벨) — lerobot 레퍼런스 무관. todo 명세 옵션 (a) 그대로 적용.
- Category B 점검: `deploy_dgx.sh` 는 수정 X (점검·보고만)

## 변경 내용 요약

### 회귀 1 — ModuleNotFoundError 'flows' 패치

**원인**: `exec python3 "${SCRIPT_DIR}/flows/entry.py"` 직접 .py 실행 시 `sys.path[0]`이 `flows/` 디렉터리 자체로 설정되어 `from flows.X import` 패턴이 탐색 실패.

**수정 (옵션 a)**: 1 라인 변경.

```bash
# 변경 전
exec python3 "${SCRIPT_DIR}/flows/entry.py" --node-config "${NODE_CONFIG}"

# 변경 후
cd "${SCRIPT_DIR}" && exec python3 -m flows.entry --node-config "${NODE_CONFIG}"
```

`cd "${SCRIPT_DIR}"` 로 interactive_cli/ 를 CWD 로 설정한 뒤 `-m flows.entry` 모듈 실행 → `sys.path[0]` 이 interactive_cli/ 루트가 되어 `from flows.X import` 정상 탐색.

dgx 와 orin 양측 모두 동일 패턴이었으므로 양쪽 동시 수정.

### 회귀 2 — 실행 권한 644 패치

양측 파일 모두 644 (`-rw-rw-r--`) 로 x 권한 없음 확인.

- `chmod 755 dgx/interactive_cli/main.sh orin/interactive_cli/main.sh` — 파일시스템 권한 변경
- `git update-index --chmod=+x` — git 인덱스 권한도 `100755` 로 동시 갱신

### deploy_dgx.sh rsync 옵션 점검 (보고)

`scripts/deploy_dgx.sh` 의 rsync 옵션: `rsync -avz --delete ...`

`-a` (archive) 플래그 = `-rlptgoD` 의 약어이며 `-p` (perms) 가 포함됨. 따라서 devPC 에서 755 로 설정된 권한이 DGX 측에 그대로 보존되어 전송됩니다. **deploy_dgx.sh 수정 불요**.

## Step 별 검증 결과

### Step 1 — orin/interactive_cli/main.sh 동일 패턴 확인

```
$ grep -n "exec python3" orin/interactive_cli/main.sh
71: exec python3 "${SCRIPT_DIR}/flows/entry.py" --node-config "${NODE_CONFIG}"

$ ls -la orin/interactive_cli/main.sh
-rw-rw-r-- ... main.sh    # 644, 동일 패턴
```

결론: dgx 와 동일 — 함께 수정.

### Step 2 — main.sh 패치 완료

dgx 57행 + orin 71행 동시 수정. 결과:
```bash
# 양측 공통
cd "${SCRIPT_DIR}" && exec python3 -m flows.entry --node-config "${NODE_CONFIG}"
```

### Step 3 — 권한 처리 완료

```
-rwxr-xr-x ... dgx/interactive_cli/main.sh    # 755
-rwxr-xr-x ... orin/interactive_cli/main.sh   # 755

git ls-files -s dgx/interactive_cli/main.sh orin/interactive_cli/main.sh
100755 a1ac07... dgx/interactive_cli/main.sh
100755 0f14e3... orin/interactive_cli/main.sh
```

### Step 4 — bash -n 정적 검증

```
dgx: bash -n PASS
orin: bash -n PASS
```

### Step 5 — devPC import smoke (회귀 1 핵심)

dgx 측:
```
$ cd dgx/interactive_cli && python3 -c "from flows import entry, env_check, mode; print('import OK')"
import OK
```

orin 측 (orin flows 는 mode.py 없음 — inference only):
```
$ cd orin/interactive_cli && python3 -c "from flows import entry, env_check, inference; print('import OK')"
import OK
```

-m 모듈 실행 직접 검증 (dgx):
```
$ cd dgx/interactive_cli && python3 -m flows.entry --help
usage: entry.py [-h] --node-config NODE_CONFIG
...
PASS — import 에러 없이 argparse 까지 진입
```

### Step 6·7 — DGX SSH 실 검증

prod-test-runner 인계. devPC 에서 DGX venv 없으므로 venv 활성 단계 이후는 SSH 실 검증 위임.

### deploy_dgx.sh 점검 보고

`rsync -avz` 내 `-a` 플래그에 `-p` (perms) 포함 → deploy 후 DGX 측 권한 755 자동 보존. 수정 불요.

## code-tester 입장에서 검증 권장 사항

- `bash -n dgx/interactive_cli/main.sh` — PASS 확인
- `bash -n orin/interactive_cli/main.sh` — PASS 확인
- `git ls-files -s dgx/interactive_cli/main.sh orin/interactive_cli/main.sh` → 양측 100755 확인
- `cd dgx/interactive_cli && python3 -m flows.entry --help` — import 통과 확인
- `cd orin/interactive_cli && python3 -m flows.entry --help` — import 통과 확인
- DGX SSH 실 실행 smoke (Step 6): prod-test-runner 위임
  - `ssh dgx "echo '2' | timeout 10 bash ~/smolvla/dgx/interactive_cli/main.sh 2>&1 | head -50"`
  - 기대: ModuleNotFoundError X, 권한 755, 메뉴 진입 후 flow 2 진입 확인
- orin SSH 실 실행 smoke (Step 6): prod-test-runner 위임
  - `ssh orin "echo '1' | timeout 10 bash ~/smolvla/orin/interactive_cli/main.sh 2>&1 | head -50"`
