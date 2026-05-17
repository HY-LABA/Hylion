# TODO-03-F — Code Test

> 작성: 2026-05-18 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈: 0건. Recommended 개선 사항: 1건.

---

## 단위 테스트 결과

```
python3 -m py_compile orin/inference/leftarm_v2_inference.py → SYNTAX_OK
bash -n orin/scripts/run_inference_leftarm_v2.sh             → BASH_SYNTAX_OK
```

pytest 대상 없음 (신규 entry 파일, 단위 테스트 스위트 미작성 — hil_inference.py 패턴과 동일).

---

## Lint·Type 결과

```
ruff check orin/inference/leftarm_v2_inference.py
→ All checks passed!
```

mypy: 본 파일은 `orin/` 영역 — upstream lerobot CLAUDE.md 기준 strict 적용 대상 아님. 생략.

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| (a) Orin ckpt 다운로드 + n_action_steps·config.json 키 점검 | ✅ | `cmd_download` + `check_n_action_steps()` 구현. config.json n_action_steps 1 → 50 자동 수정 로직 포함 (prof_train_setting §7-5 trap). `cmd_check` 에서 input_features keys + rename_map reminder 출력. |
| (b) 두 task instruction 별 정책 실행 (dry-run → live) | ✅ | `--task task1/task2` CLI 인자 + `TASK_INSTRUCTIONS` dict 분기. `cmd_dry_run()` → `--mode dry-run --max-steps 1`. `cmd_live task1/task2` → `--mode live`. |
| (c) rename_map 적용 (top→camera1, wrist→camera2) | ✅ | `apply_rename_map()` 구현. `observation.images.top` → `observation.images.camera1`, `observation.images.wrist` → `observation.images.camera2`. `robot.get_observation()` 후, `build_inference_frame()` 전 적용 (코드 line 538~558). |
| LoRA 로드 패턴 (factory.py line 537-558 일치) | ✅ | `PeftConfig.from_pretrained(ckpt_dir)` → `base_model_name_or_path` 읽기 → `SmolVLAPolicy.from_pretrained(base)` → `PeftModel.from_pretrained(policy, ckpt_dir, config=peft_config)` → `policy.to(device)` → `policy.eval()`. factory.py 패턴과 완전 일치. |
| peft lazy import + 명확한 에러 메시지 | ✅ | `load_policy_with_lora()` 내부 `from peft import PeftConfig, PeftModel`. top-level import 아님. 미설치 시 설치 안내 + orin/pyproject.toml 미등록 설명 출력. |
| task instruction 정본 일치 | ✅ | collection_log.md line 15-16 확인. task1: "Pick up the blue and yellow doll and place it on the left side of the table" / task2: "Hand the yellow can to the person" — 코드 내 `TASK_INSTRUCTIONS` dict 완전 일치. |
| CLI 인자 전체 | ✅ | --ckpt-dir / --task / --mode / --follower-port / --cameras / --flip-cameras / --n-action-steps / --max-steps / --gate-json / --output-json 모두 구현. (추가: --follower-id 도 구현됨 — DOD 범위 외 추가지만 기능 무해.) |
| fourcc="MJPG" | ✅ | `OpenCVCameraConfig(index_or_path=idx, width=640, height=480, fps=30, fourcc="MJPG")` (line 492). USB 2.0 hub 대역폭 한계 대응. |
| hil_inference.py 패턴 함수 차용 | ✅ | `parse_camera_arg`, `flip_observation_cameras`, `load_gate_config`, `apply_gate_config`, `_auto_discover_cameras` 모두 구현. SIGINT 핸들러 + try/finally disconnect 포함. dry-run/live 모드 분기 포함. |
| wrapper F2 fix (`export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}"`) 유지 | ✅ | run_inference_leftarm_v2.sh line 29 확인. |
| wrapper F3 fix (`command -v hf` 분기) 유지 | ✅ | `cmd_download` 내 line 132 확인. |
| 5 subcommand 구조 (download/check/dry-run/live/help) | ✅ | dispatch case 문 확인. dry-run\|dryrun 양쪽 수용. |
| 잔여 lerobot-record 활성 호출 없음 | ✅ | heredoc/주석 외 실행 코드에서 lerobot-record 호출 0건 확인. |
| INFERENCE_SCRIPT env 변수 정의 + override 가능 | ✅ | line 36: `INFERENCE_SCRIPT="${INFERENCE_SCRIPT:-${HOME}/smolvla/orin/inference/leftarm_v2_inference.py}"` |
| README.md 본문 "자산(현재)" 표에 leftarm_v2_inference.py 행 추가 | ✅ | git diff 확인. `leftarm_v2_inference.py` 행 추가 + hil_inference.py 행 "사전학습 ckpt 책임 보존 — 갱신 X" 명시. |
| README.md 예정 표 "05_leftarmVLA TODO-14" 행 제거 | ✅ | git diff 확인. "hil_inference.py 갱신 (학습 ckpt 인자 추가)" 행 삭제됨. |
| Coupled File Rules §6 (본문 정정, 박스 누적 X) | ✅ | README.md 본문 표 직접 수정. ⚠️ 박스 추가 없음. |

