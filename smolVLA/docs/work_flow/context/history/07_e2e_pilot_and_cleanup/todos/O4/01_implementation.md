# TODO-O4 — Implementation

> 작성: 2026-05-03 | task-executor | cycle: 1

## 목표

`orin/inference/hil_inference.py` 카메라 인덱스 사전 발견 + wrist flip 도구 정비 (03 BACKLOG #15·#16 처리)

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `orin/inference/hil_inference.py` | M | `--cameras` 기본값 None → 자동 발견 fallback (`_auto_discover_cameras`) 추가 + argparse help 개선 + 모듈 docstring 사전 단계 안내 추가 |
| `orin/inference/README.md` | M | 사전 단계 섹션 신설 (lerobot-find-cameras opencv + wrist flip 안내) + gate-json 예시 추가 |
| `docs/work_flow/specs/BACKLOG.md` | M | 03 BACKLOG #15·#16 "완료 (07 O4, 2026-05-03)" 마킹 |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 ✓, `orin/lerobot/` 미변경 ✓ (Category B 미해당)
- Coupled File Rule: `orin/pyproject.toml` 미변경 → setup_env.sh·02_orin_pyproject_diff.md 갱신 불필요 ✓
- `orin/lerobot/` 미변경 → `03_orin_lerobot_diff.md` 갱신 불필요 ✓
- 레퍼런스 직접 Read:
  - `docs/reference/lerobot/src/lerobot/cameras/opencv/camera_opencv.py` L285–337
    인용: `@staticmethod def find_cameras() -> list[dict[str, Any]]` — Linux: `/dev/video*` glob, 각 항목 `{'type': 'OpenCV', 'id': str|int, ...}` 반환
  - `docs/reference/lerobot/src/lerobot/scripts/lerobot_find_cameras.py` L47–64
    인용: `find_all_opencv_cameras()` → `OpenCVCamera.find_cameras()` 호출 패턴
- 적용: `_auto_discover_cameras()` 함수는 `OpenCVCamera.find_cameras()` 를 내부에서 import 하여 동일 패턴으로 카메라 발견. 변경 사항: 발견 수 == 2 제약 추가 (2 대 외 자동 적용 불가 — 수동 지정 유도).

## 변경 내용 요약

**hil_inference.py 변경**:

1. `--cameras` argparse 기본값을 `parse_camera_arg("top:0,wrist:1")` 에서 `None` 으로 변경. 이로써 "사용자가 명시 지정하지 않은 상태"와 "기본값과 우연히 일치한 상태"를 구별 가능해졌다.

2. `_auto_discover_cameras()` 함수 신설 — `OpenCVCamera.find_cameras()` 를 호출하여 연결된 카메라를 스캔. 정확히 2 대 발견 시 `{"top": idx0, "wrist": idx1}` 반환. 0 대 또는 3 대 이상이면 `None` 반환 + 오류 메시지 출력. Linux 에서 반환되는 `/dev/videoN` 문자열은 끝 숫자(`re` 추출)로 int 변환.

3. `main()` 내 우선순위 흐름 (gate-json 처리 후):
   - `args.cameras is None` → `_auto_discover_cameras()` 시도
   - 여전히 `None` → 경고 출력 + 기본값 `top:0,wrist:1` 적용

4. `apply_gate_config()` 의 카메라 비교 조건 `args.cameras == default_cameras` → `args.cameras is None` 으로 단순화 (일관성 향상).

5. 모듈 docstring에 "카메라 인덱스 사전 발견" + "wrist 카메라 플립" 섹션 추가 (03 BACKLOG #15·#16 참조 명시).

**README.md 변경**:

"사전 단계 — 카메라 인덱스 발견" 섹션 신설: `lerobot-find-cameras opencv` 명령 출력 예시 + 자동 발견 fallback 동작 설명. "wrist 카메라 플립" 섹션 신설: `--flip-cameras wrist` 사용 안내 + gate-json 자동 적용 방법. 사용 예시에 Step 1 (카메라 확인) + gate-json 통합 예시 추가.

## code-tester 입장에서 검증 권장 사항

- 구문: `python3 -m py_compile orin/inference/hil_inference.py` (로컬 PASS 확인됨)
- lint: `ruff check orin/inference/hil_inference.py` (로컬 PASS 확인됨)
- argparse 동작: `python3 orin/inference/hil_inference.py --help` (torch 없는 환경에서 import 실패 — Orin venv 에서 확인 필요)
- DOD 항목 1 — argparse `--cameras` help 에 "lerobot-find-cameras opencv" 명시 ✓
- DOD 항목 2 — `_auto_discover_cameras()` 자동 발견 fallback 추가 ✓
- DOD 항목 3 — 03 BACKLOG #15·#16 BACKLOG.md 마킹 ✓
- 실 카메라 검증은 PHYS_REQUIRED → verification_queue O 그룹 (Phase 3 게이트 3)

## 잔여 리스크

- `_auto_discover_cameras()` 의 `/dev/videoN` → int 변환 (`re` 숫자 추출) 은 비표준 경로 (예: `/dev/video-usb0`) 에서 실패 가능 — 이 경우 `None` 반환 + 오류 메시지 출력으로 graceful 처리
- wrist 카메라 방향과 사전학습 분포 정합 여부는 03 BACKLOG #11 (08 트리거) 잔여
- 자동 발견 순서 (첫 번째 → top, 두 번째 → wrist) 는 OS 열거 순서에 의존 — 재부팅 후 순서 변경 가능. `lerobot-find-cameras opencv` 로 사전 확인 권장 안내를 출력함으로써 사용자 주의 유도
