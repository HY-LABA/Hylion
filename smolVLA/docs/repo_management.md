# 레포 운영 및 동기화 흐름

> 기준 레포: `github.com/HY-LABA/Hylion`
> 백업 레포: `github.com/BaboGaeguri/LABA5_Bootcamp` (smolVLA 폴더 단방향 백업)
> 작성일: 2026-04-27
> 목적: smolVLA 작업물의 두 컴퓨터 동기화 + LABA5 단방향 백업 + Hylion main 정제 흐름 정리

---

## 0) 한눈에 보기

세 가지 흐름이 동시에 돌아간다:

```
                    ┌────────────────────────────────────────────────┐
                    │       [Hylion 레포 / BG 브랜치]                │
                    │       (smolVLA 작업의 단일 진실)               │
                    └────────────────────────────────────────────────┘
                              ▲                ▲
              git push/pull   │                │   git push/pull
                              │                │
              ┌───────────────┘                └───────────────┐
              │                                                │
   ┌──────────────────┐                              ┌──────────────────┐
   │ 정리용 컴퓨터    │                              │ 개발용 컴퓨터    │
   │ (Windows)        │                              │ (우분투, Orin)   │
   │ 문서·스펙 작성   │                              │ 코드 작성·테스트 │
   └──────────────────┘                              └──────────────────┘
                              │
                              │ ❶ 일상: 두 컴퓨터 사이 자유롭게 이동
                              │     (commit·push·pull 만 잘 챙기면 끝)
                              │
                              ▼
                    ┌────────────────────────────────────────────────┐
                    │  ❷ 가끔: LABA5 백업 (단방향, 덮어쓰기)         │
                    │     bash smolVLA/scripts/sync_to_laba5.sh      │
                    │     pwsh smolVLA/scripts/sync_to_laba5.ps1     │
                    │           │                                    │
                    │           ▼                                    │
                    │  github.com/BaboGaeguri/LABA5_Bootcamp/main    │
                    └────────────────────────────────────────────────┘

                    ┌────────────────────────────────────────────────┐
                    │  ❸ 산출물 확정 시: Hylion main 으로 PR         │
                    │                                                │
                    │   BG 에서 release/feature-XX 분기              │
                    │           │                                    │
                    │           ├─ git rm -r smolVLA/                │
                    │           ├─ 옮길 거만 main 폴더 구조에 정제   │
                    │           ├─ commit + push                     │
                    │           ▼                                    │
                    │   PR  →  리뷰  →  Hylion/main (팀 공용)        │
                    │           │                                    │
                    │           └─ release 브랜치 삭제 (일회성)      │
                    └────────────────────────────────────────────────┘
```

**핵심 규칙 4 줄:**
1. 모든 smolVLA 작업은 `Hylion/BG` 에서 한다. 두 컴퓨터 동기화는 `git push/pull` 이 전부.
2. LABA5 는 **단방향 백업** 만. LABA5 에서 직접 작업하지 않는다 (다음 sync 때 덮어써짐).
3. Hylion main 에는 smolVLA/ 가 절대 안 올라간다. 산출물 확정 시 release 브랜치에서 정제 후 PR.
4. `smolVLA/docs/reference/` 의 submodule 3개는 read-only. 코드 변경은 `smolVLA/orin/` 에서만.

---

## 1) 전제

- **Hylion 레포**: 팀 공용. main 직접 push 금지, 브랜치 + PR 운영. **smolVLA 작업의 진짜 동기화 채널.**
- **LABA5_Bootcamp 레포**: 사용자 개인 레포. smolVLA 폴더만 단방향 백업/공유 용도.
- **smolVLA 폴더**: 사용자 개인 작업 공간. Hylion main 에는 머지되지 않는다.
- **사용자 컴퓨터 2 대**:
  - 정리용 컴퓨터: 문서 정리, 스펙 작성, 워크플로우 운영
  - 개발용 컴퓨터: 실제 코드 작성, Orin SSH, 테스트
- **팀원**: smolVLA 폴더는 보지 않는다. Hylion main 에 정제되어 올라간 산출물만 본다.

---

## 2) 브랜치 / 레포 전략

