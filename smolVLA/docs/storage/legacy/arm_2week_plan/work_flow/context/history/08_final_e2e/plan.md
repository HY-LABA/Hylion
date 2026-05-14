# Execution Plan — 08_final_e2e

> 최초 작성: 2026-05-04 | planner
> 갱신: 2026-05-05 | planner — Wave 1.5 (그룹 U) 신규 추가, DAG 재계산, Wave 1 완료 마킹

---

## 경로 실존 확인 메모 (spec 언급 파일 vs 실제 코드베이스)

| 항목 | spec 기재 | 실 존재 여부 | 처리 |
|---|---|---|---|
| R1 upstream so_follower.py | `lerobot/robots/so_follower/so_follower.py` | 실 경로: `docs/reference/lerobot/src/lerobot/robots/so_follower/so_follower.py` | task-executor 가 실 경로 사용 |
| R1 upstream so_leader.py | `teleoperators/so_leader/so_leader.py` | 실 경로: `docs/reference/lerobot/src/lerobot/teleoperators/so_leader/so_leader.py` | task-executor 가 실 경로 사용 |
| R1 SO100Follower / SO101Follower | 별도 클래스 가정 | 실제: `SO100Follower = SOFollower`, `SO101Follower = SOFollower` (alias) — 두 클래스 인터페이스 동일 | R1 study 에서 "alias 동일 인터페이스" 명시. R2 마이그레이션은 import 이름 교체 + robot_type 문자열 교체로 충분 |
| R2 `orin/lerobot/scripts/lerobot_*.py` SO100 언급 | `lerobot_record.py` L310 `so_leader.SO100Leader` L311 `so_leader.SO101Leader` (docstring 예제) | 실존 확인. 단 현재 SO100Leader 와 SO101Leader 가 병기된 타입 힌트 형태 — docstring 교체 시 SO101 단독으로 좁히기 가능하나 Category B | task-executor 가 lerobot-upstream-check skill 적용 후 교체 여부 판단 |
| R2 `dgx/scripts/smoke_test.sh` SO100 언급 여부 | "해당 시" 조건부 | 실존 확인. grep 결과 SO100/SO101 미포함 (로봇 타입 직접 언급 없음) | R2 scope 에서 제외 — smoke_test.sh 수정 불요 |
| H2 `orin/config/cameras.json` | 실존 | 실존 확인 | 정상 |
| N1 공통 helper 위치 | `interactive_cli/common/prompt.py` 또는 각 main.sh | orin: `orin/interactive_cli/flows/` 디렉터리 존재. dgx: `dgx/interactive_cli/flows/` 존재. `common/` 서브디렉터리는 미존재 | task-executor 가 `flows/` 하위 공통 파일 (`flows/_back.py` 또는 각 flow 인라인) 선택 — `common/` 신규 디렉터리 생성 시 Category C 해당. 기존 `flows/` 하위 파일로 수용하면 Category C 불요 |
| I2 `orin/tests/measure_inference_memory.py` | 신규 작성 대상 | 미존재 — 정상 (신규) | (신규) 표기 |
| R1 `docs/storage/16_so100_vs_so101.md` | 신규 작성 대상 (게이트 1 walkthrough 에서 이관) | 실 경로: `docs/lerobot_study/08_so100_vs_so101.md` — lerobot_study 컨벤션 적용 이관 완료 | 정상 (이관 후 갱신) |
| I2 `docs/storage/17_orin_inference_memory.md` | 신규 작성 대상 | 미존재 — 정상 (신규) | (신규) 표기 |
| **U1 audit 산출물** `docs/work_flow/context/interactive_cli_audit.md` | 신규 작성 대상 | 미존재 — 정상 (신규) | (신규) 표기 |
| **U1 점검 대상** `dgx/interactive_cli/flows/` (10 파일) | `entry`, `env_check`, `mode`, `precheck`, `data_kind`, `record`, `teleop`, `training`, `transfer`, `_back` | 실존 확인 (ls 결과) | 정상 |
| **U1 점검 대상** `orin/interactive_cli/flows/` (4 파일) | `entry`, `env_check`, `inference`, `_back` | 실존 확인 (ls 결과) | 정상 |
| **U1 점검 대상** `dgx/interactive_cli/main.sh` + `orin/interactive_cli/main.sh` | main.sh 2 | 실존 확인 (ls 결과) | 정상 |
| **U1 점검 대상** `dgx/interactive_cli/README.md` + `orin/interactive_cli/README.md` | README 2 | 실존 확인 (ls 결과) | 정상 |
| **U1 점검 대상** `dgx/interactive_cli/configs/` | cameras.json, node.yaml, ports.json | 실존 확인 (ls 결과 3 파일) | 정상 |
| **U1 점검 대상** `orin/interactive_cli/configs/` | node.yaml | 실존 확인 (ls 결과 1 파일). spec 언급 "있다면" 조건부 — 존재하나 단 1 파일 | 정상 (node.yaml 만 존재 — configs/ 섹션 분량 얇음) |

