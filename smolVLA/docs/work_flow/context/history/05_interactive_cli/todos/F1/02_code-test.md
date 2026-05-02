# TODO-F1 — Code Test

> 작성: 2026-05-01 18:45 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈 0건. Recommended 2건.

---

## 단위 테스트 결과

```
테스트 없음 (F1 타입: study — spec DOD "테스트: 없음" 명시)
```

코드 스니펫 AST 파싱 (정적 검증):

```
entry.py (§3 코드블록 추출 후 ast.parse):  OK
§5 orin env_check.py 예시 (ast.parse):      OK
```

---

## Lint·Type 결과

```
bash -n 검사 (3개 bash 블록 추출):
  Block 1: OK  [경로 상수 인라인 스니펫]
  Block 2: OK  [source "$VENV_ACTIVATE" 패턴 스니펫]
  Block 3: OK  [main.sh 완성 코드 전체]

ruff / mypy: study 산출물 (docs/storage/*.md 내 코드 스니펫) — 실 파일 미존재.
  F2 task 가 실 파일 생성 후 검사 대상.
```

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. 3 노드 동일 복사 가능한 main.sh boilerplate 작성 | ✅ | §2 완성 코드 (87 라인), 노드별 변경점 주석 명시 |
| 2. flows/entry.py boilerplate 작성 | ✅ | §3 완성 코드 (239 라인), 실행 가능 상태 |
| 3. flow 0 — 환경 확인 단계 완성 | ✅ | `flow0_confirm_environment()` — datacollector 전용 Y/n, orin/dgx 즉시 통과 |
| 4. flow 0 — datacollector "이 환경 맞나요?" 분기 | ✅ | N 응답 시 `NODE_GUIDE` 전 노드 안내 + exit 0 |
| 5. flow 1 — 장치 선택 메뉴 완성 | ✅ | `flow1_select_node()` — 본 노드 [*] active, 타 노드 안내 + 재선택 루프 |
| 6. flow 1 — 본 노드만 active, 다른 노드는 안내만 | ✅ | `chosen_node != current_node` 분기 → `NODE_GUIDE` 출력 + 루프 계속 |
| 7. 04 G1 check_hardware.sh bash·python 혼합 패턴 미러 | ✅ | main.sh 가 heredoc 대신 `exec python3 ...` 호출 (단순화 적절). 설계 근거에 패턴 인용 명시 |
| 8. §1 디렉터리 구조 정의 | ✅ | 3 노드 형제 구조, F1 범위 파일 명시 |
| 9. §2 진입점 main.sh 패턴 | ✅ | venv activate + cusparseLt 패치(orin) + python3 호출 |
| 10. §3 flow 0 entry.py 코드 | ✅ | 완성 코드 포함 |
| 11. §4 flow 1 장치 선택 메뉴 동작 정리 | ✅ | 표 + 재선택 루프 명시 |
| 12. §5 노드별 차이점 정의 | ✅ | flow 2+ 분기점 표 + 후행 todo 연결 |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `docs/storage/12_interactive_cli_framework.md` §5, line 519~523 | `run_env_check()` 예시 코드가 `check_hardware.sh` 에 `--gate-json` 인자를 전달하는데, 실제 `check_hardware.sh` 는 `--gate-json` 을 지원하지 않는다. 후행 F2/O2 참고용 스니펫으로 명시되어 있으나, 그대로 복사하면 실행 오류가 발생한다. 주석 또는 TODO 로 "check_hardware.sh 는 --gate-json 미지원 — O2 구현 시 --mode 인자만 사용" 을 명시 권장. |
| 2 | `docs/storage/12_interactive_cli_framework.md` §2, line 66 | 설계 근거에서 cusparseLt 패치를 "line 162~168 패턴"으로 인용했으나, main.sh 코드 내 주석은 "line 164~168 패턴"으로 표기가 불일치한다. 실제 코드는 line 162 (source) + line 164~168 (cusparseLt 블록). 경미한 표기 불일치로 기능 영향 없음. |

---

## 레퍼런스 인용 확인

