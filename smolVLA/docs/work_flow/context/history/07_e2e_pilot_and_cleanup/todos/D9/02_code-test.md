# TODO-D9 — Code Test

> 작성: 2026-05-03 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈 0건. Recommended 1건 (2건 이하 → READY).

---

## 단위 테스트 결과

```
python -m py_compile dgx/interactive_cli/flows/precheck.py
→ py_compile PASS

bash -n dgx/interactive_cli/main.sh
→ bash -n PASS

시뮬 시나리오 4건 (인라인 Python):
  시나리오 1 PASS: follower=/dev/ttyACM0, leader=/dev/ttyACM2 (ports.json 존재 + 양쪽 유효)
  시나리오 2 PASS: ports.json 미존재 → hardcoded fallback 유지
  시나리오 3 PASS: JSON 파싱 실패 → JSONDecodeError 캐치 + fallback
  시나리오 4 PASS: leader_port=null → follower 로드 성공, leader 는 hardcoded fallback 유지
```

---

## Lint·Type 결과

```
ruff check dgx/interactive_cli/flows/precheck.py
→ All checks passed!
```

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. `_run_calibrate` 시그니처 `(configs_dir: Path) -> bool` | ✅ | L960 정확 |
| 2. `ports_path = configs_dir / _PORTS_FILENAME` + `exists()` 가드 | ✅ | L980~984 |
| 3. `json.load` → `follower_port` / `leader_port` 키 읽기 + prompt default 적용 | ✅ | L987~992, L996~1001 |
| 4. `JSONDecodeError | OSError` 예외 처리 + 경고 출력 + hardcoded fallback | ✅ | L993~994 |
| 5. 호출 위치 L1156 → `_run_calibrate(configs_dir)` 수정 | ✅ | L1156 확인 |
| 6. `configs_dir` 변수 scope 정합 (`teleop_precheck` L1081 정의) | ✅ | L1081 `_get_configs_dir(script_dir)` |
| 7. 키 정합 (`follower_port` / `leader_port`) — `_PORTS_DEFAULT` 및 `_run_find_port_self` 저장 키와 일치 | ✅ | `_run_find_port_self` 는 `f"{arm_label}_port"` 로 저장 (L345, L355) |
| 8. py_compile + ruff PASS | ✅ | 위 결과 참조 |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `precheck.py` L983~1000 | `ports_source` 가 단일 변수로 follower·leader 프롬프트에 공유됨. `leader_port` 만 null 인 경우(follower 로드 성공 → `ports_source = "ports.json 검출 결과"` 설정) leader 프롬프트에도 "source: ports.json 검출 결과" 가 표시되지만 실제 leader default 는 hardcoded fallback임. `ports_source_follower` / `ports_source_leader` 로 분리하면 안내 문자열 정확도 개선. 동작·로드 값에는 영향 없음 — UX 표시 이슈 |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경. `.claude/` 미변경 |
| B (자동 재시도 X) | ✅ | 변경 파일 `dgx/interactive_cli/flows/precheck.py` — Category B 영역 (`orin/lerobot/`, `dgx/lerobot/`, `pyproject.toml`, `setup_env.sh`, `deploy_*.sh`, `.gitignore`) 미해당 |
| Coupled File Rules | ✅ | `orin/lerobot/` / `orin/pyproject.toml` 미변경 — coupled file 갱신 의무 없음 |
| 옛 룰 (`docs/storage/` bash 예시) | ✅ | 해당 없음 |

---

## 배포 권장

**yes — prod-test-runner 진입 권장**

- py_compile PASS, ruff PASS, 시뮬 4건 PASS, Critical 0건.
- prod-test-runner 검증 포인트: DGX 배포 후 `teleop_precheck` 옵션 (1) → find-port 완료 → 캘리브 재실행 여부 y → follower prompt 에 ports.json 검출 결과(예: ttyACM0)가 default 로 표시되는지 확인.
- Recommended #1 (ports_source 분리) 은 prod-test 통과 후 후속 MINOR 패치로 처리 가능.
