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

## [02_dgx_setting](history/02_dgx_setting.md)

> 목표: DGX Spark 학습 환경 구축 + smolVLA 학습/배포 가능성 결정  
> 작성: 2026-04-27 | 완료: 2026-04-29

| # | 항목 | 발견 출처 | 우선순위 | 상태 |
|---|------|-----------|----------|------|
| 1 | DGX Spark 학교 통신처 DHCP 예약 (MAC 주소 제출) — DHCP로 IP 변동 시 SSH 단절 방지 | 04_devnetwork | 중간 | 미완 |
| 2 | DGX↔Orin 직접 SSH 경로 구성 (현재 devPC 경유 2-hop) — 체크포인트 전송 시간·대역폭 손실 감소 | TODO-10 사전 검토 | 낮음 | 미완 |
| 3 | 자유도 낮추기 재검토 — 풀 6 DOF 사이클 완주 후 VRAM 부족 / 추론 latency 초과 / 학습 수렴 실패 중 하나 트리거 시 재평가 (gripper binary, wrist_roll 고정 등). 04_leftarmVLA 또는 06_biarm_VLA 진행 중 트리거 발생 시 격상. | TODO-11 결론 | 낮음 (트리거 시 높음) | 미완 |
| 4 | DGX Spark UMA 아키텍처 — `nvidia-smi memory.total [N/A]` 확인. TODO-07 병렬학습 자원 추정 시 시스템 RAM(121Gi) 기준으로 분석 필요. VRAM 독립 수치 없음에 유의. | TODO-02 prod 검증 | 중간 | 미완 |
| 5 | Ollama 서비스 상시 실행 중 (`ollama.service`) — 학습(TODO-09) 실행 전 GPU/메모리 경합 여부 점검 및 필요 시 서비스 중단 절차 문서화 | TODO-02 prod 검증 | 중간 | 미완 |
| 6 | `docs/storage/04_devnetwork.md` DGX IP 변경 반영 — 172.16.133.66 → 172.16.136.60 (무선, Orin과 동일 대역). `~/.ssh/config` 는 갱신 완료 (2026-04-27). | TODO-02 prod 검증 | 중간 | 미완 |
| 7 | `torchvision` wheel 이 `setup_env.sh` 에서 자동 설치 안 됨 — 수동 안내만 출력되어 별도 설치 필요. `orin/scripts/setup_env.sh` 에 wheel 자동 설치 로직 추가 고려 (`docs/storage/others/torchvision-0.20.0a0+afc54f7-cp310-cp310-linux_aarch64.whl` 이미 존재). | TODO-09c prod 검증 | 중간 | 미완 |
| 8 | Orin `dpkg` 중단 상태 발생 — `sudo dpkg --configure -a` 로 수동 복구 필요. 향후 `setup_env.sh` 앞단에 dpkg 상태 체크 추가 고려. | TODO-09c prod 검증 | 낮음 | 미완 |
| 9 | `scripts/deploy_dgx.sh` 버그 2건: (1) DGX 측 대상 디렉터리 사전 생성 로직 없음 → rsync error 11 발생, (2) rsync 실패 후에도 exit code 0 반환 (마지막 `echo` 가 덮어씀). `ssh dgx "mkdir -p ~/smolvla/dgx ~/smolvla/docs/reference/lerobot"` 선행 실행 + `set -e` 또는 rsync 결과 명시적 체크 추가 필요. **TODO-09b 재테스트 전 반드시 수정.** | TODO-09b Codex 검증 | 높음 | 완료 (2026-04-28) |
| 10 | `docs/storage/06_dgx_venv_setting.md` 신규 작성 — TODO-09b 완료 후 후행 작업. 형식은 `docs/storage/05_orin_venv_setting.md` 와 대칭. DGX venv 구성(Python 3.12.3 / `.arm_finetune` / PyTorch 2.10.0+cu130), lerobot editable 설치 실측, GB10 UserWarning 동작 검증, smoke test throughput 실측치, Walking RL 동시 점유 관찰 결과 포함. | TODO-09b 완료 후행 | 중간 | 미완 |

---

## [03_smolvla_test_on_orin](history/03_smolvla_test_on_orin.md)

> 목표: Orin 위에서 사전학습 smolVLA(`lerobot/smolvla_base`) 가 하드웨어와 함께 정상 동작하는지 검증
> 작성: 2026-04-29 | 완료: 2026-04-29