```
[Hylion 레포]                       (= 작업의 메인 채널)
main                       팀 공용. 정제된 산출물만.
 ↑ PR
release/feature-XX         확정된 기능을 main 폴더 구조에 맞게 정리한 일회성 브랜치
 ↑ branch + 수동 정제
BG                         개인 작업 브랜치. smolVLA/ 통째로 존재. 영구.
 ↕ push/pull (전체 레포)
[정리용 컴퓨터]  [개발용 컴퓨터]

[LABA5_Bootcamp 레포]               (= 단방향 백업 대상)
main                       smolVLA/ 폴더만 미러
 ↑ 단방향 sync (스크립트)
[Hylion/BG 의 smolVLA/ 부분]
```

| 위치 | 수명 | smolVLA/ 포함 | 누가 봄 |
|---|---|---|---|
| `Hylion/main` | 영구 | ❌ 없음 | 팀 전체 |
| `Hylion/release/feature-XX` | 일회성 (PR 머지 후 삭제) | ❌ (제거 후 정제본만) | PR 리뷰어 |
| `Hylion/BG` | 영구 | ✅ 통째로 | 사용자만 (두 컴퓨터) |
| `LABA5_Bootcamp/main` | 영구 | ✅ (smolVLA/ 만 동기화) | 사용자만 |

**중요:** 두 컴퓨터 동기화는 **Hylion/BG** 가 담당한다. LABA5 는 동기화 채널이 아니라 백업이다.

---

## 3) 일상 동기화 흐름

### 3-1) 두 컴퓨터 간 (Hylion/BG 전체)

```
[정리용 컴퓨터]
  BG 에서 작업
       ↓ git push
  origin/BG
       ↓ git pull
  [개발용 컴퓨터]
  BG 에서 이어서 작업
       ↓ git push
  origin/BG
       ↓ git pull
  [정리용 컴퓨터]  ...
```

**원칙:**
- 컴퓨터 전환 직전 반드시 commit + push.
- 컴퓨터 전환 직후 반드시 pull (작업 시작 전).
- 같은 파일을 두 컴퓨터에서 동시에 편집하지 않는다 (충돌 방지).

### 3-2) Hylion/BG → LABA5_Bootcamp/main (smolVLA/ 폴더 단방향 백업)

전용 스크립트로 한 번에 처리한다. OS 별로 두 버전이 있고 동작은 동일하다.

**Linux / macOS (개발용 컴퓨터, 우분투):**
```bash
# Hylion 루트에서 실행
bash smolVLA/scripts/sync_to_laba5.sh

# 옵션
bash smolVLA/scripts/sync_to_laba5.sh --dry-run                  # 미리보기
bash smolVLA/scripts/sync_to_laba5.sh --no-push                  # commit 만
bash smolVLA/scripts/sync_to_laba5.sh --laba5 /path/to/LABA5     # 경로 지정 (기본 ~/LABA5_Bootcamp)
```

**Windows (정리용 컴퓨터):**
```powershell
# Hylion 루트에서 실행
pwsh smolVLA/scripts/sync_to_laba5.ps1

# 옵션
pwsh smolVLA/scripts/sync_to_laba5.ps1 -DryRun                   # 미리보기
pwsh smolVLA/scripts/sync_to_laba5.ps1 -NoPush                   # commit 만
pwsh smolVLA/scripts/sync_to_laba5.ps1 -Laba5Path 'C:\path\LABA5_Bootcamp'
```

**스크립트가 하는 일 (양쪽 동일):**
1. `Hylion/smolVLA/` → `LABA5_Bootcamp/smolVLA/` 미러 동기화
   - Linux: `rsync -a --delete`
   - Windows: `robocopy /MIR`
2. submodule 폴더 제외: `lerobot`, `seeed-lerobot`, `reComputer-Jetson-for-Beginners`
3. 위생 폴더 제외: `.git`, `.venv`, `__pycache__`, 캐시 디렉토리
4. LABA5 측에서 `git add smolVLA/ && git commit && git push`

**LABA5_Bootcamp 기본 위치:**
- Linux: `~/LABA5_Bootcamp`
- Windows: `C:\Users\<user>\Desktop\LABA5_Bootcamp` (Hylion 옆 디렉토리)

**원칙 (단방향):**
- LABA5 → Hylion 방향 sync 는 **하지 않는다.** 진짜 작업물은 항상 Hylion/BG 가 정답.
- LABA5 에서 직접 smolVLA 파일을 수정하지 않는다 (다음 sync 때 덮어써짐).
- submodule 코드 변경이 필요할 일은 없다 (read-only). 만약 lerobot upstream 변경을 받고 싶으면 `git submodule update --remote --merge` 를 Hylion/BG 에서 실행 후 commit.

---

