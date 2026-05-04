# TODO-D13 — Code Test

> 작성: 2026-05-03 15:00 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈 0건. Recommended 2건.

---

## 단위 테스트 결과

```
python3 -m py_compile dgx/interactive_cli/flows/precheck.py
→ PASS

python3 -m py_compile scripts/deploy_dgx.sh
→ 해당 없음 (bash 파일)

bash -n scripts/deploy_dgx.sh
→ PASS
```

정적 import 체인 (`precheck.py` 내 `_load_json_or_default`, `_save_json`, `_get_streamable_video_devices`, `_CAMERAS_DEFAULT`, `_PORTS_DEFAULT`) 모두 동일 파일 내 기정의 확인 완료.

---

## Lint·Type 결과

```
ruff check dgx/interactive_cli/flows/precheck.py
→ All checks passed!

bash -n scripts/deploy_dgx.sh
→ PASS
```

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. precheck 옵션 2 cameras.json null 검출 (`_load_json_or_default` 패턴) | ✅ | L1181: `_load_json_or_default(cameras_path, _CAMERAS_DEFAULT)` — D9 패턴 동일 |
| 2. wrist_left.index + overview.index 둘 다 null 여부 검사 | ✅ | L1185: `if wrist_idx_opt2 is None or overview_idx_opt2 is None` |
| 3. null 시 `_get_streamable_video_devices()` 호출 | ✅ | L1187: D8 자산 재사용 — 신규 자산 없음 |
| 4. streamable >= 2 → cameras.json 자동 갱신 + 사용자 정합 확인 권고 | ✅ | L1188~1199: `_save_json(cameras_path, new_cameras)` + "정합 확인 필요" 권고 안내 출력 |
| 5. streamable < 2 → hardcoded fallback 경고 | ✅ | L1201~1203: `streamable device 부족 (N 개) — record 가 hardcoded fallback 사용` |
| 6. ports.json null 시 안내 + 옵션 1 권장 (자동 fallback 없음) | ✅ | L1208~1211: `ports_data_opt2` null 검사 + 안내 출력 |
| 7. deploy_dgx.sh L27 `--exclude 'interactive_cli/configs/*.json'` 추가 | ✅ | 확인 완료. rsync source `dgx/` 기준 상대 경로 정확 |
| 8. 기존 rsync 옵션 (`-avz --delete`) 보존 | ✅ | L21~28 전체 옵션 보존 |
| 9. bash -n PASS | ✅ | 실행 확인 |
| 10. BACKLOG 07 #15 완료 마킹 | ✅ | "완료 (07 D13 Part B, 2026-05-03)" 형식 일관 |
| 11. cameras.json 자동 갱신 형식이 D6/D7 + D12 `_load_configs_for_record` 정합 | ✅ | `{"wrist_left": {"index": str_path}, "overview": {"index": str_path}}` — record.py 주석 L132 기대 형식과 일치 |
| 12. _save_json 실패 시 예외 처리 | ✅ | L1198~1199: `else` 분기로 실패 안내 출력 |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| R1 | `dgx/interactive_cli/configs/cameras.json` (현재 null 초기값 상태) + deploy_dgx.sh exclude 주석 | 신규 DGX 환경 셋업 시 exclude 로 인해 devPC 측 placeholder cameras.json·ports.json 이 배포되지 않으므로, DGX 측 파일을 처음부터 직접 생성하거나 옵션 1 을 먼저 거쳐야 한다는 점이 스크립트 주석 또는 문서에 명시되면 운영 혼선을 줄일 수 있음. 현재 implementation.md 에 언급됐으나 deploy_dgx.sh 주석에 1줄 추가 권장 (예: `# configs/*.json 은 DGX 측 검출 결과 보호 — 신규 환경은 옵션 1 으로 초기 생성`). |
| R2 | `precheck.py:1185` — `or` 조건 (둘 중 하나라도 null 이면 fallback 시도) | 현재 구현 (`wrist_idx is None or overview_idx is None`) 은 방어적으로 올바름. 단 wrist 만 null 이고 overview 는 이미 설정된 경우 overview 값을 버리고 전체를 재갱신하게 되는 부작용이 있음. 운영상 예외적 케이스이나 향후 cameras.json 부분 설정 시나리오가 생기면 항목별 개별 갱신 패턴 검토 가치 있음. 현재 cameras.json 은 항상 초기 placeholder 또는 완전 설정 상태이므로 실용적 영향 없음. |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경. `.claude/` 미변경. `docs/reference/` 하위 어떤 파일도 수정 없음 |
| B (자동 재시도 X) | ✅ | `scripts/deploy_dgx.sh` 변경 — Category B 해당. 단 사용자 동의 d 옵션 수령 확인 (log.md L166 "Category B 사용자 동의 d 옵션"). MAJOR 시에도 자동 재시도 X 게이트 대상이나 Critical 0건으로 해당 게이트 미진입 |
| Coupled File Rules | ✅ | `deploy_dgx.sh` 변경은 `pyproject.toml`·`setup_env.sh` Coupled Rule 무관. `orin/lerobot/`·`dgx/lerobot/` 미변경 — 03·04 diff 파일 갱신 불요 |
| D (절대 금지 명령) | ✅ | 해당 명령 없음 |
| 옵션 B 원칙 | ✅ | `orin/lerobot/`·`dgx/lerobot/` 미변경 |

---

## 논리적 결함 검사

- **cameras_path / ports_path 스코프**: `teleop_precheck()` 함수 L1084~1085 에서 정의, `elif raw == "2"` 분기 (L1175~) 에서 동일 스코프 내 사용 — 정상.
- **_CAMERAS_DEFAULT 키 일관성**: `_CAMERAS_DEFAULT` (L92~95) 의 `wrist_left`·`overview` 키와 옵션 2 분기의 `.get("wrist_left", {}).get("index")` (L1182~1183) 완전 일치.
- **자동 갱신 형식**: `new_cameras = {"wrist_left": {"index": streamable[0]}, "overview": {"index": streamable[1]}}` 에서 `streamable[N]` 은 `_get_streamable_video_devices()` 반환 `list[str]` 요소 (`/dev/videoN` 경로). `record.py` `_load_configs_for_record` 주석 (L132) 의 기대 형식 `{"wrist_left": {"index": "/dev/video0"}, ...}` 와 정합.
- **D12 회귀**: `_load_configs_for_record` 는 `record.py` 의 별도 함수로, `precheck.py` 변경과 충돌 없음. `mode.py` `_run_collect_flow` → `flow6_record(configs_dir=)` 경로도 미영향.
- **도달 불가능 코드**: 없음. `streamable >= 2` 분기와 `else` (부족 분기) 논리 완전.
- **보안 결함**: 없음. 파일 경로는 `_get_configs_dir` 경유로 고정 경로.

---

## 배포 권장

READY_TO_SHIP — prod-test-runner 진입 권장.

Part A (precheck.py): prod-test 에서 cameras.json null 상태 옵션 2 선택 → streamable 감지 후 자동 갱신 시뮬 + cameras.json 이미 설정된 상태 선택 → 갱신 없이 즉시 "다음 흐름:" 출력 확인 권장.

Part B (deploy_dgx.sh): `rsync --dry-run --exclude 'interactive_cli/configs/*.json' dgx/ /tmp/test/` 으로 configs/*.json 제외 확인 가능.
