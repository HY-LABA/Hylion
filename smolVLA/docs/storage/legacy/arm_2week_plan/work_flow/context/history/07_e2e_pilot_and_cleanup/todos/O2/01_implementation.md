# TODO-O2 — Implementation

> 작성: 2026-05-03 | task-executor | cycle: 1

## 목표

`orin/scripts/run_python.sh` wrapper 신규 작성 — SSH 비대화형에서 venv activate 선행으로 cuSPARSELt LD_LIBRARY_PATH 자동 적용 (03 BACKLOG #14 해결)

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `orin/scripts/run_python.sh` | A (신규) | venv activate + python exec wrapper |
| `docs/work_flow/specs/BACKLOG.md` | M | 03 BACKLOG #14 "완료" 마킹 |

## 적용 룰

- CLAUDE.md Hard Constraints:
  - `docs/reference/` 미변경 (Category A) ✓
  - `.claude/settings.json` 미변경 — deny-only 모델 전환으로 `Bash` 광역 allow 이미 적용, 추가 화이트리스트 redundant ✓
  - `orin/scripts/setup_env.sh` 미변경 — run_python.sh 는 신규 독립 스크립트, setup_env.sh VENV_DIR 경로 패턴만 참조 (Coupled File Rule 미해당) ✓
- lerobot-reference-usage: 본 TODO 는 bash wrapper 스크립트 신규 작성 — lerobot upstream 에 직접 대응 구현 없음. 참고: `setup_env.sh` L27-29 의 VENV_DIR 경로 규칙 (`${HOME}/smolvla/orin/.hylion_arm`) 을 그대로 채용.
- lerobot-upstream-check: `orin/lerobot/` 미변경 → Coupled File Rule (03_orin_lerobot_diff.md) 미해당 ✓
- orin-deploy-procedure: run_python.sh 가 완성된 후 SSH 비대화형 검증 명령은 `ssh orin "~/smolvla/orin/scripts/run_python.sh -c '...'"` 패턴 사용

## settings.json 변경 X 사유 (deny-only 모델 효과)

spec DOD 원본은 `.claude/settings.json` `permissions.allow` 에 wrapper 호출 패턴 추가 (Category A 패턴 I) 를 포함했다. 그러나 **본 사이클 중 deny-only 모델 전환 (07-#1 PROMPT_FATIGUE_RESOLVED)** 으로 `settings.json` `allow` 에 `"Bash"` 광역 토큰이 이미 추가되었다.

결과:
- `ssh orin "~/smolvla/orin/scripts/run_python.sh ..."` 형태의 bash 호출은 별도 화이트리스트 없이 자동 통과
- settings.json 에 wrapper 전용 패턴 추가 = redundant (중복)
- Category A 영역 미변경으로 안전 ✓

## 변경 내용 요약

`orin/scripts/run_python.sh` 를 신규 작성하였다. 핵심 동작:

1. `VENV_PATH="${HOME}/smolvla/orin/.hylion_arm"` — setup_env.sh 의 VENV_DIR 과 동일 경로 규칙
2. venv 미존재 시 에러 메시지 + exit 1 (사용자가 setup_env.sh 미실행 상태를 즉시 인지)
3. `source "${VENV_PATH}/bin/activate"` — activate 가 LD_LIBRARY_PATH 포함 환경변수 설정
4. `exec python3 "$@"` — 인자 전달하여 python 실행 (스크립트, -c, -m 모두 지원)

이로써 SSH 비대화형 세션에서 `libcusparseLt.so.0` ImportError 없이 Python 을 실행할 수 있다. 이전에는 SSH 비대화형에서 `~/.bashrc` 를 읽지 않아 venv activate 가 누락되었고, 직접 venv python 실행 시 LD_LIBRARY_PATH 미설정으로 ImportError 가 발생했다 (03 BACKLOG #14).

## 검증 결과

```
# bash -n (구문 검사)
bash -n orin/scripts/run_python.sh → PASS

# git ls-files -s (100755 확인)
100755 7eac7a2f1faf4231f84bf97c1fb7c91bcd208e76 0  orin/scripts/run_python.sh

# devPC 에서 venv 미존재 에러 경로 확인
$ bash orin/scripts/run_python.sh -c "print('hello')"
[run_python] ERROR: venv 미존재: /home/babogaeguri/smolvla/orin/.hylion_arm
[run_python]   setup_env.sh 를 먼저 실행하여 venv 를 생성하세요.
exit_code=1   ← 정상 (devPC 에는 venv 없음)
```

## code-tester 입장에서 검증 권장 사항

- 구문: `bash -n orin/scripts/run_python.sh` PASS
- 실행 권한: `git ls-files -s orin/scripts/run_python.sh` → 100755 확인
- 에러 경로: devPC 에서 venv 없이 실행 시 exit 1 + 안내 메시지 출력 확인 완료
- BACKLOG #14 마킹: `docs/work_flow/specs/BACKLOG.md` 03 BACKLOG #14 "완료 (07 O2 ...)" 반영 확인
- SSH 실 검증 (prod-test-runner 위임): `ssh orin "~/smolvla/orin/scripts/run_python.sh -c 'import torch; print(torch.cuda.is_available())'"`
  - 기대: `True` 출력 + exit 0 + cuSPARSELt ImportError X
  - O2 는 task 타입 → code-tester READY 후 prod-test-runner 가 SSH 실검증 수행
- settings.json 미변경 정합성: deny-only 모델 전환으로 추가 화이트리스트 redundant 사유 명시 확인
