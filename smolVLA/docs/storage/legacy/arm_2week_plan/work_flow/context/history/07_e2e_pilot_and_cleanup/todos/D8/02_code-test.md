# TODO-D8 — Code Test

> 작성: 2026-05-03 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈 0건. Recommended 2건.

---

## 단위 테스트 결과

```
python3 -m py_compile dgx/interactive_cli/flows/precheck.py
→ PASS (exit code 0)
```

DGX SSH import smoke (`python3 -c "from dgx.interactive_cli.flows.precheck import _get_streamable_video_devices; print('OK')"`) 는 prod-test-runner 영역 (SSH_AUTO). 정적 범위에서 py_compile PASS 로 충족.

---

## Lint · Type 결과

```
ruff check dgx/interactive_cli/flows/precheck.py
→ All checks passed!
```

mypy: 본 파일은 `docs/reference/lerobot/CLAUDE.md` 기준 strict 대상 모듈 외 범주. 적용 X.

---

## DOD 정합성

D8 는 D5+D7 후속 오케스트레이터 파생 todo (plan.md 미등재). 검증 항목은 호출 시 전달된 Part II~VIII 기준.

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| (II) lerobot pyproject.toml extras 직접 Read + deepdiff transitive 포함 확인 | ✅ | L110-114 hardware, L140 deepdiff-dep, L145 feetech — 직접 인용 확인 |
| (II) setup_train_env.sh 변경 불필요 사유 명시 | ✅ | 01_implementation.md + 04_dgx_lerobot_diff.md 양쪽에 명시 |
| (III) `_get_streamable_video_devices` 신규 구현 | ✅ | precheck.py L469-509 존재 확인 |
| (III) `_run_find_cameras_split` baseline·baseline_restored 가 _get_streamable_video_devices() 사용 | ✅ | L762: baseline = set(_get_streamable_video_devices()), L861: baseline_restored = set(_get_streamable_video_devices()) |
| (III) after_disconnect 은 _get_video_devices() 유지 | ✅ | L794, L882 — 전체 glob 유지 (비교 정합) |
| (III) _get_video_devices() backward-compat 보존 | ✅ | L450-466 변경 없음 |
| (IV) _show_frame ssh-file VSCode remote-ssh 안내 + code -r 명시 | ✅ | L679-681 |
| (IV) xdg-open poll() 결과 명시 보고 | ✅ | L696-706 — rc=None/0/기타 분기 명시 |
| (IV) X11 fallback 안내에 libgtk2 원인 후보 추가 | ✅ | L665-667 |
| py_compile PASS | ✅ | 검증 완료 |
| ruff check PASS | ✅ | 검증 완료 |
| `04_dgx_lerobot_diff.md` D8 항목 추가 | ✅ | [2026-05-04] 항목 존재 확인 (Part II 현황 + III·IV 변경 내용) |
| BACKLOG #5·#6 신규 추가 | ✅ | 07 섹션 #5 (cv2 스캔 비용), #6 (extras 누락 패턴) 존재 확인 |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | deepdiff 9.0.0 즉석 install (D5 walkthrough 임시 조치) | 현 운영 환경의 deepdiff 9.0.0 은 lerobot pyproject.toml 의 `<9.0.0` 제약 위반. lerobot 실사용 API (DeepDiff() 기본 생성자, exclude_regex_paths 키워드, truthiness 비교) 는 9.x 에서 안정하여 기능 파손 없음 — 단, 새 venv 재설치 시 pip 가 8.x 로 다운그레이드하여 자동 해소됨. 현 환경은 임시 상태. BACKLOG #3 (§3-c 정리) 처리 시 함께 확인 권장. |
| 2 | `_run_find_cameras_split` docstring L724-725 주석 불일치 | docstring 에 "baseline = set(_get_video_devices())" 라는 예전 패턴이 주석으로 남아 있음 (D8 변경 후 실제 코드는 _get_streamable_video_devices() 사용). L724-725: "baseline = set(_get_video_devices())  ← wrist + overview 모두 연결 상태" — 실제 함수명 불일치. 기능 영향 X, 문서 다듬기 권장. |

Recommended 2건 → READY_TO_SHIP.

---

## Part II — lerobot pyproject.toml 직접 인용 검증

`docs/reference/lerobot/pyproject.toml` 직접 Read 결과:

```toml
# line 110-114
hardware = [
    "lerobot[pynput-dep]",
    "lerobot[pyserial-dep]",
    "lerobot[deepdiff-dep]",
]
# line 140
deepdiff-dep = ["deepdiff>=7.0.1,<9.0.0"]
# line 145
feetech = ["feetech-servo-sdk>=1.0.0,<2.0.0", "lerobot[pyserial-dep]", "lerobot[deepdiff-dep]"]
```

01_implementation.md 인용과 일치. `hardware` 와 `feetech` 가 각각 `lerobot[deepdiff-dep]` 을 포함하므로, `setup_train_env.sh` §3 의 `[smolvla,training,hardware,feetech]` extras 로 deepdiff 가 transitive 설치됨. **setup_train_env.sh 변경 불필요 결정은 정확.**