| # | 항목 | 발견 출처 | 우선순위 | 상태 |
|---|------|-----------|----------|------|
| 1 | smolvla_base 학습 카메라 키(`camera1/2/3`)와 svla_so100_pickplace 데이터셋 카메라 키(`top/wrist`) 불일치 — 실 하드웨어 배포(05_leftarmVLA) 시 카메라 키 매핑 결정 필요 | TODO-02 분석 | 높음 | 미완 |
| 2 | `empty_cameras` 더미 패딩으로 카메라 수 불일치 forward 가능하나 학습 수렴 보장 없음 — 05_leftarmVLA 진입 시 실 검증 필요 | TODO-02 분석 | 높음 | 미완 |
| 3 | inference_baseline.py 실 실행 검증 — TODO-06b prod 실행 완료 (2026-04-29). exit 0, action shape `(1, 6)` = 정상 (`select_action` dequeue 단일 action). DOD 기대값 오기 확인 및 정정 완료 | TODO-03 / TODO-05 / TODO-06b | 높음 | 완료 (2026-04-29) |
| 4 | measure_latency.py 실 실행 검증 — TODO-06b prod 실행 완료 (2026-04-29). n=10: p50 5.59ms / p95 5.82ms / RAM 3068 MiB, n=5: p50 5.59ms / p95 6.20ms / RAM 3042 MiB. latency 감소 미확인 → 항목 13 으로 추적 | TODO-04 / TODO-05 / TODO-06b | 높음 | 완료 (실행 성공) — num_steps 효과 조사 대기 |
| 5 | `from orin.lerobot...` 임포트 일탈 — TODO-06 으로 4줄 수정 + 회귀 grep PASS (0건). 사전 점검에서 obs 구조 / 헬퍼 사용 / 카메라 키 처리 전반이 모델 forward 기대와 어긋남을 발견 → 두 파일 `smoke_test.py` 패턴으로 전면 재작성 | TODO-05 prod 검증 | 높음 | 완료 (2026-04-29) |
| 6 | `docs/lerobot_study/07c_smolvla_base_test_results.md` 작성 — TODO-06b 에서 §1~§6, TODO-07b 에서 §7(7.1~7.5) 완성 (2026-04-29). 04 시작 시점에 `docs/storage/` 에서 `docs/lerobot_study/` 로 이동·rename (2026-04-30) — 03/07 시리즈 (07/07b/07c) 정렬 일관성. | TODO-05 / TODO-06b / TODO-07b | 높음 | 완료 (2026-04-29) |
| 7 | 04 진입 시 데이터 분포 기반 action 클램프 도입 검토 — 03 의 hardware-in-the-loop 검증(TODO-07b) 에서는 모터 토크 한계 + `n_action_steps=5` 만으로 안전 확보. 04 학습 데이터의 action 분포가 확보되면 95%ile 기반 클램프 추가하여 추론 단 안전 마진 강화 | TODO-07 안전 장치 (ii) | 중간 | 미완 |
| 8 | `make_pre_post_processors` HF Hub preprocessor config 게시 여부 — TODO-06b 실행 시 오류 없이 동작 → smolvla_base 게시 확인 또는 fallback 성공으로 추정. 실 오류 미발생이므로 블로킹 아님 | TODO-06 작업 중 식별 | 중간 | 완료 (실행 오류 없음, 2026-04-29) |
| 9 | `policy.config.num_steps` runtime override 효과 미확인 — TODO-06b 에서 num_steps=10 vs 5 실 실행 결과 p50 동일(5.59ms). override 미적용 또는 해당 범위 측정 노이즈 내 가능성. → 항목 13 으로 통합 추적 | TODO-06 작업 중 식별 | 중간 | 항목 13 으로 통합 |
| 10 | `policy.config.n_action_steps = 5` queue 동작 — TODO-07b live 5/50 step 정상 실행됨(팔 동작, 안전). 단 step 0~4 action 값이 동일 chunk 출처인지(queue OK) vs 매 step 새 forward(queue 미동작)는 JSON 비교 미수행. 실용 상 live PASS 이므로 블로킹 아님. 04_leftarmVLA 진입 전 명시적 chunk 출처 확인 필요 | TODO-07 작업 중 식별 | 중간 | 실용 PASS — chunk 출처 검증 미완 |
| 11 | 카메라 슬롯 임의 매핑 (`top → camera1`, `wrist → camera2`) 의 사전학습 분포 의미 미확인 — smolvla_base config 는 `camera1/2/3` 키만 알고 그것이 의미적으로 top 인지 wrist 인지 모름. 03 단계는 정성 검증이라 OK 이나 05_leftarmVLA 진입 시 데이터 수집 단계에서 사전학습 분포 의미와 어긋나면 재정렬 필요 | TODO-07 작업 중 식별 | 낮음 (05 트리거 시 중간) | 미완 |
| 12 | `inference_baseline.py` action shape DOD 오기 정정 — `select_action` 의 `(1, 6)` 반환은 lerobot 표준 API 정상 동작. DOD 기대값 `(1, 50, *)` 는 raw `forward()` chunk shape 로 혼용된 오기였음. TODO-06b DOD 정정 + `[x]` 완료 처리 (2026-04-29) | TODO-06b PARTIAL | 중간 | 완료 (2026-04-29) |
| 13 | `num_steps=5` vs `num_steps=10` latency 미감소 — 실측 p50 동일(5.59ms). TODO-07b 실 카메라 입력에서 재측정 예정이었으나 latency 정량 재측정 미수행. 05_leftarmVLA 학습 후 실 제어 루프에서 재확인 | TODO-06b PARTIAL | 중간 | 미완 |
| 14 | SSH 비대화형 import check — `source activate` 없이 venv python 직접 실행 시 `libcusparseLt.so.0` ImportError 발생. Orin CUDA 라이브러리가 activate 스크립트를 통해서만 `LD_LIBRARY_PATH` 에 포함됨. SSH 비대화형 검증 명령에 반드시 `source activate &&` 선행 필요. 스펙·codex 검증 명령 패턴 수정 필요 | TODO-06b Codex step 5 | 낮음 | 미완 |
| 15 | 카메라 인덱스 사전 발견 단계 필요 — `hil_inference.py` 실행 전 `lerobot-find-cameras opencv` 로 top/wrist 카메라의 실제 디바이스 인덱스 확인 필수. 기본값(`top:0,wrist:1`) 이 실제 인덱스와 불일치하여 `OpenCVCamera(1)` 실패 발생 (TODO-07b 에서 재발견 필요했음). hil_inference.py argparse 기본값 또는 README 에 이 단계 명시 필요 | TODO-07b prod 검증 | 높음 | 미완 |
| 16 | wrist 카메라 방향 플립 필요 — `--flip-cameras wrist` 없이 실행 시 wrist 카메라 이미지가 뒤집힘. 05_leftarmVLA 학습 전 사전학습 분포의 wrist 카메라 방향과 일치하는지 확인 후 hil_inference.py 기본값 또는 데이터 수집 스크립트에 반영 필요 | TODO-07b prod 검증 | 높음 | 미완 |
| 17 | 팔 calibration 중간값 경직 — live 50 step 이후 팔이 calibration 중간값 근처에서 멈추고 경직됨. 사전학습 분포(lego 큐브 pick-and-place, 특정 책상 배치) 와 본 환경 차이의 예상 동작. 03 마일스톤 범위 내 정상 결과. 05_leftarmVLA 학습 및 fine-tuning 으로 해결 필요 | TODO-07b prod 검증 | 중간 | 05_leftarmVLA 이관 |

