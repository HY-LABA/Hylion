# TODO-O5 — Implementation

> 작성: 2026-05-03 | task-executor | cycle: 1

## 목표

Orin 사전학습 ckpt 로드 + 더미 obs 추론 (Wave 4 / 게이트 3) — `inference_baseline.py` 에 `--ckpt-path` 인자 추가, prod-test-runner 가 SSH 로 실 검증 수행.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `orin/tests/inference_baseline.py` | M | `--ckpt-path` / `--model-id` 인자 추가 + `main()` 함수 형태로 전환 |

## 적용 룰

- CLAUDE.md Hard Constraints Category A: `docs/reference/` 미변경
- Coupled File Rule: `orin/tests/` 는 `orin/lerobot/` 아님 — `03_orin_lerobot_diff.md` 갱신 불필요
- 레퍼런스 직접 Read:
  - `docs/reference/lerobot/src/lerobot/utils/hub.py` L88~127: `from_pretrained(pretrained_name_or_path: str | Path)` — 로컬 디렉터리 경로 또는 HF repo_id 모두 지원
  - `docs/reference/lerobot/src/lerobot/policies/utils.py` L97~137: `prepare_observation_for_inference(observation, device, task, robot_type)` 시그니처
  - `docs/reference/lerobot/src/lerobot/policies/factory.py` L241~303: `make_pre_post_processors(cfg, pretrained_path: str | None, ...)` 시그니처
  - `orin/inference/hil_inference.py` (기존 우리 코드): `--ckpt-path` / `--model-id` 충돌 방지 패턴 그대로 미러
- Category 분류: `orin/tests/` — Category B 외 (자유 수정 가능)

## 변경 내용 요약

### 가정 반증 검증 결과

spec 기재 `orin/examples/tutorial/smolvla/inference_baseline.py` 가 실제로는 `orin/tests/inference_baseline.py` 임은 plan.md 에서 이미 정정됨. 현재 `orin/tests/inference_baseline.py` 는 `MODEL_ID = "lerobot/smolvla_base"` 를 하드코딩하며 argparse 없이 스크립트 최상단에서 직접 실행하는 구조. `--ckpt-path` 인자가 없어 T3 산출물 로컬 ckpt 를 직접 받을 수 없었음.

`hil_inference.py` 는 `--ckpt-path` 를 이미 보유하나 `--follower-port` (SO-ARM 직결 필수) 와 `robot.connect()` 가 포함되어 더미 obs 전용 실행에 부적합.

### 변경 내용

`inference_baseline.py` 를 `main()` 함수 형태로 전환하고 다음 인자 추가:

- `--ckpt-path`: 로컬 pretrained_model 디렉터리 경로 (예: `~/smolvla/orin/checkpoints/07_pilot_2k/002000`)
- `--model-id`: HF Hub repo_id (예: `lerobot/smolvla_base`)

인자 우선순위: `--ckpt-path` > `--model-id` > 기본값(`lerobot/smolvla_base`). 두 인자 동시 지정 시 즉시 에러. `hil_inference.py` 의 동일 패턴을 미러.

`from_pretrained` 은 `pretrained_name_or_path: str | Path` 를 받아 로컬 경로 또는 HF repo_id 모두 처리하므로 로컬 ckpt 로드에 추가 코드 불필요. `make_pre_post_processors` 의 `pretrained_path` 인자는 `str | None` 이므로 Path 를 str 로 변환하여 전달.

DOD 항목 "action shape (1, 6) 정상" 을 stdout 으로 명시적으로 검증·출력. shape 불일치 시 stderr 경고 후 계속 진행(exit 0).

## code-tester 입장에서 검증 권장 사항

1. **syntax 검사**: `python -m py_compile orin/tests/inference_baseline.py` (devPC 에서 통과 확인)
2. **argparse smoke**: `python orin/tests/inference_baseline.py --help` — 인자 목록 확인
3. **인자 충돌 검사**: `python orin/tests/inference_baseline.py --ckpt-path /tmp/x --model-id foo` → 에러 메시지 + exit 1 확인
4. **ruff**: `ruff check orin/tests/inference_baseline.py`
5. **DOD 정합 확인**: 인자 추가 전후 기본 실행 경로(`lerobot/smolvla_base`) 동작 변경 없음 확인
6. **prod-test-runner 인계**: 아래 SSH 검증 명령 시퀀스 참조

## prod-test-runner 인계 — Orin SSH 검증 명령 시퀀스

### Step 1: ckpt 파일 존재 확인 (T3 PASS 산출물)

```bash
ssh orin "ls -la ~/smolvla/orin/checkpoints/07_pilot_2k/002000/"
```

기대: 7 파일 (model.safetensors, config.json, preprocessor_config.json 등) 합산 865M 전후.

### Step 2: wrapper 경유 더미 obs 추론 — 로컬 ckpt

```bash
ssh orin "~/smolvla/orin/scripts/run_python.sh \
  ~/smolvla/orin/tests/inference_baseline.py \
  --ckpt-path ~/smolvla/orin/checkpoints/07_pilot_2k/002000"
```

기대:
- `cuSPARSELt ImportError` 없음 (run_python.sh wrapper 효과 — LD_LIBRARY_PATH 적용)
- `[load] 로컬 ckpt 경로: ...` 출력
- `[DOD] action shape (1, 6) OK` 출력
- `[done] exit 0` 출력
- exit code: 0

### Step 3: fallback — lerobot/smolvla_base (T3 ckpt 정합 실패 시)

T3 ckpt 가 `svla_so100_pickplace` fine-tune 결과이므로 camera key 매핑
(camera1/camera2/camera3 vs top/wrist) 불일치 가능성 있음.
로컬 ckpt 로드 실패 또는 shape 불일치 발생 시:

```bash
ssh orin "~/smolvla/orin/scripts/run_python.sh \
  ~/smolvla/orin/tests/inference_baseline.py"
```

(인자 없음 → 기본값 `lerobot/smolvla_base` HF Hub 다운로드 또는 캐시 사용)

### Step 4: verification_queue 마킹

다음 항목은 PHYS_REQUIRED — verification_queue 에 추가:

```
O 그룹 | SSH_AUTO | O5 더미 obs forward (run_python.sh wrapper + ckpt 로드 + action shape)
O 그룹 | PHYS_REQUIRED | O5 SO-ARM 직결 hil_inference 50-step (시연장 이동 시)
```

## ckpt 정합 위험 사항

T3 ckpt (`07_pilot_2k`, `svla_so100_pickplace` 2000-step fine-tune) 는
`lerobot/smolvla_base` 의 input_features 를 상속 — camera1/camera2/camera3 3 슬롯.
`inference_baseline.py` 는 `policy.config.input_features` 에서 자동 추출하므로
camera key 는 fine-tune ckpt 의 config 를 따름.
action dim 도 fine-tune ckpt config 에 따라 6 이 아닐 수 있음 → DOD 검증 결과를
prod-test-runner 가 stdout 에서 확인 후 이상 시 보고 (03 BACKLOG #1·#2 트리거).

## Wave 4 (게이트 3) 의존 관계

- O2 (run_python.sh wrapper) PASS 조건 — Step 2 검증 시 wrapper 사용 전제
- T3 (sync_ckpt) PASS 조건 — Orin 측 ckpt 존재 전제
- 본 todo 는 코드 변경 최소 (inference_baseline.py 인자 추가만) — 실 검증은 prod-test-runner 책임