**핵심 정정 메모 — R2 Category B 범위 최소화**:
`lerobot_record.py` L310-311 의 `SO100Leader | SO101Leader` 는 타입 힌트 형태로 두 클래스를 병기. 이것을 SO101 단독으로 교체하면 기존 SO100 사용자 지원 차단 위험. R2 에서 docstring 교체 대신 **실 활성 코드 (`hil_inference.py`, tests/, examples/)의 import/인스턴스화** 교체에 집중하고 `orin/lerobot/scripts/` 은 최소 변경 권장. code-tester 가 Category B 영역 scope 를 엄격하게 판단.

---

## DAG

```
[Wave 1 — S + R + H + N 그룹] ✅ 완료 (2026-05-04)

  S1 ✅  S2 ✅  R1 ✅  H1 ✅  N1 ✅  (동시 시작, 5건)
    ↓
  R2 ✅  H2 ✅  N1 MINOR cycle 1 ✅
    ↓
  R3 ✅  N2 ✅
    ↓
  Wave 1 전체 (9 todo) COMPLETED

      ↓
  Phase 3 게이트 1 ✅ 통과 (2026-05-04 정합 검증 + 사용자 승인)
  + DGX 시연장 도착 확인 ✅ (2026-05-04 C1 셋업 진행 중)
      ↓

[Wave 1.5 — U 그룹 (Wave 2 차단)]  ← 현재 진입 지점 (2026-05-05)

  [U1 — Phase 2 자율] 🟡 진입 대기
    task-executor: dgx + orin interactive_cli 전체 audit 보고서 작성
    → 산출물: docs/work_flow/context/interactive_cli_audit.md (신규)
    → code-tester: 점검 대상 커버리지 + 6 컬럼 정합 + 인용 정확도 검증
    → prod-test-runner: 보고서 파일 존재 + 형식 정합 (AUTO_LOCAL)
    → spec 본문 U1 [x] 완료 마킹
      ↓ U1 PASS

  [Phase 1 재진입 게이트] ← awaits_user
    메인 Claude 가 사용자에게 interactive_cli_audit.md 보고서 내용 제시
    사용자가 발견 항목별 우선순위 결정 (즉시 / BACKLOG 이관 / 기각)
    "즉시" 항목 목록 확정
      ↓ 사용자 우선순위 결정 완료

  [U2~Un — Phase 2 자율] — placeholder (본 시점 미정)
    메인이 "즉시" 항목을 묶음 분해 → spec 에 U2~Un 신규 todo 추가
    → /start-spec 재호출 → Phase 2 자동화 정정
    → "BACKLOG 이관" 항목 → BACKLOG.md 08 섹션 추가 (W1 확장)
    → "기각" 항목 → audit 보고서 사유 기록만
    → U2~Un 전체 code-tester + prod-test-runner 정상 흐름
      ↓ U2~Un 전체 PASS

[Wave 2 재개 — C 그룹, PHYS_REQUIRED]

  C1 진행 중 (§7 작성 완료) — calibrate 단계 재개
    C1 calibrate: 사용자 시연장 calibrate (follower + leader, 새 ID)
    → prod-test-runner: C1 PHYS 상태 확인 (SSH ls /dev/video*)
      ↓ C1 완료

  C2 lego pick-place 데이터 수집 (사용자 운영)
    → /verify-result "C2 완료 N episodes"
      ↓ Wave 2 PASS

[Wave 3 — T 그룹, SSH_AUTO 순차]

  T1 (DGX lerobot-train --steps=2000 --save_freq=1000 백그라운드)
    ↓ T1 PASS (ckpt 001000/ + 002000/ 존재)
  T2 (sync_ckpt_dgx_to_orin.sh — DGX→devPC→Orin rsync)
    ↓ Wave 3 PASS

[Wave 4 — I 그룹, PHYS_REQUIRED + AUTO_LOCAL 병렬]

  I1 (Orin + SO-101 추론 50~100 step — PHYS_REQUIRED)
  ||
  I2 (measure_inference_memory.py 신규 + 측정 — AUTO_LOCAL + SSH_AUTO)
    ↓ Wave 4 PASS
    ↓ Phase 3 게이트 2

[Wave 5 — W 그룹, 자율 병렬]

  W1 (BACKLOG 마킹 — U2~Un "BACKLOG 이관" 항목 포함)
  ||
  W2 (reflection 입력 정리)
    ↓ /wrap-spec
```

