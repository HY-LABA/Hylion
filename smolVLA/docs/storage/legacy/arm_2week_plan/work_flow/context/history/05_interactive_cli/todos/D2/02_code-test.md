# TODO-D2 — Code Test

> 작성: 2026-05-01 | code-tester | cycle: 1

## Verdict

**`MAJOR_REVISIONS`**

Critical 이슈 1건 (entry.py 상대 import → `python3 entry.py` 직접 호출 시 ImportError 런타임 실패).

---

## 단위 테스트 결과

ruff 미설치 환경이므로 `python3 -m py_compile` + AST 파싱 + 로직 검증으로 대체.

```
python3 -m py_compile on 6 files: ALL OK (구문 오류 없음)
AST parse: ALL OK (env_check, teleop, data_kind, record, transfer, entry)

logic validation inline:
  _validate_repo_id("user/name")  → True   OK
  _validate_repo_id("badformat")  → False  OK
  _validate_repo_id("a/b/c")      → False  OK
  _validate_num_episodes(50)      → True   OK
  _validate_num_episodes(0)       → False  OK
  data_kind_choice 1~5 in map     → OK
  data_kind_choice 6 not in map   → OK

entry.py 직접 실행 (python3 datacollector/interactive_cli/flows/entry.py --help):
  Traceback:
    File "...entry.py", line 22, in <module>
      from .env_check import flow2_env_check
  ImportError: attempted relative import with no known parent package
  → FAIL (Critical)

orin/entry.py 직접 실행:
  usage: entry.py [-h] --node-config NODE_CONFIG  → OK
dgx/entry.py 직접 실행:
  usage: entry.py [-h] --node-config NODE_CONFIG  → OK
```

---

## Lint·Type 결과

```
ruff: 미설치 (환경에 없음) — 수동 AST/import 검사로 대체
mypy: 미실행 (ruff 동일 사유)

수동 import 스캔 결과 (AST walk):
  env_check.py : os, sys, Path, NamedTuple — 모두 사용됨
  teleop.py    : subprocess, sys, Path — 모두 사용됨
  data_kind.py : NamedTuple — 사용됨
  record.py    : os, re, subprocess, sys, Path — 모두 사용됨
  transfer.py  : os, subprocess, sys, Path — 모두 사용됨
  entry.py     : argparse, sys, Path, yaml(optional) — 사용됨
                 flow2~7 imports — 상대 import 사용 (Critical, 아래 참조)

비-Critical 경고:
  record.py: _lerobot import 에서 `import lerobot as _lr` 와 `import lerobot` 이중 임포트
  (noqa: F401 마킹되어 있어 의도적이나, 한 번만 해도 충분)
```

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. flow 2~7 모두 구현 | ✅ | env_check/teleop/data_kind/record/transfer 5개 모듈 + entry 통합 |
| 2. run_teleoperate.sh subprocess 호출 | ✅ | teleop.py `subprocess.run(["bash", teleop_script, "all"], check=False)` |
| 3. push_dataset_hub.sh subprocess 호출 | ✅ | transfer.py `_transfer_to_hub()` 에서 `subprocess.run(cmd, check=False)` |
| 4. sync_dataset_collector_to_dgx.sh 직접 호출 금지 + 안내 | ✅ | transfer.py `_guide_rsync_to_dgx()` — 안내 메시지만 출력, subprocess 호출 없음 |
| 5. lerobot-record draccus 인자 동적 생성 | ✅ | record.py `build_record_args()` — 고정 인자 + 사용자 입력 조합 |
| 6. 04 G3 check_hardware 책임 흡수 | ✅ | env_check.py 5단계 (venv/USB/camera/lerobot/data_dir) |
| 7. 사용자 결정 옵션 1 적용 | ✅ | data_kind.py `DATA_KIND_OPTIONS[1].single_task = "Pick up the object and place it in the target area."` + `default_num_episodes = 50` |
| 8. record.py `SINGLE_TASK_MAP[1]` 동일 | ✅ | `"Pick up the object and place it in the target area."` |
| 9. entry.py 통합 연결 (`_run_datacollector_flows`) | ✅ (코드 존재) / ❌ (런타임 실패) | 상대 import 때문에 main.sh 호출 시 ImportError 발생 — Critical |
| 10. validation 4항목 | △ | 3항목은 실효. 4번째(카메라 인덱스) validation은 자기 자신과 비교 — 항상 통과 (Recommended) |

