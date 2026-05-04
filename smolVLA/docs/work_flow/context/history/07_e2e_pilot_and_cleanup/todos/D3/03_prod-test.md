# TODO-D3 — Prod Test

> 작성: 2026-05-03 | prod-test-runner | cycle: 1

## Verdict

**`NEEDS_USER_VERIFICATION`**

AUTO_LOCAL + SSH_AUTO 자동 검증 전 항목 PASS. PHYS_REQUIRED 항목 (SO-ARM·카메라 직결 실검증) 은 시연장 이동 시 사용자 검증 필요.

---

## 배포 대상

- DGX (`dgx/scripts/check_hardware.sh` 단일 파일)

## 배포 결과

- **파일 동기화 방법**: MD5 사전 비교 → devPC 와 DGX 원격 파일 MD5 일치 확인 (`e3f4878d258952bbfb71f5f0881cf4d4`) — 명시적 rsync 불필요 (이미 동기화 상태)
- **결과**: 동기화 완료 (파일 일치)
- **Category B 해당 여부**: `check_hardware.sh` 는 `deploy_*.sh`, `setup_env.sh`, `orin/lerobot/`, `dgx/lerobot/`, `pyproject.toml`, `.gitignore` 어디에도 해당 없음 — Category B 비해당, 자율 배포 조건 충족

---

## 자동 비대화형 검증 결과

### A. devPC 정적 (AUTO_LOCAL)

| 검증 항목 | 명령 | 결과 |
|---|---|---|
| bash -n 문법 검증 | `bash -n dgx/scripts/check_hardware.sh` | exit 0 — PASS |
| X4·X5 잔재 0건 | `grep -n "X4\|X5" dgx/scripts/check_hardware.sh` | 매치 0건 — PASS |
| setup_train_env.sh 갱신 메시지 4곳 | `grep -n "setup_train_env.sh" dgx/scripts/check_hardware.sh` | L34, L249, L282, L345 — 4곳 확인 PASS |
| 5-step 함수 5건 | `grep -n "^step_.*() {" dgx/scripts/check_hardware.sh` | step_venv·step_dialout·step_soarm_port·step_v4l2·step_cameras — 5건 PASS |

### B. DGX SSH 비대화형 (SSH_AUTO)

| 검증 항목 | 명령 | 결과 |
|---|---|---|
| SSH 연결 | `ssh dgx "echo SSH_OK && hostname"` | SSH_OK / spark-8434 — PASS |
| 파일 동기화 확인 | MD5 비교 | devPC = DGX (e3f4878d...) — 동기화 완료 |
| DGX bash -n | `ssh dgx "bash -n ~/smolvla/dgx/scripts/check_hardware.sh"` | exit 0 — PASS |
| X4·X5 잔재 DGX 측 | `ssh dgx 'grep -n "X4\|X5" ...'` | 매치 0건 — PASS |
| setup_train_env.sh 메시지 DGX 측 | `ssh dgx 'grep -n "setup_train_env.sh" ...'` | 4곳 확인 — PASS |
| check_hardware.sh 실 실행 | `ssh dgx 'bash ~/smolvla/dgx/scripts/check_hardware.sh ...'` | 아래 상세 참조 |

#### 실 실행 결과 (SO-ARM 미연결 환경)

```
[PASS] venv: python: /home/laba/smolvla/dgx/.arm_finetune/bin/python3
[PASS] dialout: 사용자 laba 는 dialout 그룹 멤버
[FAIL] soarm_port: 포트 미발견 — SO-ARM USB 연결 확인 필요 (/dev/ttyACM* or /dev/ttyUSB*)
[FAIL] v4l2: v4l2 장치 미발견 — 카메라 USB 연결 확인 필요 (/dev/video*)
[FAIL] cameras: 카메라 미발견 — USB 카메라 연결 확인 필요
[DONE] 3개 FAIL / 2개 PASS
해결 힌트 블록 출력 확인 (setup_train_env.sh §3-c 안내 포함)
exit code: 1
```

검증 결과 분석:
- Step 1 (venv) PASS: venv 활성화 정상
- Step 2 (dialout) PASS: laba 사용자 dialout 그룹 멤버 확인
- Step 3 (soarm_port) FAIL: SO-ARM 미연결 → 안내 메시지 정상 출력, 전체 중단 없이 계속 진행 — **설계 의도 부합**
- Step 4 (v4l2) FAIL: 카메라 미연결 → 안내 메시지 정상 출력, 전체 중단 없이 계속 진행 — **설계 의도 부합**
- Step 5 (cameras) FAIL: 카메라 미연결 (import 오류 아님, 카메라 0개 검출) → 안내 메시지 정상 출력 — **설계 의도 부합**
- `set -e` 미사용 동작 확인: 3개 FAIL 누적 후 finalize_output 까지 전체 진행 정상
- exit code = 1 (overall_exit=1 패턴 정상, 중단 없이 FAIL 누적)
- 해결 힌트 블록: `setup_train_env.sh §3-c` 안내 포함 — 07 갱신 반영 확인

---

## DOD 자동 부합

| DOD 항목 | 자동 검증 가능 | 결과 |
|---|---|---|
| 1. bash -n PASS | yes — bash -n (devPC + DGX 양측) | ✅ exit 0 |
| 2. 시연장 이동 시 즉시 사용 가능 (에러 메시지 명확, 한 줄 실행) | yes (부분) — SSH 실행 + 출력 분석 | ✅ 각 FAIL 에 대응 명령 안내 존재 확인, set -e 미사용으로 step 별 FAIL 이 전체 중단 없이 누적, 해결 힌트 블록 포함 |
| 3. PHYS_REQUIRED 마킹 (06 V1 BACKLOG 와 이중 등록 X) | no — 사용자 실물 검증 필요 (시연장 이동) | → verification_queue D 그룹에 추가 |

DOD 3 의 실물 검증 (SO-ARM·카메라 직결 5-step PASS 확인) 은 PHYS_REQUIRED — 자동 검증 불가.

---

## 사용자 실물 검증 필요 사항 (verification_queue D 그룹 추가)

1. **DGX 시연장 이동 + 하드웨어 직결 5-step 검증** (PHYS_REQUIRED)
   - DGX 에 SO-ARM 2대 (follower + leader) + 카메라 2대 (top + wrist) USB 직결
   - `cd ~/smolvla && bash dgx/scripts/check_hardware.sh` 실행
   - 기대: `[DONE] 모든 점검 PASS (5단계)` + FAIL 0건
   - FAIL 발생 시 해결 힌트 블록 지시에 따라 처리
   - 06 V1 BACKLOG (BACKLOG.md L125) 와 통합 — D3 verification 통과 시 06 V1 BACKLOG 완료 처리 가능

---

## CLAUDE.md 준수

| 항목 | 확인 | 메모 |
|---|---|---|
| Category A 영역 수정 X | ✅ | prod-test-runner 는 배포·검증만 — 코드 수정 없음 |
| Category B 영역 변경된 deploy | ✅ | check_hardware.sh 는 Category B 비해당, 자율 배포 조건 충족 |
| 자율 영역만 사용 | ✅ | ssh 비대화형 검증 (bash -n, grep, 실 실행), MD5 비교 — 모두 자율 영역 |
| 큰 다운로드·긴 실행 | ✅ | 해당 없음 (단순 스크립트 실행, <30초) |
| 가상환경 재생성·업그레이드 | ✅ | 해당 없음 |
