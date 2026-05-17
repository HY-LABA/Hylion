# TODO-03-E — Code Test

> 작성: 2026-05-17 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈 0건. Recommended 이슈 0건.

---

## 단위 테스트 결과

```
python3 -c "import ast; ast.parse(open('orin/lerobot/scripts/lerobot_record.py').read()); print('AST_OK')"
→ AST_OK

bash -n orin/scripts/run_inference_leftarm_v2.sh && echo "SYNTAX_OK"
→ SYNTAX_OK
```

두 파일 모두 syntax/AST 통과.

---

## Lint·Type 결과

ruff·mypy 는 devPC 환경에 orin venv 미활성화 상태이므로 자율 실행 범위 외.
AST parse (Python stdlib) 로 syntax 정합 확인 완료.

---

## DOD 정합성

TODO-03 DOD 기준 (spec §TODO-03 구현 대상 포인트로 평가):

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| F1: reachy2_camera import → try/except ImportError wrap | ✅ | `lerobot_record.py` line 83-87, 사용자 승인 옵션 A |
| F1: except 절 orin trim 주석 포함 | ✅ | "orin trim — reachy2_camera 모듈 미포함 (inference-only, SO-ARM 작업 무관)" |
| F2: set -euo pipefail 직후 LD_LIBRARY_PATH 초기화 | ✅ | line 24 `export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}"`, 설명 주석 포함 |
| F3: cmd_download 에 hf 우선 + huggingface-cli fallback | ✅ | `command -v hf` 분기 → `hf download` / `huggingface-cli download` |
| 기존 5 subcommand 모두 유지 | ✅ | download/check/dry-run/live/help 모두 dispatch 블록에 존재 |
| task instruction 문자열 일치 (collection_log.md 정본) | ✅ | TASK1="Pick up the blue and yellow doll and place it on the left side of the table", TASK2="Hand the yellow can to the person" — 정본과 일치 |
| lerobot-record 인자 구조 유지 | ✅ | --robot.type/port/cameras, --policy.path/device, --dataset.* 인자 구조 이전 산출물과 동일 |
| Coupled File Rule §3: 03_orin_lerobot_diff.md 갱신 | ✅ | [2026-05-17] 항목 신규 추가, 날짜·이유·before/after·영향범위·inference-only 여부 전부 포함 |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

없음.

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경, `.claude/` 미변경 (git diff + git status 확인) |
| B (Category B 영역 변경) | ✅ | `orin/lerobot/scripts/lerobot_record.py` 수정 — 사용자 2026-05-17 23:45 옵션 A 승인 완료. 다른 `orin/lerobot/` 영역 추가 변경 없음 |
| Coupled File Rules §3 | ✅ | `orin/lerobot/` 코드 수정 → `03_orin_lerobot_diff.md` 동시 갱신 — git diff 로 37줄 entry 확인 |
| 옛 룰 (docs/storage/ bash 예시) | ✅ | `03_orin_lerobot_diff.md` 신규 entry 는 코드 diff 기록이며, bash 명령 예시 추가 아님 |
| Category C | ✅ | 해당 없음 (새 디렉터리·외부 의존성·시스템 환경 변경 없음) |
| Category D | ✅ | deny 명령 없음 |

---

## 상세 검증 근거

### F1 — lerobot_record.py

- upstream (`docs/reference/lerobot/src/lerobot/scripts/lerobot_record.py`) line 83: `from lerobot.cameras.reachy2_camera import Reachy2CameraConfig  # noqa: F401` (plain import)
- orin 버전 line 83-87: try/except ImportError wrap — upstream 코드 흐름 보존 + Orin trim 불일치 해소. except 절에 trim 사유 주석 포함.
- `ruff: # noqa: F401` 유지됨 (try 블록 내부에서도 유효).
- 인접 카메라 import (OpenCVCameraConfig, RealSenseCameraConfig, ZMQCameraConfig) 는 orin/lerobot/cameras/ 에 해당 모듈 존재 → try/except 불필요. reachy2 만 예외 처리한 이유 명확.
- upstream 대비 변경은 line 83 영역(try/except 4줄 추가) + 기존 등록된 robots/teleoperators import trim(이전 이력) 만. F1 패치 외 신규 변경 없음 확인.

### F2 — run_inference_leftarm_v2.sh

- `set -euo pipefail` (line 20) 직후 line 24에 `export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}"` 위치 정확.
- F2 설명 주석 (line 21-23) 포함 — nounset(-u) 보호 목적 명시.
- bash -n SYNTAX_OK 확인.

### F3 — run_inference_leftarm_v2.sh

- `cmd_download` 함수 내 `command -v hf >/dev/null 2>&1` 분기 존재.
- `hf download` 우선, `huggingface-cli download` fallback — 두 경로 모두 동일 인자(`$CKPT_REPO_ID --local-dir $CKPT_LOCAL_DIR`) 사용.
- F3 설명 주석 (line 124-125) 포함.

### 03_orin_lerobot_diff.md §F1 entry

- 날짜: `[2026-05-17]` ✅
- 이유: upstream cameras/reachy2_camera 추가 vs orin trim 불일치 해소 ✅
- before/after 코드 블록 ✅
- 영향 범위 표 (lerobot-record CLI 가용성 복원, SO-ARM 추론 경로 무영향, Reachy2 카메라 orin 미지원 명시) ✅
- inference-only 트리밍 여부: yes + 사유 명시 ✅
- 형식: 기존 entry들과 동일 헤더 패턴 (`### [YYYY-MM-DD] 파일 — 사유`) ✅

---

## 배포 권장

READY_TO_SHIP — prod-test-runner 진입 권장.

prod-test-runner 가 확인할 Orin SSH 항목:
- `lerobot-record --help` — F1 패치 후 ImportError 없이 도움말 출력
- `./run_inference_leftarm_v2.sh dry-run` — F2+F3 수정 후 set -u 에러 없이 동작 + `hf`/`huggingface-cli` 경로 확인
- `./run_inference_leftarm_v2.sh download` — F3 fallback 동작 + n_action_steps 자동 점검
