# TODO-P1 — Implementation

> 작성: 2026-05-03 | task-executor | cycle: 1

## 목표

`scripts/dev-connect.sh` 에서 datacollector 라인(L4) 제거 — Wave 1 잔재 정리.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| scripts/dev-connect.sh | M | L4 `code --remote ssh-remote+datacollector /home/smallgaint` 삭제 |

## 적용 룰

- CLAUDE.md Hard Constraints: docs/reference/ 미변경 ✓
- Coupled File Rule: lerobot 코드 변경 없음 — 03_orin_lerobot_diff.md 갱신 불필요 ✓
- 레퍼런스 활용: 본 todo 는 lerobot 레퍼런스 무관 (스킬 `lerobot-reference-usage` 적용 범위 외)
- Category B 영역: scripts/dev-connect.sh 는 Category B 목록 외 — 재시도 게이트 불필요 ✓

## 변경 내용 요약

`scripts/dev-connect.sh` 는 devPC 에서 VSCode Remote-SSH 세션 3 개(orin·dgx·datacollector)를 동시에 여는 유틸리티다. datacollector 호스트는 06 사이클에서 폐기 결정되었으나 이 파일에만 잔재가 남아 있었다. L4 한 줄을 제거해 파일을 4줄 → 3줄로 축소했다. 사용자 `~/.ssh/config` 의 `Host datacollector` alias 는 사용자 환경 의존 사항이므로 변경하지 않았다 (spec 메모대로 보고만).

## 변경 전/후 diff

```diff
 #!/bin/bash
 code --remote ssh-remote+orin /home/laba
 code --remote ssh-remote+dgx /home/laba
-code --remote ssh-remote+datacollector /home/smallgaint
```

## DOD 달성 확인

### L4 제거 완료

```
1  #!/bin/bash
2  code --remote ssh-remote+orin /home/laba
3  code --remote ssh-remote+dgx /home/laba
```

파일 총 3 줄 (빈 줄 없음).

### datacollector / smallgaint 잔재 grep 결과

```
$ grep -n "datacollector\|smallgaint" scripts/dev-connect.sh
(출력 없음, exit code: 1)
```

grep 0건 — DOD 충족.

## code-tester 인계 사항

- 검증 명령: `grep -c "datacollector\|smallgaint" scripts/dev-connect.sh` → 출력 `0` 확인
- 파일 줄 수 확인: `wc -l scripts/dev-connect.sh` → `3` 확인
- 변경 범위가 단순 삭제 1 줄이므로 lerobot diff·pyproject 관련 coupled file 갱신 불필요
- 사용자 `~/.ssh/config` Host datacollector 항목은 사용자 영역 — code-tester 범위 외