### deepdiff 9.0.0 vs <9.0.0 호환성 평가

lerobot 코드의 deepdiff 사용 위치:
- `motors/motors_bus.py` L394: `DeepDiff(dict1, dict2)` — 기본 생성자
- `common/control_utils.py` L238: `DeepDiff(v1, v2, exclude_regex_paths=[regex])` — exclude_regex_paths 키워드

두 패턴 모두 deepdiff 7.x ~ 9.x 공통 안정 API. 9.0 changelog 상 Delta class 내부 변경이 있으나 lerobot 은 DeepDiff 생성자와 결과 truthiness 비교만 사용 — 파손 위험 없음.

**결론**: D5 walkthrough 즉석 install 한 deepdiff 9.0.0 은 임시 환경 상태이며, lerobot 기능 파손 없음. 새 venv 재설치 시 pip 가 `<9.0.0` 제약에 따라 8.x 자동 설치하여 영구 해소. Recommended #1 로 분류 (Critical 아님).

---

## Part III — `_get_streamable_video_devices` 정합 검증

- **cv2.VideoCapture 시도 + isOpened + read 성공 device 만 반환**: L499-508 확인 — 정합.
- **cv2 ImportError fallback**: L492-496 — cv2 미설치 시 전체 목록 반환 (필터링 불가 fallback). 정합.
- **BLE001 noqa**: L507 `except Exception:  # noqa: BLE001` — ruff BLE001 (Blind exception) 규칙을 의도적으로 억제. device open 실패는 모든 예외 포괄이 타당 (Permission, IOError 등). 적절.
- **baseline·baseline_restored 통합**: `_run_find_cameras_split` L762, L861 에서 _get_streamable_video_devices() 호출 확인. 분리 후 after 상태(L794, L882)는 _get_video_devices() 유지 — 비교 정합 보존.
- **시간 비용**: 주석 L482-483 에 "device 수 × ~1초" 명시. BACKLOG #5 로 추적 중. 수용 가능.

---

## Part IV — `_show_frame` ssh-file 안내 강화 검증

- **VSCode remote-ssh Explorer 안내**: L679 "좌측 Explorer 에서 아래 파일 클릭 → 자동 미리보기" — 존재 확인.
- **code -r 명령**: L680 `code -r {saved}` — 존재 확인.
- **xdg-open poll() 보고**: L696-706 — rc=None(실행 중), rc=0(성공), else(실패) 3분기 명시 보고.
- **X11 fallback libgtk2 안내**: L665-667 — "2) libgtk2 미설치" 원인 후보 추가 확인.

---

## Part V — 정적 검증 + 회귀

| 검증 | 결과 |
|---|---|
| py_compile | PASS |
| ruff check | PASS |
| _get_video_devices() 보존 | L450-466 변경 없음 — backward-compat 확인 |
| D6·D7 함수 보존 (`_run_find_cameras_split`, `_run_find_port_self`, `detect_display_mode` 등) | 변경 없음 확인 |

---

## Part VI — Coupled File Rule 검증

| 체크 | 결과 |
|---|---|
| `dgx/lerobot/` 변경 | 미존재 유지 — 옵션 B 원칙 준수 |
| `dgx/pyproject.toml` 변경 | 변경 없음 |
| `04_dgx_lerobot_diff.md` D8 항목 추가 | ✅ [2026-05-04] 항목 추가 확인 (Part II/III/IV 기술) |
| `setup_train_env.sh` 변경 | 변경 없음 (Category B 미터치) |

Coupled File Rules 준수 — lerobot-upstream-check 스킬 위반 없음.

---

## Part VII — BACKLOG 신규 항목 적정성

BACKLOG.md 07_e2e_pilot_and_cleanup 섹션:
- **#5** (L147): `_get_streamable_video_devices` cv2 스캔 비용 — 낮음 (08 트리거 시 중간). 적절.
- **#6** (L148): lerobot extras 누락 패턴 3회 반복 — 낮음, reflection 후보. 적절.

우선순위·내용 모두 D8 task-executor 분석과 일치. 적정.

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경. `.claude/` 미변경 |
| B (자동 재시도 X) | ✅ | `setup_train_env.sh` 변경 없음. `dgx/lerobot/` 미존재 유지. `.gitignore` 미변경 |
| Coupled File Rules | ✅ | `dgx/lerobot/` 미변경 → `04_dgx_lerobot_diff.md` 미변경도 정합. 단, `setup_train_env.sh` 변경 X 결정에 대해 `04_dgx_lerobot_diff.md` 에 현황 기록 추가 — 룰 이상 없음 |
| 옛 룰 (`docs/storage/` bash 예시) | ✅ | `04_dgx_lerobot_diff.md` 는 내용 추가이나 bash 명령 예시 추가 아님 — 위반 없음 |

---

## 배포 권장

**READY_TO_SHIP** — prod-test-runner 진입 권장.

정적 검증(py_compile + ruff) PASS. DOD 전 항목 충족. Coupled File Rules 준수. Critical 이슈 0건, Recommended 2건 (deepdiff 9.0.0 임시 환경 상태 + docstring 주석 불일치 — 기능 영향 없음).