---

## 병렬 그룹

### Wave 1 — 완료 (9 todo 전체) ✅

Wave 1 dispatch 기록: S1·S2·R1·H1·N1 동시 시작 → R2·H2 병렬 → R3·N2 병렬 → 전체 완료.

### Wave 1.5 — 현재 활성

| 단계 | 내용 | 병렬 가능성 |
|---|---|---|
| U1 단독 | audit 보고서 작성 (단일 task-executor) | 독립 — 다른 Wave 2+ 와 파일 독립이지만 Wave 2 진입 차단 |
| Phase 1 재진입 | 사용자 우선순위 결정 | awaits_user — 단독 (병렬 X) |
| U2~Un | 정정 todo 분해 후 결정 (Phase 1 재진입 완료 후) | 정정 항목 간 독립성에 따라 결정 (본 시점 미확정) |

**현재 dispatch 가능한 단일 todo**: U1 (단독 즉시 dispatch 가능).

### Wave 4 — I 그룹 부분 병렬 (기존 유지)

| 분리 전략 | 내용 |
|---|---|
| I2 선행 작성 (devPC) | measure_inference_memory.py 코드 + 17_orin_inference_memory.md §1·§2 구조 devPC 에서 선작성. code-tester AUTO_LOCAL 통과. |
| I1 시연장 실행 | Orin + SO-101 직결 추론 50~100 step (사용자 운영) |
| I2 측정 병행 | I1 실행 중 measure_inference_memory.py 시연장에서 동시 실행 → §2 실측값 채움 |

### Wave 5 — W 그룹 완전 병렬 (기존 유지)

W1 + W2 완전 병렬 (BACKLOG.md vs ANOMALIES.md/log.md 독립). 단 W1 은 U2~Un "BACKLOG 이관" 항목도 포함하므로 U 그룹 완전 완료 후 실행.

---

## 확신 가정 (병렬 진행 OK)

1. **upstream SO100 = SO101 alias 확정** (Wave 1 완료 — R1 실증): `so_follower.py` L232-233 확인. R2 마이그레이션 완료.

2. **Wave 1 전체 PASS 확정**: S1·S2·R1·R2·R3·H1·H2·N1·N2 모두 code-tester + prod-test AUTOMATED_PASS. spec 본문 [x] 마킹 완료.

3. **U1 코드 수정 X**: audit 보고서 작성만 (docs/work_flow/context/ 하위 신규 파일) — Category A/B/C 저촉 없음. 즉시 dispatch 가능.

4. **U1 산출물 경로 Category C 불요**: `docs/work_flow/context/` 기존 디렉터리 — 신규 디렉터리 생성 불요. awaits_user 없음.

5. **dgx flows 10 실존 확인**: `_back`, `data_kind`, `entry`, `env_check`, `mode`, `precheck`, `record`, `teleop`, `training`, `transfer` — ls 실 확인.

6. **orin flows 4 실존 확인**: `_back`, `entry`, `env_check`, `inference` — ls 실 확인.

7. **dgx configs 3 실존 확인**: `cameras.json`, `node.yaml`, `ports.json` — ls 실 확인.

8. **orin configs 1 실존 확인**: `node.yaml` — ls 실 확인. (dgx 대비 sparse — audit 에서 분량 차이 반영)

9. **N1 helper 위치 확정**: `flows/_back.py` 신규 파일 (orin·dgx 양쪽) 로 이미 구현. Category C 회피 완료.

