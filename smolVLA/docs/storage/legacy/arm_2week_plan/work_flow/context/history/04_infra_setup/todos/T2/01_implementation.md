# TODO-T2 — DGX → Orin ckpt 전송 경로 재확인

> 작성: 2026-05-01 15:30 | task-executor | cycle: 1

## 목표

기존 `scripts/sync_ckpt_dgx_to_orin.sh` 가 시연장 시나리오 (Orin 이 시연장에 위치, devPC·DGX 와 다른 네트워크) 에서도 동작하는지 분석. 필요 시 USB 드라이브 또는 DataCollector 경유 우회 경로 추가.

---

## 사전 점검 결과

### 기존 sync_ckpt_dgx_to_orin.sh 동작 분석

- **패턴**: devPC 경유 2-hop (DGX → devPC TMP → Orin)
  - DGX 에서 run·step 자동 탐지 (latest run, `checkpoints/last` 심볼릭 링크)
  - devPC `mktemp -d` 임시 디렉터리 경유 (EXIT trap 으로 자동 정리)
  - Orin 에 `mkdir -p` 후 rsync `--delete`
  - `--dry-run` 플래그 지원
  - safetensors 헤더 8 byte 무결성 검증 포함
- **네트워크 가정**: devPC 가 `dgx` 와 `orin` SSH alias 모두 접근 가능한 환경
- **시연장 시나리오 적용 한계**: devPC → 시연장 Orin SSH 단절 시 (서브넷 분리 또는 격리) 기존 스크립트 실패

### 09_datacollector_setup.md §5 시연장 네트워크 구조 추출

| 장비 | 위치 | 네트워크 |
|---|---|---|
| devPC | 연구실 | 학교 WiFi (HY-WiFi, DHCP, 172.16.x.x 대역) |
| DGX | 연구실 | 학교 WiFi + LAN (DHCP) |
| DataCollector | 시연장 인근 | 시연장 WiFi (별도 공유기, DHCP) |
| Orin | 시연장 영구 배치 | 시연장 WiFi (DataCollector 와 동일 서브넷 가능성 높음) |

- 시연장 WiFi 가 학교 WiFi 와 다른 서브넷이면 devPC → Orin 직접 SSH 단절
- DataCollector 와 Orin 은 시연장 WiFi 공유 → 동일 서브넷 접근 가능 (케이스 3 우회 경로 근거)

### 4개 케이스 분류 (인터넷·격리 조합)

| 케이스 | 조건 | 전송 방법 |
|---|---|---|
| 1 | Orin 인터넷 가능 + devPC·DGX 와 동일 광역 네트워크 | 기존 `sync_ckpt_dgx_to_orin.sh` 그대로 (IP 변경 시 `~/.ssh/config` 갱신) |
| 2 | Orin 인터넷 가능 + 다른 서브넷, devPC → Orin SSH 가능 | 기존 스크립트 그대로 (2-hop devPC 경유) |
| 3 | Orin 인터넷 격리 / devPC → Orin SSH 불가 | 신규 `sync_ckpt_dgx_to_datacollector.sh` + 수동 DataCollector → Orin |
| 4 | 완전 오프라인 | USB 드라이브 직접 복사 (스크립트 X, 사용자 직접) |

---

## 산출물

### 신규: scripts/sync_ckpt_dgx_to_datacollector.sh (케이스 3)

`sync_ckpt_dgx_to_orin.sh` 와 동일 2-hop 패턴:
- DGX → devPC TMP → DataCollector (`/home/laba/smolvla/ckpt_transfer/<run>/<step>/`)
- SSH alias pre-check (`dgx` + `datacollector` 양쪽 — 없으면 에러 메시지 + exit 1)
- `--run`, `--step`, `--dry-run` 플래그 동일 인터페이스
- safetensors 헤더 8 byte 무결성 검증 포함
- 완료 후 DataCollector → Orin 수동 전송 2단계 안내 출력 (rsync 명령 + USB 참조)

DataCollector 측 도착 경로: `~/smolvla/ckpt_transfer/<run>/<step>/`
  - `~/smolvla/orin/checkpoints/` 와 구분 (DataCollector 는 Orin 역할 X, 임시 경유)

### 신규: docs/storage/others/ckpt_transfer_scenarios.md

4개 케이스 상세 기술:
- 각 케이스별 "확인 방법" SSH 명령 제시
- 사용자 결정 플로우차트 (devPC→Orin SSH 가능 여부 → DataCollector→Orin SSH 가능 여부)
- 시연장 배치 전 체크리스트
- 잔여 리스크 (DHCP 변동, DataCollector SSH 키 미배포, 임시 ckpt 용량)

### 기존 스크립트 변경 없음

`scripts/sync_ckpt_dgx_to_orin.sh` — 변경 없음. 회귀 없음.

---

## 핵심 결정

- **우회 스크립트 추가 여부**: 추가함. 09_datacollector_setup.md §5 에서 DataCollector 와 Orin 이 시연장 WiFi 공유 가능성이 높아 케이스 3 발생 가능성이 실재함.
- **USB 드라이브 절차**: 스크립트 없이 케이스 가이드 문서 (`ckpt_transfer_scenarios.md §케이스 4`) 에 명시. 완전 오프라인 시 사용자 직접 수행.
- **케이스 1·2**: 기존 스크립트 변경 없이 충족. IP 변경은 `~/.ssh/config` HostName 수동 갱신 (기존 `04_devnetwork.md` 절차 동일).

