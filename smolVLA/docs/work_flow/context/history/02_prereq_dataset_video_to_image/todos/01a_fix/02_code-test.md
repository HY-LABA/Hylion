# TODO-1a-fix — Code Test

> 작성: 2026-05-16 10:50 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈 0건. Recommended 개선 사항 1건 (기존 ruff E731, 이번 변경과 무관한 pre-existing).

---

## 단위 테스트 결과

```
대상: Python 파일 — dgx/finetune/leftarm_v2/run_train.py
      YAML 파일   — dgx/finetune/leftarm_v2/config/train_config.yaml

python3 -c "import ast; ast.parse(open('dgx/finetune/leftarm_v2/run_train.py').read()); print('AST OK')"
→ AST OK

python3 -c "import yaml; d=yaml.safe_load(open('dgx/finetune/leftarm_v2/config/train_config.yaml')); print('YAML OK'); print('dataset_video_backend:', repr(d.get('dataset_video_backend')))"
→ YAML OK
→ dataset_video_backend: 'pyav'
```

---

## Lint·Type 결과

```
ruff check dgx/finetune/leftarm_v2/run_train.py
→ E731 Do not assign a `lambda` expression, use a `def`
     dgx/finetune/leftarm_v2/run_train.py:102:5  b = lambda x: str(x).lower()

  Found 1 error. (이번 변경과 무관 — line 102 는 기존 코드. 신규 추가 라인 L89, L121 에 lint 이슈 없음)
```

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| train_config.yaml L37 에 `dataset_video_backend: pyav` 추가 | ✅ | grep 확인: L37 정확 위치, 값 `pyav` (오타 없음) |
| train_config.yaml 에 ANOMALIES #2·#3 + researcher 보고서 참조 주석 포함 | ✅ | L30-36: `ANOMALIES #2·#3 참조`, `docs/work_flow/context/research/m1.5_video_decode_oom.md §3` 명시 |
| run_train.py required 튜플에 `"dataset_video_backend"` 추가 | ✅ | L88-89: `"dataset_return_uint8", "prefetch_factor", "persistent_workers", "dataset_video_backend"` — 튜플 끝에 정확 삽입 |
| run_train.py cmd 리스트에 `--dataset.video_backend={train['dataset_video_backend']}` 추가 | ✅ | L121: `f"--dataset.video_backend={train['dataset_video_backend']}"` — L120 (return_uint8) 다음 라인 위치 정확 |
| 기존 cmd 라인 무변경 | ✅ | git diff 확인: L103-120 기존 라인 일체 수정 없음 |
| training_log.md 시도 3 사고 entry 추가 (L232-268) | ✅ | 실제 L232-268 구간에 "시도 3 사고 — 2026-05-16" 제목으로 entry 존재 |
| traceback 핵심 정보 포함 (`undefined symbol: torch_dtype_float4_e2m1fn_x2` + PyTorch 2.10.0+cu130) | ✅ | L241: `FFmpeg 6 wheel: undefined symbol: torch_dtype_float4_e2m1fn_x2`, L240: `PyTorch 2.10.0+cu130` |
| 후속 조치 명시 (video_backend=pyav 강제, 재시도 예정) | ✅ | L260-265: 조치 2건 (`train_config.yaml` pyav 명시, `run_train.py` required 추가) + 재시도 시도 3 양식 참조 |
| 기존 시도 1·2 entry 손상 없음 | ✅ | git diff: 기존 내용 무변경, `---` 구분선 뒤에 새 섹션만 append |
| 시도 1·2 entry 형식과 일관 (제목·메타 표·항목별 본문) | ✅ | 제목 `## 시도 3 사고 — ...`, 환경 표, 원인 분석, 후속 조치 구조 일관 |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `run_train.py:102` — `b = lambda x: str(x).lower()` | ruff E731 위반 (pre-existing, 이번 변경 아님). 별도 `def b(x): return str(x).lower()` 로 교체 권장. 이번 TODO 범위 밖이므로 Recommended 처리. |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경. `.claude/` 미변경. |
| B (자동 재시도 X 영역) | ✅ | `orin/lerobot/`, `orin/pyproject.toml`, `setup_env.sh`, `deploy_*.sh`, `.gitignore` 미변경. 변경 대상은 `dgx/finetune/` 하위로 Category B 외 영역. |
| Coupled File Rules | ✅ | pyproject.toml 변경 없음. orin/lerobot/ 변경 없음. dgx/scripts/ 변경 없음. Coupled file 규칙 해당 없음. |
| Category D 명령 | ✅ | 스크립트 변경 없음. 해당 없음. |
| 옛 룰 (docs/storage/ bash 예시) | ✅ | docs/storage/ 미변경. |

---

## 라인 번호 정합성 검증

| 항목 | 보고 라인 | 실제 라인 | 일치 |
|---|---|---|---|
| train_config.yaml `dataset_video_backend: pyav` | L37 | L37 | ✅ |
| train_config.yaml `dataset_return_uint8: true` (video_backend 다음) | L38 | L38 | ✅ |
| run_train.py required 튜플 끝 `"dataset_video_backend"` | L89 | L89 | ✅ |
| run_train.py cmd `--dataset.video_backend=...` | L121 | L121 | ✅ |
| training_log.md 사고 entry 시작 | L232 | L232 | ✅ |

---

## 배포 권장

**yes** — prod-test-runner 진입 권장.

Recommended 1건 (pre-existing lambda, 이번 변경과 무관) 으로 READY_TO_SHIP 기준 충족.