## 4) 메인 머지 흐름 (확정 산출물 → Hylion main)

`BG` 의 산출물 중 확정된 것을 Hylion main 에 올릴 때:

```
1. BG 에서 release 브랜치 분기
   git checkout BG
   git checkout -b release/feature-XX

2. smolVLA/ 폴더 통째로 제거 (submodule 포함)
   git rm -r smolVLA/
   git rm -f .gitmodules     # 선택: smolVLA submodule 만 정의되어 있다면

3. 사용자가 직접 main 폴더 구조에 맞게 정제본 배치
   (예: smolVLA/orin/ → src/orin/, smolVLA/docs/storage/ → docs/ 등)

4. commit + push
   git add .
   git commit -m "Add: <기능 설명>"
   git push -u origin release/feature-XX

5. PR 생성 → 리뷰 → main 머지

6. release 브랜치 삭제
   git branch -d release/feature-XX
   git push origin --delete release/feature-XX
```

**중요:**
- 정제는 **사용자가 직접 손으로** 한다 (자동화 없음).
- `BG` 는 release 작업 후에도 그대로 살아있다 — 다음 작업 사이클 계속.
- `.gitignore` 는 이 흐름을 막아주지 않는다 (이미 트래킹된 smolVLA/ 는 ignore 무시됨). 반드시 `git rm` 으로 제거.

---

## 5) `.gitignore` 의 역할

Hylion 레포의 `.gitignore` 는 "main 보호용" 이 아니라 **"두 컴퓨터 동기화 위생용"** 이다.

| 카테고리 | 패턴 예시 | 이유 |
|---|---|---|
| Python 캐시 | `__pycache__/`, `*.pyc` | 매 실행마다 새로 생김, push/pull 충돌 |
| 가상환경 | `.venv/`, `venv/` | 컴퓨터마다 절대경로 다름 |
| OS 자동 생성 | `.DS_Store`, `Thumbs.db` | 무의미 diff |
| 민감 정보 | `.env`, `*.key`, `*.pem` | 실수 push 방지 |
| 캡처 산출물 | `cam*.jpg`, `*.mp4` | 테스트 산출물 |

**ignore 하지 않는 것 (smolVLA 작업 공간 전체 동기화 필요):**
- `smolVLA/` 폴더 자체
- `smolVLA/docs/work_flow/` 의 모든 하위 (specs, context, history)
- `smolVLA/.claude/commands/`, `smolVLA/AGENTS.md`, `smolVLA/CLAUDE.md`
- 작업 중 산출물 전체

---

## 6) Submodule 처리

`smolVLA/docs/reference/` 하위 외부 참조 (lerobot, seeed-lerobot, reComputer-Jetson-for-Beginners) 는 사용자만 사용한다.

**방침:**
- Hylion 루트의 `.gitmodules` 에 등록 → 사용자 작업 브랜치에서 `git submodule update --init --recursive` 로 받음
- 팀원은 default clone 시 submodule 받지 않으면 빈 폴더로 봄 (에러 없음, 무시 가능)
- Hylion main 에는 `smolVLA/` 자체가 안 올라가므로 submodule 도 자연스럽게 안 올라감
- LABA5 백업 sync 에서는 **submodule 폴더를 제외** 한다 (1GB+ 가 LABA5 commit 으로 들어가는 것 방지). LABA5 쪽에서는 사용자가 직접 `git submodule update --init` 으로 받는다.

**등록되는 submodule 3개:**

| name | path | url |
|---|---|---|
| `smolVLA/lerobot` | `smolVLA/docs/reference/lerobot` | `https://github.com/huggingface/lerobot` |
| `smolVLA/reComputer-Jetson-for-Beginners` | `smolVLA/docs/reference/reComputer-Jetson-for-Beginners` | `https://github.com/Seeed-Projects/reComputer-Jetson-for-Beginners.git` |
| `smolVLA/docs/reference/seeed-lerobot` | `smolVLA/docs/reference/seeed-lerobot` | `https://github.com/Seeed-Projects/lerobot` |

**최신화:**
```bash
git submodule update --remote --merge
```

---

## 7) 첫 클론 / 셋업 절차 (컴퓨터당 한 번)

### 7-1) 우분투 (개발용 컴퓨터)

작업 위치는 사용자 홈 (`~`) 기준으로 가정한다. 다른 위치에 두려면 경로만 조정.

