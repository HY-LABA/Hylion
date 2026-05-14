# TODO-R2 — Code Test

> 작성: 2026-05-04 14:30 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈 0건. Recommended 2건.

---

## 단위 테스트 결과

pytest 가 devPC 환경에 설치되어 있지 않아 직접 실행 불가. 대신 py_compile 문법 검사 + grep 검증 + lint 로 대체.

```
python -m py_compile (활성 코드 6개): 0건 이상 없음 (exit 0)
python -m py_compile (Category B 5개): 0건 이상 없음 (exit 0)
```

활성 코드 모두 문법 유효. Category B 파일도 이상 없음.

---

## Lint·Type 결과

```
ruff check (활성 코드 6개):
  orin/tests/smoke_test.py:
    F841 Local variable `e` is assigned to but never used (L131, L183) — pre-existing
    F401 `re` imported but unused (L149)                                — pre-existing
  기타 5개 파일: 이상 없음

ruff check (Category B lerobot_record.py):
  F821 Undefined name `koch_leader` (L312) — pre-existing (upstream import 축소 결과)
  F821 Undefined name `omx_leader`  (L313) — pre-existing (동일)
  기타 4개 파일: 이상 없음
```

smoke_test.py 의 F841/F401 3건 및 lerobot_record.py F821 2건은 R2 변경 전부터 존재하는 pre-existing 이슈임을 git diff 로 확인. R2 변경 범위와 무관.

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. hil_inference.py import SO101Follower/Config + ROBOT_TYPE "so101_follower" + 인스턴스화 | ✅ | L60 import, L65 ROBOT_TYPE, L433 Config, L438 Follower — 4곳 확인 |
| 2. measure_latency.py ROBOT_TYPE "so101_follower" | ✅ | L25 확인 |
| 3. smoke_test.py robot_type="so101_follower" | ✅ | L174 확인 |
| 4. inference_baseline.py ROBOT_TYPE "so101_follower" | ✅ | L43 확인 |
| 5. using_smolvla_example.py import SO101 + 인스턴스화 + follower_id 주석 + robot_type 주석 | ✅ | import L7, Config L41, Follower L42, follower_id comment L31, robot_type comment L46 확인 |
| 6. record.py SO100 언급 영역 마이그레이션 (docstring [3] so101_follower) | ✅ | L30 확인 |
| 7. Category B lerobot_*.py docstring SO100 → SO101 교체 + COMPATIBLE_DEVICES 보존 | ✅ | 5개 파일 docstring 교체 확인. COMPATIBLE_DEVICES 리스트에 so100_follower/so100_leader 보존 확인 (L56-57) |
| 8. dgx/scripts/smoke_test.sh scope 제외 | ✅ | grep 결과 SO100 미포함 확인 (R2 변경 불필요 검증) |
| 9. svla_so100_pickplace 그대로 유지 | ✅ | grep 결과 ≥1건 (orin+dgx 전체 보존). SO100 class/robot_type 변경에 영향 없음 |
| 10. 03_orin_lerobot_diff.md 갱신 (Coupled File Rule) | ✅ | 2026-05-04 R2 항목 추가 확인. grep -c "R2\|2026-05-04" → 2 |
| 11. 16_so100_vs_so101.md §7-1 파일수 오기 4 → 6 정정 | ✅ | grep -c "6개\|6 파일" → 2 (§7-1 + 요약 섹션 양쪽 정정 확인) |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `orin/inference/hil_inference.py:271` | `--follower-id` default 값이 `"follower_so100"` 으로 남아 있음. R1 §7-1 표에는 포함되지 않은 라인이고 spec DOD 명시 범위 외이므로 Critical 아님. 다음 정합 사이클 (또는 R3 prod-test 이전) 에 `"follower_so101"` 로 갱신 권장 |
| 2 | `orin/tests/smoke_test.py:131,149,183` | ruff F841/F401 pre-existing 3건. R2 도입 아님 — 별도 lint fix todo 등록 권장 |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | docs/reference/ 미변경, .claude/ 미변경 확인 |
| B (자동 재시도 X) | ✅ | orin/lerobot/scripts/ 5개 파일 변경 — docstring 최소 변경 + COMPATIBLE_DEVICES 보존. 변경 성격 확인 완료 |
| Coupled File Rules | ✅ | 03_orin_lerobot_diff.md 동시 갱신 확인. orin/pyproject.toml 변경 없어 02_*.md 갱신 불필요 |
| 옛 룰 (docs/storage/ bash 예시) | ✅ | 03_orin_lerobot_diff.md 및 16_so100_vs_so101.md 에 bash 예시 신규 추가 없음 |

### Category B 상세 검증

`orin/lerobot/scripts/` 5개 파일의 변경이 docstring 수준에 한정됨을 git diff 확인:
- lerobot_record.py: 2줄 (L24, L37 docstring --robot.type / --teleop.type)
- lerobot_replay.py: 1줄 (L24 docstring --robot.type)
- lerobot_calibrate.py: 1줄 (L24 docstring --teleop.type)
- lerobot_setup_motors.py: 1줄 (L22 docstring --teleop.type)
- lerobot_find_joint_limits.py: 2줄 (L24, L27 docstring --robot.type / --teleop.type)

실 코드 (COMPATIBLE_DEVICES, 함수 로직) 미변경 확인. upstream 원칙 준수.

`lerobot_record.py` L310 `so_leader.SO100Leader` 코드 라인은 R2 변경 아님 — upstream 그대로 보존 (Category B 원칙).

---

## 배포 권장

yes — prod-test-runner 진입 권장.

Recommended 1 (`--follower-id` default 값) 은 CLI 기본값 문제로 prod-test 단계의 SSH 실행 시 `--follower-id` 를 명시 지정하면 영향 없음. R3 prod-test 또는 별도 ad-hoc 으로 처리 가능.
