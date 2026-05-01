# TODO-T2 — DGX → 시연장 Orin ckpt 전송 경로 재확인

> 작성: 2026-05-01 15:30 | task-executor | cycle: 1

## 요약

기존 `scripts/sync_ckpt_dgx_to_orin.sh` 의 동작을 분석하고 시연장 시나리오별 4개 케이스를 정의했다.
케이스 3 (시연장 Orin 인터넷 격리 → DataCollector 경유 우회) 대응 스크립트 신규 작성 + 케이스 가이드 문서 작성.

## 사전 점검

### sync_ckpt_dgx_to_orin.sh 동작 분석

- 패턴: **devPC 경유 2-hop** (DGX → devPC TMP → Orin)
- DGX 에서 run·step 자동 탐지 (latest run, last 심볼릭 링크)
- devPC TMP 를 중간 경유지로 사용 (mktemp -d, EXIT trap 으로 정리)
- Orin 측 safetensors 헤더 8 byte 무결성 검증 포함
- `--dry-run` 플래그 지원
- 네트워크 가정: devPC 가 DGX (dgx alias) 와 Orin (orin alias) 양쪽 SSH 접근 가능

### 시연장 네트워크 구조 (09_datacollector_setup.md §5)

| 장비 | 위치 | 네트워크 |
|---|---|---|
| devPC | 연구실 | 학교 WiFi (HY-WiFi, DHCP) |
| DGX | 연구실 | 학교 WiFi + LAN (DHCP) |
| DataCollector | 시연장 인근 | 시연장 WiFi (DHCP) |
| Orin | 시연장 영구 배치 | 시연장 WiFi (DHCP) |

DataCollector 와 Orin 이 시연장 WiFi 를 공유 → 동일 서브넷 가능성 높음.
devPC·DGX 는 연구실 학교 WiFi → 서브넷 분리 가능성 있음.

### 4개 케이스 확정

| 케이스 | 조건 | 전송 방법 |
|---|---|---|
| 1 | Orin 인터넷 가능 + devPC·DGX 와 동일 광역 네트워크 | 기존 sync_ckpt_dgx_to_orin.sh |
| 2 | Orin 인터넷 가능 + 다른 서브넷, devPC → Orin SSH 가능 | 기존 sync_ckpt_dgx_to_orin.sh |
| 3 | Orin 인터넷 격리 또는 devPC → Orin SSH 불가 | 신규 sync_ckpt_dgx_to_datacollector.sh + 수동 DataCollector → Orin |
| 4 | 완전 오프라인 | USB 드라이브 직접 복사 (스크립트 X) |

## 산출물

### 1. scripts/sync_ckpt_dgx_to_datacollector.sh (신규 — 케이스 3)

`sync_ckpt_dgx_to_orin.sh` 와 동일 패턴 (devPC 2-hop):
- DGX → devPC TMP → DataCollector (`/home/laba/smolvla/ckpt_transfer/<run>/<step>/`)
- SSH alias pre-check (dgx + datacollector 양쪽)
- `--dry-run` 플래그 지원
- safetensors 헤더 무결성 검증 포함
- 완료 후 DataCollector → Orin 수동 전송 안내 출력

### 2. docs/storage/others/ckpt_transfer_scenarios.md (신규)

4개 케이스 상세 설명 + 사용자 결정 플로우차트 + 시연장 배치 전 체크리스트 + 잔여 리스크.

## 기존 스크립트 회귀 여부

`sync_ckpt_dgx_to_orin.sh` 변경 없음. 신규 스크립트는 독립 파일로 추가.

## Category B 판단 근거

CLAUDE.md Category B 에는 `scripts/deploy_*.sh` 만 명시. `sync_*.sh` 는 명시 없으나 동일 `scripts/` 디렉터리의 배포·전송 스크립트 카테고리이므로 보수적 처리. 단, spec 의 TODO-T2 DOD 에 "필요 시 `scripts/sync_ckpt_dgx_to_datacollector.sh` 같은 우회 스크립트" 구현이 명시되어 있어 진행.