10. **C1 §7 작성 완료 + 시연장 셋업 부분 완료**: Seeed 매트·카메라 마운트·lego pick-place 환경 확인. calibrate 단계 U 후 재개 대기.

11. **T2 장기 실행**: 07 사이클 906MB 전송 검증 완료. 재활용 가능.

12. **HF Hub 캐시**: 07 T1 완료 — svla_so100_pickplace + smolvla_base DGX 캐시 존재.

13. **I2 tegrastats sudo 불요**: Jetson tegrastats 일반 사용자 권한 실행 가능.

---

## 확인 필요 가정 (awaits_user)

### 신규 — Wave 1.5 U 그룹

| TODO | 질문 | 시점 | 영향 |
|---|---|---|---|
| U2~Un 정의 | U1 audit 보고서 완료 후 메인이 사용자에게 발견 항목별 우선순위 제시 (즉시 / BACKLOG 이관 / 기각). 사용자 결정 완료 전 U2~Un dispatch 불가 | U1 code-tester PASS 직후 | Wave 2 진입 시점 결정 |

**U1 자체는 awaits_user X** — audit 보고서 작성은 코드 수정 없는 자율 작업. 즉시 dispatch 가능.

### 기존 유지

| TODO | 시점 | 질문 |
|---|---|---|
| T1 | Wave 3 진입 전 | DGX lerobot-train --steps=2000 장기 실행 (1.5~3h) 비대화형 백그라운드 OK? (a) prod-test-runner 자율 실행, (b) 사용자 직접 실행 후 /verify-result |

**결론**: Wave 1.5 에서 사용자 결정 필요 사항은 **U1 완료 후 우선순위 결정 1건** 뿐. U1 자체는 즉시 dispatch 가능.

---

## U2~Un 묶음 분해 전략 (planner 사전 가이드)

U1 audit 보고서 완료 후 Phase 1 재진입 시 메인이 "즉시" 항목을 묶음으로 분해해야 한다. 아래 4 옵션의 trade-off 와 권장안을 제시한다.

### 옵션 비교

| 옵션 | 묶음 방식 | todo 수 | 장점 | 단점 |
|---|---|---|---|---|
| A — 카테고리별 | UX 묶음 / UI 묶음 / 정합성 묶음 | 최대 3 | 영향 영역 명확 분리. code-tester 가 각 카테고리 기준 정합 검증 용이 | 동일 파일 중복 수정 가능 (UI+정합성 이 같은 파일 건드릴 수 있음) |
| B — flow 별 | dgx record 묶음 / dgx training 묶음 / dgx precheck 묶음 / orin inference 묶음 ... | M (flow 수 의존) | 파일 충돌 최소화. 각 todo 가 단일 flow 파일만 수정 → 병렬화 극대화 | todo 수 많아짐. 동일 패턴 반복 정정이 여러 todo 로 쪼개져 context 중복 |
| C — severity 별 | Critical 묶음 / Major 묶음 / Minor·Nit 묶음 | 최대 3 | 중요도 순 처리 보장. Critical 먼저 완료 확인 후 Major 진행 | 같은 파일에 Critical+Minor 혼재 시 파일 수정 2회 (비효율) |
| D — 혼합 | Critical 단독 → 나머지 카테고리 또는 flow 별 | 3~5 | Critical 즉시 차단 해소. 나머지는 파일 분리 기반 병렬화 | 분해 복잡도 증가. 메인의 판단 부담 |

### 권장안: **옵션 D (혼합)** — 단 audit 결과 따라 메인이 최종 판단

**근거**:
- C0~C0e ad-hoc 5건의 패턴을 보면 critical 이슈 (calibration JSON 미검증 → C0e) 와 UX 이슈 (episode_time_s 60s → C0) 가 혼재. Critical 은 즉시 차단 해소가 우선.
- 나머지는 **flow 별 묶음 (옵션 B 방향)** 이 파일 충돌 최소화 + code-tester 검증 범위 명확화에 유리. `dgx/interactive_cli/flows/` 파일들이 서로 독립적이어서 병렬 dispatch 가능.
- 단, severity 분포가 Minor·Nit 위주로 나오면 **옵션 A (카테고리별 3 묶음)** 이 todo 수 최소화 측면에서 더 효율적.

