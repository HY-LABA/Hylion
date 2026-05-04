# TODO-D10 — Prod Test

> 작성: 2026-05-03 | prod-test-runner | cycle: 1

## Verdict

**`NEEDS_USER_VERIFICATION`**

자동 검증 전 항목 PASS. PHYS_REQUIRED 1건 (게이트 4 walkthrough) 시연장 대기.

---

## 배포 대상

- DGX (dgx/interactive_cli/flows/*.py + BACKLOG.md)

## 배포 결과

- 명령: `bash scripts/deploy_dgx.sh`
- 결과: 성공
- 전송 파일: `interactive_cli/flows/precheck.py`, `record.py`, `teleop.py` + configs JSON 2건
- speedup: 39.72 (rsync delta)
- DGX 수신 확인:
  - `precheck.py` 51226B (2026-05-04 16:04)
  - `record.py`   17736B (2026-05-04 16:03)
  - `teleop.py`    6538B (2026-05-04 16:02)

---

## 자동 비대화형 검증 결과

| 검증 | 명령 | 결과 |
|---|---|---|
| devPC py_compile (3파일) | `python3 -m py_compile teleop.py record.py precheck.py` | 3/3 PASS |
| devPC ruff lint | `ruff check teleop.py record.py precheck.py` | All checks passed! |
| devPC bash -n | `bash -n dgx/interactive_cli/main.sh` | PASS |
| devPC import smoke | `python3 -c "from flows.teleop import ...; from flows.record import ...; from flows.precheck import ..."` | 3모듈 ALL OK |
| devPC build_record_args 회귀 | `build_record_args(1, 'user/ds', 10)` single_task 기본값 + 커스텀 파라미터 | 기본값 True, 커스텀 True |
| DGX py_compile (3파일) | `ssh dgx python3 -m py_compile ...` | 3/3 PASS |
| DGX import smoke | `ssh dgx python3 -c "from flows.teleop import ...; ..."` | 3모듈 ALL OK |
| DGX build_record_args 시그니처 | inspect.signature — 파라미터 6개 포함 single_task | PASS |
| DGX build_record_args 회귀 | None 기본값 + 커스텀 단일 task | 기본값 True, 커스텀 True |
| DGX G1 grep | `grep "흐름:" teleop.py` `grep "다음 단계 (record"` `grep "강제 진행 (비권장)"` | 각 1건 확인 |
| DGX G2 grep | `grep "번호 선택" record.py` `grep "single_task.*None"` | 각 확인 |
| DGX G3 grep | `grep "다음 흐름:" precheck.py` `grep "4. 학습 분기"` | L1167+L1179 2곳 확인 |
| BACKLOG G4 grep | `grep "D10 G4" BACKLOG.md` | #10~#14 5건 모두 확인 |
| DGX menu walkthrough (flow1→flow2→flow3 종료) | `echo -e '2\n3'` pipe | flow1 DGX 선택·flow2 preflight 5/5 PASS·flow3 mode 정상 |
| DGX menu walkthrough (수집 mode → precheck → flow3 흐름) | `echo -e '2\n\n1\n2\n3'` pipe | precheck 옵션 2 → 4단계 흐름 출력 PASS + flow3 3단계 흐름 출력 PASS + flow4 비정상 종료 "강제 진행 (비권장)" PASS |

---

## DOD 자동 부합

| DOD 항목 | 자동 검증 | 결과 |
|---|---|---|
| G1-a: flow3_teleoperate 3단계 흐름 안내 출력 | yes — grep + walkthrough 육안 출력 | ✅ |
| G1-b: flow4 returncode==0 "Enter=다음 단계 (record + 학습)" | yes — grep 확인 | ✅ |
| G1-b: flow4 비정상 종료 "Enter=강제 진행 (비권장)" | yes — grep + walkthrough 출력 | ✅ |
| G1-c: 'r' 재시도 / Ctrl+C 종료 동작 보존 | yes — code-tester L151/L146~L149 확인 | ✅ |
| G2-a: flow6_record 학습 task 텍스트 UI 출력 ("번호 선택 [1~2]") | yes — grep 확인 | ✅ |
| G2-a: (1) 기본값 / (2) 커스텀 / 빈 입력 fallback 분기 | yes — import + build_record_args 회귀 테스트 | ✅ |
| G2-b: build_record_args 시그니처 `single_task: str | None = None` | yes — inspect.signature DGX 확인 | ✅ |
| G2-b: None 시 SINGLE_TASK_MAP fallback | yes — 회귀 테스트 기본값 True | ✅ |
| G2-b: flow6_record → build_record_args single_task 전달 | yes — code-tester L421~427 확인 | ✅ |
| G3: 옵션 2 분기 4단계 흐름 안내 | yes — grep + walkthrough 출력 | ✅ |
| G3: 옵션 1 완료 경로 4단계 흐름 안내 | yes — grep L1167 확인 | ✅ |
| G3: return "proceed" / "cancel" 동작 보존 | yes — code-tester 확인 | ✅ |
| G4: BACKLOG 07 #10~#14 신규 5건 | yes — grep "D10 G4" 5건 확인 | ✅ |
| D6·D7·D8·D9 다른 함수 보존 | yes — DGX import smoke 전 함수 정상 | ✅ |
| mode.py flow6_record 호출 체인 정합 | yes — code-tester 확인 + DGX 배포 동일 파일 | ✅ |
| 게이트 4 walkthrough — G1·G2·G3 사용자 실물 확인 | no — PHYS_REQUIRED | → verification_queue |

---

## 사용자 실물 검증 필요 사항 (verification_queue 추가됨)

1. **[D10-1] 게이트 4 통합 walkthrough — G1·G2·G3 효과 직접 확인 (PHYS_REQUIRED)**
   - D9 까지의 precheck 흐름 + D10 신규 UI 를 통합하여 SO-ARM + 카메라 DGX 직결 환경에서 전체 walkthrough:
     - G1: flow3 텔레오퍼레이션 시작 시 "흐름: 1. Enter ... / 2. Ctrl+C *정상 종료* / 3. 종료 후 다음 단계" 출력 확인
     - G1-b: teleop 후 flow4 — 정상 종료 시 "Enter=다음 단계 (record + 학습)", 비정상 시 "Enter=강제 진행 (비권장)" 출력 확인
     - G2: flow6 record 진입 시 "학습 task 텍스트" UI — (1) 기본값 / (2) 커스텀 입력 분기 동작 확인
     - G3: precheck 옵션 2 선택 시 "다음 흐름: 1.teleop / 2.data_kind → record / 3.transfer / 4.학습 분기" 출력 확인
   - D9 효과 (calibrate prompt 기본값 ports.json 반영) 와 함께 e2e 풀 사이클 확인 권장

---

## CLAUDE.md 준수

- Category B 영역 (`dgx/interactive_cli/flows/*.py`, `BACKLOG.md`) 변경: Category B 비해당 (`orin/lerobot/`, `dgx/lerobot/`, `pyproject.toml`, `setup_env.sh`, `deploy_*.sh`, `.gitignore` 미변경)
- deploy_dgx.sh 자체: 스크립트 내용 미변경 — Category B 해당 없음
- 자율 영역만 사용: yes (rsync 배포 + SSH read-only + pytest/python-c 범주)
- docs/reference/ 변경: 0건
- orin/lerobot/ 변경: 0건
- Coupled File Rule: 불해당 (pyproject.toml·orin/lerobot/ 미변경)
