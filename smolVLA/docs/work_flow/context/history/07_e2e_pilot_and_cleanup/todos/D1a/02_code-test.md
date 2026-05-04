# TODO-D1a — Code Test

> 작성: 2026-05-04 10:15 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈 0건. Recommended 개선 사항 0건.

## 단위 테스트 결과

```
bash -n dgx/interactive_cli/main.sh → exit 0 (PASS)
bash -n orin/interactive_cli/main.sh → exit 0 (PASS)

dgx import smoke:
  cd dgx/interactive_cli && python3 -c "from flows import entry, env_check, mode; print('dgx import OK')"
  → dgx import OK (PASS)

orin import smoke:
  cd orin/interactive_cli && python3 -c "from flows import entry, env_check, inference; print('orin import OK')"
  → orin import OK (PASS)

dgx -m flows.entry --help:
  cd dgx/interactive_cli && python3 -m flows.entry --help
  → usage: entry.py [-h] --node-config NODE_CONFIG
    interactive_cli flow 0·1 — 진입 확인 + 장치 선택
  → ModuleNotFoundError X (PASS)

orin -m flows.entry --help:
  cd orin/interactive_cli && python3 -m flows.entry --help
  → usage: entry.py [-h] --node-config NODE_CONFIG
    interactive_cli flow 0·1 — 진입 확인 + 장치 선택
  → ModuleNotFoundError X (PASS)
```

## Lint·Type 결과

```
대상 파일: dgx/interactive_cli/main.sh, orin/interactive_cli/main.sh
파일 유형: bash 스크립트 — ruff/mypy 해당 없음
bash -n 구문 검사: 양측 PASS (위 단위 테스트 결과 참조)
```

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. 회귀1 패치: dgx main.sh:57 `exec python3 "${SCRIPT_DIR}/flows/entry.py"` → `cd "${SCRIPT_DIR}" && exec python3 -m flows.entry` | ✅ | git diff 확인. line 57 정확히 패치됨 |
| 2. 회귀1 패치: orin main.sh:71 동일 패턴 | ✅ | git diff 확인. line 71 정확히 패치됨 |
| 3. `--node-config "${NODE_CONFIG}"` 인자 보존 | ✅ | 양측 패치 라인에 인자 그대로 보존 |
| 4. main.sh 나머지 부분 회귀 X (venv activate, NODE_CONFIG 체크 등) | ✅ | git diff 1라인 변경만 확인 (orin 은 주석 1행 추가 포함, 기능 코드 변경 없음) |
| 5. 회귀2 권한: git 인덱스 100755 | ✅ | `git ls-files -s` → 100755 a1ac07... dgx, 100755 0f14e3... orin |
| 6. 회귀2 권한: 파일시스템 -rwxr-xr-x | ✅ | `ls -la` → 양측 -rwxr-xr-x 확인 |
| 7. bash -n 정적 검증 PASS | ✅ | 양측 exit 0 |
| 8. devPC import smoke 0 에러 (dgx: entry, env_check, mode) | ✅ | "dgx import OK" 출력 확인 |
| 9. devPC import smoke 0 에러 (orin: entry, env_check, inference) | ✅ | "orin import OK" 출력 확인 |
| 10. orin flows/ mode.py 없는 inference-only 구성 설계 정합 | ✅ | ls orin/interactive_cli/flows/ → entry.py env_check.py inference.py __init__.py (mode.py 없음 — 설계 의도 부합) |
| 11. dgx flows/ mode.py 포함 구성 정합 | ✅ | ls dgx/interactive_cli/flows/ → entry.py env_check.py mode.py record.py teleop.py training.py transfer.py data_kind.py (mode.py 포함) |
| 12. deploy_dgx.sh rsync -a = -rlptgoD (-p 포함) 결론 적정 | ✅ | rsync 3.2.7 확인. -a (archive) = -rlptgoD 는 표준 동작으로 -p (perms) 포함 — deploy_dgx.sh 수정 불요 결론 타당 |
| 13. Category B (deploy_*.sh) 변경 X | ✅ | git diff 확인 — scripts/ 미변경 |
| 14. Category A 영역 변경 X | ✅ | docs/reference/, .claude/ 미변경 |

## Critical 이슈

없음.

## Recommended 개선 사항

없음.

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | docs/reference/ 미변경, .claude/agents/*.md 미변경, .claude/settings.json 미변경 |
| B (자동 재시도 X 영역) | ✅ | orin/lerobot/, dgx/lerobot/ 미변경. scripts/deploy_*.sh 미변경 (점검·보고만). .gitignore 미변경 |
| Coupled File Rules | ✅ | orin/lerobot/ 미변경 → 03_orin_lerobot_diff.md 갱신 불요. orin/pyproject.toml 미변경 → setup_env.sh·02_*.md 갱신 불요 |
| D (절대 금지 명령) | ✅ | rm -rf, sudo, git push --force 등 사용 흔적 없음. chmod 755 사용 (chmod 777 아님) |
| 옛 룰 (docs/storage/ bash 예시) | ✅ | docs/storage/ 미변경 |

## 패치 정합 상세

git diff HEAD~1 에서 확인된 변경 내용:

- `dgx/interactive_cli/main.sh`: mode 100644 → 100755, line 57 패치 1행 (정확)
- `orin/interactive_cli/main.sh`: mode 100644 → 100755, 주석 1행 갱신 (datacollector 노드 종료 명시) + line 71 패치 1행 (정확)

오진 가능 사항: orin main.sh 에 주석 변경이 1행 더 포함되나 이는 기능 코드가 아닌 헤더 주석 (06_dgx_absorbs_datacollector 결정 반영) — Critical 아님.

## 배포 권장

READY_TO_SHIP — prod-test-runner 즉시 진입 권장.

prod-test-runner 체크리스트 (위임):
- SSH dgx: `echo "2" | timeout 10 bash ~/smolvla/dgx/interactive_cli/main.sh 2>&1 | head -50` — ModuleNotFoundError X, 메뉴 진입 확인
- SSH orin: `echo "1" | timeout 10 bash ~/smolvla/orin/interactive_cli/main.sh 2>&1 | head -50` — 동일 확인
- 권한 755 DGX 측 rsync 보존 확인 (`ls -la ~/smolvla/dgx/interactive_cli/main.sh`)