**Phase 1 재진입 시 메인 판단 흐름**:
1. audit §3 severity 분포 확인
2. Critical 존재 시 → D: Critical 단독 todo (U2) 먼저 dispatch
3. Critical 없거나 완료 후 나머지:
   - "즉시" 항목이 3개 flow 이하 → A 옵션 (카테고리별 3 묶음)
   - "즉시" 항목이 4개 flow 이상 → B 옵션 (flow 별 분리, 병렬화)
4. 사용자가 특정 flow 를 묶어서 처리 원하면 그 판단 우선

**사용자 결정이 우선** — 위는 권장안 (reference only).

---

## Phase 3 검증 큐 후보

### 게이트 1 — Wave 1 (S·R·H·N) ✅ 완료

| TODO | 환경 레벨 | 검증 결과 |
|---|---|---|
| S1 | `AUTO_LOCAL` | AUTOMATED_PASS (2026-05-04) |
| S2 | `AUTO_LOCAL` | AUTOMATED_PASS (2026-05-04) |
| R1 | `AUTO_LOCAL` | AUTOMATED_PASS (2026-05-04) |
| R2 | `AUTO_LOCAL` | AUTOMATED_PASS (2026-05-04) |
| R3 | `SSH_AUTO` | AUTOMATED_PASS (2026-05-04) |
| H1 | `AUTO_LOCAL` | AUTOMATED_PASS (2026-05-04) |
| H2 | `AUTO_LOCAL` | AUTOMATED_PASS (2026-05-04) |
| N1 | `AUTO_LOCAL` | AUTOMATED_PASS (2026-05-04, MINOR cycle 1 포함) |
| N2 | `SSH_AUTO` | AUTOMATED_PASS (2026-05-04) |

**게이트 1 PASS 확정** (사용자 승인 2026-05-04).

---

### Wave 1.5 — U 그룹

| TODO | 환경 레벨 | 검증 방식 | 비고 |
|---|---|---|---|
| U1 | `AUTO_LOCAL` | code-tester: 점검 대상 파일 커버리지 (dgx flows 10 + orin flows 4 + main.sh 2 + README 2 + configs/) + 6 컬럼 정합 + file_path:line_number 인용 정확도 + severity 정의 일관 적용. prod-test-runner: 보고서 파일 존재 + §1~§4 섹션 구조 정합 | 코드 수정 X — 보고서 파일 단독 산출 |
| U2~Un | 미정 | U1 완료 + 사용자 우선순위 결정 후 정의 | 정정 유형에 따라 `AUTO_LOCAL` 또는 `SSH_AUTO` 예상. PHYS_REQUIRED 가능성 낮음 (interactive-cli 정정은 devPC 자율 검증 범위) |

---

### 게이트 2 전 — Wave 2~4 (C·T·I)

| TODO | 환경 레벨 | 검증 방식 | 비고 |
|---|---|---|---|
| C1 | `PHYS_REQUIRED` | 사용자 육안 — 시연장 셋업 (§7 작성 완료) + calibrate 완료 확인. SSH 가능 시 dgx `ls /dev/video*` `lsusb` 확인 | calibrate 단계 U 후 재개 |
| C2 | `PHYS_REQUIRED` | 사용자 육안 — episode 개수 정합 + 사용자 `/verify-result "C2 완료 N episodes"` | 시연장 직접 운영 |
| T1 | `SSH_AUTO` | prod-test-runner — DGX SSH: ckpt `001000/`·`002000/` 존재 + loss log exit 0 확인 | 장기 실행 (1.5~3h) 백그라운드. T1 dispatch 전 사용자 동의 1건 (awaits_user 표 참조) |
| T2 | `SSH_AUTO` | prod-test-runner — Orin SSH: rsync 완료 + ckpt 파일 size 비교 (헤더 8byte 확인) | 07 T3 검증 패턴 재활용 |
| I1 | `PHYS_REQUIRED` | 사용자 운영 — 시연장 Orin + SO-101 + 카메라 직결 추론 50~100 step. 동영상/사진 + 정성 평가 | 07 BACKLOG #9 연계 |
| I2 (코드) | `AUTO_LOCAL` | code-tester — measure_inference_memory.py py_compile + tegrastats 파서 정합 | — |
| I2 (측정) | `SSH_AUTO` | prod-test-runner — Orin SSH: measure_inference_memory.py dry-run (측정 스크립트 실행 가능 확인) | 실측값은 I1 병행 시 채움 |

