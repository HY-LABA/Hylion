# 레포 운영 및 동기화 흐름

> 기준 레포: `github.com/HY-LABA/Hylion`
> 보조 레포: `github.com/BaboGaeguri/LABA5_Bootcamp` (smolVLA 폴더 미러)
> 작성일: 2026-04-27
> 목적: smolVLA 작업물의 두 컴퓨터 동기화 + LABA5 양방향 미러 + Hylion main 정제 흐름 정리

---

## 1) 전제

- **Hylion 레포**: 팀 공용. main 직접 push 금지, 브랜치 + PR 운영.
- **LABA5_Bootcamp 레포**: 사용자 개인 레포. smolVLA 폴더만 main 으로 미러링.
- **smolVLA 폴더**: 사용자 개인 작업 공간. Hylion main 에는 머지되지 않는다.
- **사용자 컴퓨터 2 대**:
  - 정리용 컴퓨터: 문서 정리, 스펙 작성, 워크플로우 운영
  - 개발용 컴퓨터: 실제 코드 작성, Orin SSH, 테스트
- **팀원**: smolVLA 폴더는 보지 않는다. Hylion main 에 정제되어 올라간 산출물만 본다.

---

## 2) 브랜치 / 레포 전략

```
[Hylion 레포]
main                       팀 공용. 정제된 산출물만.
 ↑ PR
release/feature-XX         확정된 기능을 main 폴더 구조에 맞게 정리한 일회성 브랜치
 ↑ branch + 수동 정제
BG                         개인 작업 브랜치. smolVLA/ 통째로 존재. 영구.
 ↕ push/pull (전체 레포)
[정리용 컴퓨터]  [개발용 컴퓨터]

[LABA5_Bootcamp 레포]
main                       smolVLA/ 폴더 내용만 루트 기준으로 미러
 ↕ git subtree push/pull (smolVLA/ 폴더만)
[Hylion/BG 의 smolVLA/ 부분]
```

| 위치 | 수명 | smolVLA/ 포함 | 누가 봄 |
|---|---|---|---|
| `Hylion/main` | 영구 | ❌ 없음 | 팀 전체 |
| `Hylion/release/feature-XX` | 일회성 (PR 머지 후 삭제) | ❌ (제거 후 정제본만) | PR 리뷰어 |
| `Hylion/BG` | 영구 | ✅ 통째로 | 사용자만 (두 컴퓨터) |
| `LABA5_Bootcamp/main` | 영구 | ✅ (이게 곧 레포 루트) | 사용자만 |

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

### 3-2) Hylion/BG ↔ LABA5_Bootcamp/main (smolVLA/ 폴더만)

git subtree 로 smolVLA/ 폴더만 LABA5 main 에 push/pull.

**LABA5 → Hylion (LABA5 에서 변경분 가져오기):**
```bash
git subtree pull --prefix=smolVLA laba5 main --squash
```

**Hylion → LABA5 (Hylion 에서 변경분 보내기):**
```bash
git subtree push --prefix=smolVLA laba5 main
```

**원격 등록 (한 번만):**
```bash
git remote add laba5 https://github.com/BaboGaeguri/LABA5_Bootcamp.git
```

**원칙:**
- subtree 명령은 항상 BG 브랜치 위에서 실행한다.
- LABA5 와 BG 양쪽에서 동시에 같은 파일을 편집하지 않는다.
- subtree pull 직후에는 BG 를 origin 으로 push 해서 두 컴퓨터 동기화도 갱신한다.

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

Hylion 레포의 `.gitignore` 는 "main 보호용" 이 아니라 **"두 컴퓨터 동기화 위생용 + LABA5 미러 위생용"** 이다.

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
- LABA5_Bootcamp 의 `.gitmodules` 와 **submodule name·path·url 모두 동일**하게 유지 (subtree 양방향 호환)
- 팀원은 default clone 시 submodule 받지 않으면 빈 폴더로 봄 (에러 없음, 무시 가능)
- Hylion main 에는 `smolVLA/` 자체가 안 올라가므로 submodule 도 자연스럽게 안 올라감

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

## 7) 첫 이관 절차 (한 번만)

### 사용자 직접 수행

1. `git clone https://github.com/HY-LABA/Hylion.git` (두 컴퓨터 모두)
2. `git checkout BG` (origin/BG 추적)
3. LABA5_Bootcamp/smolVLA/ 폴더 전체를 Hylion/ 루트로 복사 붙여넣기

### Hylion 레포 AI 에게 인계

4. main 기준으로 BG 최신화 (`git merge --ff-only origin/main`)
5. Hylion 루트에 `.gitignore` 보강 (5절 패턴 기준)
6. Hylion 루트에 `.gitmodules` 신설 — 6절 표의 submodule 3개 등록
7. 기존 `smolVLA/docs/reference/{lerobot, seeed-lerobot, reComputer-Jetson-for-Beginners}/` 디스크 폴더 제거 후 `git submodule add` 로 새로 받기

### 사용자 직접 수행

8. `git add . && git commit -m "Init: smolVLA workspace"` → push
9. 다른 컴퓨터에서 pull 받아 동일 상태 확인
10. 사용자 작업 컴퓨터에서 `git submodule update --init --recursive` 실행 (submodule 받기)
11. LABA5 remote 등록 (`git remote add laba5 https://github.com/BaboGaeguri/LABA5_Bootcamp.git`)
12. 첫 subtree push 검증 (`git subtree push --prefix=smolVLA laba5 main`)
