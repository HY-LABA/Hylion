# TODO-03-H — Implementation

> 작성: 2026-05-18 | task-executor | cycle: 1

## 목표

시연장 직전 발견된 rotation 정합 결함 복원 — `leftarm_v2_inference.py` 의 `OpenCVCameraConfig` 생성 시 rotation/width/height 누락 → 수집 분포와 불일치 수정.

## 조사 결과 (작업 시작 전 확인)

### base_config.yaml cameras 섹션 정확값

```yaml
cameras:
  top:   { width: 480, height: 640, fps: 30, color_mode: rgb, fourcc: MJPG, rotation: -90 }
  wrist: { width: 640, height: 480, fps: 30, color_mode: rgb, fourcc: MJPG }
  # wrist rotation 미명시 → 0 (NO_ROTATION)
```

주석 정보: `width/height 는 "회전 후 출력 크기"`. top 은 하드웨어 640x480 캡처 → CCW 90° → 480x640.

### Cv2Rotation enum 매핑 (`docs/reference/lerobot/src/lerobot/cameras/configs.py`)

| 정수값 | enum name | 의미 |
|---|---|---|
| 0 | `NO_ROTATION` | 회전 없음 |
| 90 | `ROTATE_90` | CW 90° |
| 180 | `ROTATE_180` | 180° |
| -90 | `ROTATE_270` | CCW 90° (=270° CW) |

`-90` 정수 직접 전달 → `Cv2Rotation(-90)` = `ROTATE_270` 자동 변환 (`__post_init__` 에서 `self.rotation = Cv2Rotation(self.rotation)` 처리). 명시적 변환 불필요.

`OpenCVCameraConfig` 필드 (reference line 61-66):
```python
index_or_path: int | Path
color_mode: ColorMode = ColorMode.RGB
rotation: Cv2Rotation = Cv2Rotation.NO_ROTATION
warmup_s: int = 1
fourcc: str | None = None
backend: Cv2Backends = Cv2Backends.ANY
# fps, width, height 는 부모 CameraConfig 에서 상속 (None 이 default)
```

### wrapper (`run_inference_leftarm_v2.sh`) 변경 불필요 근거

wrapper 는 cameras.json 에서 `top.index` / `wrist.index` 만 파싱 → Python 에 `--cameras top:N,wrist:M` 전달.
rotation/width/height/fps/fourcc 는 `leftarm_v2_inference.py` 의 `apply_gate_config` 가 `--gate-json` 경유로 cameras.json 에서 직접 읽음. wrapper 는 `--gate-json ${CONFIG_DIR}` 를 이미 전달하고 있어 추가 변경 불필요.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `orin/config/cameras.json` | M | schema 확장: rotation/width/height/fps/fourcc 신규 필드 추가 (top=-90,480x640 / wrist=0,640x480) |
| `orin/inference/leftarm_v2_inference.py` | M | apply_gate_config: cameras.json 신규 필드 추출 + _camera_params 저장; OpenCVCameraConfig 생성: slot별 rotation/width/height/fps/fourcc 적용 |
| `orin/inference/README.md` | M | "사전 단계" 섹션 앞에 cameras.json 신규 필드 안내 한 줄 추가 (Coupled Rules §6) |
| `docs/work_flow/specs/BACKLOG.md` | M | ad-hoc 메모 #11 등록 (CLAUDE.md §walkthrough 의무) |

## 적용 룰

- CLAUDE.md Hard Constraints Category A: `docs/reference/` 미변경 ✓
- Category B 미해당: `orin/inference/`·`orin/config/` 변경 — `orin/lerobot/`·`orin/pyproject.toml`·`setup_env.sh` 미변경 ✓
- Coupled File Rule §6: `cameras.json` schema 변경 → README 갱신 ✓
- ad-hoc 사후 보고: BACKLOG #11 `[ad-hoc]` 등록 ✓
- 레퍼런스 활용: `docs/reference/lerobot/src/lerobot/cameras/configs.py` 직접 Read — `Cv2Rotation(int, Enum)` 에서 `ROTATE_270 = -90` 확인. `OpenCVCameraConfig.__post_init__` 에서 `self.rotation = Cv2Rotation(self.rotation)` 정수 자동 변환 확인.

## 변경 내용 요약

**결함**: `leftarm_v2_inference.py` line 491-493 에서 모든 카메라에 `width=640, height=480, rotation=0` 고정 → top 카메라가 수집 시 480x640 + CCW90° 회전 적용된 분포와 맞지 않아 추론 입력 이미지가 학습 분포와 완전 불일치.

**수정 (방안 A)**: `cameras.json` 을 단일 진실원천으로 삼아 rotation/width/height/fps/fourcc 를 명시. `apply_gate_config` 가 cameras.json 에서 신규 필드를 읽어 `args._camera_params` 에 저장. OpenCVCameraConfig 생성 루프에서 slot(camera1/camera2) ↔ name(top/wrist) 매핑을 통해 각 카메라별 파라미터를 적용.

하위 호환: 기존 cameras.json (index/flip 만) 사용 시 rotation 누락 경고 출력 후 default 0 적용 → 기존 hil_inference.py / lego_v1_inference.py 패턴과 동일하게 동작. `--gate-json` 미지정 시에도 `_camera_params = {}` 로 초기화되어 default 값으로 동작.

## code-tester 입장에서 검증 권장 사항

- **syntax**: `python3 -m py_compile orin/inference/leftarm_v2_inference.py` ✓ (이미 확인)
- **JSON**: `python3 -c "import json; json.load(open('orin/config/cameras.json'))"` ✓ (이미 확인)
- **lint**: `ruff check orin/inference/leftarm_v2_inference.py` ✓ (All checks passed)
- **rotation 정합 확인**: cameras.json.top.rotation=-90 이 `Cv2Rotation(-90)` = `ROTATE_270` 으로 변환되어 OpenCVCameraConfig 에 전달되는지 trace
- **하위 호환**: cameras.json 에서 rotation 필드 제거 후 `apply_gate_config` 호출 시 경고 출력 + default=0 적용 확인
- **_camera_params 없는 경로**: `--gate-json` 미지정 시 `getattr(args, "_camera_params", {})` 로 빈 dict → default 적용 확인
- **DOD**: base_config.yaml top(rotation=-90,480x640) / wrist(rotation=0,640x480) 값이 추론 OpenCVCameraConfig 에 동일하게 반영됨

## 잔여 리스크

- **사용자 시연장에서 cameras.json index 채울 때**: `index` 필드만 채우면 OK. 신규 필드(rotation/width/height/fps/fourcc)는 수집 정합값이 이미 기재돼 있어 *건드리지 않아야 함*.
- **wrist 카메라 flip**: cameras.json.wrist.flip=false (기본) — 수집 시 flip 적용 여부와 맞는지 사용자가 시연장에서 확인 필요 (기존 동작 유지, rotation fix 외 변경 없음).
- **_camera_params 는 argparse Namespace 동적 속성**: 표준 Python 관행이나 IDE/type checker 경고 가능. 엄밀히는 dataclass 또는 별도 변수 전달이 더 명확하나, 기존 apply_gate_config 패턴(args 직접 변조)과 일관성 유지를 위해 선택.
