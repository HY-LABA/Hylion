# TODO-03-B — Code Test

> 작성: 2026-05-17 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈 0건, Recommended 2건.

---

## 단위 테스트 결과

```
bash -n orin/scripts/run_inference_leftarm_v2.sh
EXIT: 0  (문법 오류 없음)

pytest: 해당 없음 (shell script — Python 단위 테스트 없음)
ruff: 해당 없음 (shell script)
mypy: 해당 없음 (shell script)
```

---

## Lint·Type 결과

```
shellcheck 미실행 (devPC 환경 미설치). bash -n 문법 검사로 대체.
bash -n: 통과 (EXIT 0)

비고 (수동 코드 리뷰로 대체):
- set -euo pipefail 확인 ✅
- #!/usr/bin/env bash shebang 확인 ✅
- shellcheck source=/dev/null 주석 활용 — source 지시어 경고 억제 적절 ✅
- line 162 인라인 주석 (echo "..." # current value: ...) — bash -n 통과, 기능상 문제 없음 ✅
```

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| (a) ckpt 다운로드 + n_action_steps 점검·수정 | ✅ | `download` subcommand: huggingface-cli download + check_n_action_steps (1→50 자동 수정) |
| (b) lerobot-record eval 모드, 두 task instruction 별 실행 | ✅ | `live task1` / `live task2` subcommand: task instruction 별 분기, --policy.path 전달 |
| (c) 성능평가 시트 신설 | ✅ | TODO-03-A 담당. 03-B 범위 외 |
| (d) M2 진입 가치 판단 | ✅ | TODO-03-A 담당. 03-B 범위 외 |
| 5 subcommand 구현 (download/check/dry-run/live/help) | ✅ | 모두 구현. dry-run/dryrun 별칭도 지원 |
| task 인자 검증 (task1/task2) | ✅ | live subcommand case 문에서 task1/task2 외 → ERROR + exit 1 |
| n_action_steps 자동 수정 로직 | ✅ | check_n_action_steps 함수: python3 -c로 config.json read+write, 1→50 수정 |
| config null 처리 | ✅ | validate_robot_config: FOLLOWER_PORT/TOP_IDX/WRIST_IDX 중 None 있으면 에러 + 안내 + exit 1 |
| Coupled Rules §6 — orin/scripts/README.md 신규 작성 | ✅ | README.md 신규 작성 완료. 스크립트 목록 표 + 사전 조건 + 관련 문서 포함 |

---

## 레퍼런스 정합성 검증

### task instruction 정합

collection_log.md 정본 (grep 확인):
- task1: `"Pick up the blue and yellow doll and place it on the left side of the table"` ✅
- task2: `"Hand the yellow can to the person"` ✅

스크립트 내 (line 29-30):
- TASK1_INSTRUCTION="Pick up the blue and yellow doll and place it on the left side of the table" ✅
- TASK2_INSTRUCTION="Hand the yellow can to the person" ✅

### lerobot-record 인자 구조 정합

| 인자 | 레퍼런스 출처 | 스크립트 값 | 정합 |
|---|---|---|---|
| --robot.type=so100_follower | config_so_follower.py:45-46 `@RobotConfig.register_subclass("so100_follower")` | 동일 | ✅ |
| --robot.cameras (JSON dict) | lerobot_record.py:26 예시 패턴 `{name: {type: opencv, index_or_path: N, ...}}` | 동일 패턴 | ✅ |
| --policy.path | lerobot_record.py:255-257 `__get_path_fields__ = ["policy"]` | --policy.path="${CKPT_LOCAL_DIR}" | ✅ |
| --dataset.rename_map | lerobot_record.py:210 `DatasetRecordConfig.rename_map: dict[str, str]` | '{"observation.images.top":"observation.images.camera1",...}' | ✅ |
| --dataset.single_task | lerobot_record.py:30 예시 패턴 | --dataset.single_task="${task_instruction}" | ✅ |
| entrypoint lerobot-record | pyproject.toml:279 `lerobot-record="lerobot.scripts.lerobot_record:main"` | lerobot-record 직접 호출 | ✅ |

### rename_map 정합

학습 시 (prof_train_setting §3): top→camera1, wrist→camera2
스크립트 RENAME_MAP (line 224): `{"observation.images.top":"observation.images.camera1","observation.images.wrist":"observation.images.camera2"}`
→ 완전 일치 ✅

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `orin/README.md` 트리 (line 37-40) | 트리 구조에 `run_teleoperate.sh` 표기(실존 X) + `README.md`, `run_python.sh`, `run_inference_leftarm_v2.sh` 미등록. 이는 기존부터 누적된 drift — 초기 커밋 이후 미갱신. TODO-03-B 신규 파일 추가로 drift 심화. BACKLOG 등록 + 다음 사이클 정정 권장. Critical 상향 불요 (기존 drift 연장). |
| 2 | `cmd_live` line 209 | `check_n_action_steps` 가 `live` 실행 시마다 호출되어 config.json 을 재수정함 (n_action_steps 가 이미 50이면 "OK" 출력만). 기능상 문제 없으나 `download` 후 `live` 연속 실행 시 재확인 비용 미미. 개선 필요성 낮음 — 문서화로 충분. |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` read-only 참조만. `.claude/` 미변경 |
| B (자동 재시도 X) | ✅ | `orin/lerobot/` 미변경. `orin/pyproject.toml` 미변경. `setup_env.sh` 미변경. `deploy_*.sh` 미변경. `orin/scripts/run_inference_leftarm_v2.sh` 는 Category B 파일 아님 |
| C (사용자 동의 필수) | ✅ | `orin/scripts/` 실존 디렉터리 — 신규 디렉터리 생성 없음. 신규 외부 의존성 없음 |
| D (절대 금지 명령) | ✅ | rm -rf / sudo / git push --force 등 없음. huggingface-cli download 는 허용 |
| Coupled File Rules §6 | ✅ | `orin/scripts/` 신규 파일 추가 → `orin/scripts/README.md` 신규 작성으로 충족. `orin/README.md` 상위 트리 미갱신은 기존 drift 연장 — Recommended #1 로 분류 |
| Lerobot upstream check | ✅ | `orin/lerobot/` 코드 변경 없음. `orin/pyproject.toml` 변경 없음. Coupled File Rules 1·2·3 미해당 |

---

## 배포 권장

yes — prod-test-runner 진입 권장.

TODO-03-B 는 SSH_AUTO 항목 (Orin SSH 점검 시퀀스) — prod-test-runner 가 Orin SSH 접속 후 config.json 확인, CLI dry-run, rename_map 정합 확인 수행.
