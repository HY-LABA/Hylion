# TODO-O3 — Prod Test

> 작성: 2026-05-01 | prod-test-runner | cycle: 1

## Verdict

**`NEEDS_USER_VERIFICATION`**

자율 정적 검증 전부 통과. Orin SSH 네트워크 불통으로 원격 read-only 검증 불가 (연결 시도 시 timeout). 배포 + 실물 실행은 사용자 직접 수행 필요.

---

## 배포 대상

- orin (변경 파일: `orin/interactive_cli/flows/{env_check,inference,entry}.py`, `orin/inference/hil_inference.py`)

## 배포 결과

- 명령: `bash scripts/deploy_orin.sh`
- 결과: **미실행** — Orin SSH 연결 불가 (ssh orin / ssh laba@ubuntu 모두 timeout)
- 스크립트 정적 검토: `SRC = smolVLA/orin/`, `rsync -avz --delete`, exclude 목록에 `interactive_cli/` 없음 → deploy 실행 시 `interactive_cli/` 포함 전송 확인됨
- deploy 실행 권한: Category B 외 변경 (orin/lerobot/ 미포함) → 자율 실행 가능이나, 현재 Orin SSH 연결 불통으로 사용자 환경 확인 후 실행 위임

---

## 자동 비대화형 검증 결과

| 검증 | 명령 | 결과 |
|---|---|---|
| py_compile — env_check.py | `python3 -m py_compile orin/interactive_cli/flows/env_check.py` | PASS |
| py_compile — inference.py | `python3 -m py_compile orin/interactive_cli/flows/inference.py` | PASS |
| py_compile — entry.py | `python3 -m py_compile orin/interactive_cli/flows/entry.py` | PASS |
| py_compile — hil_inference.py | `python3 -m py_compile orin/inference/hil_inference.py` | PASS |
| AST parse — 4개 파일 전체 | `python3 -c "ast.parse(...)"` | PASS (SyntaxError 없음) |
| bash -n — main.sh | `bash -n orin/interactive_cli/main.sh` | PASS |
| entry.py import (devPC) | `importlib` 모듈 로드 | PASS (ImportError 없음) |
| hil_inference.py --model-id / --ckpt-path 인자 존재 | `grep "model-id\|ckpt-path" hil_inference.py` | PASS (line 247, 257 확인) |
| effective_model 우선순위 시뮬레이션 | `python3 -c "argparse 시뮬레이션"` | PASS — 인자 미전달 시 `effective_model = "lerobot/smolvla_base"` 확인 |
| 03 사이클 회귀 없음 | effective_model == MODEL_ID (인자 미전달) | PASS |
| deploy_orin.sh 정적 검토 | `grep SRC/rsync/exclude` | PASS — `orin/` 전체 sync, `interactive_cli/` exclude 없음 |
| Orin SSH read-only | `ssh orin "ls ~/smolvla/orin/interactive_cli/"` | **FAIL (Connection timed out)** — 네트워크 불통, 실물 검증 불가 |

### Orin SSH 연결 실패 상세

```
ssh: connect to host 172.16.137.232 port 22: Connection timed out
```

- `ssh orin` 및 `ssh laba@ubuntu` 모두 불통
- devPC ↔ Orin 네트워크 연결 필요 (`docs/storage/04_devnetwork.md` 참조)
- SSH 불통 = 배포 불가 상태 (rsync target 도달 불가)

---

## DOD 자동 부합

| DOD 항목 | 자동 검증 가능 | 결과 |
|---|---|---|
| Orin 에서 실 인터페이스 진입 | no (사용자 실물) | → verification_queue |
| flow 0~5 완주 (env_check + inference flow) | no (사용자 실물) | → verification_queue |
| 04 G2 통합: Orin 카메라 2대 + SO-ARM follower first-time/resume | no (사용자 실물) | → verification_queue |
| 04 G2 통합: hil_inference 50-step 정상 실행 | no (사용자 실물) | → verification_queue |
| 구문 정합 (py_compile + AST) | yes | ✅ |
| bash -n main.sh | yes | ✅ |
| 03 사이클 회귀 없음 (effective_model 기본값) | yes (정적 시뮬레이션) | ✅ |
| deploy_orin.sh scope 확인 (interactive_cli/ 포함) | yes (정적 검토) | ✅ |

