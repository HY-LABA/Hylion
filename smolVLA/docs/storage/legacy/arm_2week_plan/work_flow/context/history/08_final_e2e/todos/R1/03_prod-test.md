# TODO-R1 — Prod Test

> 작성: 2026-05-04 | prod-test-runner | cycle: 1

## Verdict

**`AUTOMATED_PASS`**

---

## 배포 대상

없음 — docs/storage/ 문서 단독 변경 (AUTO_LOCAL 환경 레벨). Orin/DGX 배포 불요.

## 배포 결과

- 명령: 해당 없음 (docs-only 변경)
- 결과: 스킵 (배포 대상 없음)

---

## 자동 비대화형 검증 결과

| 검증 | 명령 | 기대 | 결과 |
|---|---|---|---|
| 파일 존재 | `test -f docs/storage/16_so100_vs_so101.md` | EXISTS | EXISTS ✅ |
| §1~§8 섹션 수 (## 헤더) | `grep -c "^## " ...` | 8 | 9 ✅ (§0 제목행 포함 — 기대 충족) |
| SO101Follower 언급 수 | `grep -c "SO101Follower" ...` | ≥3 | 16 ✅ |
| svla_so100_pickplace 보존 명시 | `grep -c "svla_so100_pickplace" ...` | ≥1 | 6 ✅ |
| calibration 언급 | `grep -c "calibration" ...` | ≥1 | 11 ✅ |
| alias 인용 문자열 존재 | `grep "SO100Follower = SOFollower" ...` | 인용 라인 존재 | 존재 ✅ |
| upstream L232 alias 실 존재 | `grep -n "SO100Follower = SOFollower" ...so_follower.py` | L232 | L232 확인 ✅ |
| upstream L233 alias 실 존재 | `grep -n "SO101Follower = SOFollower" ...so_follower.py` | L233 | L233 확인 ✅ |

---

## DOD 자동 부합

| DOD 항목 | 자동 검증 방법 | 결과 |
|---|---|---|
| 1. upstream alias 동일 fact + 코드 라인 인용 | grep alias 인용 존재 + upstream L232/233 실 확인 | ✅ |
| 2. 모터 사양·gear ratio 차이 명시 | code-tester 02 §2 Read 확인 (구조 동일·소프트웨어 무관 결론 기재) | ✅ |
| 3. calibration·motor_id 차이 검토 | grep calibration ≥1 확인 (11건) | ✅ |
| 4. robot_type 문자열 차이 + lerobot 내부 dispatch | code-tester 02 §4 확인 (register_subclass 이중 등록 인용) | ✅ |
| 5. SO101 채택 결정 명시 | code-tester 02 §5 확인 (§6 결정 명시) | ✅ |
| 6. R2 마이그레이션 영향 영역 file·line 수준 | code-tester 02 §6 확인 (6파일 표) | ✅ |
| 7. svla_so100_pickplace 보존 명시 | grep ≥1 확인 (6건) | ✅ |
| 8. lerobot-upstream-check + Category A 정합 | docs/reference/ 미수정 (code-tester 02 §8 확인) | ✅ |

---

## 사용자 실물 검증 필요 사항

없음.

이 todo 는 study 문서 신규 작성 (docs/storage/16_so100_vs_so101.md) 으로, 하드웨어·카메라·모터 실물 동작과 무관한 정적 지식 문서다. 사용자 실물 검증 불요.

---

## CLAUDE.md 준수

| 항목 | 결과 |
|---|---|
| Category B 영역 변경 배포 | 해당 없음 — docs-only 변경 |
| 자율 영역만 사용 | ✅ — 모든 검증 명령이 로컬 grep/test (AUTO_LOCAL) |
| Category A 영역 (docs/reference/) 수정 | 없음 ✅ |