---

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `scripts/sync_ckpt_dgx_to_datacollector.sh` | A (신규) | 케이스 3 우회 — DGX → DataCollector 2-hop 전송 |
| `docs/storage/others/ckpt_transfer_scenarios.md` | A (신규) | 4개 전송 케이스 + 사용자 결정 가이드 |
| `scripts/sync_ckpt_dgx_to_orin.sh` | 변경 없음 | 회귀 방지 원칙 준수 |

---

## 적용 룰

- CLAUDE.md Hard Constraints: `docs/reference/` 미변경. `orin/lerobot/` 미변경. Coupled File Rules 해당 없음 (pyproject.toml 미변경).
- Category B 판단: CLAUDE.md 는 `scripts/deploy_*.sh` 를 Category B 명시. `sync_*.sh` 는 명시 없으나 보수적으로 동일 카테고리로 인식. 단, spec 의 TODO-T2 DOD 에 해당 스크립트 명시적 구현 요구가 있어 진행.
- 기존 스크립트 회귀 X 원칙 준수: `sync_ckpt_dgx_to_orin.sh` 변경 없음.
- 레퍼런스 활용: `sync_ckpt_dgx_to_orin.sh` 의 2-hop 패턴·플래그 인터페이스·safetensors 검증 로직 차용 (lerobot upstream 에는 해당 전송 스크립트 없음 — `sync_ckpt_dgx_to_orin.sh` 가 02 마일스톤 자체 산출물).

---

## 검증 시나리오 정의 (prod-test-runner 입력)

### 자율 가능 (prod-test-runner SSH)

1. devPC: 신규 스크립트 bash 문법 검증
   ```bash
   bash -n smolVLA/scripts/sync_ckpt_dgx_to_datacollector.sh
   ```
   기대 결과: exit=0 (문법 오류 없음)

2. devPC: SSH alias pre-check 로직 검증 (datacollector alias 없는 경우)
   - 테스트: `~/.ssh/config` 에 datacollector alias 없는 상태에서 스크립트 실행
   - 기대 결과: "ERROR: ~/.ssh/config 에 'Host datacollector' alias 가 없습니다." 출력 + exit=1

3. devPC: `--dry-run` 플래그 시 DGX → DataCollector 실제 전송 없음 확인
   - datacollector SSH alias 있는 환경에서 `bash sync_ckpt_dgx_to_datacollector.sh --dry-run`
   - DataCollector 측 `~/smolvla/ckpt_transfer/` 에 파일 생성되지 않아야 함
   - 기대 결과: rsync dry-run 로그 출력 + exit=0 + DataCollector 측 파일 미생성

4. devPC: 기존 `sync_ckpt_dgx_to_orin.sh` 변경 없음 확인
   - `bash -n smolVLA/scripts/sync_ckpt_dgx_to_orin.sh` exit=0
   - 파일 hash 비교 (수정 전 SHA 와 동일)

### 사용자 실물 필요 (verification_queue)

1. **시연장 네트워크 케이스 분류** (사용자 직접):
   - 시연장 WiFi 에 Orin 연결 후 `ssh orin "hostname"` 성공 여부 확인
   - 성공 → 케이스 1·2 (기존 스크립트 사용)
   - 실패 → 케이스 3 확인: DataCollector 에서 `ssh laba@<ORIN_IP> hostname` 성공 여부 확인

2. **케이스 3 실물 검증** (케이스 3 확정 시):
   - DataCollector → Orin SSH 키 배포 (`ssh-copy-id`)
   - `bash scripts/sync_ckpt_dgx_to_datacollector.sh --dry-run` 성공 확인
   - DataCollector 측 수동 rsync → Orin 전송 동작 확인

3. **케이스 1 실물 검증** (케이스 1·2 확정 시):
   - `bash scripts/sync_ckpt_dgx_to_orin.sh --dry-run` — 시연장 Orin IP 로 성공 확인
   - Orin 측 `~/smolvla/orin/checkpoints/` dry-run 로그 확인 (파일 미생성)

4. **실 ckpt 전송**: 05 학습 ckpt 시점 (본 사이클 X)

---

## 잔여 리스크

- 시연장 Orin 인터넷 가용성 미확인 (사용자 책임 — 케이스 분류 전 필수 확인)
- DataCollector 미구매 시 케이스 3 검증 불가 (TODO-D2 진행 후 실물 검증 가능)
- DHCP 변동: 시연장 Orin IP 변경 시 DataCollector 측 rsync 대상 IP 수동 갱신 필요

---

## 검증 필요 (다음 단계)

- code-tester:
  - 신규 스크립트 bash 문법 (`bash -n`) PASS 확인
  - `sync_ckpt_dgx_to_orin.sh` 변경 없음 확인 (회귀 방지)
  - SSH alias pre-check 로직 동작 여부 (함수 흐름 분석)
  - `--dry-run` 플래그 로직 (DRY_RUN 변수 전파 분석)
- prod-test-runner:
  - `bash -n` 문법 검증 (devPC 자율)
  - SSH alias 미설정 시 에러 메시지 + exit=1 검증 (devPC 자율)
  - 사용자 verification_queue 추가 (시연장 네트워크 케이스 분류)