---

## Critical 이슈 (없음)

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `orin/inference/README.md` (사용 예시 섹션) | `hil_inference.py` 전용 dry-run/live 사용 예시만 있고 `leftarm_v2_inference.py` 사용 예시가 없음. 후속 마일스톤 README 갱신 시 추가 권장 (시연 전 runbook 목적). 현재 wrapper 주석과 `cmd_help` 내용으로 충분히 대체 가능하므로 Critical 아님. |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경. `.claude/` 미변경. |
| B (자동 재시도 X 영역) | ✅ (주의) | `orin/lerobot/scripts/lerobot_record.py` 변경 확인됨 — Category B 영역. 단, 이 변경은 **TODO-03-E (F1 fix)** 에서 이미 처리된 것으로, Coupled File Rules `03_orin_lerobot_diff.md` 동시 갱신 완료 확인. TODO-03-F 에서 신규 추가된 Category B 영역 변경은 없음. |
| Coupled File Rules | ✅ | `orin/lerobot/` 변경 (lerobot_record.py) → `03_orin_lerobot_diff.md` 동시 갱신 확인 (TODO-03-E 산출물). `orin/inference/README.md` 본문 정정 완료. `orin/pyproject.toml` 수정 없음 → setup_env.sh·02_pyproject_diff 갱신 의무 없음. |
| C (사용자 동의 필수) | ✅ | 신규 디렉터리 생성 없음. peft 의존성 추가는 TODO-03-F 범위 외 (lazy import 처리 + BLOCKER 메모). |
| D (절대 금지 명령) | ✅ | rm -rf·sudo·git push --force 등 없음. |
| 옛 룰 | ✅ | `docs/storage/` 하위 bash 명령 예시 추가 없음. |

---

## peft BLOCKER 명시

`leftarm_v2_inference.py` 는 코드 정합 검증 통과 (syntax·lint·패턴·DOD 모두 충족). 단 **Orin 실 환경 동작에는 peft>=0.10.0 설치가 필수**:

- `load_policy_with_lora()` 내 `from peft import PeftConfig, PeftModel` 이 미설치 시 ImportError 발생.
- orin/pyproject.toml 에 peft 미등록 (Category B+C — 사용자 동의 필요).
- 설치 명령 (사용자 동의 후): `pip install peft>=0.10.0` (Orin venv 내).
- Phase 3 시연 전 반드시 처리 필요. prod-test-runner 에서 peft import 가능 여부 사전 확인 권장.

---

## 배포 권장

READY_TO_SHIP — prod-test-runner 진입 권장.

단, prod-test-runner 는 다음을 우선 점검할 것:
1. Orin venv 에 peft 설치 여부 (`python -c "import peft"`)
2. peft 미설치 시 verdict NEEDS_USER_VERIFICATION (peft 설치 사용자 동의 요청)
3. ckpt 로컬 경로 존재 여부 (`~/smolvla/orin/checkpoints/leftarm_v2_A2_pc_2026-05-17/`)
