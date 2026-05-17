# TODO-03-B — Implementation

> 작성: 2026-05-17 | task-executor | cycle: 1

## 목표

prof_computer 학습 ckpt (`BaboGaeguri/leftarm_v2_A2_pc_2026-05-17`) 를 Orin 에서 추론하기 위한 thin shell wrapper 신규 작성. `lerobot-record` CLI 를 policy 모드로 호출하는 단일 진입점.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `orin/scripts/run_inference_leftarm_v2.sh` | 신규 (N) | lerobot-record 기반 추론 wrapper (5 subcommand) |
| `orin/scripts/README.md` | 신규 (N) | scripts/ 디렉터리 문서 신규 작성 (M1.5 reflection §6 coupled file 의무) |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 (read 참조만) ✓
- Category B 영향 없음: `orin/lerobot/` 수정 X, `orin/pyproject.toml` 수정 X, `setup_env.sh` 수정 X ✓
- Category C 미해당: `orin/scripts/` 디렉터리 실존, 신규 의존성 없음 ✓
- Coupled File Rule §6 (M1.5 reflection 도출): 신규 파일 추가 → `orin/scripts/README.md` 신규 작성 ✓
- 레퍼런스 직접 Read:
  - `docs/reference/lerobot/src/lerobot/scripts/lerobot_record.py` (전체)
    - `RecordConfig.__get_path_fields__` → `--policy.path=<dir>` 로 ckpt 로드 (line 255-257)
    - `DatasetRecordConfig.rename_map: dict[str, str]` (line 210) → `--dataset.rename_map='{...}'`
    - 카메라 인자: `--robot.cameras="{name: {type: opencv, index_or_path: N, ...}}"` (line 26)
    - robot type 키: `so100_follower` (line 35, 확인: robots/so_follower/config_so_follower.py line 45-46)
    - entrypoint: `lerobot-record="lerobot.scripts.lerobot_record:main"` (pyproject.toml line 279)
  - `docs/reference/lerobot/src/lerobot/robots/so_follower/config_so_follower.py`
    - `@RobotConfig.register_subclass("so100_follower")` (line 45-46) → robot.type 키 확정
  - `dgx/docs/finetune/leftarm_v2/collection_log.md`
    - task1 instruction: "Pick up the blue and yellow doll and place it on the left side of the table" (line 15)
    - task2 instruction: "Hand the yellow can to the person" (line 16)

## lerobot-record vs lerobot-eval 판단 결과

`pyproject.toml` (line 279, 283):
- `lerobot-record="lerobot.scripts.lerobot_record:main"` — 데이터 수집 + **policy 모드 동시 지원**
- `lerobot-eval="lerobot.scripts.lerobot_eval:main"` — 별도 eval 전용 entrypoint 존재

`lerobot_record.py RecordConfig` (line 218-257):
- `policy: PreTrainedConfig | None = None` — policy 가 있으면 robot 을 policy 로 제어
- `__post_init__` (line 241): `--policy.path` 인자 존재 시 `PreTrainedConfig.from_pretrained(policy_path)` 로드
- policy 모드에서 `lerobot-record` = **데이터 기록 + policy 추론** 동시. 즉 eval 기록에도 사용 가능.

**결론**: `prof_train_setting.md §5-3` 의 `lerobot-record` 지시 + upstream 코드 확인으로 `lerobot-record --policy.path=<ckpt>` 가 추론 실행 방법으로 정확함. `lerobot-eval` 은 별도 엔드포인트이나 본 사이클에서는 `lerobot-record` policy 모드 사용 (데이터 수집과 동일 경로, 추론 에피소드 기록 가능).

## 스크립트 인자 구조 (확정)

```bash
lerobot-record \
    --robot.type=so100_follower \
    --robot.port="${FOLLOWER_PORT}" \
    --robot.cameras="{top: {type: opencv, index_or_path: ${TOP_IDX}, width: 640, height: 480, fps: 30}, \
                      wrist: {type: opencv, index_or_path: ${WRIST_IDX}, width: 640, height: 480, fps: 30}}" \
    --policy.path="${CKPT_LOCAL_DIR}" \
    --policy.device=cuda \
    --dataset.repo_id="local/leftarm_v2_eval_<timestamp>" \
    --dataset.single_task="<task instruction>" \
    --dataset.num_episodes=10 \
    --dataset.episode_time_s=60 \
    --dataset.reset_time_s=30 \
    --dataset.rename_map='{"observation.images.top":"observation.images.camera1","observation.images.wrist":"observation.images.camera2"}' \
    --dataset.push_to_hub=false \
    --display_data=true
```

