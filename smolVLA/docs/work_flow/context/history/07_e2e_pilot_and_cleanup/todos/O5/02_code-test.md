# TODO-O5 — Code Test

> 작성: 2026-05-03 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈: 0건. Recommended 개선 사항: 1건.

---

## 단위 테스트 결과

```
# argparse logic — Python 3.13 devPC 에서 실행 (Orin Python 3.10 대상 코드 검증)

Test 1 PASS: no args -> both None
Test 2 PASS: --ckpt-path only
Test 3 PASS: --model-id only
Test 4 PASS: conflict detected (ckpt_path is not None and model_id is not None)
Test 5 PASS: expanduser -> /home/babogaeguri/smolvla/orin/checkpoints/007
Test 6a PASS: ckpt_path -> Path
Test 6b PASS: model_id -> str
Test 6c PASS: no args -> default (lerobot/smolvla_base)
All tests PASSED

# DOD exit 0 보장 확인
DOD exit 0 guaranteed: True (shape mismatch goes to stderr, continues)
Exit path: main() returns None -> __name__==main -> implicit sys.exit(0)
```

충돌 검사 로직 (`args.ckpt_path is not None and args.model_id is not None`) 정상 동작 확인.
우선순위 체인 (`--ckpt-path > --model-id > DEFAULT_MODEL_ID`) 정상 동작 확인.
DOD shape 불일치 시 stderr 출력 후 exit 0 보장 확인.

pytest 는 해당 없음 (orin/tests/inference_baseline.py 는 pytest 형식 아님 — SSH 실행 전용 스크립트, test 타입 todo).

---

## Lint·Type 결과

```
# py_compile
python -m py_compile orin/tests/inference_baseline.py
Exit: 0   ← PASS

# ruff check
ruff check orin/tests/inference_baseline.py
All checks passed!
Exit: 0   ← PASS
```

