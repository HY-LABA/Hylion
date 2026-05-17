# TODO-03-H — Code Test

> 작성: 2026-05-18 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈 0건, Recommended 0건.

---

## 단위 테스트 결과

```
python3 -m py_compile orin/inference/leftarm_v2_inference.py
→ syntax OK (exit 0)

python3 -c "import json; data=json.load(open('orin/config/cameras.json')); print(data)"
→ JSON OK
{'top': {'index': None, 'rotation': -90, 'width': 480, 'height': 640, 'fps': 30, 'fourcc': 'MJPG', 'flip': False},
 'wrist': {'index': None, 'rotation': 0, 'width': 640, 'height': 480, 'fps': 30, 'fourcc': 'MJPG', 'flip': False}}
```

pytest 는 별도 단위 테스트 파일 없음 (orin/inference/ 에 test_*.py 미존재 — 기존 패턴 동일).
정적 검증 (py_compile + JSON 파싱 + ruff) 으로 대체.

---

## Lint·Type 결과

```
ruff check orin/inference/leftarm_v2_inference.py
→ All checks passed!
```

mypy: orin/inference/leftarm_v2_inference.py 는 엄밀 mypy 대상 아님 (CLAUDE.md 레퍼런스 기준 mypy strict 는 cameras/motors/configs 등 lerobot 내부 모듈에만 적용). 스킵.

---

## DOD 정합성

본 TODO-03-H 는 spec 본문의 TODO-03 ad-hoc 파생 항목. 목표: cameras.json schema 확장 + apply_gate_config rotation/width/height 추출 + OpenCVCameraConfig 생성 시 slot별 파라미터 적용.

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| cameras.json schema 확장: top rotation=-90/480x640, wrist rotation=0/640x480 | ✅ | 실제값 `{'top': {'rotation': -90, 'width': 480, 'height': 640, ...}, 'wrist': {'rotation': 0, 'width': 640, 'height': 480, ...}}` — base_config.yaml 와 정합 |
| 기존 index/flip 필드 보존 | ✅ | top: index=null, flip=false / wrist: index=null, flip=false 유지 |
| apply_gate_config 내 신규 필드 (rotation/width/height/fps/fourcc) 추출 | ✅ | line 181-200: cam_entry.get("rotation", 0) 등 5개 필드 모두 추출, cam_params 에 저장 후 args._camera_params 에 할당 |
| 누락 시 경고 + default 적용 (하위 호환) | ✅ | line 188-193: "rotation" not in cam_entry 검사 → stderr 경고 출력 후 default 0 적용 |
| --gate-json 미지정 시 _camera_params={} 보장 | ✅ | line 203-204: cameras_data is None 분기 → args._camera_params={}; line 231-232: hasattr 가드 이중 보장 |
| OpenCVCameraConfig 생성 시 cameras.json 값 적용 (slot별) | ✅ | line 528-546: _cam_params.get(name, {}) 로 top/wrist 파라미터 추출 → OpenCVCameraConfig(index_or_path, width, height, fps, fourcc, rotation) 전달 |
| rotation=-90 → Cv2Rotation(-90) = ROTATE_270 자동 변환 | ✅ | orin/lerobot/cameras/opencv/configuration_opencv.py line 70: `self.rotation = Cv2Rotation(self.rotation)` — __post_init__ 에서 정수 자동 변환 확인. Cv2Rotation.ROTATE_270 = -90 확인 (orin/lerobot/cameras/configs.py) |
| README.md 본문 갱신 (Coupled Rules §6, ⚠️ 박스만 추가 X) | ✅ | "사전 단계" 섹션 앞에 cameras.json 신규 필드 안내 한 줄 본문 삽입 확인 (diff 검증). 박스 패턴 없음 — 본문 직접 정정 |
| BACKLOG.md #11 [ad-hoc] entry 등록 (CLAUDE.md §walkthrough 의무) | ✅ | #11 항목: `[ad-hoc] rotation 정합 복원 ... 완료 (TODO-03-H 2026-05-18)` 확인. 상태 "완료" |

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
| A (절대 금지 영역) | ✅ | docs/reference/ 미변경. .claude/agents/, .claude/skills/, settings.json 미변경 |
| B (자동 재시도 X) | ✅ 해당 없음 | orin/inference/ + orin/config/ 변경 — orin/lerobot/ 미변경, orin/pyproject.toml 미변경, setup_env.sh 미변경, deploy_*.sh 미변경 |
| Coupled File Rules §6 | ✅ | cameras.json schema 변경 → orin/inference/README.md 본문 직접 갱신 (⚠️ 박스 패턴 없음) |
| D (절대 금지 명령) | ✅ | 해당 명령 없음 |
| 옛 룰 (docs/storage/ bash 예시 추가 X) | ✅ | docs/storage/ 미변경 |

---

## 배포 권장

READY_TO_SHIP — prod-test-runner 진입 권장.

본 fix 는 PHYS_REQUIRED 단계 직전 시연장 ad-hoc 긴급 수정. 코드 자체는 정적 검증 완료 (syntax, JSON, lint). 실제 rotation 적용 여부는 Orin 실물 카메라 연결 시 확인 필요 (PHYS_REQUIRED — 기존 verification_queue 의 TODO-03 live 추론 항목에 포함).
