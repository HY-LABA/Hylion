# TODO-R1 — Implementation

> 작성: 2026-05-04 | task-executor | cycle: 1

## 목표

SO-100 vs SO-101 upstream 클래스 차이 study + `docs/storage/16_so100_vs_so101.md` 신규 작성.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `docs/storage/16_so100_vs_so101.md` | 신규 | SO100/SO101 alias 구조 + 채택 결정 + R2 마이그레이션 영향 영역 정리 |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/lerobot/` 직접 수정 X. 읽기·인용만 수행. ✓
- Coupled File Rule: 코드 파일 수정 없음 → `03_orin_lerobot_diff.md` 갱신 불요 ✓
- 레퍼런스 직접 Read:
  - `docs/reference/lerobot/src/lerobot/robots/so_follower/so_follower.py` — L232-233 alias 라인 직접 확인
  - `docs/reference/lerobot/src/lerobot/teleoperators/so_leader/so_leader.py` — L158-159 alias 라인 직접 확인
  - `docs/reference/lerobot/src/lerobot/robots/so_follower/config_so_follower.py` — register_subclass 이중 등록 확인
  - `docs/reference/lerobot/src/lerobot/teleoperators/so_leader/config_so_leader.py` — register_subclass 이중 등록 확인
  - `docs/storage/02_hardware.md` §6 — SO-101 Arm Kit Pro BOM (12V follower, 7.4V leader) 확인

## 변경 내용 요약

lerobot upstream 에서 `SO100Follower = SOFollower` (L232), `SO101Follower = SOFollower` (L233) 로 두 클래스가 동일 `SOFollower` 의 단순 alias 임을 직접 Read 로 확인했다. Config 도 동일하게 `SO100FollowerConfig = SOFollowerRobotConfig`, `SO101FollowerConfig = SOFollowerRobotConfig` alias 이며, `config_so_follower.py` 에서 `"so101_follower"` 와 `"so100_follower"` 두 robot_type 문자열이 동일 클래스에 이중 등록되어 있다. SOLeader / SOLeaderTeleopConfig 도 같은 패턴. 모터 초기화 코드는 모두 `"sts3215"` 단일 타입 · ID 1-6 고정으로 SO100/101 분기 없다.

활성 코드 현황 grep 결과 R2 직접 수정 대상 파일은 5개 (orin/inference/hil_inference.py, orin/tests 3건, orin/examples 1건, dgx/interactive_cli/flows/record.py) 이며, `orin/lerobot/scripts/` 는 Category B 영역으로 최소 변경 권고. 운영 유의 사항으로 calibration JSON 경로가 robot_type 문자열 의존이므로 SO101 전환 시 재calibration 또는 기존 JSON 이전이 필요하다.

## code-tester 입장에서 검증 권장 사항

- upstream 코드 인용 정합: `SO100Follower = SOFollower` (L232), `SO101Follower = SOFollower` (L233) 가 문서에 정확히 인용됐는지
- `SO100Leader = SOLeader` (L158), `SO101Leader = SOLeader` (L159) 인용 정합
- register_subclass 이중 등록 (`"so101_follower"`, `"so100_follower"`) 인용 정합
- §6 채택 결정 명시 여부: "SO101Follower / SO101Leader / so101_follower / so101_leader" 채택 명확히 기재
- §7 R2 영향 영역 파일·라인 수준 식별 여부
- §8 데이터셋 ID 보존 명시 여부
- docs/reference/ 직접 수정 없음 확인 (Category A)