| 레퍼런스 | 인용 라인 | 실제 확인 | 결과 |
|---|---|---|---|
| `orin/tests/check_hardware.sh` line 41~49 (경로 상수 블록) | §2 설계 근거 | SCRIPT_DIR·VENV_ACTIVATE·CUSPARSELT_PATH 상수 — 실제 line 41~49 정확 일치 | ✅ |
| `orin/tests/check_hardware.sh` line 152~172 (step_venv) | §2 설계 근거, 설계 결정표 | `step_venv()` 함수 — 실제 line 152~172 정확 일치 | ✅ |
| `orin/tests/check_hardware.sh` line 164~168 (cusparseLt 패치) | main.sh 코드 주석, 설계 결정표 | cusparseLt `if [[ -d ... ]]` 블록 — 실제 line 164~168 정확 일치 | ✅ |
| `orin/tests/check_hardware.sh` line 185~203 (python3 heredoc) | §2 설계 근거 | `cuda_out=$(python3 - <<'PYEOF' ... PYEOF)` — 실제 line 185~203 정확 일치 | ✅ |
| `orin/tests/check_hardware.sh` line 226~244 (python3 heredoc) | §2 설계 근거 | `port_out=$(python3 - <<'PYEOF' ... PYEOF)` — 실제 line 226~244 정확 일치 | ✅ |
| `orin/tests/check_hardware.sh` line 128~144 (record_step) | entry.py 독스트링 | 환경변수 경유 특수문자 처리 패턴 — 실제 line 128~144 정확 일치 | ✅ |
| `orin/inference/hil_inference.py` line 80~120 (load_gate_config) | §3 설계 근거, entry.py 독스트링 | `load_gate_config()` 함수 — 실제 line 80~119 (120은 빈 줄), 내용 일치 | ✅ |
| `orin/inference/hil_inference.py` line 92~119 (path 처리 부분) | 설계 결정표 | `Path.is_dir()` 분기 + None 반환 — 실제 line 92~119 일치 | ✅ |
| `orin/inference/hil_inference.py` line 122~177 (apply_gate_config) | §3 설계 근거, 설계 결정표 | `apply_gate_config()` CLI 우선 패턴 — 실제 line 122~177 일치 | ✅ |
| `orin/inference/hil_inference.py` line 236~245 (--gate-json argparse) | 01_implementation.md 인용 | `--gate-json` argparse 정의 — 실제 line 235~245 (1 라인 offset), 내용 일치 | ✅ |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경, `.claude/agents/*.md` 미변경, `settings.json` 미변경 |
| B (자동 재시도 X 영역) | ✅ | `orin/lerobot/`, `dgx/lerobot/`, `pyproject.toml`, `setup_env.sh`, `deploy_*.sh`, `.gitignore` 미변경 |
| Coupled File Rules | ✅ | orin/lerobot/ 미변경 — 03_orin_lerobot_diff.md 갱신 불필요 |
| Category C (신규 디렉터리) | ✅ | F1 신규 파일은 `docs/storage/` 내 (허용 영역). F2 의 `orin/interactive_cli/` 등 신규 디렉터리는 plan.md line 113 "Category C 동의 이미 충족" 확인됨 |
| Category D (금지 명령) | ✅ | 금지 명령 사용 없음 |
| 옛 룰 (docs/storage/ bash 명령 예시) | ✅ | bash 코드 스니펫은 main.sh 자체 (핵심 산출물). 실행 명령 예시 추가 없음 |

---

## F2 인계 가능성 평가

F1 산출물이 F2 에 인계하기에 충분한 완성도를 갖춤:

1. **main.sh 완성 코드**: 노드별 1줄 변경 지점 (`VENV_ACTIVATE` 경로) + orin 전용 삭제 블록 (`CUSPARSELT_PATH`) 이 주석으로 명확히 표시됨. 복사 후 수정 범위가 명확.
2. **flows/entry.py 완성 코드**: `--node-config` argparse + `load_node_config()` + `flow0_confirm_environment()` + `flow1_select_node()` + `main()` 구조. 3 노드 동일 복사 가능, node.yaml 의 `node` 값만 다름.
3. **flows/__init__.py**: 1행 패키지 선언.
4. **configs/node.yaml**: 노드별 3 개 예시 (orin/dgx/datacollector) 제공.
5. **F2 복사 절차**: 01_implementation.md 에 1~5 단계 절차 명시.
6. **노드별 차이점**: cusparseLt 블록 (orin 전용 삭제), VENV_ACTIVATE 경로 (1줄), node.yaml node 값 (1 필드). 모두 명확히 분리됨.

---

## 배포 권장

READY_TO_SHIP — 즉시 후행 todo (F2) 진입 권장.

본 todo 는 study 타입이므로 prod-test-runner 진입 없음. F2 task 가 실 파일 생성 후 prod-test 에서 통합 검증.