**게이트 2 통과 조건**: T1·T2 SSH_AUTO AUTOMATED_PASS. C1·C2·I1 사용자 PHYS_REQUIRED 확인 완료. I2 AUTO_LOCAL PASS + SSH_AUTO dry-run PASS.

---

## Category 분류

### Category B 해당 todo

| TODO | Category B 영역 | 처리 방침 | 상태 |
|---|---|---|---|
| R2 | `orin/lerobot/scripts/lerobot_*.py` docstring 수정 | 자율 1 cycle dispatch 완료. code-tester READY_TO_SHIP + prod-test AUTOMATED_PASS. | ✅ 완료 |

### Category C 검토 결과

| 항목 | 결론 |
|---|---|
| N1 공통 helper 신규 위치 | `flows/_back.py` 신규 파일로 구현 완료. Category C 불요. |
| I2 orin/tests/ 하위 신규 파일 | `orin/tests/` 기존 디렉터리 존재 — Category C 불요 |
| R1 docs/lerobot_study/ 하위 신규 파일 | `docs/lerobot_study/` 기존 디렉터리 존재 — Category C 불요 |
| I2 docs/storage/ 하위 신규 파일 | `docs/storage/` 기존 디렉터리 존재 — Category C 불요 |
| **U1 docs/work_flow/context/ 하위 신규 파일** | `docs/work_flow/context/` 기존 디렉터리 존재 — Category C 불요 |

---

## 스킬 의존 매핑

| TODO | 적용 스킬 |
|---|---|
| R1 | `lerobot-upstream-check`, `lerobot-reference-usage` ✅ 완료 |
| R2 | `lerobot-upstream-check` (Category B 판정), `claude-md-constraints` ✅ 완료 |
| R3 | `orin-deploy-procedure` ✅ 완료 |
| N2 | `orin-deploy-procedure` ✅ 완료 |
| U1 | `claude-md-constraints` (Category A/B/C 저촉 없음 확인) |
| T1·T2 | `orin-deploy-procedure` (DGX/Orin SSH 검증) |
| I2 (harness) | `harness-engineering-principles` (측정 검증 프레임워크 적용) |
| W1·W2 | `claude-md-constraints` (BACKLOG·ANOMALIES 갱신 정책) |

---

## dispatch 순서 — 구체

### Wave 1 ✅ 완료

전체 완료 (2026-05-04). S1·S2·R1·R2·R3·H1·H2·N1·N2 AUTOMATED_PASS. 상세 log: `context/log.md` 참조.

### Wave 1.5 — 현재 활성

```
[즉시 dispatch 가능 — 1건]
task-executor: U1
  → 점검 대상:
      dgx/interactive_cli/flows/ (10 파일: entry, env_check, mode, precheck,
          data_kind, record, teleop, training, transfer, _back)
      dgx/interactive_cli/main.sh
      dgx/interactive_cli/README.md
      dgx/interactive_cli/configs/ (cameras.json, node.yaml, ports.json)
      orin/interactive_cli/flows/ (4 파일: entry, env_check, inference, _back)
      orin/interactive_cli/main.sh
      orin/interactive_cli/README.md
      orin/interactive_cli/configs/ (node.yaml)
  → 산출물: docs/work_flow/context/interactive_cli_audit.md
  → 코드 수정 X (audit 만)

→ U1 task-executor 완료:
code-tester: U1 (AUTO_LOCAL — 커버리지 + 6컬럼 정합 + 인용 정확도)
  → READY 시: prod-test-runner U1 (파일 존재 + §1~§4 구조 확인)
  → spec 본문 U1 [x] 완료 마킹

→ U1 PASS 후:
[Phase 1 재진입 — awaits_user]
메인 Claude: 사용자에게 audit 보고서 제시
사용자: 항목별 우선순위 결정 (즉시 / BACKLOG 이관 / 기각)

→ 사용자 결정 완료:
메인: "즉시" 항목 묶음 분해 (D 권장안 참조)
→ spec 에 U2~Un 신규 todo 추가
→ /start-spec 재호출 → Phase 2 U2~Un 자동화

→ U2~Un 전체 PASS → Wave 2 재개
```