```bash
# 0. 사전 확인 — git, ssh 키 (GitHub push 권한) 준비됐는지
git --version
ssh -T git@github.com    # (HTTPS 만 쓰면 생략 가능)

# 1. Hylion 클론
cd ~
git clone https://github.com/HY-LABA/Hylion.git
cd Hylion

# 2. BG 브랜치로 전환 (origin/BG 자동 추적)
git checkout BG

# 3. reference submodule 3개 받기 (lerobot, seeed-lerobot, reComputer)
#    수 GB 다운로드 + 시간 소요. 네트워크 좋은 곳에서 한 번만.
git submodule update --init --recursive

# 4. 받은 후 상태 확인
git submodule status
#   ba27aab... smolVLA/docs/reference/lerobot (...)
#   bfcb505... smolVLA/docs/reference/reComputer-Jetson-for-Beginners (heads/main)
#   0f39248... smolVLA/docs/reference/seeed-lerobot (heads/main)

# 5. (선택, LABA5 백업 쓸 사람만) LABA5_Bootcamp 클론
cd ~
git clone https://github.com/BaboGaeguri/LABA5_Bootcamp.git
#   기본 위치 ~/LABA5_Bootcamp 가 백업 스크립트의 default 다. 다른 위치면 매번 --laba5 로 지정.

# 6. (선택) 백업 스크립트 실행 권한 확인
cd ~/Hylion
ls -l smolVLA/scripts/sync_to_laba5.sh
#   -rwxr-xr-x ... 가 보이면 OK. 안 그러면: chmod +x smolVLA/scripts/sync_to_laba5.sh

# 7. 백업 dry-run (실제 변경 없이 미리보기)
bash smolVLA/scripts/sync_to_laba5.sh --dry-run
```

**Orin/하드웨어 세팅은 별도 문서:**
- `smolVLA/docs/storage/04_devnetwork.md` — devPC ↔ Orin SSH (`~/.ssh/config` 등록)
- `smolVLA/docs/storage/05_orin_venv_setting.md` — Orin venv / PyTorch 설치
- `smolVLA/orin/scripts/setup_env.sh` — Orin 안에서 실행 (devPC 에서 실행 X)

### 7-2) Windows (정리용 컴퓨터)

PowerShell 사용. 명령어 동일, 경로 표기와 백업 스크립트만 다르다.

```powershell
# 1. Hylion 클론
cd C:\Users\admin\Desktop
git clone https://github.com/HY-LABA/Hylion.git
cd Hylion

# 2. BG 브랜치
git checkout BG

# 3. submodule
git submodule update --init --recursive

# 4. (선택) LABA5_Bootcamp 클론 — Hylion 옆 디렉토리에
cd ..
git clone https://github.com/BaboGaeguri/LABA5_Bootcamp.git
#   기본 위치 C:\Users\<user>\Desktop\LABA5_Bootcamp 가 .ps1 의 default

# 5. (선택) 백업 dry-run
cd Hylion
pwsh smolVLA/scripts/sync_to_laba5.ps1 -DryRun
```

### 7-3) 셋업 검증 체크리스트

두 컴퓨터 어느 쪽이든 끝나면 아래 4가지 확인:

- [ ] `git branch --show-current` → `BG`
- [ ] `git status` → `Your branch is up to date with 'origin/BG'.` + working tree clean
- [ ] `ls smolVLA/docs/reference/lerobot/README.md` 가 존재 (submodule 받아짐)
- [ ] `git remote -v` → `origin https://github.com/HY-LABA/Hylion.git` 만 있음 (`laba5` remote 없음 — subtree 안 씀)

---

## 8) 일상 운영 요약

```
[작업 시작]
  git pull origin BG          # 다른 컴퓨터에서 작업한 거 받기
  (코드 작성, 문서 정리, Orin 테스트 ...)

[작업 종료 / 컴퓨터 전환 / 매일 끝날 때]
  git add . && git commit -m "..."
  git push origin BG          # 두 컴퓨터 동기화의 진짜 채널

[가끔, LABA5 백업하고 싶을 때]
  bash smolVLA/scripts/sync_to_laba5.sh        # 우분투
  pwsh smolVLA/scripts/sync_to_laba5.ps1       # Windows

[가끔, lerobot upstream 변경 받고 싶을 때]
  git submodule update --remote --merge
  git add smolVLA/docs/reference/<changed>
  git commit -m "submodule: bump <name> to <new SHA>"
  git push origin BG

[Hylion main 으로 산출물 올릴 때 — 4절 참조]
```
