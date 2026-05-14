# TODO-D11 — Implementation

> 작성: 2026-05-03 | task-executor | cycle: 1

## 목표

`dgx/interactive_cli/flows/teleop.py` 의 `_run_teleop_script` 에 KeyboardInterrupt catch 추가 + `flow3_teleoperate` 안내 강화 — Ctrl+C 후 flow4 prompt 정상 진입 보장.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `dgx/interactive_cli/flows/teleop.py` | M | `_run_teleop_script` try/except KeyboardInterrupt 추가 + `flow3_teleoperate` 안내 강화 |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 (read-only 준수) ✓
- 옵션 B 원칙: `dgx/lerobot/`, `orin/lerobot/` 미변경 ✓ — lerobot upstream 변경 X
- Coupled File Rule: `teleop.py` 는 `orin/lerobot/`·`pyproject.toml` 미포함 → coupled file 갱신 불요 ✓
- 레퍼런스 직접 Read: `docs/reference/lerobot/src/lerobot/scripts/lerobot_teleoperate.py` L239
  - 인용: `except KeyboardInterrupt: pass` (line 239) + `finally: teleop.disconnect(); robot.disconnect()`
  - 적용: 동일 패턴으로 `_run_teleop_script` 에 `except KeyboardInterrupt: return 0` 구현
  - 변경 사항: upstream 은 자신(lerobot-teleoperate) 내부에서 catch. 우리는 subprocess 부모(Python)에서 catch → return 0 으로 정상 종료 처리.

## 변경 내용 요약

### Part A — `_run_teleop_script` KeyboardInterrupt catch (L70~83)

기존 `subprocess.run(cmd, check=False)` 호출을 `try/except KeyboardInterrupt` 로 감쌌다. lerobot upstream `lerobot_teleoperate.py` 는 내부에서 `except KeyboardInterrupt: pass` 로 자체 정리(disconnect)하고 프로세스가 종료된다. Ctrl+C 는 process group 전체로 SIGINT 를 보내므로 subprocess(lerobot-teleoperate) 와 부모 Python 프로세스 모두 수신한다. 기존 코드는 부모의 KeyboardInterrupt 를 처리하지 않아 entry.py 까지 propagate 되어 프로세스 죽음이 발생했다. 수정 후 catch → `return 0` 으로 flow4 정상 분기 진입이 보장된다.

### Part B — `flow3_teleoperate` 안내 강화 (L104~111)

기존 3줄 흐름 안내에서 2번 항목을 "Ctrl+C 가 유일한 종료 방법" 으로 명시하고, lerobot 특유의 동작(teleop 도중 'Teleop loop time: ...' 출력만 보이고 종료 안내 없음)을 주석(※)으로 추가했다. 사용자가 Ctrl+C 를 언제 눌러야 하는지 혼동 없이 파악할 수 있다.

### Part C — flow4 정합 확인

`flow4_confirm_teleop` (L127~) 는 `prev_returncode == 0` 분기에서 "텔레오퍼레이션이 완료되었습니다." 메시지를 출력하므로, `_run_teleop_script` 가 KeyboardInterrupt → `return 0` 를 반환하면 자동으로 정상 완료 분기로 진입한다. 코드 변경 없이 정합 확인 완료.

## lerobot-teleoperate 종료 패턴 확인 결과

파일: `docs/reference/lerobot/src/lerobot/scripts/lerobot_teleoperate.py`

```python
# L227~245 (Read 직접 확인)
try:
    teleop_loop(...)
except KeyboardInterrupt:
    pass
finally:
    if cfg.display_data:
        shutdown_rerun()
    teleop.disconnect()
    robot.disconnect()
```

- Ctrl+C 가 `teleop_loop` 를 중단시키고 `finally` 블록에서 disconnect 수행 후 프로세스 정상 종료.
- lerobot upstream 변경 X (옵션 B 준수).

## 검증 결과

- `py_compile`: PASS (`python3 -m py_compile dgx/interactive_cli/flows/teleop.py`)
- `import smoke`: PASS (`python3 -c "import flows.teleop"`)
- `ruff check`: PASS (`ruff check dgx/interactive_cli/flows/teleop.py` → "All checks passed!")

## code-tester 인계 사항 / 검증 권장

- 단위: `python3 -m py_compile dgx/interactive_cli/flows/teleop.py`
- lint: `ruff check dgx/interactive_cli/flows/teleop.py`
- import smoke: `python3 -c "import sys; sys.path.insert(0, 'dgx/interactive_cli'); import flows.teleop"`
- KeyboardInterrupt 로직 확인:
  - `_run_teleop_script` 내 `try/except KeyboardInterrupt` 블록 존재 여부
  - `except KeyboardInterrupt: ... return 0` 반환 확인
  - `flow3_teleoperate` 안내 문자열에 "Ctrl+C 한 번 누르면" + "※ teleop 도중에는" 문구 존재 여부
- DOD 항목:
  1. `_run_teleop_script` try/except KeyboardInterrupt → return 0 + 사용자 안내 ✓
  2. `flow3_teleoperate` 안내 강화 — Ctrl+C 강조 + lerobot 도중 안내 X 사실 명시 ✓
  3. py_compile + ruff PASS ✓
  4. 사용자 walkthrough 재시도 시 Ctrl+C 후 flow4 prompt 정상 진입 — PHYS_REQUIRED (실물 검증 필요)
