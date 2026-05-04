# TODO-D4 — Prod Test

> 작성: 2026-05-03 | prod-test-runner | cycle: 1

## Verdict

**`NEEDS_USER_VERIFICATION`**

자동 검증 전 항목 통과. 사용자 실물 검증 항목 2건 (PHYS_REQUIRED — 시연장 SO-ARM 직결 환경).

---

## 배포 대상

- DGX (SSH_AUTO)

---

## 배포 결과

- 명령: `bash scripts/deploy_dgx.sh`
- 결과: 성공
- 전송 파일:
  - `dgx/interactive_cli/configs/cameras.json` (신규)
  - `dgx/interactive_cli/configs/ports.json` (신규)
  - `dgx/interactive_cli/flows/entry.py` (수정)
  - `dgx/interactive_cli/flows/env_check.py` (수정)
  - `dgx/interactive_cli/flows/mode.py` (수정)
  - `dgx/interactive_cli/flows/precheck.py` (신규)
- 전송량: 8,075 bytes sent / 377 bytes received (speedup 22.50)
- DGX 원격 경로: `/home/laba/smolvla/dgx/`

---

## 자동 비대화형 검증 결과

### A. devPC 정적 (AUTO_LOCAL)

| 검증 | 명령 | 결과 |
|---|---|---|
| py_compile 9파일 | `python3 -m py_compile dgx/interactive_cli/flows/*.py` | ALL_OK |
| ruff 9파일 | `python3 -m ruff check dgx/interactive_cli/flows/` | All checks passed! |
| bash -n | `bash -n dgx/interactive_cli/main.sh` | OK (exit 0) |
| import smoke | `python3 -c "from flows import precheck; ..."` | mode OK / precheck OK |
| calib_dir | `from flows.precheck import _get_calib_dir; print(...)` | `/home/babogaeguri/.cache/huggingface/lerobot/calibration` |

git ls-files 확인 (참고사항):
- `precheck.py`, `configs/ports.json`, `configs/cameras.json` — untracked 상태 (`??`)
- git 미추가이나 rsync 배포는 파일시스템 기준으로 정상 전송됨
- `mode.py` — 100644 git 추적 확인

### B. DGX 배포 후 원격 파일 확인 (SSH_AUTO)

| 검증 | 명령 | 결과 |
|---|---|---|
| 신규 파일 존재 | `ssh dgx "ls -la ~/smolvla/dgx/interactive_cli/flows/precheck.py configs/ports.json configs/cameras.json flows/mode.py"` | 전 파일 확인 (18353B / 51B / 67B / 9980B) |
| py_compile 전체 (DGX) | `ssh dgx "python3 -m py_compile dgx/interactive_cli/flows/*.py"` | ALL_OK |
| import smoke (DGX) | `ssh dgx "python3 -c 'from flows import precheck; print(_get_calib_dir())'"`  | import OK / calib_dir: `/home/laba/smolvla/.hf_cache/lerobot/calibration` |
| configs JSON 내용 | `ssh dgx "cat ~/smolvla/dgx/interactive_cli/configs/ports.json && cat configs/cameras.json"` | placeholder null 형식 정상 |

DGX 측 calib_dir 이 `/home/laba/smolvla/.hf_cache/lerobot/calibration` 으로 표시됨 — `HF_HOME=/home/laba/smolvla/.hf_cache` 환경변수 적용, 기대치 정합. 해당 디렉터리 실존 확인 (precheck UI에서 "(존재)" 표시).

### C. menu walkthrough simulation (SSH_AUTO) — 07-#2 의도 첫 적용

#### 시나리오 1: DGX(2) → 수집(1) → precheck 취소(3)

입력: `echo -e '2\n1\n3'`

