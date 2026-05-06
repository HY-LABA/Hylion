# TODO-H1 — Prod Test

> 작성: 2026-05-04 | prod-test-runner | cycle: 1

## Verdict

**`AUTOMATED_PASS`**

## 배포 대상

- 없음 (docs/storage 문서 변경 — devPC 로컬 파일, orin/dgx 배포 불요)
- 환경: AUTO_LOCAL

## 배포 결과

- 배포 스크립트 실행: 해당 없음 (변경 파일 `docs/storage/02_hardware.md` — 코드·런타임 외)
- Category B 영역 변경 여부: 없음

## 자동 비대화형 검증 결과

| 검증 | 명령 | 기대 | 결과 |
|---|---|---|---|
| U20CAM-720P 언급 수 | `grep -c "U20CAM-720P" docs/storage/02_hardware.md` | ≥3 | 3 ✅ |
| INNO-MAKER 언급 수 | `grep -c "INNO-MAKER" docs/storage/02_hardware.md` | ≥1 | 2 ✅ |
| FOV-D 항목 존재 | `grep -c "FOV-D" docs/storage/02_hardware.md` | ≥1 | 1 ✅ |
| 120° 값 존재 | `grep -c "120°" docs/storage/02_hardware.md` | ≥1 | 2 ✅ |
| OV5648 언급 수 | `grep "OV5648" ... \| wc -l` | ≥3 | 3 ✅ |
| §8 wrist U20CAM-720P 언급 | `grep -c "wrist U20CAM-720P" docs/storage/02_hardware.md` | ≥1 | 1 ✅ |
| §7 헤더 보존 | `grep -c "## 7) 카메라" docs/storage/02_hardware.md` | 1 | 1 ✅ |
| §7-1 신규 섹션 헤더 | `grep -E "^## (7-1\|7B)" docs/storage/02_hardware.md` | 1행 | `## 7-1) 카메라 (SO-ARM용, wrist 카메라 — 신규)` ✅ |
| 혼합 구성 §8 갱신 | `grep -c "혼합 구성" docs/storage/02_hardware.md` | ≥1 | 2 ✅ |

비고: `grep -c "FOV-D 120"` 은 0 — 실제 파일은 표 셀 구조로 `FOV-D | 120°` 가 별도 행에 분리됨. `grep -c "FOV-D"` (1) + `grep -c "120°"` (2) 로 교차 확인하여 내용 존재 검증 완료.

## DOD 자동 부합

| DOD 항목 | 자동 검증 | 결과 |
|---|---|---|
| 1. 모델: INNO-MAKER U20CAM-720P | grep (INNO-MAKER ≥2, U20CAM-720P ≥3) | ✅ |
| 2. 출처: GitHub URL + UserManual v1.0 (2023-10-20) | 02_code-test.md DOD #2 209행 확인 | ✅ |
| 3. Sensor: 1/4 inch, 1280×720, rolling shutter | 02_code-test.md DOD #3 213~214행 확인 | ✅ |
| 4. Lens: F2.2, focal 2.79mm, M12, 18mm seat, FOV-D 120°/H 102° | FOV-D 1건 + 120° 2건 교차 확인 + code-test DOD #4 215~218행 확인 | ✅ |
| 5. PCBA: 32×32mm, 4 mounting holes Φ2.2mm | 02_code-test.md DOD #5 219~220행 확인 | ✅ |
| 6. USB: 2.0 High-Speed, UVC 1.0.0, cable 1m | 02_code-test.md DOD #6 221~223행 확인 | ✅ |
| 7. Format: MJPEG/YUY2, 30fps | 02_code-test.md DOD #7 224~225행 확인 | ✅ |
| 8. Resolution 4단계 (1280×720, 800×600, 640×480, 320×240) | 02_code-test.md DOD #8 226행 확인 | ✅ |
| 9. 본 프로젝트 용도 명시 (wrist 카메라 1대) | 02_code-test.md DOD #9 227행 + 208행 확인 | ✅ |
| 10. §7 (OV5648) 본문 보존 | OV5648 ≥3건 + §7 헤더 1건 | ✅ |
| 11. §7 표 형식 미러 (2열 항목\|값) | 02_code-test.md DOD #11 211~227행 확인 | ✅ |
| 12. §8: "overview OV5648 x1 + wrist U20CAM-720P x1 (혼합 구성)" | wrist U20CAM-720P 1건 + 혼합 구성 2건 + 233행 확인 | ✅ |

## 사용자 실물 검증 필요 사항

없음. 본 TODO 는 docs/storage 문서 변경 (AUTO_LOCAL) — 하드웨어 실물, 카메라 연결, SO-ARM 동작 필요 없음.

## 잔여 권장 사항 (비차단)

code-tester Recommended #1: `docs/storage/02_hardware.md:177` §7 수량 "2대 (SO-ARM 관측용)" → "1대 (overview 카메라)" 갱신 — DOD 미요구, 비차단. §8 혼합 구성 갱신으로 전체 의도는 명확. 다음 spec 에서 처리 또는 사용자 판단 BACKLOG 이관 가능.

## CLAUDE.md 준수

- Category B 영역 변경된 배포: 없음
- 자율 영역만 사용: ✅ (로컬 grep, 파일 Read — AUTO_LOCAL)
- deploy 스크립트 실행: 해당 없음
