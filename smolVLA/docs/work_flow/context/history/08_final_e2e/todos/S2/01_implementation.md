# TODO-S2 — Implementation

> 작성: 2026-05-04 | task-executor | cycle: 1

## 목표

specs/README.md "활성 spec 번호 현황" 표 갱신 — 08_final_e2e 삽입 반영 (기준일, 시프트, 활성 표기).

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `docs/work_flow/specs/README.md` | M | 활성 spec 번호 현황 표 갱신 (기준일·시프트·활성 표기) |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경 (해당 없음) — doc 파일 수정이므로 Category A 미해당
- Coupled File Rule: lerobot 영역 미변경 — Coupled File Rules 미해당
- 레퍼런스 활용: 문서 갱신 작업으로 코드 레퍼런스 불요 (SKILL_GAP 없음)

## 변경 내용 요약

`docs/work_flow/specs/README.md` 의 "활성 spec 번호 현황" 섹션을 다음 4가지 변경 사항으로 갱신했다.

1. **기준일 갱신**: `(2026-05-03 기준)` → `(2026-05-04 기준)`
2. **시프트 배경 주석 추가**: `<!-- 08_final_e2e 삽입으로 기존 08~11 → 09~12 시프트 (S2 갱신, 2026-05-04) -->` 신규 주석을 기존 두 주석 다음에 추가. 기존 두 주석(`06_dgx_absorbs_datacollector`, `07_e2e_pilot_and_cleanup` 관련) 보존.
3. **표 행 갱신**:
   - 07 행: `e2e_pilot_and_cleanup` 상태를 `활성 (현 사이클)` → `history` 로 변경, bold 해제
   - 08 행 신규 추가: `final_e2e` — `활성 (현 사이클)` (bold)
   - 기존 08→09, 09→10, 10→11, 11→12 시프트: 번호 갱신 + 괄호 내 "구 NN" 표기 갱신
4. **시프트 주석 각주 갱신**: `08_final_e2e.md` 삽입 배경 기재.

## code-tester 입장에서 검증 권장 사항

```bash
# 1. 활성 spec 단 1건 확인
grep "활성 (현 사이클)" docs/work_flow/specs/README.md

# 2. 표 행 수 확인 (01~12 = 12행 + 헤더 1행 = 13행)
grep -c "^|" docs/work_flow/specs/README.md

# 3. 07 이 history 로 마킹됐는지 확인
grep "07" docs/work_flow/specs/README.md | grep "history"

# 4. 08 이 활성으로 마킹됐는지 확인
grep "08" docs/work_flow/specs/README.md | grep "활성"

# 5. 09~12 시프트 확인 (구 NN 표기)
grep "구 0[89]\|구 1[012]" docs/work_flow/specs/README.md

# 6. 기준일 확인
grep "기준일\|기준" docs/work_flow/specs/README.md | head -5

# 7. 시프트 주석 3건 존재 확인
grep -c "시프트" docs/work_flow/specs/README.md
```

DOD 체크:
- [x] 07_e2e_pilot_and_cleanup → "history" 마킹
- [x] 신규 `08_final_e2e` → "활성 (현 사이클)" 표기
- [x] 09~12 시프트 반영 (구 08~11)
- [x] 기준일 2026-05-03 → 2026-05-04 갱신
- [x] 시프트 배경 주석 추가 (08_final_e2e 삽입)

## 잔여 리스크

없음. 순수 문서 갱신이며 코드·의존성 변경 없음. README.md 의 표 정합성은 grep 으로 즉시 확인 가능.
