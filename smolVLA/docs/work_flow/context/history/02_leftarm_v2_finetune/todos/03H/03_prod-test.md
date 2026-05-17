# TODO-03-H — Prod Test

> 작성: 2026-05-18 | prod-test-runner | cycle: 1

## Verdict

**`NEEDS_USER_VERIFICATION`**

## 배포 대상
- orin

## 배포 결과

| 파일 | 명령 | 결과 |
|---|---|---|
| `orin/inference/leftarm_v2_inference.py` | `scp ... orin:~/smolvla/orin/inference/` | 성공 |
| `orin/config/cameras.json` | `scp ... orin:~/smolvla/orin/config/` | 성공 |
| `orin/inference/README.md` | `scp ... orin:~/smolvla/orin/inference/` | 성공 |

⚠️ `deploy_orin.sh` 호출 X (BACKLOG #1). scp 개별 배포.
⚠️ cameras.json index 는 null 상태 유지 — 사용자가 시연장에서 직접 채울 예정.

## 자동 비대화형 검증 결과

| 검증 | 명령 | 결과 |
|---|---|---|
| top-level import smoke | `ssh orin python3 -c "import leftarm_v2_inference"` | OK |
| cameras.json schema 인식 | `json.load` + key 열거 | `['index', 'rotation', 'width', 'height', 'fps', 'fourcc', 'flip']` 전체 인식 ✅ |
| top camera 회전 정합 | `cams["top"]["rotation"]` | -90, 480x640 ✅ |
| wrist camera 회전 정합 | `cams["wrist"]["rotation"]` | 0, 640x480 ✅ |
| OpenCVCameraConfig enum 변환 | `rotation=-90` → `cfg.rotation` | `Cv2Rotation.ROTATE_270` ✅ |

## DOD 자동 부합

| DOD 항목 | 자동 검증 | 결과 |
|---|---|---|
| leftarm_v2_inference.py import 정상 | yes (import smoke) | ✅ |
| cameras.json rotation/width/height/fps/fourcc/flip 신규 필드 인식 | yes (json.load + key 열거) | ✅ |
| rotation -90 → Cv2Rotation.ROTATE_270 enum 자동 변환 | yes (OpenCVCameraConfig instantiation) | ✅ |
| live 추론 정상 동작 (cameras.json index 채운 후) | no — index null 상태 (사용자 채워야 함) | → verification_queue |

## 사용자 실물 검증 필요 사항

1. cameras.json `top.index` / `wrist.index` 채우기 (시연장 SSH 에서 직접 편집)
2. live 추론 재시도 — `bash ~/smolvla/orin/scripts/run_inference_leftarm_v2.sh live task1`

## CLAUDE.md 준수
- Category B 영역 변경 없음 (cameras.json·leftarm_v2_inference.py 는 일반 배포 대상)
- deploy_orin.sh 호출 X (rsync --delete 위험 회피, BACKLOG #1)
- 자율 영역만 사용: scp + ssh python3 -c ✅