인자 출처:
- `--robot.type=so100_follower`: `config_so_follower.py:45-46` `@RobotConfig.register_subclass("so100_follower")`
- `--robot.cameras`: `lerobot_record.py:26` 예시 패턴 그대로 (`{name: {type: opencv, index_or_path: N, width: W, height: H, fps: F}}`)
- `--policy.path`: `lerobot_record.py:255-257` `__get_path_fields__ = ["policy"]` → draccus 가 이 필드를 path 로 파싱
- `--dataset.rename_map`: `lerobot_record.py:210` `DatasetRecordConfig.rename_map: dict[str, str]`
- rename_map 값: `prof_train_setting.md §3` 학습 시 `top→camera1, wrist→camera2` 적용 → 추론 시 동일 매핑 필요

## 변경 내용 요약

`orin/scripts/run_inference_leftarm_v2.sh` 는 `lerobot-record` CLI 를 policy 모드로 호출하는 5-subcommand bash wrapper 다. `download` 는 HF Hub 에서 ckpt 를 받아 `n_action_steps=1→50` 자동 수정 (prof_train_setting §7-5 함정), `check` 는 config.json 의 image feature 키·rename_map 정합 출력, `dry-run` 은 CLI 인식 확인 + 명령 골자 echo, `live` 는 실 SO-ARM + 카메라로 추론 실행, `help` 는 사용법 출력이다.

robot config (follower_port, top/wrist camera index) 는 `orin/config/{ports,cameras}.json` 에서 읽는다. 현재 두 파일 모두 `null` 값 — 시연장 환경에서 사용자가 채우거나 환경 변수로 override 한다. null 값이 있으면 `live` 실행 시 에러 + 안내 메시지를 출력하고 종료한다.

rename_map (`top→camera1, wrist→camera2`) 은 학습 시 적용된 값과 동일하게 자동 적용되므로 사용자가 별도 지정 불필요하다.

## code-tester 입장에서 검증 권장 사항

- **syntax lint**: `bash -n orin/scripts/run_inference_leftarm_v2.sh`
- **help 출력**: `./orin/scripts/run_inference_leftarm_v2.sh help` — 5 subcommand 안내 출력 확인
- **dry-run 출력 정합**: `dry-run` subcommand 가 lerobot-record --help 를 호출하는지 확인 (venv 없으면 source 실패 — SSH 환경에서만 완전 실행 가능)
- **n_action_steps 자동 수정 로직**: `check_n_action_steps` 함수의 python3 -c 구문이 config.json read + write 정확히 수행하는지
- **null 검사 로직**: `validate_robot_config` 에서 FOLLOWER_PORT=None 일 때 exit 1 + 안내 메시지 출력 확인
- **DOD 정합**:
  - (a) download + n_action_steps 점검·수정 ✓ (`download` subcommand)
  - (b) 두 task instruction 별 추론 실행 ✓ (`live task1` / `live task2`)
  - (c) 성능평가 시트는 별도 TODO-03-C (prod-test-runner) 또는 spec §83 의 `prof_computer/docs/orin_eval_2026-05-17.md` 로 분리
- **Category A 위반 없음**: `docs/reference/` 미변경 확인

## 가정 / 잔여 리스크

| 항목 | 내용 | 처리 |
|---|---|---|
| orin/config null 값 | `ports.json`, `cameras.json` 모두 null — 시연장 의존 | `live` 실행 시 에러 + 안내. env override 가이드 제공 |
| `--robot.id` 미전달 | `SOFollowerConfig` 에 `id` 필드 존재 (config_so_follower.py). 필수 여부 미확인 | lerobot 이 id 없어도 기본값 사용 가능성. 필요 시 `--robot.id=left_arm` 추가 (Phase 3 사용자가 dry-run 오류로 확인) |
| `lerobot-eval` vs `lerobot-record` | upstream 에 `lerobot-eval` 별도 존재 (pyproject.toml:283). 단 prof_train_setting §5-3 + record.py policy 모드 확인으로 `lerobot-record` 선택 | dry-run 으로 CLI 인식 확인. 오류 시 `lerobot-eval` 대체 시도 |
| LoRA adapter 로드 | 학습이 LoRA only (adapter 125MB). `make_policy` 가 base + adapter 합성하는지 확인 필요 | lerobot SmolVLA PEFT 지원 확인 (prof_train_setting §10 가설 직접 증명). 오류 시 Phase 3 사용자가 보고 |
| dataset.repo_id 로컬 경로 | `local/leftarm_v2_eval_<timestamp>` — lerobot 이 슬래시 없는 local repo_id 를 허용하는지 미확인 | `push_to_hub=false` 설정. 오류 시 사용자 HF username 포함 실제 repo_id 로 대체 필요 |