---

## [04_infra_setup](04_infra_setup.md)

> 목표: 05_leftarmVLA 진입 가능한 4-노드 인프라 셋업 — devPC + DataCollector(신규) + DGX + 시연장 Orin
> 작성: 2026-04-30

| # | 항목 | 발견 출처 | 우선순위 | 상태 |
|---|------|-----------|----------|------|
| 1 | upstream 동기화 시 `orin/pyproject.toml [project.scripts]` 의 entrypoint 정리 (lerobot-eval / lerobot-train 제거) 가 덮어씌워질 수 있음 — 동기화 절차에 본 항목 명시 필요 (현재 `02_orin_pyproject_diff.md` 갱신만으로 추적) | TODO-O1 study | 중간 | 미완 |
| 2 | run_teleoperate.sh 의 임시 보관 위치 — TODO-O2 진행 시점에 DataCollector 디렉터리 미존재 시 `docs/storage/others/run_teleoperate.sh.archive` 같은 임시 위치 후보. TODO-D2 시점에 최종 이동. 임시 보관 형식 (확장자 `.archive` 등) 일관 컨벤션 결정 필요 | TODO-O1 study | 낮음 | 미완 |
| 3 | `orin/config/ports.json`, `cameras.json` 의 git 추적 vs gitignore 정책 결정 — TODO-O1 §1-2 에서 git 추적 가정. 단 사용자 환경 의존(시연장 셋업 후 안정적) 이라 별 인스턴스 환경에서 충돌 가능. 정책 명문화 필요 | TODO-O1 study | 낮음 | 미완 |
| 4 | `orin/examples/tutorial/smolvla/` 가 1개 파일 (`using_smolvla_example.py`) 만 남은 디렉터리 — 평탄화 (`examples/tutorial/using_smolvla_example.py`) 검토 가능. 단 upstream 구조 보존 원칙대로면 그대로 유지가 자연스러움. TODO-O3 검증 시점에 사용자와 합의 | TODO-O2b | 낮음 | 미완 |
| 5 | 향후 마일스톤별 추론 entry point 가 늘어날 때 `orin/inference/` 의 하위 구조 결정 (archive/, milestone 별 디렉터리 등). 05_leftarmVLA TODO-14 진입 시 hil_inference.py 가 ckpt 인자로 다양한 정책을 받을 수 있는지에 따라 결정 | TODO-O2b | 낮음 (05 트리거 시 중간) | 미완 |
