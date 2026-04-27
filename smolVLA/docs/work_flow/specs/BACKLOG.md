# Backlog

> 각 스펙의 Backlog를 스펙별로 모아 관리하는 중앙 문서.  
> `/complete-task` 또는 `/complete-test` 실행 시 신규 항목 추가 및 상태 업데이트가 자동 반영됨.  
> 스펙 파일 자체에는 Backlog 섹션을 두지 않는다.

---

## [01_teleoptest](history/01_teleoptest.md)

> 목표: Orin 환경 재검증 + SO-ARM 단일 쌍 teleoperation 동작 확인  
> 작성: 2026-04-25 | 완료: 2026-04-27

| # | 항목 | 발견 출처 | 우선순위 | 상태 |
|---|------|-----------|----------|------|
| 1 | SO-ARM USB 포트 고정을 위한 udev rule 검토 (`ttyACM*` 번호가 연결 순서에 따라 바뀜) — 20260427 포트 역전 실제 발생으로 우선순위 상향 | TODO-02 / TODO-03a | 높음 | 미완 |
| 2 | `lerobot-find-port` 대화형 스크립트 → 비대화형 SSH 실행 지원 방법 확인 | TODO-02 | 낮음 | 미완 |
| 3 | `orin/scripts/` 파일구조 재편: 레퍼런스에서 가져와 수정한 스크립트와 신규 작성 스크립트를 디렉터리 또는 네이밍으로 명확히 구분 (예: `adapted/`, `custom/` 또는 접두사 규칙) | TODO-02 | 중간 | 미완 |
| 4 | `laba` 사용자를 `dialout` 그룹에 추가 (`sudo usermod -aG dialout laba`) | TODO-02 prod 검증 | - | 완료 |
| 5 | rsync 배포 플로우 명문화 — devPC에서 코드 수정 후 Orin 배포까지 절차를 `docs/` 또는 스크립트로 정리 | TODO-02 prod 검증 | 중간 | 미완 |
| 6 | `ImportError: cannot import name 'bi_openarm_follower' from 'lerobot.robots'` — 수정 완료 (2026-04-26) | TODO-02 prod 검증 | - | 완료 |
| 7 | `lerobot-calibrate`는 `input()` 호출 대화형 스크립트 — 비대화형 SSH에서 EOFError 발생. 문서화 또는 주석 추가 고려 | TODO-02 prod 검증 | 낮음 | 미완 |
| 8 | motor encoder 진단 스크립트 구현 → TODO-03a로 승격 (2026-04-27) | TODO-03 prod 검증 | - | 완료 |
| 9 | 포트 식별→저장→encoder 진단 통합 스크립트 개선 — 현재는 `lerobot-find-port` 결과를 수동 복사하여 `diagnose_motor_encoder.py --port`에 입력 필요 | TODO-03a prod 검증 | 낮음 | 미완 |
| 10 | follower `id_=3` (elbow_flex 추정) `Torque_Enable` write 실패 간헐 발생 — 재실행으로 복구되나 원인 미확정 (케이블 접촉 불량, 초기화 타이밍, firmware 이슈 가능성) | TODO-04 prod 검증 | 중간 | 미완 |
| 11 | Orin에 `v4l2-ctl` 미설치 — `sudo apt install v4l-utils` 로 설치 가능. `setup_env.sh` 또는 설치 문서에 추가 고려 | TODO-05 prod 검증 | 낮음 | 미완 |
| 12 | OV5648 카메라 화각·포커스 실측값을 `docs/storage/02_hardware.md`에 반영 필요 — 화각: 수평 FOV 약 53°(68°는 대각), 포커스: Auto Focus(스펙 시트의 Fixed는 오류) | TODO-05 prod 검증 | 중간 | 미완 |

---

## [02_dgx_setting](02_dgx_setting.md)

> 목표: DGX Spark 학습 환경 구축 + smolVLA 학습/배포 가능성 결정  
> 작성: 2026-04-27 | TODO-02 완료: 2026-04-27

| # | 항목 | 발견 출처 | 우선순위 | 상태 |
|---|------|-----------|----------|------|
| 1 | DGX Spark 학교 통신처 DHCP 예약 (MAC 주소 제출) — DHCP로 IP 변동 시 SSH 단절 방지 | 04_devnetwork | 중간 | 미완 |
| 2 | DGX↔Orin 직접 SSH 경로 구성 (현재 devPC 경유 2-hop) — 체크포인트 전송 시간·대역폭 손실 감소 | TODO-10 사전 검토 | 낮음 | 미완 |
| 3 | 자유도 낮추기 재검토 — 풀 6 DOF 사이클 완주 후 VRAM 부족 / 추론 latency 초과 / 학습 수렴 실패 중 하나 트리거 시 재평가 (gripper binary, wrist_roll 고정 등). 04_leftarmVLA 또는 06_biarm_VLA 진행 중 트리거 발생 시 격상. | TODO-11 결론 | 낮음 (트리거 시 높음) | 미완 |
| 4 | DGX Spark UMA 아키텍처 — `nvidia-smi memory.total [N/A]` 확인. TODO-07 병렬학습 자원 추정 시 시스템 RAM(121Gi) 기준으로 분석 필요. VRAM 독립 수치 없음에 유의. | TODO-02 prod 검증 | 중간 | 미완 |
| 5 | Ollama 서비스 상시 실행 중 (`ollama.service`) — 학습(TODO-09) 실행 전 GPU/메모리 경합 여부 점검 및 필요 시 서비스 중단 절차 문서화 | TODO-02 prod 검증 | 중간 | 미완 |
| 6 | `docs/storage/04_devnetwork.md` DGX IP 변경 반영 — 172.16.133.66 → 172.16.136.60 (무선, Orin과 동일 대역). `~/.ssh/config` 는 갱신 완료 (2026-04-27). | TODO-02 prod 검증 | 중간 | 미완 |
