# TODO-O4 — Code Test

> 작성: 2026-05-03 14:30 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈 0건. Recommended 이슈 2건.

---

## 단위 테스트 결과

```
$ python3 -m py_compile orin/inference/hil_inference.py && echo "py_compile PASS"
py_compile PASS
```

구문 오류 없음. torch·lerobot 미설치 환경에서도 컴파일 단계는 정상 통과.

---

## Lint·Type 결과

```
$ ruff check orin/inference/hil_inference.py
All checks passed!
```

ruff 지적 사항 없음.

mypy: 변경된 파일이 `orin/lerobot/` 영역 밖 (orin/inference/) 이므로 strict mypy 적용 대상 외. 생략.

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. argparse 또는 README 에 `lerobot-find-cameras opencv` 사전 발견 단계 명시 | ✅ | hil_inference.py L282 argparse help + L36 모듈 docstring + README.md L47–78 사전 단계 섹션 |
| 2. wrist flip 필요 시 `--flip-cameras wrist` 안내 명시 | ✅ | hil_inference.py L292 argparse help + L43–45 모듈 docstring + README.md L79–89 wrist 플립 섹션 |
| 3. 가능 시 hil_inference.py 진입 시 카메라 자동 발견 fallback 추가 | ✅ | `_auto_discover_cameras()` L137–190 신설. 우선순위 흐름: CLI --cameras > gate-json cameras.json > 자동 발견 > 기본값 top:0,wrist:1 |
| 4. 03 BACKLOG #15·#16 "완료 (07 O4, 2026-05-03)" 마킹 | ✅ | BACKLOG.md L72·L73 각각 "완료 (07 O4, 2026-05-03): ..." 형식 마킹 |

DOD 4항 모두 충족.

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| R1 | `hil_inference.py` L169–178 `_to_idx` 중첩 함수 | `_auto_discover_cameras()` 내부에서만 쓰이는 `_to_idx` 가 같은 이름의 함수가 `apply_gate_config()` 내부 (L227) 에도 별도로 정의됨. 두 함수 모두 소규모라 기능적 문제는 없으나, 모듈 수준 헬퍼로 공통화하면 유지보수성 향상 가능 |
| R2 | `hil_inference.py` L154–164 에서 `len(found) == 0` 과 `len(found) != 2` 를 따로 분기 | `len(found) == 0` 은 `len(found) != 2` 의 부분집합이므로 메시지만 다르게 출력하면 합쳐도 무방. 현행 코드는 기능 문제 없음 (별개 메시지 노출 의도적) |

Recommended 2건 — READY_TO_SHIP 기준 충족.

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경. `.claude/agents/*.md`, `.claude/skills/**/*.md`, `settings.json` 미변경 |
| B (자동 재시도 X) | ✅ | `orin/lerobot/`, `dgx/lerobot/`, `orin/pyproject.toml`, `setup_env.sh`, `deploy_*.sh`, `.gitignore` 미변경 |
| Coupled File Rules | ✅ 해당 없음 | `orin/pyproject.toml` 미변경 → setup_env.sh·02_orin_pyproject_diff.md 갱신 불필요. `orin/lerobot/` 미변경 → 03_orin_lerobot_diff.md 갱신 불필요 |
| lerobot-reference-usage | ✅ | `docs/reference/lerobot/src/lerobot/cameras/opencv/camera_opencv.py` L285–337 직접 Read 인용. `find_cameras()` 반환 형식 (`{'id': str|int, ...}`) 및 Linux `/dev/video*` glob 패턴 정확히 반영. 레퍼런스 없이 추측 작성 없음 |
| 옛 룰 (docs/storage/ bash 예시) | ✅ | `docs/storage/` 하위 bash 예시 추가 없음 |

---

## 추가 검증 — _auto_discover_cameras() 패턴 정합성

upstream `find_cameras()` 반환 형식 (L285–337 직접 확인):
- 반환: `list[dict]`, 각 항목 `{'name': str, 'type': str, 'id': str|int, 'backend_api': str, 'default_stream_profile': {...}}`
- Linux: `id` 는 `str` (`'/dev/video0'` 등), 비-Linux: `id` 는 `int`

구현 L181: `found[0]["id"]` 접근 정확. `_to_idx()` 내부에서 `int(v)` 우선 시도 → 실패 시 `re.search(r"(\d+)$", str(v))` 추출 — Linux str 경로와 비-Linux int 양쪽 처리 정확.

발견 수 == 2 조건 하에서만 자동 적용 (L158 `if len(found) != 2: return None`). 0대 및 3대 이상 graceful 처리 확인.

---

## 배포 권장

READY_TO_SHIP — prod-test-runner 진입 권장.

실 카메라 동작 검증 (`_auto_discover_cameras()` 실제 발견 + 인덱스 정합)은 PHYS_REQUIRED → verification_queue O 그룹 게이트 3 대기 (spec 합의).
