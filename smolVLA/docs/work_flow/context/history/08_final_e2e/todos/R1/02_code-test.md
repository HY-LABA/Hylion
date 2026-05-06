# TODO-R1 — Code Test

> 작성: 2026-05-04 14:30 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 0건, Recommended 1건.

---

## 단위 테스트 결과

```
해당 없음 — TODO-R1 은 study 문서 신규 작성 (docs/storage/16_so100_vs_so101.md).
코드 파일 변경 없음 → pytest 실행 대상 없음.
```

## Lint·Type 결과

```
해당 없음 — .md 파일 단독 변경. ruff/mypy 대상 없음.
```

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| 1. upstream so_follower.py + so_leader.py 비교 — alias 동일 fact + 코드 라인 인용 | ✅ | §2: SO100Follower = SOFollower (L232), SO101Follower = SOFollower (L233). upstream 직접 Read 확인 완료. |
| 2. 모터 사양·gear ratio 차이 (있으면 명시, 없으면 동일) | ✅ | §3: "모터 사양·gear ratio 차이가 lerobot 코드 수준에서 SO100 vs SO101 분기 없음. 동일." 명시. 하드웨어 실제 차이(12V/7.4V gear)도 표로 정리 후 소프트웨어 무관 결론. |
| 3. calibration·motor_id 차이 검토 | ✅ | §4: motor_id 1~6 동일 매핑 명시. calibration 절차 동일 + calibration JSON 경로만 type 문자열 의존으로 달라짐 명시. |
| 4. robot_type 문자열 (so100_follower vs so101_follower) 차이 + lerobot 내부 dispatch | ✅ | §5: register_subclass 이중 등록 코드 인용 (config_so_follower.py L45/46). orin/lerobot/robots/utils.py 두 분기 모두 존재 확인. |
| 5. 본 프로젝트 채택 결정 명시: SO101 클래스 + robot_type "so101_follower"/"so101_leader" | ✅ | §6: "결정: SO101Follower / SO101Leader + robot_type 'so101_follower' / 'so101_leader'" 명시. 근거 5개 열거. |
| 6. R2 마이그레이션 영향 영역 (file·line 수준) | ✅ | §7: 직접 수정 대상 표 (hil_inference.py 다중 라인, measure_latency.py, smoke_test.py, inference_baseline.py, using_smolvla_example.py, record.py), Category B 영역 방침, 변경 불요 파일 표 포함. |
| 7. 데이터셋 ID svla_so100_pickplace 보존 명시 | ✅ | §8: "외부 HF Hub 자원, 이름 변경 X" 명시. §6 에도 동일 보존 결정 기재. |
| 8. lerobot-upstream-check + lerobot-reference-usage skill 정합 (Category A 직접 수정 X) | ✅ | docs/reference/ 수정 없음 (git status 확인). 01_implementation.md 에서 읽기·인용만 수행 선언. Coupled File Rule 해당 없음 (코드 파일 변경 없음). |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `docs/storage/16_so100_vs_so101.md` L248 및 요약 §3 | §7-1 파일 수 오기: L248 "**4개**" → 실제 6개 (표에 hil_inference.py·measure_latency.py·smoke_test.py·inference_baseline.py·using_smolvla_example.py·record.py 6파일 열거). 요약 §3 "총 5개 파일"도 불일치. R2 작업 시 표를 기준으로 삼으므로 실질 해악 낮으나, 수치 불일치가 혼선 유발 가능. R2 착수 전 수정 권장. |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경 (git status 확인). `.claude/` 미변경. |
| B (자동 재시도 X) | ✅ | `orin/lerobot/`, `dgx/lerobot/`, `pyproject.toml` 등 Category B 영역 변경 없음. |
| Coupled File Rules | ✅ | 코드 파일 변경 없음 → `03_orin_lerobot_diff.md` 갱신 불요. 해당 없음. |
| 옛 룰 | ✅ | `docs/storage/` 하위 bash 명령 예시 추가 없음. |

---

## 인용 코드 라인 정합 검증 결과

| 인용 | 실제 | 판정 |
|---|---|---|
| `SO100Follower = SOFollower (L232)` | upstream L232 확인 | ✅ |
| `SO101Follower = SOFollower (L233)` | upstream L233 확인 | ✅ |
| `SO100Leader = SOLeader (L158)` | upstream L158 확인 | ✅ |
| `SO101Leader = SOLeader (L159)` | upstream L159 확인 | ✅ |
| `config_so_follower.py L45 @register_subclass("so101_follower")` | L45 확인 | ✅ |
| `config_so_follower.py L46 @register_subclass("so100_follower")` | L46 확인 | ✅ |
| `config_so_follower.py L52/53 alias` | L52/53 확인 | ✅ |
| `config_so_leader.py L33/34 register_subclass` | L33/34 확인 | ✅ |
| `config_so_leader.py L40/41 alias` | L40/41 확인 | ✅ |
| `orin/lerobot/robots/utils.py L35-38 so100_follower 분기` | L35 확인 (elif 블록 4줄) | ✅ |
| `orin/lerobot/robots/utils.py L39-42 so101_follower 분기` | L39 확인 | ✅ |
| `orin/lerobot/teleoperators/utils.py L50-53 so100_leader 분기` | L50 확인 | ✅ |
| `orin/lerobot/teleoperators/utils.py L54-57 so101_leader 분기` | L54 확인 | ✅ |

---

## 배포 권장

READY_TO_SHIP — prod-test-runner 진입 권장.

study 문서 단독 변경이므로 prod-test 는 파일 존재·섹션 정합 정적 검증으로 충분 (AUTO_LOCAL 레벨).
