# TODO-D12 — Code Test

> 작성: 2026-05-03 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈 0건. Recommended 개선 사항 2건.

---

## 단위 테스트 결과

```
=== _validate_camera_indices (4케이스) ===
  [OK] int 정상 (0, 1):          ok=True
  [OK] int 음수 (-1, 0):         ok=False, wrist_left=-1 (int 인덱스는 0 이상이어야 함)
  [OK] str 정상 (/dev/video0, /dev/video2): ok=True
  [OK] str /dev/ 미시작 (video0, /dev/video2): ok=False, wrist_left='video0' (str 경로는 /dev/ 로 시작해야 함)

=== _load_configs_for_record ===
  [OK] 미존재 경로 → ({}, {}) — 예외 없음
  [OK] 정상 JSON 로드 → cameras_data={'wrist_left': {'index': '/dev/video0'}, 'overview': {'index': '/dev/video2'}}
                         ports_data={'follower_port': '/dev/ttyACM1', 'leader_port': '/dev/ttyACM0'}
  [OK] JSONDecodeError → ({}, {}) + 경고 출력, 예외 미전파
  [OK] index=null → None is not None 분기 → hardcoded fallback 유지 (정상)

=== build_record_args 기존 호환 ===
  [OK] follower_port 기본값 '/dev/ttyACM1' == FOLLOWER_PORT
  [OK] leader_port  기본값 '/dev/ttyACM0' == LEADER_PORT
  [OK] 기존 호출 (follower_port/leader_port 생략) → 하드코딩 상수 유지

=== build_record_args str 경로 전달 ===
  [OK] index_or_path: /dev/video0 — 따옴표 없이 cameras_str 에 삽입 (draccus YAML 파서 수용 형식)

=== flow6_record 시그니처 ===
  [OK] configs_dir 기본값 None — 기존 호출 호환

=== mode.py ===
  [OK] _run_collect_flow: configs_dir = script_dir / "configs" 계산 후 flow6_record(configs_dir=...) 전달
  [OK] flow7_select_transfer 호출 위치 변경 없음 (D12 변경 외 로직 보존)
```

---

## Lint·Type 결과

```
$ python3 -m py_compile dgx/interactive_cli/flows/record.py
PASS

$ python3 -m py_compile dgx/interactive_cli/flows/mode.py
PASS

$ ruff check dgx/interactive_cli/flows/record.py dgx/interactive_cli/flows/mode.py
All checks passed!
```

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. record.py 가 cameras.json + ports.json 로드 + hardcoded fallback | ✅ | `_load_configs_for_record` 신설. configs_dir=None 시 기존 동작 완전 동일 확인 |
| 2. 사용자 안내 출력 (config source 명시) | ✅ | flow6_record 헤더 직후 cameras/ports 출처 출력. 미설정 항목 있으면 v4l2 메타 device 차단 경고 출력 |
| 3. BACKLOG 07 #15 신규 추가 | ✅ | deploy_dgx.sh 가 configs/ 덮어쓰는 문제 — 우선순위 중간, 미완 상태로 정상 등록 |
| 4. py_compile + ruff PASS | ✅ | 위 결과 참조 |
| 5. 사용자 walkthrough 재시도 시 cameras.json 검출 결과 사용 | — | PHYS_REQUIRED — 사용자 검증 위임 (prod-test 단계 이관) |
| BACKLOG 07 #4 완료 마킹 | ✅ | 완료 (D12, 2026-05-03) 마킹 + 요약 정확 |
| D9 패턴 동일 구조 | ✅ | precheck.py L979~1001 와 동일한 `json.load` + `JSONDecodeError|OSError` fallback 패턴 |
| cameras.json·ports.json 키 정합 (D6/D7 구조) | ✅ | wrist_left.index / overview.index (precheck.py L947~950 확인), follower_port / leader_port (precheck.py _run_find_port_self 확인) |
| lerobot OpenCVCamera 레퍼런스 인용 정확 | ✅ | `configuration_opencv.py` L61: `index_or_path: int \| Path` 직접 Read 확인. `camera_opencv.py` L158: `cv2.VideoCapture(self.index_or_path, ...)` 직접 Read 확인 |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| R1 | `record.py` L444~449 (`cameras_source` 업데이트 로직) | `cameras_source` 가 단일 문자열 변수로 wrist+overview 양쪽을 대표. overview 만 있고 wrist 가 None 인 부분 로드 케이스에서 출력이 "cameras.json 검출 결과" 로 표시되지만 wrist 는 hardcoded 0. D6/D7 모두 두 키를 항상 함께 저장하므로 실질 영향은 낮음 (엣지 케이스). 향후 per-camera source 변수로 분리하면 더 정확한 출력 가능 |
| R2 | `record.py` L481~485 (경고 출력 이모지) | `"  ⚠ 미설정 항목..."` — 이모지 사용. 일부 터미널 환경에서 깨질 수 있음. `"  [경고]"` 같은 ASCII 접두사로 대체 권장 |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경, `.claude/` 미변경 확인 |
| B (자동 재시도 X) | ✅ | `dgx/interactive_cli/flows/` 는 Category B 외 영역. `orin/lerobot/`, `dgx/lerobot/`, `pyproject.toml`, `deploy_*.sh`, `.gitignore` 미변경 |
| Coupled File Rules | ✅ | Category B 영역 미변경 — Coupled File 갱신 불요 |
| 옛 룰 (docs/storage/ bash 예시) | ✅ | BACKLOG.md 수정만 — bash 예시 미추가 |

---

## 배포 권장

READY_TO_SHIP — prod-test-runner 진입 권장.

prod-test 검증 포인트:
- `python3 -m py_compile` + ruff 이미 PASS (LOCAL_AUTO 완료)
- `import flows.record; import flows.mode` smoke import PASS
- DOD 5번 (cameras.json 실물 사용) 은 PHYS_REQUIRED — Phase 3 사용자 검증 위임
