# TODO-H1 — Implementation

> 작성: 2026-05-04 | task-executor | cycle: 1

## 목표

`docs/storage/02_hardware.md` 에 INNO-MAKER U20CAM-720P wrist 카메라 사양을 §7-1 신규 추가하고 §8 로봇 구성 수량 카메라 항목 갱신.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `docs/storage/02_hardware.md` | M | §7 (OV5648) 직후 §7-1 (U20CAM-720P) 신규 추가 + §8 카메라 항목 혼합 구성으로 갱신 |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 — 해당 없음 (docs/storage 변경) ✓
- Coupled File Rule: 해당 영역(docs/storage) 은 coupled file 규칙 외 ✓
- 레퍼런스 활용: 본 TODO 는 하드웨어 문서 추가 (코드 신규 작성 X) — lerobot-reference-usage 스킬 대상 외 (코드 구현 아님). SKILL_GAP 해당 없음.

## 변경 내용 요약

`docs/storage/02_hardware.md` 의 §7 (OV5648 카메라) 를 보존한 채, 직후에 §7-1 신규 섹션을 추가했다. §7 표 형식을 미러하여 U20CAM-720P 사양 15개 항목을 표로 정리했다: 센서 (1/4", rolling shutter), 렌즈 (F2.2, 2.79mm, M12, 18mm seat, FOV-D 120°/H 102°), PCBA (32×32mm, 4홀 Φ2.2mm), USB (2.0 HS, UVC 1.0.0, 1m), 포맷 (MJPEG/YUY2, 30fps), 해상도 4종, 용도 명시.

§8 "로봇 구성 수량" 카메라 행을 기존 "2대" 단순 표기에서 "overview OV5648 x1 + wrist U20CAM-720P x1 (혼합 구성)" 으로 갱신하여 두 카메라 역할을 명시했다.

## code-tester 입장에서 검증 권장 사항

- 정합성 확인: §7 OV5648 본문 항목 수 변화 없음 (보존) 확인
- §7-1 표 항목 수: 15개 — spec DOD 기재 항목 (Sensor, Lens, PCBA, USB, Format, Resolution, 용도) 모두 포함 여부 확인
- §8 카메라 행: "overview OV5648 x1 + wrist U20CAM-720P x1 (혼합 구성)" 문자열 존재 확인
- grep 검증:
  - `grep "U20CAM-720P" docs/storage/02_hardware.md` — 최소 3건 (헤더·모델·§8)
  - `grep "7-1" docs/storage/02_hardware.md` — 헤더 존재
  - `grep "OV5648" docs/storage/02_hardware.md` — §7 원본 보존 확인
  - `grep "혼합 구성" docs/storage/02_hardware.md` — §8 갱신 확인
