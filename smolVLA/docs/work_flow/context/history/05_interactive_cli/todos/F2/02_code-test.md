# TODO-F2 — Code Test

> 작성: 2026-05-02 09:00 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 0건, Recommended 1건.

---

## 단위 테스트 결과

```
bash -n orin/interactive_cli/main.sh        → PASS
bash -n dgx/interactive_cli/main.sh         → PASS
bash -n datacollector/interactive_cli/main.sh → PASS

python3 -m py_compile orin/interactive_cli/flows/entry.py        → PASS
python3 -m py_compile dgx/interactive_cli/flows/entry.py         → PASS
python3 -m py_compile datacollector/interactive_cli/flows/entry.py → PASS

diff orin/entry.py dgx/entry.py          → IDENTICAL
diff orin/entry.py datacollector/entry.py → IDENTICAL

diff orin/flows/__init__.py dgx/flows/__init__.py          → IDENTICAL
diff orin/flows/__init__.py datacollector/flows/__init__.py → IDENTICAL

F1 §3 코드블록 vs orin/entry.py → IDENTICAL (7533 chars, 문자 단위 일치)

15개 파일 존재 확인 → 전부 EXISTS
```

## Lint·Type 결과

```
ruff: 환경에 설치되지 않아 직접 실행 불가 (python3 -m ruff → module not found).
mypy: 동일 이유 (비설치 환경).

수동 코드 검토 결과:
- entry.py line 162~170: `options` 리스트 생성 후 append만 되고 실제로 참조되지 않음 (미사용 변수).
  F1 §3 코드 원본 그대로이므로 F2 도입 결함 아님 — Recommended 로 분류.
- 그 외 PEP 8·타입 어노테이션·import 순서 이상 없음.
```

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| F1 산출물 (main.sh + flows/entry.py) 을 3 노드에 동일 복사 | ✅ | entry.py 3 파일 문자 단위 IDENTICAL 확인. F1 §3 코드블록과도 완전 일치 |
| 각 노드 configs/node.yaml 환경 설정 분리 | ✅ | node: orin/dgx/datacollector 각각 정확. venv 경로 노드별 분리 |
| main.sh 가 자기 노드를 인식하여 flow 1 의 본 노드 active 처리 가능 | ✅ | main.sh → --node-config 전달 → entry.py 가 node.yaml 로드 → node 값으로 분기. orin/dgx/datacollector 각자 node.yaml 고유값 보유 |
| orin venv 경로: `~/smolvla/orin/.hylion_arm/bin/activate` | ✅ | orin/main.sh line 33 일치 |
| dgx venv 경로: `~/smolvla/dgx/.arm_finetune/bin/activate` | ✅ | dgx/main.sh line 30 일치 |
| datacollector venv 경로: `~/smolvla/datacollector/.hylion_collector/bin/activate` | ✅ | datacollector/main.sh line 31 일치 |
| cusparseLt 블록 orin only | ✅ | orin/main.sh line 55~57 포함. dgx·datacollector 해당 블록 없음 |
| 3 노드 동일 복사 + deploy 3번 동기화 필요 README 명시 | ✅ | 3개 README 모두 "devPC 에서 한 곳 수정 후 deploy_orin/dgx/datacollector 3 번으로 동기화" 명시 |
| main.sh 호출법 명시 (`bash <node>/interactive_cli/main.sh`) | ✅ | 3개 README 모두 해당 노드별 호출법 코드블록 포함 |
| F1 §5 `--gate-json` 코드 미복사 (§2·§3 만) | ✅ | entry.py + main.sh 에 --gate-json / run_env_check 패턴 없음 확인 |
| cusparseLt 라인 인용 정확성 | ✅ | check_hardware.sh 실제 line 164~168 (if 블록+주석 포함) 과 일치. "line 156~162" (venv source) 도 실제 범위 일치 |

## Critical 이슈

없음.

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `flows/entry.py` line 162, 170 (3 노드 동일) | `options` 리스트가 생성·append 되지만 실제 로직에서 참조되지 않음. F1 §3 원본 코드 그대로이므로 F2 책임 아님 — 후행 todo (flow 1 고도화 시) 또는 F1 §3 정정 트랙에서 처리 권장 |

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/`, `.claude/` 미변경 |
| B (자동 재시도 X) | ✅ | `orin/lerobot/`, `dgx/lerobot/`, `pyproject.toml`, `setup_env.sh`, `deploy_*.sh`, `.gitignore` 미변경 |
| Coupled File Rules | ✅ | lerobot/pyproject 영역 변경 없음 — 03_orin_lerobot_diff.md / 02_orin_pyproject_diff.md 갱신 불필요 |
| C (사용자 동의) | ✅ | spec 본문 라인 89~118 에서 신규 디렉터리 (orin/dgx/datacollector 하위) 사용자 합의 완료 확인 |
| D (금지 명령) | ✅ | rm -rf / sudo / force push 등 없음 |
| 옛 룰 (`docs/storage/` bash 예시) | ✅ | docs/storage/ 미변경 |

## 세부 검증 메모

### 라인 인용 정확성 검증

`check_hardware.sh` 직접 Read 결과:
- `step_venv()` 함수: line 152~173
- `venv source 패턴` (if + source 블록): line 156~162
- `cusparseLt if 블록 + 주석`: line 164~168

orin/main.sh 주석의 "line 156~162", "line 164~168" 인용 — 실제와 일치.

### entry.py F1 §3 코드 완전 일치 확인

`docs/storage/12_interactive_cli_framework.md` §3 코드블록을 추출하여 orin/interactive_cli/flows/entry.py 와 diff → IDENTICAL (7,533 chars, 차이 없음).

### bash 안전 플래그

3 노드 main.sh 모두 `set -uo pipefail` 적용. `set -e` 미포함은 `check_hardware.sh` 동일 패턴이므로 일관성 있음. venv 파일 미존재 시 `if [[ ! -f ]]` 로 명시적 처리됨.

### `__pycache__` 잔여 리스크

최상위 `.gitignore` line 13~14 에 `__pycache__/`, `*.pyc` 이미 포함 — git 추적 없음. rsync deploy 시 `--exclude` 별도 확인은 prod-test 단계 또는 deploy 스크립트 검토 시 처리 가능.

### F2 prod-test 진입 여부

본 F2 는 정적 분석 + 파일 존재 검증만으로 DOD 충족 확인 완료. **F2 prod-test 별도 진입 X — D3·O3·X3 통합 검증으로 처리** (실 노드 SSH main.sh 호출은 각 노드 prod 검증 todo 에 포함).

## 배포 권장

READY_TO_SHIP — prod-test-runner 진입 권장.
단, F2 prod-test 는 별도 진입하지 않고 D3·O3·X3 에 통합하여 실 노드 검증 수행 권고.