mypy 는 orin/tests/ 가 strict mypy 적용 대상 외 (lerobot CLAUDE.md 기준 envs/configs/optim/model/cameras/motors/transport 만 strict) — 해당 없음.

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. T3 ckpt 또는 fallback lerobot/smolvla_base 로드 | ✅ | --ckpt-path / --model-id / 기본값 3-way 분기 구현. Path.expanduser() 적용 |
| 2. inference_baseline.py 패턴으로 더미 obs forward 1 회 | ✅ | input_features 자동 추출 + dummy_obs 구성 + select_action 호출 유지 |
| 3. exit 0 + action shape (1, 6) 정상 출력 | ✅ | `[DOD] action shape (1, 6) OK` 출력. 불일치 시 stderr + exit 0 (계속 진행) |
| 4. SO-ARM 직결 hil_inference 50-step BACKLOG 마킹 | ✅ | prod-test-runner 인계 문서에 verification_queue 마킹 지침 명시 |
| 5. --ckpt-path / --model-id 충돌 방지 (hil_inference.py 패턴 미러) | ✅ | 동일 패턴. hil_inference 는 parser.error() 사용, inference_baseline 는 sys.exit(1) — 기능 동일 |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `orin/tests/inference_baseline.py:83` | 충돌 검사 시 `sys.exit(1)` 대신 `parser.error(...)` 사용 권장. hil_inference.py 와 완전 일치 + argparse 표준 에러 형식 통일. 기능 차이는 없으며 minor 스타일 차이. |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경. `.claude/agents/`, `.claude/skills/` 미변경. `.claude/settings.json` 변경 존재하나 O5 task-executor 산출물 아님 — Phase 1 deny-only 모델 전환 (07-#1 PROMPT_FATIGUE_RESOLVED) 으로 주석 확인. O2 implementation.md 에 "settings.json 미변경 사유" 명시됨. |
| B (자동 재시도 X 영역) | ✅ | `orin/lerobot/`, `dgx/lerobot/` 미변경. `orin/pyproject.toml` 미변경. `orin/scripts/setup_env.sh` 변경 존재하나 O5 산출물 아님 (O3 산출물). `.gitignore` 변경 존재하나 O5 산출물 아님 (P2 산출물). |
| Coupled File Rules | ✅ | `orin/lerobot/` 미변경 — `03_orin_lerobot_diff.md` 갱신 불필요. `orin/pyproject.toml` 미변경 — `setup_env.sh`·`02_orin_pyproject_diff.md` 갱신 불필요. implementation.md 에 명시 확인. |
| 옛 룰 | ✅ | `docs/storage/` 에 bash 명령 예시 추가 없음. |

---

## 레퍼런스 인용 정합성 (lerobot-reference-usage)

| 레퍼런스 | 인용 라인 | 실제 시그니처 확인 | 정합 |
|---|---|---|---|
| `hub.py` L88~127 `from_pretrained` | code L104 | `pretrained_name_or_path: str \| Path` — 로컬 디렉터리 또는 HF repo_id 지원 | ✅ 코드가 Path 또는 str 그대로 전달 |
| `factory.py` L241~303 `make_pre_post_processors` | code L131~135 | `pretrained_path: str \| None` | ✅ `pretrained_path_str` 로 Path→str 변환 후 전달 |
| `utils.py` L97~137 `prepare_observation_for_inference` | code L140~142 | `(observation, device, task, robot_type)` | ✅ 정확히 일치. device 는 torch.device 객체 전달 |

---

## 논리적 결함 검사

**Python 3.10 타입 어노테이션 호환성**: `str | Path` (PEP 604, Python 3.10+), `dict[str, ...]` (PEP 585, Python 3.9+) — Orin Python 3.10 대상으로 호환.

**회귀 위험**: 이전 코드는 `DEVICE = "cuda"` 하드코딩이었으나 신규 코드는 `torch.device("cuda" if torch.cuda.is_available() else "cpu")` — devPC 에서 실행 시 "cpu" 로 graceful fallback. Orin (CUDA 있음) 에서는 동일하게 "cuda" 선택. 회귀 없음.

**make_pre_post_processors `pretrained_path` 전달 시 로컬 ckpt 케이스 검토**: `effective_model` 이 Path 인 경우 `str(effective_model)` 로 변환하여 전달. HF Hub 케이스는 그대로 str. `None` 은 전달 안 됨 (항상 기본값 `DEFAULT_MODEL_ID` 로 채워짐). 정합.

**T3 ckpt 정합 위험**: implementation.md 에 명시된 대로, T3 ckpt (svla_so100_pickplace fine-tune) 의 camera key (top/wrist) 가 smolvla_base 의 input_features (camera1/camera2/camera3) 와 매핑 불일치 가능성 존재. 코드는 `policy.config.input_features` 에서 자동 추출하므로 로컬 ckpt 로드 시 그 ckpt 의 config 를 따름 — 코드 분기 자체는 정합. 실 정합 여부는 prod-test-runner SSH 검증에서 확인 (DOD 요건도 prod-test 위임).

---

## 배포 권장

READY_TO_SHIP — prod-test-runner 진입 권장.

prod-test-runner 검증 포인트:
1. `ssh orin "ls -la ~/smolvla/orin/checkpoints/07_pilot_2k/002000/"` — T3 ckpt 존재 확인
2. `ssh orin "~/smolvla/orin/scripts/run_python.sh ~/smolvla/orin/tests/inference_baseline.py --ckpt-path ~/smolvla/orin/checkpoints/07_pilot_2k/002000"` — 로컬 ckpt 로드 + `[DOD] action shape (1, 6) OK` 출력 + exit 0
3. 로컬 ckpt 로드 실패 또는 shape 불일치 시 `BACKLOG #1·#2` 트리거 보고
4. verification_queue 에 `O 그룹 | SSH_AUTO | O5 더미 obs forward` 마킹 확인