---

## Critical 이슈 (MAJOR_REVISIONS 사유)

### 1. entry.py 상대 import → main.sh 호출 시 ImportError 런타임 실패

- 위치: `datacollector/interactive_cli/flows/entry.py:22~26`
- 사유: `from .env_check import ...` 등 상대 import 5줄을 사용하지만, `main.sh` 가 `python3 "${SCRIPT_DIR}/flows/entry.py"` 로 직접 호출 (스크립트 모드). 파이썬은 스크립트 직접 실행 시 `__package__`가 `None`이 되어 상대 import 불가 → `ImportError: attempted relative import with no known parent package` 발생.
- 실측 확인: `python3 datacollector/interactive_cli/flows/entry.py --help` → ImportError (실패)
- 비교: orin/entry.py, dgx/entry.py 는 `_CLI_DIR = Path(__file__).parent.parent` + `sys.path.insert(0, str(_CLI_DIR))` 주입 후 `from flows.env_check import ...` 절대 import 패턴 사용 → 정상 동작
- 수정 요청:
  ```python
  # 상대 import 제거, orin/entry.py 패턴으로 교체
  _THIS_DIR = Path(__file__).parent
  _CLI_DIR = _THIS_DIR.parent
  if str(_CLI_DIR) not in sys.path:
      sys.path.insert(0, str(_CLI_DIR))

  from flows.env_check import flow2_env_check
  from flows.teleop import flow3_teleoperate, flow4_confirm_teleop
  from flows.data_kind import flow5_select_data_kind
  from flows.record import flow6_record
  from flows.transfer import flow7_select_transfer
  ```

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `record.py:336~339` | `_validate_camera_indices` 4번째 validation이 자기 자신과 비교 (항상 True) — 실질적 검증 없음. 의도가 "flow 2에서 받은 인덱스를 그대로 사용했는가"라면 이 validation 항목은 불필요하거나, `flow6_record` 시그니처에 `env_check_wrist`, `env_check_overview` 별도 파라미터를 받아 실제 비교해야 함. |
| 2 | `record.py:314` vs `record.py:335` | `_validate_data_kind_choice(data_kind_choice)` 이중 호출 — 첫 번째(314)가 early-exit이라 중복 호출. 불필요한 중복이나 기능 오류는 아님. |
| 3 | `env_check.py:steps` | D1 §1 스펙 순서: venv(1)→USB(2)→camera(3)→lerobot(4)→data_dir(5). 구현 순서: venv→USB→lerobot→data_dir→camera(별도). 카메라가 마지막으로 재배치됨. 기능상 문제는 없으나 스펙 순서와 다름. |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경. `.claude/` 미변경 |
| B (자동 재시도 X) | ✅ | `orin/lerobot/`, `pyproject.toml`, `setup_env.sh`, `deploy_*.sh` 미변경 |
| Coupled File Rules | ✅ | `orin/lerobot/` 미변경 → `03_orin_lerobot_diff.md` 갱신 불필요 |
| Category C | ✅ | `datacollector/interactive_cli/` 는 spec 합의된 디렉터리 |
| Category D | ✅ | `rm -rf`, `sudo` 등 금지 명령 없음 |
| 옛 룰 | ✅ | `docs/storage/` 에 bash 명령 예시 추가 없음 |

---

## 배포 권장

**no** — Critical 1건 해소 후 재제출 필요.

- task-executor 수정 요청 사항: `datacollector/interactive_cli/flows/entry.py` 의 상대 import 5줄을 orin/entry.py 패턴 (sys.path 주입 + 절대 import) 으로 교체.
- Recommended 3건은 1회 수정 시 함께 처리 권장 (특히 Recommended 1: `_validate_camera_indices` 자기참조 이슈).
- Category B 비해당 → MAJOR 시에도 task-executor 1회 재호출 가능.
