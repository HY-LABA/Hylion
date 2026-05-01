# 20260501_1505 — TODO-G2: hil_inference.py --gate-json 통합

> task-executor | 2026-05-01 15:05 | cycle: 1

## 작업 요약

`orin/inference/hil_inference.py` 에 `--gate-json` 옵션 추가.
check_hardware.sh (G1 산출물) 가 생성한 `orin/config/ports.json` / `cameras.json` cache 를
읽어서 미지정 CLI 인자를 자동으로 채운다.

## 변경 파일

| 파일 | 종류 | 요약 |
|---|---|---|
| `orin/inference/hil_inference.py` | M | `--gate-json` 옵션 + `load_gate_config` / `apply_gate_config` 헬퍼 추가 (75 줄 순 추가) |

## 핵심 결정

1. **gate JSON 대상**: `check_hardware.sh --output-json` 결과 파일(summary only)이 아닌 `orin/config/ports.json` + `cameras.json` cache 를 대상으로 함. summary JSON 에는 구조화된 포트·카메라 정보가 없음.
2. **경로 지정 방식**: 디렉터리 경로 또는 ports.json 파일 경로 중 하나로 지정. 부모 디렉터리 자동 탐색.
3. **카메라 인덱스 타입**: check_hardware.sh 가 str (예: `/dev/video0`) 저장 → `_to_idx()` 헬퍼로 int/str 자동 변환. `OpenCVCameraConfig.index_or_path` 가 두 타입 모두 허용.
4. **--follower-port required 처리**: argparse `required=True` → `default=None` 으로 변경 후 `parser.parse_args()` 이후 명시적 검증. gate-json 로딩 후 follower_port 가 채워지면 오류 없이 진행.

## BACKLOG 해소

| BACKLOG | 해소 방법 |
|---|---|
| 03 #15 카메라 인덱스 발견 | G1 cache + G2 `--gate-json` 자동 채움 |
| 03 #16 wrist flip | G1 cache + G2 `--gate-json` flip_cameras 자동 채움 |

## 잔여 (prod-test-runner 책임)

- ANOMALIES #1 (bash -n sandbox 차단) — Orin SSH 에서 bash -n 재실행 해소
- 사용자 실물 검증 3건 → verification_queue.md 추가

## 레퍼런스 활용

- 기존 `hil_inference.py` argparse 패턴 그대로 유지 (인자 선언 + 검증 순서)
- 신규 헬퍼 2개는 레퍼런스 미존재, TODo 명시 자산으로 사전 승인된 구현
