# TODO-H1 — Code Test

> 작성: 2026-05-04 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈: 0건. Recommended: 1건.

## 단위 테스트 결과

본 TODO는 마크다운 문서 추가 (코드 X). pytest 대상 없음.

```
해당 없음 — docs/storage/02_hardware.md 순수 문서 변경
```

## Lint·Type 결과

```
해당 없음 — .md 파일, ruff/mypy 대상 외
```

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. 모델: INNO-MAKER U20CAM-720P | ✅ | 207행: `INNO-MAKER U20CAM-720P` |
| 2. 출처: GitHub URL + UserManual v1.0 (2023-10-20) | ✅ | 209행: URL + `UserManual v1.0 (2023-10-20)` |
| 3. Sensor: 1/4 inch, 1280×720, rolling shutter | ✅ | 213행 센서, 214행 Rolling Shutter |
| 4. Lens: F2.2, focal 2.79mm, M12, 18mm seat, FOV-D 120°/H 102° | ✅ | 215~218행 모두 존재 |
| 5. PCBA: 32×32mm, 4 mounting holes Φ2.2mm | ✅ | 219~220행 |
| 6. USB: 2.0 High-Speed, UVC 1.0.0, cable 1m | ✅ | 221~223행 |
| 7. Format: MJPEG/YUY2, 30fps | ✅ | 224~225행 |
| 8. Resolution 4단계 (1280×720, 800×600, 640×480, 320×240) | ✅ | 226행 4단계 모두 기재 |
| 9. 본 프로젝트 용도 명시 (wrist 카메라 1대) | ✅ | 227행 + 208행 |
| 10. §7 (OV5648) 본문 보존 | ✅ | 174~203행 원본 유지 확인 |
| 11. §7 표 형식 미러 (2열 항목\|값) | ✅ | 211~227행 동일 2열 구조 |
| 12. §8: "overview OV5648 x1 + wrist U20CAM-720P x1 (혼합 구성)" 명시 | ✅ | 233행 정확히 일치 |

## Critical 이슈

없음.

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `02_hardware.md:177` | §7 수량이 "2대 (SO-ARM 관측용)"으로 남아 있음. §7-1 추가로 실제 구성은 OV5648 x1 + U20CAM x1 이므로 "1대 (overview 카메라)"로 갱신하면 §7·§7-1·§8 수량 일관성이 높아짐. DOD 미요구 사항이므로 Recommended. |

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | docs/reference/ 미변경. .claude/ 미변경 |
| B (자동 재시도 X 영역) | ✅ | 해당 없음 (orin/lerobot, pyproject.toml 등 미변경) |
| Coupled File Rules | ✅ | docs/storage 변경 — Coupled File 규칙 대상 외 |
| 옛 룰 (docs/storage bash 예시) | ✅ | bash 명령 예시 추가 없음 |

## 배포 권장

READY_TO_SHIP — prod-test-runner 진입 권장.
