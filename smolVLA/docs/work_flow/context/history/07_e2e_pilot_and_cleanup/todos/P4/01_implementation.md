# TODO-P4 — Implementation

> 작성: 2026-05-03 | task-executor | cycle: 1

## 목표

`docs/work_flow/specs/README.md` 의 활성 spec 번호 표를 07_e2e_pilot_and_cleanup 신규 삽입 + 기존 07~10 → 08~11 시프트에 맞게 갱신.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `docs/work_flow/specs/README.md` | M | 활성 spec 표 갱신 (06→history, 07 신규, 기존 07~10→08~11) + 시프트 주석·날짜·배경 설명 갱신 |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 ✓
- Coupled File Rule: 해당 없음 (orin/lerobot, pyproject.toml 미변경) ✓
- 레퍼런스 활용: 문서 갱신 작업 — 코드 레퍼런스 불필요 ✓

## 변경 내용 요약

`docs/work_flow/specs/README.md` L107~126 구간을 갱신했다. 06_dgx_absorbs_datacollector 가 이미 history 상태로 완료되었고 07_e2e_pilot_and_cleanup 이 현 활성 사이클로 신규 삽입됨에 따라, 기존 표에서 06 항목의 상태를 "history" 로 전환하고 07 행에 e2e_pilot_and_cleanup 을 활성으로 추가했다. 기존 07(leftarmVLA)~10(biarm_deploy) 항목은 각각 08~11 로 번호를 시프트했으며, 구 번호를 괄호 안에 명시했다.

추가로 날짜 헤딩을 2026-05-02 → 2026-05-03 으로 갱신하고, 시프트 주석을 기존 M1 주석 아래에 병렬로 추가했으며, 표 아래의 시프트 배경 설명 라인도 07_e2e_pilot_and_cleanup 삽입 기준으로 재작성했다.

## 변경 전/후 diff

### Before (L107~126)

```
## 활성 spec 번호 현황 (2026-05-02 기준)

<!-- 06_dgx_absorbs_datacollector 삽입으로 기존 06~09 → 07~10 시프트 (M1 갱신) -->

| 번호 | spec 명 | 상태 |
|---|---|---|
| 01 | orin_setting | history |
| 02 | dgx_setting | history |
| 03 | smolvla_test_on_orin | history |
| 04 | infra_setup | history |
| 05 | interactive_cli | history |
| **06** | **dgx_absorbs_datacollector** | **활성 (현 사이클)** |
| 07 | leftarmVLA | 대기 (구 06) |
| 08 | biarm_teleop_on_dgx | 대기 (구 07) |
| 09 | biarm_VLA | 대기 (구 08) |
| 10 | biarm_deploy | 대기 (구 09) |

> 번호 시프트 배경: 06_dgx_absorbs_datacollector 삽입으로 기존 `06_leftarmVLA` → `07_leftarmVLA`, `07~09` → `08~10`. 상세: `06_dgx_absorbs_datacollector.md` §본 마일스톤의 위치.
```

### After (L107~127)

```
## 활성 spec 번호 현황 (2026-05-03 기준)

<!-- 06_dgx_absorbs_datacollector 삽입으로 기존 06~09 → 07~10 시프트 (M1 갱신) -->
<!-- 07_e2e_pilot_and_cleanup 삽입으로 기존 07~10 → 08~11 시프트 (P4 갱신, 2026-05-03) -->

| 번호 | spec 명 | 상태 |
|---|---|---|
| 01 | orin_setting | history |
| 02 | dgx_setting | history |
| 03 | smolvla_test_on_orin | history |
| 04 | infra_setup | history |
| 05 | interactive_cli | history |
| 06 | dgx_absorbs_datacollector | history |
| **07** | **e2e_pilot_and_cleanup** | **활성 (현 사이클)** |
| 08 | leftarmVLA | 대기 (구 07) |
| 09 | biarm_teleop_on_dgx | 대기 (구 08) |
| 10 | biarm_VLA | 대기 (구 09) |
| 11 | biarm_deploy | 대기 (구 10) |

> 번호 시프트 배경: 07_e2e_pilot_and_cleanup 삽입으로 기존 `07_leftarmVLA` → `08_leftarmVLA`, `08~10` → `09~11`. 상세: `07_e2e_pilot_and_cleanup.md` §본 마일스톤의 위치.
```

## DOD 달성 확인

| DOD 항목 | 결과 |
|---|---|
| 표 갱신 완료 (06 → history, 07 신규, 기존 07~10 → 08~11) | ✓ |
| 시프트 주석 추가 (P4 갱신, 2026-05-03) | ✓ |
| 날짜 정합 (2026-05-03) | ✓ |
| 배경 설명 라인 갱신 (07_e2e_pilot_and_cleanup 기준) | ✓ |

## code-tester 입장에서 검증 권장 사항

- 표 행 수: 11개 spec 행 (01~11) 확인
- 06 행 상태: "history" (bold 없음) 확인
- 07 행 상태: **bold** + "활성 (현 사이클)" 확인
- 08~11 행 구 번호 괄호: 08=(구 07), 09=(구 08), 10=(구 09), 11=(구 10) 확인
- 주석 2줄 병렬 존재 확인 (M1 + P4)
- 날짜 헤딩: 2026-05-03 확인
- 배경 설명: "07_e2e_pilot_and_cleanup" + "08~11" 언급 확인
