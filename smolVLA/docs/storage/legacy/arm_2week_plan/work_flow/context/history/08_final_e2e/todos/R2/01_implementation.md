# TODO-R2 — Implementation

> 작성: 2026-05-04 | task-executor | cycle: 1

## 목표

활성 코드 SO100 → SO101 일괄 마이그레이션 + R1 Recommended 흡수 (§7 파일수 오기 정정)

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `orin/inference/hil_inference.py` | M | import SO101Follower/Config + ROBOT_TYPE "so101_follower" + docstring + 인스턴스화 |
| `orin/tests/measure_latency.py` | M | ROBOT_TYPE "so101_follower" |
| `orin/tests/smoke_test.py` | M | robot_type="so101_follower" |
| `orin/tests/inference_baseline.py` | M | ROBOT_TYPE "so101_follower" |
| `orin/examples/tutorial/smolvla/using_smolvla_example.py` | M | import SO101 + 인스턴스화 + follower_id 주석 + robot_type 주석 |
| `dgx/interactive_cli/flows/record.py` | M | docstring [3] 예시 so101_follower (상수 ROBOT_TYPE 은 이미 so101_follower 였음) |
| `orin/lerobot/scripts/lerobot_record.py` | M (Category B) | docstring 예시 so101_follower/leader |
| `orin/lerobot/scripts/lerobot_replay.py` | M (Category B) | docstring 예시 so101_follower |
| `orin/lerobot/scripts/lerobot_calibrate.py` | M (Category B) | docstring 예시 so101_leader |
| `orin/lerobot/scripts/lerobot_setup_motors.py` | M (Category B) | docstring 예시 so101_leader |
| `orin/lerobot/scripts/lerobot_find_joint_limits.py` | M (Category B) | docstring 예시 so101_follower/leader |
| `docs/storage/lerobot_upstream_check/03_orin_lerobot_diff.md` | M | R2 Category B 변경 이력 추가 (Coupled File Rule) |
| `docs/storage/16_so100_vs_so101.md` | M | §7-1 파일수 오기 4개→6개, §요약 5개→6개 정정 |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 ✓
- Coupled File Rule: `orin/lerobot/` 변경 → `03_orin_lerobot_diff.md` 동시 갱신 ✓
- lerobot-upstream-check: Category B (`orin/lerobot/scripts/`) docstring 수준 최소 변경 ✓, 하위 호환 분기 보존 ✓
- lerobot-reference-usage: R1 study `docs/storage/16_so100_vs_so101.md` 가 레퍼런스. alias 구조 확인 (SO100Follower = SO101Follower = SOFollower) — 인터페이스 완전 호환 확인 후 교체.

## 변경 내용 요약

R1 study (16_so100_vs_so101.md) 결과를 기반으로 활성 코드 전반의 SO100 → SO101 일괄 마이그레이션을 적용했다. upstream 확인 결과 SO100Follower / SO101Follower 는 동일 SOFollower 클래스의 alias 이므로 인터페이스 호환성이 완전 보장되며, 변경은 import 이름 + ROBOT_TYPE 문자열 교체만으로 충분하다.

`dgx/interactive_cli/flows/record.py` 의 상수 `ROBOT_TYPE = "so101_follower"` (L101) 는 이미 SO101 로 되어 있었고, 레퍼런스 docstring 인용 부분 (L30) 만 so100 → so101 로 수정했다. Category B 영역인 `orin/lerobot/scripts/` 5개 파일은 docstring 예시 교체에 한정했으며, `lerobot_setup_motors.py` 의 `COMPATIBLE_DEVICES` 리스트는 SO100 하위 호환을 위해 so100_follower/so100_leader 를 그대로 보존했다.

## Category B 영향

| 파일 | 변경 성격 | 하위 호환 |
|---|---|---|
| `orin/lerobot/scripts/lerobot_record.py` | docstring SO101 교체 | SO100 동작 영향 없음 |
| `orin/lerobot/scripts/lerobot_replay.py` | docstring SO101 교체 | SO100 동작 영향 없음 |
| `orin/lerobot/scripts/lerobot_calibrate.py` | docstring SO101 교체 | SO100 동작 영향 없음 |
| `orin/lerobot/scripts/lerobot_setup_motors.py` | docstring SO101 교체, COMPATIBLE_DEVICES 보존 | SO100 동작 영향 없음 |
| `orin/lerobot/scripts/lerobot_find_joint_limits.py` | docstring SO101 교체 | SO100 동작 영향 없음 |

`orin/lerobot/robots/utils.py`, `orin/lerobot/teleoperators/utils.py` 의 so100_follower/so100_leader 분기는 R1 §7-2 방침대로 보존 (so101 분기 이미 존재).

## code-tester 입장에서 검증 권장 사항

- grep 검증: `grep -rn "SO100Follower\|SO100FollowerConfig\|SO100Leader\|so100_follower\|so100_leader" orin/inference/ orin/tests/ orin/examples/ dgx/interactive_cli/flows/record.py` — 0건 (svla_so100_pickplace 제외)
- import 정합: `from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig` 라인 존재 확인
- ROBOT_TYPE: `orin/inference/hil_inference.py`, `orin/tests/measure_latency.py`, `orin/tests/inference_baseline.py` 에서 `ROBOT_TYPE = "so101_follower"` 확인
- smoke_test.py: `robot_type="so101_follower"` 확인
- 데이터셋 ID 보존: `svla_so100_pickplace` 문자열 변경 없음 확인
- 03_orin_lerobot_diff.md: 2026-05-04 R2 항목 존재 확인
- 16_so100_vs_so101.md: §7-1 "6개", §요약 "6개" 확인
- Category B 하위 호환: `orin/lerobot/robots/utils.py` 에 `so100_follower` 분기 보존 확인

## 잔여 리스크

- calibration JSON 경로가 robot_type 의존 (`so100_follower` vs `so101_follower`) — Orin 에서 SO101 로 처음 연결 시 재calibration 또는 기존 JSON 이전 필요. 코드 레벨 해결 불가, 운영 단계 처리 (R1 §4, §6 기재 내용).
