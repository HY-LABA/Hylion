# TODO-P3 — Implementation

> 작성: 2026-05-03 | task-executor | cycle: 1

## 목표

`arm_2week_plan.md` 에 신규 `07_e2e_pilot_and_cleanup` 항목 추가 + 기존 07~10 → 08~11 시프트 (헤더·주석·번호·내부 cross-ref 일관성 유지).

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `arm_2week_plan.md` | M | 신규 07 항목 추가 + 기존 07~10 → 08~11 시프트 (헤더·주석·내부 ref 포함) |

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경. Category B 해당 없음 (마크다운 문서 수정만).
- Coupled File Rule: lerobot upstream 영향 영역 미터치 — Coupled File 갱신 불필요.
- 레퍼런스 활용: 코드 구현 없음 (문서 수정만). 레퍼런스 검색 불필요.
- 06 시프트 패턴 (`<!-- 신규 삽입 ... 기존 NN~MM → NN+1~MM+1 시프트. -->`) 을 그대로 따름.

## 변경 내용 요약

`arm_2week_plan.md` 의 `06_dgx_absorbs_datacollector` 항목 다음에 신규 `[ ] 07_e2e_pilot_and_cleanup` 마일스톤 항목을 추가했다. 항목 내용은 spec 본문 (`07_e2e_pilot_and_cleanup.md`) 의 §본 마일스톤의 위치, §사용자 결정 사항, §Todo 요약을 정리해 그룹별 (P/D/T/O/W) 주요 작업, Phase 1 합의 결정 사항 (A~J), 종착점, spec 파일 경로를 기재했다.

기존 07_leftarmVLA ~ 10_biarm_deploy 는 각각 08~11 로 시프트했다. 각 항목의 헤더 (예: `### [ ] 08_leftarmVLA`) 와 HTML 주석 (`<!-- 구 NN_xxx. MM_yyy (YYYY-MM-DD) 삽입으로 인해 NN+1 로 시프트. -->`) 을 갱신하고, 직전 시프트 이력 라인 (06 시프트로 07 → 08 된 사실 등) 도 누적 보존했다. 내부 cross-ref (예: `09 양팔 학습의 사전 단계가 아니다`, `09 에서 수집한`, `10 학습 시`) 도 새 번호에 맞게 갱신했다.

## 변경 전/후 핵심 diff

### 신규 추가 (06_dgx_absorbs_datacollector 다음)

```
### [ ] 07_e2e_pilot_and_cleanup

<!-- 신규 삽입 (2026-05-03). 기존 07~10 → 08~11 시프트. -->
...
- spec 파일: `docs/work_flow/specs/07_e2e_pilot_and_cleanup.md`
```

### 헤더 시프트

| Before | After |
|---|---|
| `### [ ] 07_leftarmVLA` | `### [ ] 08_leftarmVLA` |
| `### [ ] 08_biarm_teleop_on_dgx` | `### [ ] 09_biarm_teleop_on_dgx` |
| `### [ ] 09_biarm_VLA` | `### [ ] 10_biarm_VLA` |
| `### [ ] 10_biarm_deploy` | `### [ ] 11_biarm_deploy` |

### 주석 갱신 (누적 보존)

- 08_leftarmVLA: 07→08 이력 + 06 삽입으로 07 이력 두 줄 누적
- 09_biarm_teleop_on_dgx: 08→09 이력 + 06 삽입으로 07→08 이력 두 줄 누적
- 10_biarm_VLA: 09→10 이력 + 06 삽입으로 08→09 이력 두 줄 누적
- 11_biarm_deploy: 10→11 이력 + 06 삽입으로 09→10 이력 두 줄 누적

### 내부 cross-ref 갱신

- `08_leftarmVLA` 본문: `"09 양팔 학습의 사전 단계가 아니다 (09 는...)"`  → `"10 양팔 학습의 사전 단계가 아니다 (10 은...)"`
- `09_biarm_teleop_on_dgx` 본문: `"결정사항 (08 진행 중 확정)"` → `"결정사항 (09 진행 중 확정)"`, `"09 학습 시 expert 학습..."` → `"10 학습 시 expert 학습..."`
- `10_biarm_VLA` 본문: `"08 에서 수집한"` → `"09 에서 수집한"`

### 보존된 06 결정 이력

- `06_dgx_absorbs_datacollector` 항목의 `<!-- 신규 삽입 (2026-05-02). 기존 06~09 → 07~10 시프트. -->` 그대로 유지
- `08_leftarmVLA` 주석의 06 시프트 이력 라인 (`06_dgx_absorbs_datacollector (2026-05-02) 삽입으로 인해 07 로 시프트.`) 보존
- 09, 10, 11 도 동일하게 06 시프트 이력 라인 누적 보존

## 시프트 검증

```
grep 결과:
L157: ### [ ] 07_e2e_pilot_and_cleanup   ← 신규
L182: ### [ ] 08_leftarmVLA              ← 구 07
L199: ### [ ] 09_biarm_teleop_on_dgx     ← 구 08
L217: ### [ ] 10_biarm_VLA               ← 구 09
L232: ### [ ] 11_biarm_deploy            ← 구 10
```

마일스톤 번호 00~06 (기존) + 07 (신규) + 08~11 (시프트) 연속성 확인. 누락 없음.

## code-tester 입장에서 검증 권장 사항

- 헤더 일관성: `grep -n "^### \[ \]" arm_2week_plan.md` 로 07·08·09·10·11 순서 확인
- 주석 누락 없음: `grep -n "<!-- 구\|<!-- 신규" arm_2week_plan.md` 로 5 개 시프트 주석 확인
- 06 이력 보존: `grep -n "06_dgx_absorbs_datacollector" arm_2week_plan.md` 로 기존 이력 라인 유지 확인
- DOD 달성:
  - [x] 신규 07 항목 추가 (06 다음 위치)
  - [x] 기존 07~10 → 08~11 시프트 (헤더·주석·번호·내부 cross-ref 일관성)
  - [x] 06 결정 이력 보존 (`<!-- 06_dgx_absorbs_datacollector ... -->` 류)
  - [x] 04·05·06 의 의도된 history 참조 (legacy 이관 사유 라인) 보존