주요 출력 (요약):
```
flow 1 — 장치 선택
  → DGX [*] 선택 (2)

preflight PASS (5/5)

flow 2 — DGX 환경 체크 (preflight)
  → PASS

flow 3 — mode 선택
  → (1) 수집 선택

flow 2 — DGX 환경 체크 (학습 + 수집 통합)
  시나리오: smoke / mode: collect
  [항목 6] USB 포트 확인: leader(/dev/ttyACM0) PASS / follower(/dev/ttyACM1) PASS
  [항목 7] dialout: PASS
  [항목 8] v4l2: 4개 발견 PASS
  [항목 9] SO-ARM 포트 응답: SKIP (pyserial 미설치 — 생략)
  → 수집 환경 체크 PASS

============================================================
 teleop 사전 점검
============================================================

  모터 포트     : (미설정 — lerobot-find-port 실행 필요)
  카메라 인덱스 : (미설정 — lerobot-find-cameras 실행 필요)
  캘리브 위치   : /home/laba/smolvla/.hf_cache/lerobot/calibration (존재)

  ※ 캘리브레이션 값은 웬만하면 변하지 않음.
    같은 SO-ARM 으로 이어서 작업 시 재사용 가능.

어떻게 진행할까요?
  (1) 새 학습 데이터 수집 시작 — ...
  (2) 기존 설정 그대로 진행 ...
  (3) 취소

번호 선택 [1~3]: 3
[precheck] 취소됩니다.
[mode] 사전 점검에서 취소를 선택했습니다. 수집 mode 를 종료합니다.
```

결과: **PASS** — precheck UI 도달 + 정보 표시 정상 + "3" 취소 → return 0 정합.

특이 사항: DGX에 SO-ARM이 연결되어 있어 env_check 항목 6~7~8 PASS (항목 9는 pyserial 미설치로 SKIP). precheck UI까지 정상 도달.

#### 시나리오 2: DGX(2) → 수집(1) → precheck 기존 진행(2)

입력: `echo -e '2\n1\n2'`

주요 흐름:
```
[precheck] 기존 설정으로 teleop 진행합니다.

flow 3 — 텔레오퍼레이션 진입
Enter 를 누르면 run_teleoperate.sh 가 실행됩니다.

[flow 3] 취소됨. (비대화형 — Enter 없어 rc=1)
[flow 4] 종료됩니다.
[mode] 수집 flow 가 오류 또는 중단으로 종료되었습니다.
```

결과: **PASS** — precheck "2" → proceed → `_run_collect_flow()` 진입 정합 확인. teleop 단계까지 흐름 도달 (SO-ARM 실 동작은 PHYS_REQUIRED).

#### 시나리오 3: precheck 옵션(1) — find-port + find-cameras 자동 실행

입력: `echo -e '2\n1\n1\n\n\n\n\nN'`

주요 흐름:
```
[precheck] lerobot-find-port 실행 (2회 — leader / follower)
  → lerobot-find-port subprocess 실행 (SO-ARM 연결 — 실 실행)
  → 사용자 포트 입력 Enter=건너뜀 → follower=(건너뜀) leader=(건너뜀)

[precheck] lerobot-find-cameras opencv 실행 중...
  → lerobot-find-cameras subprocess 실행
  → 카메라 인덱스 Enter=건너뜀

[precheck] 포트 정보 저장: configs/ports.json
[precheck] 카메라 정보 저장: configs/cameras.json

캘리브 재실행 [y/N]: N
[precheck] 캘리브레이션 재실행 건너뜀.
[precheck] 포트·카메라 재발견 완료. teleop 로 진행합니다.

flow 3 — 텔레오퍼레이션 진입 → [flow 3] 취소됨.
```

결과: **PASS** — 옵션(1) 분기 전체 정합. find-port × 2회, find-cameras, 캘리브 [y/N], proceed 반환 정상. 실 포트·카메라 저장은 사용자 입력 필요 (PHYS_REQUIRED).

---

## DOD 자동 부합

