# TODO-G1 — Code Test

> 작성: 2026-05-01 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈 0건. Recommended 2건. 레퍼런스 활용 정확, DOD 전 항목 충족, Hard Constraints 준수.

---

## 단위 테스트 결과

```
bash -n orin/tests/check_hardware.sh: 실행 시도 → Bash 권한 차단 (sandbox 정책)
shellcheck: 미설치 확인 불가 (동일 사유)
```

ANOMALY: `SKILL_GAP` — bash -n / shellcheck 실행이 sandbox 정책으로 차단됨. 정적 문법 검증을 수동 코드 리뷰로 대체 수행 (아래 결과 참조).

**수동 문법 리뷰 결과 (bash -n 대체):**

- shebang: `#!/usr/bin/env bash` — 올바름
- `set -uo pipefail` — 올바름 (set -e 의도적 미포함, 이유 주석 명시)
- 모든 `case` 문: `esac` 종결 확인 OK (라인 69-83)
- 모든 `if/fi`, `while/done` 쌍: 수동 추적 OK
- heredoc: `<<'PYEOF' ... PYEOF` 따옴표형 (변수 확장 없음) — 라인 185/226/342 모두 올바름
- 단, 라인 108-113의 Python 초기화 인라인 `-c "..."` 내 `${MODE}`, `${TMP_RESULT_JSON}` 은 bash 문자열 확장 방식. MODE는 검증된 값(first-time/resume)이고 TMP_RESULT_JSON은 mktemp 경로(공백 없음)이므로 실제 위험 없음
- `trap 'rm -f "${TMP_RESULT_JSON}"' EXIT` — 임시 파일 정리 OK
- 함수 정의 완결성: `step_venv`, `step_cuda`, `step_soarm_port`, `step_cameras`, `finalize_output`, `main` 모두 닫힘 확인
- 변수 quoting: `"$1"`, `"$2"`, `"${PORTS_JSON}"` 등 주요 변수 대부분 인용 처리됨

**문법 오류 의심 항목 없음** (SKILL_GAP으로 최종 확정은 Orin prod 시 bash -n 재실행 권고).

---

## Lint·Type 결과

```
ruff: bash 파일 — 대상 외
mypy: bash 파일 — 대상 외
```

Python 인라인 코드 (check_hardware.sh 내 python3 -c 블록) 정적 분석:
- json, os, sys, platform, pathlib.Path 등 표준 라이브러리만 사용 — import 오류 없음
- `from lerobot.cameras.opencv import OpenCVCamera` — orin/lerobot/cameras/opencv/__init__.py 에서 OpenCVCamera export 확인 OK

YAML 파싱 가능성:
- `first_time.yaml`: 유효 YAML 구조 (key: value, 중첩 블록 정상). 파싱 가능.
- `resume.yaml`: 유효 YAML 구조. 파싱 가능.

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. --mode {first-time,resume} 인자 처리 | ✅ | 라인 69-91, 유효성 검사 + exit 2 |
| 2. --config YAML 인자 처리 | ✅ | 라인 72-73, 기본값 자동 설정 (라인 93-99) |
| 3. --quiet 인자 처리 | ✅ | 라인 74-75, QUIET=true/false 플래그 |
| 4. --output-json FILE 인자 처리 | ✅ | 라인 76-77, finalize_output에서 cp (라인 513-516) |
| 5. 점검 단계 1: venv activate | ✅ | step_venv(), source $VENV_ACTIVATE, cusparseLt LD_LIBRARY_PATH |
| 6. 점검 단계 2: CUDA 라이브러리 | ✅ | step_cuda(), torch.cuda.is_available() + tensor 연산 |
| 7. 점검 단계 3: SO-ARM 포트 발견 | ✅ | step_soarm_port(), ttyACM*/ttyUSB* glob, ports.json 갱신/비교 |
| 8. 점검 단계 4: 카메라 인덱스·flip 발견 | ✅ | step_cameras(), OpenCVCamera.find_cameras(), cameras.json 갱신/비교 |
| 9. first-time 모드: cache 갱신 | ✅ | ports.json·cameras.json 환경변수 경유 Python 작성 |
| 10. resume 모드: cache 비교 | ✅ | 포트/카메라 목록과 cache 대조, 불일치 시 FAIL |
| 11. BACKLOG 03 #14 (SSH 비대화형 cusparseLt) 해소 | ✅ | 스크립트 자체 source activate + LD_LIBRARY_PATH 설정 |
| 12. BACKLOG 03 #15 (카메라 인덱스 발견) 해소 | ✅ | OpenCVCamera.find_cameras() 호출 + cameras.json cache |
| 13. BACKLOG 03 #16 (wrist flip 확인) 해소 | ✅ | first-time 모드 사용자 프롬프트 + cameras.json wrist.flip 저장 |
| 14. BACKLOG 01 #1 (SO-ARM 포트 변동) 해소 | ✅ | 동적 ttyACM*/ttyUSB* 스캔 + ports.json cache |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `check_hardware.sh` 라인 40-41 | `ORIN_DIR` 도출에 `cd "${SCRIPT_DIR}/.."` 사용. `readlink -f`나 상위 디렉터리 직접 참조가 더 명확하나, 기능 동작에는 문제 없음 |
| 2 | `check_hardware.sh` 라인 236-237 | `find_available_ports()` 레퍼런스(upstream)는 `/dev/tty*` 전체 glob. 스크립트는 ttyACM*/ttyUSB*로 의도적으로 범위 축소. 이 결정이 01_implementation.md에 명시되어 있으나, 스크립트 내 주석에 "upstream과 의도적 차이" 표시를 추가하면 향후 유지보수 시 혼동 방지 가능 |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | docs/reference/ 미변경. .claude/agents/*.md, .claude/skills/**/*.md, .claude/settings.json 미변경 확인 |
| B (자동 재시도 X 영역) | ✅ (최소 변경) | .gitignore 변경 있음 — 코멘트 블록만 추가, 실 패턴 추가 없음. 라인 234-239 확인: orin/config/ cache 추적 정책 주석만. orin/lerobot/ 미변경. pyproject.toml 미변경 |
| Coupled File Rules | ✅ | orin/lerobot/ 미변경 → 03_orin_lerobot_diff.md 갱신 불필요. orin/pyproject.toml 미변경 → 02_orin_pyproject_diff.md 갱신 불필요 |
| 옵션 B 원칙 | ✅ | check_hardware.sh는 lerobot CLI가 아닌 Python import 경로로 OpenCVCamera를 직접 호출. orin/lerobot/ 파일 미수정 |
| Category D (금지 명령) | ✅ | rm -rf, sudo, git push --force 등 사용 없음 |
| 옛 룰 (docs/storage/ bash 예시 추가 X) | ✅ | docs/storage/ 미변경 |