---

## 03 사이클 회귀 영향 정적 분석 결과

**분석 대상**: `orin/inference/hil_inference.py` 의 `--model-id` / `--ckpt-path` 추가가 기존 호출 패턴에 미치는 영향

**결론: 회귀 없음**

| 시나리오 | 호출 패턴 | effective_model | 결과 |
|---|---|---|---|
| 03 사이클 기존 호출 | `python hil_inference.py --gate-json ... --mode ...` (model 인자 없음) | `MODEL_ID = "lerobot/smolvla_base"` | 기존 동작 완전 유지 |
| O3 신규 hub 호출 | `... --model-id <repo_id>` | `args.model_id` | 신규 경로 |
| O3 신규 local 호출 | `... --ckpt-path <path>` | `Path(args.ckpt_path).expanduser()` | 신규 경로 |
| 충돌 시 | `--model-id X --ckpt-path Y` 동시 | `parser.error()` | 명시적 오류 |

- `--follower-port`, `--gate-json` 등 기존 인자 구조 무변경 → 03 사이클 호출 스크립트 무영향
- line 246~266 에 `default=None` 으로 추가 → 미전달 시 분기 진입 없음

---

## 사용자 실물 검증 필요 사항 (verification_queue 추가됨)

1. **Orin 네트워크 연결 확인** — devPC ↔ Orin SSH 연결 확립 (`docs/storage/04_devnetwork.md`)
2. **deploy 실행** — `bash scripts/deploy_orin.sh` (devPC 에서, SSH 연결 후)
3. **check_hardware.sh --mode first-time 완료** — `ports.json` + `cameras.json` 생성 확인
4. **카메라 2대 + SO-ARM follower 물리 연결** — top·wrist 카메라, follower 포트
5. **main.sh 실행 + flow 0~5 완주**:
   - flow 0: Orin 노드 진입 (VSCode remote-ssh, 확인 단계 없음)
   - flow 1: orin [*] 선택 (1 입력)
   - flow 2: env_check.py — `check_hardware.sh --mode resume` exit 0 확인
   - flow 3: 기본값 (3) 선택 → `lerobot/smolvla_base`
   - flow 4: dry-run (1) 선택 → hil_inference subprocess 실행 확인
   - flow 5: `/tmp/hil_dryrun.json` 생성 + 결과 출력 확인
6. **04 G2 verification_queue 통합 — first-time/resume 환경 검증**
7. **04 G2 verification_queue 통합 — hil_inference 50-step 실행** (live 모드, max-steps=50)
8. **03 사이클 회귀 확인** — 인자 미전달 직접 호출 시 기존 동작 동일 (`smolvla_base` 모델 로드)

---

## CLAUDE.md 준수

| 항목 | 결과 |
|---|---|
| Category A (docs/reference/ 미수정, .claude/ 미수정) | ✅ |
| Category B (orin/lerobot/ 미변경, deploy_orin.sh 미변경) | ✅ — deploy 실행은 Category B 외 변경 대상, 자율 실행 가능 |
| Category D (rm -rf / sudo / force-push 없음) | ✅ |
| ssh read-only 자율 실행 시도 | ✅ — 실행했으나 네트워크 불통 (timeout), 환경 문제, 에이전트 오류 아님 |
| 큰 다운로드 / 5분 이상 실행 | N.A. — SSH 불통으로 미도달 |
| 자율성 경계 (deploy 실행) | — SSH 불통으로 미실행. 연결 복구 후 Category B 외 → 자율 실행 가능. 사용자에게 위임 |