### Wave 2 재개 (PHYS_REQUIRED — 사용자 운영)

```
[U 그룹 완료 확인 후]
→ 사용자 시연장 calibrate 재개 (C1 calibrate 단계)
  → follower + leader calibrate (새 ID, force_new_id=True)
  → calibration.json 갱신 + lerobot JSON 실존 검증 (C0e 로직)
→ prod-test-runner: C1 PHYS 확인 (SSH dgx ls /dev/video* + lsusb)
→ C2: 사용자 lego pick-place 데이터 수집 (50+ episodes)
→ 사용자 /verify-result "C2 완료 N episodes"

→ Wave 2 완료 → Wave 3 진입
```

### Wave 3 (SSH_AUTO — 순차)

```
[T1 dispatch 전 — 사용자 장기 실행 동의 1건 확인]
→ 동의 후:
prod-test-runner: T1 (DGX SSH — lerobot-train 백그라운드)
  → ckpt 001000/ + 002000/ 존재 확인 → T1 PASS

→ T1 PASS 후:
prod-test-runner: T2 (sync_ckpt_dgx_to_orin.sh 실행)
  → Orin ckpt size 비교 + safetensors 헤더 검증 → T2 PASS

→ Wave 3 완료 → Wave 4 진입
```

### Wave 4 (PHYS_REQUIRED + AUTO_LOCAL 병렬)

```
[선행 — devPC 자율]
task-executor: I2 코드 (measure_inference_memory.py 신규 + docs §1~§3 구조)
→ code-tester: I2 AUTO_LOCAL (py_compile + tegrastats 파서)
→ prod-test-runner: I2 SSH_AUTO dry-run (Orin)

[시연장 실물 — 사용자 운영]
→ I1: 사용자 Orin + SO-101 + 카메라 직결 추론 (T2 ckpt 로드)
→ I2 측정: I1 중 measure_inference_memory.py 병행

→ 사용자 /verify-result "I1 추론 정성 + I2 메모리 측정 완료"
→ 게이트 2
```

### Wave 5 (자율 병렬)

```
[동시 dispatch — U2~Un 완료 확인 후]
task-executor: W1 (BACKLOG.md 08 섹션 마킹 + U2~Un "BACKLOG 이관" 항목 추가)
task-executor: W2 (ANOMALIES.md 08 섹션 + log.md 점검)

→ W1·W2 code-tester (AUTO_LOCAL) PASS
→ /wrap-spec
```

---

## 잠재 차단 위험

| 위험 | 영향 | 대응 |
|---|---|---|
| U1 audit 발견 사항 광범위 (100+ 건) | Phase 1 재진입 사용자 결정 부담 | U1 DOD §3 severity 분포 요약으로 사용자 결정 보조. §4 우선순위 결정 prompt 구조화 |
| U2~Un 정정 중 C0~C0e 와 충돌 | ad-hoc 5건이 이미 파일 수정 — audit 기준 시점 (최신 코드 기준) | U1 task-executor 가 현재 코드 상태 기준으로 audit (C0~C0e 정정 후 상태). 이전 상태 재정정 X |
| calibrate 재개 시 new ID 또는 JSON 경로 이슈 | C1 차단 | C0e 로직 (is_file() 검증) 이미 적용됨. 시연장 재calibrate 시 force_new_id=True 확인 |
| HF Hub 차단 (시연장 학교 WiFi) | T1 학습 데이터셋 접근 | 07 사이클 캐시 활용. 네트워크 불필요 가능성 높음 |
| SO101 클래스 인터페이스 추가 차이 | Wave 3+ 실 운영 시 발견 | R1 study alias 동일 확인 완료. 실 위험 낮음. 발견 시 사용자 보고 |
| wrist 광각 카메라 분포 차이 | T1 수렴 부진 / I1 추론 부정확 | BACKLOG #1 등록. 본 사이클 정성 평가로 판단. 부진 시 09 이관 |
| tegrastats 파싱 JetPack 6.2 포맷 차이 | I2 측정 오파싱 | I2 코드 작성 시 JetPack 6.2 출력 포맷 참조 (`docs/reference/nvidia_official/`) |