---

## 레퍼런스 활용 검증

### find_available_ports() 패턴

- **레퍼런스** (`lerobot_find_port.py` 라인 41): `ports = [str(path) for path in Path("/dev").glob("tty*")]`
- **스크립트 구현** (라인 236-237): `ttyACM*` + `ttyUSB*` 만 스캔
- **판정**: 의도적 축소 (Feetech 서보 특화). 레퍼런스 기반이며 범위를 좁힌 합리적 특화. lerobot-reference-usage 위반 아님 (레퍼런스를 무시한 게 아닌, 레퍼런스 기반으로 도메인 필요에 맞게 특화한 것). 단 코드 주석에 upstream과의 차이 명시 권장 (Recommended #2).

### OpenCVCamera.find_cameras() import 경로

- **레퍼런스** (`cameras/opencv/__init__.py`): `from .camera_opencv import OpenCVCamera` / `__all__ = ["OpenCVCamera", "OpenCVCameraConfig"]`
- **orin/lerobot 경로**: `orin/lerobot/cameras/opencv/__init__.py` — 동일 구조 확인
- **스크립트** (라인 345): `from lerobot.cameras.opencv import OpenCVCamera`
- **판정**: import path 정확. orin/lerobot이 lerobot 패키지로 설치되므로 `lerobot.cameras.opencv` 경로 유효.

### find_cameras() 반환값 구조 활용

- **레퍼런스 반환**: `{"id": str|int, "name": ..., "type": ..., "backend_api": ..., "default_stream_profile": {"format": ..., "fourcc": ..., "width": ..., "height": ..., "fps": ...}}`
- **스크립트 접근** (라인 349-356): `c["id"]`, `c.get("name", "")`, `c.get("default_stream_profile", {}).get("width/height/fps")`
- **판정**: 레퍼런스 구조에 정확히 대응. Linux에서 `id`는 str("/dev/video0") 타입이며 라인 456의 `str(c['id'])` 변환도 안전함.

---

## ANOMALIES

- `SKILL_GAP`: bash -n / shellcheck 실행이 sandbox 정책으로 차단됨. 문법 검증을 수동 코드 리뷰로 대체. Orin prod 검증(TODO-G2) 시 `bash -n orin/tests/check_hardware.sh` 재실행 권고.

---

## 배포 권장

**READY_TO_SHIP** — prod-test-runner (TODO-G2) 진입 권장.

- Critical 이슈 0건
- Recommended 2건 (주석 보강 수준, 기능 영향 없음)
- DOD 14개 항목 전부 충족
- Hard Constraints (Category A/B/D) 모두 준수
- 레퍼런스 활용 정확 (import path 검증 완료, find_cameras 반환 구조 일치)
- YAML 2개 파싱 가능 확인
- JSON 출력 schema 일관 (status: "PASS"/"FAIL", detail, summary.pass/fail/exit_code)
- .gitignore 변경은 코멘트 블록만 (Category B 최소 변경 원칙 준수)