| DOD 항목 | 자동 검증 | 결과 |
|---|---|---|
| mode.py + precheck.py py_compile PASS | yes (devPC + DGX) | ✅ |
| ruff PASS | yes (devPC) | ✅ |
| main.sh bash -n PASS | yes (devPC) | ✅ |
| 흐름: 수집 → env_check → precheck → _run_collect_flow 순서 | yes (시나리오 1·2 walkthrough) | ✅ |
| 표시 정보 (모터 포트·카메라 인덱스·캘리브 위치) 실 저장 위치 인용 | yes (import smoke calib_dir 일치 + precheck UI 출력 확인) | ✅ |
| 메뉴 분기 3개 (1·2·3) 코드 정합 | yes (시나리오 1=취소 / 2=proceed / 3=find-port 분기) | ✅ |
| 옵션(1) find-port + find-cameras 자동 재실행 + 캘리브 별도 묻기 | yes (시나리오 3 실행) | ✅ |
| 회귀 1 (D1a ModuleNotFoundError) 재발 X | yes (시나리오 1·2·3 全 시퀀스 크래시 없음) | ✅ |
| DGX precheck 도달 walkthrough | yes (DGX에 SO-ARM 연결 — env_check 6~9 통과 후 precheck UI 도달) | ✅ (예상 외 FULL 검증) |
| 실 teleop·find-port 결과 SO-ARM 직결 완전 검증 | no (pyserial 미설치로 항목 9 SKIP, 비대화형으로 실 포트 미입력) | → verification_queue |

---

## D. 신규 디렉터리 분산 보고 (Recommended #1 후속)

### 현재 상태

| 디렉터리 | 파일 | 용도 |
|---|---|---|
| `dgx/config/` | `dataset_repos.json`, `README.md` | 학습 데이터셋 repo 목록 (기존) |
| `dgx/interactive_cli/configs/` | `ports.json`, `cameras.json`, `node.yaml` | interactive_cli 전용 모터 포트·카메라 인덱스 캐시 (신규) |

### 15_orin_config_policy.md 정합성 검토

`docs/storage/15_orin_config_policy.md` 는 `orin/config/` 기준 정책 문서. 핵심 정책 3가지:
1. git 추적 유지 (null placeholder 포함)
2. 환경별 충돌 주의 (devPC vs Orin 값 상이 가능)
3. 갱신 절차: 시연장 셋업 후 check_hardware.sh 실행 시 갱신

dgx/interactive_cli/configs/ 에 적용된 패턴:
- null placeholder: ✅ 적용 (ports.json·cameras.json 초기값 null)
- 모듈 응집: ✅ interactive_cli 전용이므로 dgx/interactive_cli/configs/ 위치 타당
- git 추적 정책: 미명문화 (orin/config/ 정책 문서가 orin 전용 명칭)

### 판단

`dgx/interactive_cli/configs/` 는 interactive_cli 전용 모듈 응집 관점에서 OK. `dgx/config/` 와의 분산은 의도된 역할 분리. 단 dgx 측 config 정책 문서가 없으므로 다음 사이클 wrap 시 통합 검토 권고.

→ BACKLOG 후보: "dgx/interactive_cli/configs/ git 추적 정책 명문화 + 15_orin_config_policy.md DGX 확장" (Critical X, 다음 사이클 검토)

---

## 사용자 실물 검증 필요 사항 (verification_queue 추가됨)

1. **[D4-1] SO-ARM 직결 환경 pyserial 설치 후 항목 9 PASS 확인** — DGX 에 SO-ARM 직결 + pyserial 설치 환경에서 env_check 항목 9 (`serial.Serial` 포트 응답) PASS 확인. 현재 `SKIP` 처리로 precheck 도달은 성공했으나 항목 9 정합 미검증.
2. **[D4-2] precheck 옵션(1) — 실 포트·카메라 입력 후 ports.json·cameras.json 갱신 정합** — 시연장 SO-ARM + 카메라 직결 환경에서 `lerobot-find-port` 실 결과로 포트 입력, `lerobot-find-cameras` 실 인덱스 입력 → `dgx/interactive_cli/configs/ports.json·cameras.json` 갱신값 확인.

---

## CLAUDE.md 준수

| 항목 | 결과 |
|---|---|
| Category B 영역 변경된 deploy 여부 | 없음 — 변경 파일은 dgx/interactive_cli/ 전용 (Category B 외). 자율 배포 적용 |
| ssh read-only 검증 자율 | ✅ |
| ssh pytest·py_compile 자율 | ✅ |
| deploy_dgx.sh 자율 (Category B 외) | ✅ |
| docs/reference/ 변경 | 없음 ✅ |
| Category A 영역 수정 | 없음 ✅ |
| Category D 명령 | 없음 ✅ |
