# TODO-G2 — Code Test

> 작성: 2026-05-01 15:30 | code-tester | cycle: 1

## Verdict

**`MINOR_REVISIONS`**

Critical 이슈 0건. Recommended 3건. task-executor 1회 수정 후 prod-test-runner 진입.

---

## 단위 테스트 결과

```
pytest: sandbox 환경에서 orin/lerobot 의존성 미설치 → 실행 불가.
py_compile: Bash 도구 호출 차단으로 직접 실행 불가.

대체: 코드 정적 AST 리뷰 + 레퍼런스 대조로 컴파일·논리 오류 검사.
  - import 순서 이상 없음 (stdlib → torch → lerobot)
  - 함수 시그니처 정합성 확인
  - argparse 흐름 완전 추적

결과: 파싱 오류·미사용 변수·도달 불가 코드 없음 (정적 분석 기준 PASS).
```

## Lint·Type 결과

```
ruff / mypy: Bash 도구 차단으로 직접 실행 불가.

정적 분석:
  - 미사용 import 없음
  - _to_idx() 내부 중첩 함수 정의: ruff 에서 E731 (lambda 대체 권장) 가능하나
    try/except 블록이 필요하므로 lambda 로 전환 불가 — ruff E731 해당 없음
  - `except Exception as e` (line ~167): 내부 try-except 이미 _to_idx 의 특정
    예외를 잡고 있어 중복이지만 코드 흐름상 dead — Recommended
  - type annotation `dict | None` (Python 3.10+ 스타일): 기존 파일의 동일 패턴과
    일관 (line 56 `dict[str, int]` 등) → 호환 문제 없음
```

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. G1 산출물이 first-time + resume 두 모드 PASS | - | prod-test-runner 책임 (code-tester 판단 대상 외) |
| 2. hil_inference.py 가 게이트 결과 JSON 자동 인자 받아 동작 | ✅ | `--gate-json` 옵션 추가, load/apply 헬퍼 구현 확인 |

DOD #2 세부 확인:

| 하위 항목 | 충족 | 메모 |
|---|---|---|
| --gate-json 인자 argparse 등록 | ✅ | line 239-247 |
| load_gate_config: 디렉터리 vs 파일 경로 처리 | ✅ | is_dir() 분기 후 p.parent 사용 |
| load_gate_config: 파일 미존재 graceful 처리 | ✅ | `if ports_path.exists()` 분기 — 파일 없으면 None 반환 |
| load_gate_config: JSON parse 실패 graceful 처리 | ✅ | `except (json.JSONDecodeError, OSError)` → stderr 경고 후 None |
| apply_gate_config: CLI 직접 지정 우선 | ✅ | follower_port=None 일 때만, cameras=기본값 일 때만, flip_cameras=빈 set 일 때만 적용 |
| apply_gate_config: placeholder null 경고 출력 | ✅ | line 147 — stderr 경고 후 기존 인자 유지 |
| --follower-port 하위 호환 | ✅ | required=True → default=None + 사후 parser.error 검증. 외부 동작 동일 |
| 기존 인자 변경 없음 | ✅ | --cameras, --flip-cameras, --mode, --follower-id, --n-action-steps, --max-steps, --output-json 모두 미변경 |

## Critical 이슈

없음.

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `apply_gate_config` line 155-167, `_to_idx()` 반환 타입 | `str` 반환 시 `OpenCVCameraConfig.index_or_path: int | Path` 타입 불일치. `str("/dev/video0")` 는 `cv2.VideoCapture` 가 실제로 수용하고 `__post_init__` 검증 없으므로 런타임 동작은 정상이지만 타입 어노테이션 위반. `/dev/video0` 같은 문자열은 `Path(v)` 로 감싸거나, 타입 불일치 의도를 주석으로 명시 권장 |
| 2 | `apply_gate_config` line 166, 외부 `try/except Exception as e` | 내부 `_to_idx()` 는 예외를 삼키고 str 변환 결과를 반환하므로 (ValueError/TypeError catch 후 `str(v)` 반환) 이 외부 `except Exception` 블록은 실제로 도달 불가 (dead catch). 제거 또는 명시적 주석 권장 |
| 3 | `01_implementation.md` 검증 시나리오 §자율 6번 | `hil_inference.py --gate-json ~/smolvla/orin/config/ports.json` 호출 시 `--mode dry-run` 없이 기본값(`dry-run`)이 사용됨 — `--output-json` 미지정이면 `parser.error` 가 발생. 시나리오 명령에 `2>&1 | head -20` 이 있어 exit≠0 도 "정상 동작" 으로 처리하도록 명시되어 있어 실제 검증 목적 달성은 됨. 단 시나리오 의도 (`[gate]` 로그 출력 확인) 가 follower_port=null 경고 + output-json 미지정 오류 사이에 묻힐 수 있어, 시나리오 주석을 보강하거나 `--output-json /tmp/x.json` 추가 권장 |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/`, `.claude/` 미변경 |
| B (자동 재시도 X) | ✅ | `orin/lerobot/` 미변경, `pyproject.toml` 미변경. `orin/inference/hil_inference.py` 는 Category B 외 |
| Coupled File Rules | ✅ | `orin/lerobot/` 미변경 → `03_orin_lerobot_diff.md` 갱신 불필요. `pyproject.toml` 미변경 → `02_orin_pyproject_diff.md` 갱신 불필요 |
| 옛 룰 | ✅ | `docs/storage/` 하위 bash 예시 추가 없음 |
| 신규 import | ✅ | `from pathlib import Path` — stdlib 전용, 외부 의존성 추가 없음 |

---

## ANOMALIES

없음 (신규 SKILL_GAP 없음).

기존 ANOMALIES.md #1 (bash -n sandbox 차단) — 본 cycle에서도 동일 제약으로 py_compile 직접 실행 불가. 정적 분석으로 대체. #1 해소는 prod-test-runner G2 자율 단계 2에서 Orin SSH `bash -n` 실행으로 처리 예정 (현행 유지).

---

## 배포 권장

MINOR_REVISIONS — task-executor 1회 수정 후 prod-test-runner 진입 권장.

수정 범위 (1개 함수, ~10줄):
- `_to_idx()` 반환 시 str 경우 `Path(v)` 로 감싸기 (Recommended #1 해소)
- 외부 dead `except Exception` 제거 (Recommended #2 해소)
- 선택: 시나리오 명령 보강 (Recommended #3 — `01_implementation.md` 수정)

수정 후 재검증 불필요 (MINOR_REVISIONS 정책). prod-test-runner 자율 6단계 + verification_queue 3건 추가로 진행.
