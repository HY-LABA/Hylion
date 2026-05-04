# TODO-W4 — Code Test

> 작성: 2026-05-03 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈 0건. Recommended 1건 (bash 예시 포함 — 기존 storage 관행과 일치하고 DOD 직접 요구 내용이라 Critical 아님).

---

## 단위 테스트 결과

```
대상: docs/storage/15_orin_config_policy.md (정책 문서, 코드 없음)
      docs/work_flow/specs/BACKLOG.md (마크다운 문서)

pytest: 해당 없음 (Python 코드 변경 없음)
bash -n: 해당 없음 (실행 스크립트 변경 없음)

파일 존재 확인:
  /home/babogaeguri/Desktop/Hylion/smolVLA/docs/storage/15_orin_config_policy.md — PASS (135 줄)
  /home/babogaeguri/Desktop/Hylion/smolVLA/docs/work_flow/specs/BACKLOG.md — PASS (수정됨)

git 추적 상태:
  orin/config/README.md, cameras.json, ports.json — 3파일 모두 추적 중, 변경 없음 (PASS)

BACKLOG 04 #3 완료 마킹:
  "완료 (07 W4 정책 문서 신규 — `docs/storage/15_orin_config_policy.md`, 2026-05-03)" — PASS
```

---

## Lint·Type 결과

```
ruff check: 해당 없음 (Python 코드 변경 없음)
mypy: 해당 없음

.gitignore 변경 여부 (W4 범위):
  W4 task-executor 는 .gitignore 미변경 선언 — 확인 필요

  git diff HEAD~1 HEAD -- .gitignore 결과:
    datacollector/.hylion_collector/, datacollector/data/ 2줄 제거 확인됨
    → 이는 TODO-P2 의 산출물 (별도 커밋 아님, 현재 working tree 에 unstaged 상태)
    → W4 task-executor 가 이 변경을 수행하지 않음 확인
    → git status 확인: .gitignore 는 "Changes not staged for commit" 에 포함,
       15_orin_config_policy.md 는 "Untracked files" 에 포함,
       BACKLOG.md 는 "Changes not staged for commit" 에 포함

  결론: W4 산출물은 정책 문서 신규 + BACKLOG.md 마킹 2건 뿐.
        .gitignore 변경은 TODO-P2 영역 (별개 todo). W4 는 Category B 미개입 ✓
```

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. `orin/config/ports.json`·`cameras.json` 의 git 추적 vs gitignore 정책 결정 | ✅ | §1 에서 "git 추적 유지 (결정 (a))" + `.gitignore` 변경 X 명시 |
| 2. 정책 문서 작성 (`docs/storage/15_orin_config_policy.md` 신규) | ✅ | 135줄 8섹션 신규 작성 확인 |
| 3. `.gitignore` 변경 X (Category B 회피) | ✅ | W4 task-executor 는 .gitignore 미변경. 현 working tree 의 .gitignore 변경은 TODO-P2 산출물 (별도 todo) |
| (검증 항목) §1 8개 섹션 완전성 | ✅ | §1~§8 전부 포함 (결정·추적 파일·결정 사유·충돌 가능성·override·갱신 절차·변경 이력·차후 후보) |
| (검증 항목) 사용자 결정 (a) 일관성 | ✅ | "git 추적 유지", ".gitignore 변경 X (Category B 회피)" 본문 일관 |
| (검증 항목) 현 orin/config/ 상태 반영 | ✅ | git ls-files 3파일 목록·null placeholder 값 정확 |
| (검증 항목) override 방법 안내 | ✅ | §5-1 git stash 방법, §5-2 local.json 패턴 도입 후보 명시 |
| (검증 항목) storage 형식 정합 | ✅ | 04_devnetwork.md 형식 (header/목적/날짜/섹션 구조) 에 준함 |
| (검증 항목) BACKLOG 04 #3 마킹 | ✅ | "완료 (07 W4 정책 문서 신규 — `docs/storage/15_orin_config_policy.md`, 2026-05-03)" 확인 |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `docs/storage/15_orin_config_policy.md` §5-1, §6 | bash 코드 블록 2개 포함 — CLAUDE.md "옛 룰": docs/storage/ 에 bash 명령 예시 추가는 사용자 명시 요청 시에만 허용. 단 (a) 기존 05·06_* storage 문서가 이미 bash 예시 포함하여 실질적 관행과 일치, (b) DOD 가 override 방법·갱신 절차를 요구하므로 bash 예시가 DOD 직접 충족 내용임. 이 문서가 처음 bash 예시를 storage 에 추가하는 신규 작성이 아니므로 Critical 해당 없음. 차후 룰 명확화 시 참조 |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경. `.claude/agents/*.md`, `.claude/skills/**/*.md`, `.claude/settings.json` 미변경 |
| B (자동 재시도 X) | ✅ | `orin/lerobot/`·`dgx/lerobot/`·`pyproject.toml`·`setup_env.sh`·`deploy_*.sh` 미변경. `.gitignore` 변경은 W4 산출물 아님 (TODO-P2 별개) |
| Coupled File Rules | ✅ | Category B 영역 미변경 → coupled file 갱신 불요 |
| 새 디렉터리 생성 | ✅ | `docs/storage/` 기존 디렉터리에 파일 추가. Category C 대상 아님 |
| 옛 룰 (bash 예시) | ⚠️ | §5-1·§6 에 bash 블록 포함. DOD 직접 요구 + 기존 관행 일치로 Critical 아님. Recommended #1 |

---

## 배포 권장

**yes — prod-test-runner 진입 권장**

Critical 0건, Recommended 1건. `READY_TO_SHIP`.
prod-test-runner 는 `docs/storage/15_orin_config_policy.md` 존재 확인 + BACKLOG 마킹 grep 확인 수준의 정적 검증만 수행하면 됨 (코드 배포·ssh 검증 불요).
