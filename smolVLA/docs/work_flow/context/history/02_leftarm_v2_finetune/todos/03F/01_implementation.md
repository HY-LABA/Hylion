# TODO-03-F — Implementation

> 작성: 2026-05-18 | task-executor | cycle: 1

## 목표

lerobot-record 폐기 (F1·F4·F5·F6 연쇄 import 실패 — trim 구조와 근본 양립 불가) 후,
`orin/inference/leftarm_v2_inference.py` 신규 작성 + wrapper 재조정.
`hil_inference.py` 는 사전학습 ckpt 책임 보존 (갱신 X).

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `orin/inference/leftarm_v2_inference.py` | 신규 | v2 LoRA adapter 추론 entry — task1/task2 분기 + rename_map + peft lazy import |
| `orin/scripts/run_inference_leftarm_v2.sh` | M | lerobot-record 호출 → leftarm_v2_inference.py 직접 호출로 교체 (dry-run/live 재작성) |
| `orin/inference/README.md` | M | 자산 표에 leftarm_v2_inference.py 행 추가, 예정 표 정정 (Coupled Rules §6) |

## 적용 룰

- CLAUDE.md Hard Constraints Category A: `docs/reference/` 미변경 ✓, `.claude/` 미변경 ✓
- Category B 미해당: 신규 파일 `orin/inference/` — `orin/lerobot/`, `orin/pyproject.toml`, `orin/scripts/setup_env.sh`, `deploy_*.sh` 영향 없음 ✓
- Coupled File Rules §6: `orin/inference/README.md` 본문 정정 동시 완료 ✓
- 레퍼런스 활용:
  - hil_inference.py: parse_camera_arg, flip_observation_cameras, load_gate_config, apply_gate_config, _auto_discover_cameras, inference loop 전체 패턴 차용 (검증된 구현)
  - lego_v1_inference.py: fourcc="MJPG" (USB 2.0 hub), GATE_CAMERA_ALIAS 패턴, measured_empty 로그 패턴 차용
  - `docs/reference/lerobot/src/lerobot/policies/factory.py` line 537-558: LoRA 로드 패턴
    인용: `peft_config = PeftConfig.from_pretrained(peft_pretrained_path)` →
          `policy = policy_cls.from_pretrained(pretrained_name_or_path=peft_config.base_model_name_or_path)` →
          `policy = PeftModel.from_pretrained(policy, peft_pretrained_path, config=peft_config)`
  - collection_log.md: task instruction 확정값 (line 15-16)

## 변경 내용 요약

**hil_inference.py / lego_v1_inference.py 코드 조사 결과**:

- 공통 패턴: SmolVLAPolicy.from_pretrained(model_path) → policy.eval() → make_pre_post_processors() → robot.connect() → while loop (get_observation → build_inference_frame → preprocess → select_action → postprocess → make_robot_action → send_action) → finally robot.disconnect()
- lego_v1_inference.py 는 fourcc="MJPG" 추가 (USB 2.0 hub 대역폭 한계), GATE_CAMERA_ALIAS (top→overview) 패턴 도입
- 두 파일 모두 `SmolVLAPolicy.from_pretrained(model_id)` 직접 로드 — LoRA adapter 없음

**leftarm_v2_inference.py 핵심 구조**:

1. `load_policy_with_lora(ckpt_dir, device)`: `docs/reference/lerobot/src/lerobot/policies/factory.py` line 537-558 패턴을 직접 구현. `PeftConfig.from_pretrained(ckpt_dir)` → `base_model_name_or_path` 읽기 → `SmolVLAPolicy.from_pretrained(base)` → `PeftModel.from_pretrained(policy, ckpt_dir)`
2. `apply_rename_map(obs)`: observation dict 의 `observation.images.top` → `observation.images.camera1`, `observation.images.wrist` → `observation.images.camera2` rename. robot.get_observation() 이 slot key 로 반환하면 no-op (hil_inference.py 의 SLOT_MAP 매핑과 병용 가능)
3. CLI `--task task1/task2`: TASK_INSTRUCTIONS dict 분기 (collection_log.md 확정값)
4. `--n-action-steps default=50`: config.json 이미 수정됨 (prod-test cycle 1 확인). 안전 목적 낮추기 가능
5. fourcc="MJPG": lego_v1_inference.py 패턴 차용 (USB 2.0 hub 대역폭 한계)

**LoRA 로드 방법**:

- `peft` 라이브러리 필요 (`PeftConfig`, `PeftModel`)
- orin/pyproject.toml 에 peft 미등록 → Orin 환경에 미설치 확인 (SSH 검증: `ModuleNotFoundError: No module named 'peft'`)
- `load_policy_with_lora` 에서 lazy import + 미설치 시 명확한 에러 메시지 + 설치 안내 출력
- orin/pyproject.toml 에 peft 추가는 Category B+C (의존성 추가 — 사용자 동의 필요) → 별도 처리

**wrapper 변경 diff 핵심**:

- 헤더 주석: `Wraps: lerobot-record` → `Wraps: orin/inference/leftarm_v2_inference.py`
- `INFERENCE_SCRIPT` env 변수 추가 (기본값: `~/smolvla/orin/inference/leftarm_v2_inference.py`)
- `cmd_dry_run()`: lerobot-record --help 출력 → `python ${INFERENCE_SCRIPT} --mode dry-run --max-steps 1 ... || true`
- `cmd_live()`: lerobot-record 명령 → `python ${INFERENCE_SCRIPT} --mode live --task ${task_key} ...`
- F2 fix (`export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}"`) 보존 ✓
- F3 fix (`command -v hf` 분기) 보존 (download subcommand) ✓
- 5 subcommand 구조 보존 ✓
- task1/task2 인자 검증 보존 ✓

**orin/inference/README.md 갱신**:

- "자산 (현재)" 표에 `leftarm_v2_inference.py` 행 추가 (책임: v2 LoRA adapter + rename_map + task 분기, 출처: TODO-03-F 2026-05-18)
- hil_inference.py 행에 "사전학습 ckpt 책임 보존 — 갱신 X" 명시
- "자산 (예정)" 표에서 "05_leftarmVLA TODO-14 hil_inference.py 갱신" 행 제거 (leftarm_v2_inference.py 신규로 완료)

## code-tester 입장에서 검증 권장 사항

- `bash -n orin/scripts/run_inference_leftarm_v2.sh` — shell syntax 체크
- `python -m py_compile orin/inference/leftarm_v2_inference.py` — Python syntax 체크
- `ruff check orin/inference/leftarm_v2_inference.py` — lint
- DOD 정합:
  - task instruction 확인: TASK_INSTRUCTIONS["task1"] == collection_log.md line 15
  - LoRA 로드 패턴: factory.py line 537-558 와 일치 확인
  - rename_map 적용: apply_rename_map 이 `observation.images.top` → `observation.images.camera1` 으로 변환하는지
  - F2 fix 보존: wrapper line 24 `export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}"`
  - F3 fix 보존: wrapper `cmd_download` 내 `command -v hf` 분기
  - Coupled Rules §6: README.md 갱신 확인

## 잔여 리스크

1. **peft 미설치 (BLOCKER 잠재)**: Orin 환경에 `peft>=0.10.0` 미설치. `leftarm_v2_inference.py` 실행 시 `load_policy_with_lora()` 에서 ImportError 발생 + 설치 안내 출력. **peft 설치는 Category B+C — 사용자 동의 필요.** Phase 3 시연 전 반드시 처리 필요.
   - 설치 명령 (동의 후): `pip install peft>=0.10.0`
   - orin/pyproject.toml `[project.optional-dependencies].smolvla` 에 추가 권장 (별도 사용자 승인)

2. **rename_map 적용 지점**: robot.get_observation() 이 slot key ('camera1', 'camera2') 로 반환할 가능성 있음 (hil_inference.py 는 camera_config 에 slot key 로 등록하므로). 이 경우 `apply_rename_map` 은 no-op — 정합. 실 환경에서 observation key 확인 권장.

3. **PeftModel + select_action 호환성**: `PeftModel.from_pretrained(policy, ...)` 후 `policy.select_action(obs_frame)` 호환 여부. lerobot/factory.py 는 `PeftModel` 반환 후 `policy.to(device)` 호출 — 본 구현도 동일. `lerobot_eval.py` line 299-304 는 `isinstance(policy, PeftModel)` 확인으로 `select_action` 호환 전제. Orin 실 환경 dry-run 으로 확인 필요.

4. **empty_cameras**: 학습 ckpt 의 `config.json` 에 `empty_cameras` 실측값 미파악 (로컬 ckpt 없음). 실 환경에서 `policy.config.empty_cameras` 로그 확인 후 camera3 영향 판단.
