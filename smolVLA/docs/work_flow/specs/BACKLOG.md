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
| 3 | 자유도 낮추기 재검토 — 풀 6 DOF 사이클 완주 후 VRAM 부족 / 추론 latency 초과 / 학습 수렴 실패 중 하나 트리거 시 재평가 (gripper binary, wrist_roll 고정 등). 06_leftarmVLA 또는 08_biarm_VLA 진행 중 트리거 발생 시 격상. | TODO-11 결론 | 낮음 (트리거 시 높음) | 미완 |
| 4 | DGX Spark UMA 아키텍처 — `nvidia-smi memory.total [N/A]` 확인. TODO-07 병렬학습 자원 추정 시 시스템 RAM(121Gi) 기준으로 분석 필요. VRAM 독립 수치 없음에 유의. | TODO-02 prod 검증 | 중간 | 미완 |
| 5 | Ollama 서비스 상시 실행 중 (`ollama.service`) — 학습(TODO-09) 실행 전 GPU/메모리 경합 여부 점검 및 필요 시 서비스 중단 절차 문서화 | TODO-02 prod 검증 | 중간 | 완료 (07 T2 + D2, preflight_check.sh §4 Ollama GPU 점유 체크 + training.py preflight 5단계 흡수, 2026-05-04) |
| 6 | `docs/storage/04_devnetwork.md` DGX IP 변경 반영 — 172.16.133.66 → 172.16.136.60 (무선, Orin과 동일 대역). `~/.ssh/config` 는 갱신 완료 (2026-04-27). | TODO-02 prod 검증 | 중간 | 미완 |
| 7 | `torchvision` wheel 이 `setup_env.sh` 에서 자동 설치 안 됨 — 수동 안내만 출력되어 별도 설치 필요. `orin/scripts/setup_env.sh` 에 wheel 자동 설치 로직 추가 고려 (`docs/storage/others/torchvision-0.20.0a0+afc54f7-cp310-cp310-linux_aarch64.whl` 이미 존재). | TODO-09c prod 검증 | 중간 | 완료 (07 O3, setup_env.sh SMOLVLA_ROOT 기반 wheel 자동 설치 경로 정정, 2026-05-03) |
| 8 | Orin `dpkg` 중단 상태 발생 — `sudo dpkg --configure -a` 로 수동 복구 필요. 향후 `setup_env.sh` 앞단에 dpkg 상태 체크 추가 고려. | TODO-09c prod 검증 | 낮음 | 완료 (07 O3, setup_env.sh pre-flight dpkg 사전 체크 + 안내 추가, 2026-05-03) |
| 9 | `scripts/deploy_dgx.sh` 버그 2건: (1) DGX 측 대상 디렉터리 사전 생성 로직 없음 → rsync error 11 발생, (2) rsync 실패 후에도 exit code 0 반환 (마지막 `echo` 가 덮어씀). `ssh dgx "mkdir -p ~/smolvla/dgx ~/smolvla/docs/reference/lerobot"` 선행 실행 + `set -e` 또는 rsync 결과 명시적 체크 추가 필요. **TODO-09b 재테스트 전 반드시 수정.** | TODO-09b Codex 검증 | 높음 | 완료 (2026-04-28) |
| 10 | `docs/storage/06_dgx_venv_setting.md` 신규 작성 — TODO-09b 완료 후 후행 작업. 형식은 `docs/storage/05_orin_venv_setting.md` 와 대칭. DGX venv 구성(Python 3.12.3 / `.arm_finetune` / PyTorch 2.10.0+cu130), lerobot editable 설치 실측, GB10 UserWarning 동작 검증, smoke test throughput 실측치, Walking RL 동시 점유 관찰 결과 포함. | TODO-09b 완료 후행 | 중간 | 미완 |

---

## [03_smolvla_test_on_orin](history/03_smolvla_test_on_orin.md)

> 목표: Orin 위에서 사전학습 smolVLA(`lerobot/smolvla_base`) 가 하드웨어와 함께 정상 동작하는지 검증
> 작성: 2026-04-29 | 완료: 2026-04-29

| # | 항목 | 발견 출처 | 우선순위 | 상태 |
|---|------|-----------|----------|------|
| 1 | smolvla_base 학습 카메라 키(`camera1/2/3`)와 svla_so100_pickplace 데이터셋 카메라 키(`top/wrist`) 불일치 — 실 하드웨어 배포(06_leftarmVLA) 시 카메라 키 매핑 결정 필요 | TODO-02 분석 | 높음 | 미완 |
| 2 | `empty_cameras` 더미 패딩으로 카메라 수 불일치 forward 가능하나 학습 수렴 보장 없음 — 06_leftarmVLA 진입 시 실 검증 필요 | TODO-02 분석 | 높음 | 미완 |
| 3 | inference_baseline.py 실 실행 검증 — TODO-06b prod 실행 완료 (2026-04-29). exit 0, action shape `(1, 6)` = 정상 (`select_action` dequeue 단일 action). DOD 기대값 오기 확인 및 정정 완료 | TODO-03 / TODO-05 / TODO-06b | 높음 | 완료 (2026-04-29) |
| 4 | measure_latency.py 실 실행 검증 — TODO-06b prod 실행 완료 (2026-04-29). n=10: p50 5.59ms / p95 5.82ms / RAM 3068 MiB, n=5: p50 5.59ms / p95 6.20ms / RAM 3042 MiB. latency 감소 미확인 → 항목 13 으로 추적 | TODO-04 / TODO-05 / TODO-06b | 높음 | 완료 (실행 성공) — num_steps 효과 조사 대기 |
| 5 | `from orin.lerobot...` 임포트 일탈 — TODO-06 으로 4줄 수정 + 회귀 grep PASS (0건). 사전 점검에서 obs 구조 / 헬퍼 사용 / 카메라 키 처리 전반이 모델 forward 기대와 어긋남을 발견 → 두 파일 `smoke_test.py` 패턴으로 전면 재작성 | TODO-05 prod 검증 | 높음 | 완료 (2026-04-29) |
| 6 | `docs/lerobot_study/07c_smolvla_base_test_results.md` 작성 — TODO-06b 에서 §1~§6, TODO-07b 에서 §7(7.1~7.5) 완성 (2026-04-29). 04 시작 시점에 `docs/storage/` 에서 `docs/lerobot_study/` 로 이동·rename (2026-04-30) — 03/07 시리즈 (07/07b/07c) 정렬 일관성. | TODO-05 / TODO-06b / TODO-07b | 높음 | 완료 (2026-04-29) |
| 7 | 04 진입 시 데이터 분포 기반 action 클램프 도입 검토 — 03 의 hardware-in-the-loop 검증(TODO-07b) 에서는 모터 토크 한계 + `n_action_steps=5` 만으로 안전 확보. 04 학습 데이터의 action 분포가 확보되면 95%ile 기반 클램프 추가하여 추론 단 안전 마진 강화 | TODO-07 안전 장치 (ii) | 중간 | 미완 |
| 8 | `make_pre_post_processors` HF Hub preprocessor config 게시 여부 — TODO-06b 실행 시 오류 없이 동작 → smolvla_base 게시 확인 또는 fallback 성공으로 추정. 실 오류 미발생이므로 블로킹 아님 | TODO-06 작업 중 식별 | 중간 | 완료 (실행 오류 없음, 2026-04-29) |
| 9 | `policy.config.num_steps` runtime override 효과 미확인 — TODO-06b 에서 num_steps=10 vs 5 실 실행 결과 p50 동일(5.59ms). override 미적용 또는 해당 범위 측정 노이즈 내 가능성. → 항목 13 으로 통합 추적 | TODO-06 작업 중 식별 | 중간 | 항목 13 으로 통합 |
| 10 | `policy.config.n_action_steps = 5` queue 동작 — TODO-07b live 5/50 step 정상 실행됨(팔 동작, 안전). 단 step 0~4 action 값이 동일 chunk 출처인지(queue OK) vs 매 step 새 forward(queue 미동작)는 JSON 비교 미수행. 실용 상 live PASS 이므로 블로킹 아님. 06_leftarmVLA 진입 전 명시적 chunk 출처 확인 필요 | TODO-07 작업 중 식별 | 중간 | 실용 PASS — chunk 출처 검증 미완 |
| 11 | 카메라 슬롯 임의 매핑 (`top → camera1`, `wrist → camera2`) 의 사전학습 분포 의미 미확인 — smolvla_base config 는 `camera1/2/3` 키만 알고 그것이 의미적으로 top 인지 wrist 인지 모름. 03 단계는 정성 검증이라 OK 이나 06_leftarmVLA 진입 시 데이터 수집 단계에서 사전학습 분포 의미와 어긋나면 재정렬 필요 | TODO-07 작업 중 식별 | 낮음 (06 트리거 시 중간) | 미완 |
| 12 | `inference_baseline.py` action shape DOD 오기 정정 — `select_action` 의 `(1, 6)` 반환은 lerobot 표준 API 정상 동작. DOD 기대값 `(1, 50, *)` 는 raw `forward()` chunk shape 로 혼용된 오기였음. TODO-06b DOD 정정 + `[x]` 완료 처리 (2026-04-29) | TODO-06b PARTIAL | 중간 | 완료 (2026-04-29) |
| 13 | `num_steps=5` vs `num_steps=10` latency 미감소 — 실측 p50 동일(5.59ms). TODO-07b 실 카메라 입력에서 재측정 예정이었으나 latency 정량 재측정 미수행. 06_leftarmVLA 학습 후 실 제어 루프에서 재확인 | TODO-06b PARTIAL | 중간 | 미완 |
| 14 | SSH 비대화형 import check — `source activate` 없이 venv python 직접 실행 시 `libcusparseLt.so.0` ImportError 발생. Orin CUDA 라이브러리가 activate 스크립트를 통해서만 `LD_LIBRARY_PATH` 에 포함됨. SSH 비대화형 검증 명령에 반드시 `source activate &&` 선행 필요. 스펙·codex 검증 명령 패턴 수정 필요 | TODO-06b Codex step 5 | 낮음 | 완료 (07 O2, run_python.sh wrapper 신규 + deny-only 모델 효과로 settings.json 불요, 2026-05-03) |
| 15 | 카메라 인덱스 사전 발견 단계 필요 — `hil_inference.py` 실행 전 `lerobot-find-cameras opencv` 로 top/wrist 카메라의 실제 디바이스 인덱스 확인 필수. 기본값(`top:0,wrist:1`) 이 실제 인덱스와 불일치하여 `OpenCVCamera(1)` 실패 발생 (TODO-07b 에서 재발견 필요했음). hil_inference.py argparse 기본값 또는 README 에 이 단계 명시 필요 | TODO-07b prod 검증 | 높음 | 완료 (07 O4, 2026-05-03): --cameras 기본값 None → 자동 발견 fallback 추가 + README 사전 단계 명시 + argparse help 개선 |
| 16 | wrist 카메라 방향 플립 필요 — `--flip-cameras wrist` 없이 실행 시 wrist 카메라 이미지가 뒤집힘. 06_leftarmVLA 학습 전 사전학습 분포의 wrist 카메라 방향과 일치하는지 확인 후 hil_inference.py 기본값 또는 데이터 수집 스크립트에 반영 필요 | TODO-07b prod 검증 | 높음 | 완료 (07 O4, 2026-05-03): README 에 wrist flip 사전 단계 + gate-json 자동 적용 안내 추가. 사전학습 분포 정합 여부는 03 BACKLOG #11 (08 트리거) 잔여 |
| 17 | 팔 calibration 중간값 경직 — live 50 step 이후 팔이 calibration 중간값 근처에서 멈추고 경직됨. 사전학습 분포(lego 큐브 pick-and-place, 특정 책상 배치) 와 본 환경 차이의 예상 동작. 03 마일스톤 범위 내 정상 결과. 06_leftarmVLA 학습 및 fine-tuning 으로 해결 필요 | TODO-07b prod 검증 | 중간 | 06_leftarmVLA 이관 |
| 18 | Orin cuSPARSELt Option B 수동 설치 (NVIDIA deb local) — 현재 `LD_LIBRARY_PATH` 패치로 우회 운영. Option B 적용 시 패치 완전 제거 가능. **보류 (문제 발생 시 재시도)** — 정상 동작 중인 환경 변경 비용 > 효익 | 구 `docs/storage/logs/todo.md` §2·§A-2 (2026-04-23) | 낮음 | 미완 |
| 19 | (선택) Seeed SharePoint JP 6.2 PyTorch 2.7 wheel 별도 test venv 설치 → cusparselt 해소 여부 확인. 현재 JP 6.0 wheel + LD_LIBRARY_PATH 패치 OK 라 보류. 06·07 학습 후 PyTorch 2.5 한계 트리거 시 격상 | 구 `docs/storage/logs/todo.md` §A-4 (2026-04-23) | 낮음 (트리거 시 중간) | 미완 |

---

## [04_infra_setup](04_infra_setup.md)

> 목표: 06_leftarmVLA 진입 가능한 4-노드 인프라 셋업 — devPC + DataCollector(신규) + DGX + 시연장 Orin
> 작성: 2026-04-30

| # | 항목 | 발견 출처 | 우선순위 | 상태 |
|---|------|-----------|----------|------|
| 1 | upstream 동기화 시 `orin/pyproject.toml [project.scripts]` 의 entrypoint 정리 (lerobot-eval / lerobot-train 제거) 가 덮어씌워질 수 있음 — 동기화 절차에 본 항목 명시 필요 (현재 `02_orin_pyproject_diff.md` 갱신만으로 추적) | TODO-O1 study | 중간 | 완료 (07 W3 명문화 — 02_orin_pyproject_diff.md 에 동기화 절차 섹션 추가, 2026-05-03) |
| 2 | run_teleoperate.sh 의 임시 보관 위치 — TODO-O2 진행 시점에 DataCollector 디렉터리 미존재 시 `docs/storage/others/run_teleoperate.sh.archive` 같은 임시 위치 후보. TODO-D2 시점에 최종 이동. 임시 보관 형식 (확장자 `.archive` 등) 일관 컨벤션 결정 필요 | TODO-O1 study | 낮음 | 완료 (2026-05-01 TODO-D2: datacollector/scripts/run_teleoperate.sh 로 최종 이관) |
| 3 | `orin/config/ports.json`, `cameras.json` 의 git 추적 vs gitignore 정책 결정 — TODO-O1 §1-2 에서 git 추적 가정. 단 사용자 환경 의존(시연장 셋업 후 안정적) 이라 별 인스턴스 환경에서 충돌 가능. 정책 명문화 필요 | TODO-O1 study | 낮음 | 완료 (07 W4 정책 문서 신규 — `docs/storage/15_orin_config_policy.md`, 2026-05-03) |
| 4 | `orin/examples/tutorial/smolvla/` 가 1개 파일 (`using_smolvla_example.py`) 만 남은 디렉터리 — 평탄화 (`examples/tutorial/using_smolvla_example.py`) 검토 가능. 단 upstream 구조 보존 원칙대로면 그대로 유지가 자연스러움. TODO-O3 검증 시점에 사용자와 합의 | TODO-O2b | 낮음 | 미완 |
| 5 | 향후 마일스톤별 추론 entry point 가 늘어날 때 `orin/inference/` 의 하위 구조 결정 (archive/, milestone 별 디렉터리 등). 06_leftarmVLA TODO-14 진입 시 hil_inference.py 가 ckpt 인자로 다양한 정책을 받을 수 있는지에 따라 결정 | TODO-O2b | 낮음 (06 트리거 시 중간) | 미완 |
| 6 | 시연장 미러링 자동 검증 스크립트 — DataCollector 측 사진·조도·색온도 자동 측정·비교 (사용자 답 E: 본 사이클은 육안+사진 결정. 06/07 학습 결과로 미러링 부족 진단 시 트리거) | TODO-M1 | 낮음 (06·07 트리거 시 중간) | 미완 |
| 7 | Phase 3 사용자 검증 대기 7건 (X3 smoke·save_dummy / G2 first-time/resume + hil_inference / D3 16단계 / M2 시연장 측정·재현 / T1 dummy push / T2 시연장 네트워크 / T3 dry-run) — 시간·환경 의존이라 BACKLOG 이관. 상세 절차는 `context/history/04_infra_setup/verification_queue.md` 참조. D3 관련 DataCollector 항목 → 완료 (06 결정 — 불요, 2026-05-02). X3·O3·G2·T1·T2·시연장 항목 → 06 V 그룹 prod 검증으로 통합 | wrap 시점 | 중간 | 일부 완료 (06 결정 적용), 잔여 → 06 V 그룹 통합 |
| 8 | TODO-G3 dispatch 누락 (orchestrator gap) — DataCollector 측 `check_hardware.sh` 이식. G1 산출물 (`orin/tests/check_hardware.sh`) 을 `datacollector/tests/` 에 이식 + venv path 갱신. D3 사용자 셋업 시 함께 처리 권고 | wrap 시점 | 낮음 (D3 트리거 시 중간) | 완료 (06 결정 — 불요, 2026-05-02): DataCollector 머신 운영 종료. DGX 가 check_hardware 책임 흡수 (06 X3) |
| 9 | TODO-G4 dispatch 누락 (orchestrator gap) — DataCollector check_hardware.sh prod 검증. G3 의존. G3·D3 완료 후 자연 처리 | wrap 시점 | 낮음 (D3 트리거 시 중간) | 완료 (06 결정 — 불요, 2026-05-02): DataCollector 머신 운영 종료. DGX 측 check_hardware 검증은 06 V2 prod 검증으로 통합 |
| 10 | `datacollector/scripts/setup_env.sh §3` PyTorch 설치 시 CPU wheel index 명시 (`--index-url https://download.pytorch.org/whl/cpu`) — 현재 PyPI default 가 CUDA wheel + nvidia-* 자동 dep 로 디스크 ~2GB 낭비 (GPU 없는 환경에서 절대 사용 X). CPU wheel 적용 시 ~250MB·다운로드 ~10분 → ~1분. 다음 사이클 적용 권장 | 05 D3 검증 진행 중 (2026-05-02) | 중간 | 완료 (06 결정 — 불요, 2026-05-02): datacollector/ 노드 legacy 이관. 해당 setup_env.sh 는 `docs/storage/legacy/02_datacollector_separate_node/` 에 보관 |
| 11 | DataCollector Python 3.12 셋업 또는 lerobot 옵션 B 직접 적용 — lerobot upstream 5+ 파일 (utils/io_utils.py:93, datasets/streaming_dataset.py:58, processor/pipeline.py:255, motors/motors_bus.py:51,52) 이 PEP 695 generic syntax 사용 → Python 3.12+ 강제. 학교 WiFi 의 launchpad timeout 으로 deadsnakes PPA 막힘. 후보: (a) deadsnakes PPA — 다른 네트워크에서 시도 / (b) uv standalone Python 3.12 / (c) 옵션 B 직접 작성 — orin 패턴 미러 (`datacollector/lerobot/` 5개 파일 backport + `05_datacollector_lerobot_diff.md` 신규 작성, 04 D1 §3-5 통합 처리). (c) 가 lerobot upstream 동기화 시 매번 backport 부담이지만 즉시 진행 가능 | 05 D3 검증 lerobot import FAIL (2026-05-02) | 높음 (다음 사이클 진입 차단 가능성) | 완료 (06 결정 — 불요, 2026-05-02): DGX 가 데이터 수집 흡수. DGX 는 이미 Python 3.12.3 + `.arm_finetune` venv 운영 중 — PEP 695 syntax 차단 무관 |
| 12 | DataCollector lerobot-calibrate (follower + leader) 실 수행 + main.sh flow 0~7 완주 검증 — 본 사이클은 flow 0~2 까지만 검증. flow 3 (teleop) 부터 lerobot-record 호출 시 #11 의존. #11 처리 후 진입 가능 | 05 D3 검증 미완 (2026-05-02) | 중간 | 완료 (06 결정 — 불요, 2026-05-02): DataCollector 머신 운영 종료 (06 결정). DGX 측 calibrate 는 06 V2 prod 검증 (dgx flow 0~7 완주) 으로 통합 |
| 13 | DataCollector flow 7 분기 3건 (HF Hub push + rsync devPC 호출 + 안함) 실 검증 — 04 BACKLOG #7 T1 통합. #11·#12 의존 | 05 D3 검증 미완 (2026-05-02) | 중간 | 완료 (06 결정 — 불요, 2026-05-02): DGX flow 7 옵션 H 재정의로 흡수 (06 X1 study). 분기 옵션 → (HF Hub / 로컬 dgx 보관 / Orin rsync) 로 재정의 |
| 14 | env_check.py `_check_motor_ids()` `'NoneType' object has no attribute 'close'` 에러 — 직접 ssh 호출에선 PASS 였는데 main.sh 흐름에선 FAIL. 환경 의존 (lerobot-find-port 직후 USB 상태·timing 추정). `port_handler.openPort()` 결과 검사 후 `finally: port_handler.closePort()` 호출 패턴이 None-safe X 의심. fix: `port_handler` None check + `try: port_handler.openPort()` 자체 except 보호. 다음 사이클 진단·수정 | 05 main.sh flow 0~2 검증 (2026-05-02) | 낮음 | 미완 (06 V2 통합 처리): DGX env_check.py 통합 시 동일 패턴 진단·수정 |

---

## [05_interactive_cli](history/05_interactive_cli.md)

> 목표: orin·dgx·datacollector 세 노드 공통 대화형 CLI 게이트웨이
> 작성: 2026-05-01 | 사이클 종료: 2026-05-02

| # | 항목 | 발견 출처 | 우선순위 | 상태 |
|---|------|-----------|----------|------|
| 1 | TODO-D3 미완 — datacollector/interactive_cli/ prod 검증 (flow 0~7 완주 + flow 7 분기 3건 + env_check 7단계). 04 BACKLOG #7·#8·#9 통합 대상. Python 3.12 차단 (#11) 으로 flow 3~ 진입 불가 상태 | D3 NEEDS_USER_VERIFICATION (2026-05-02) | 중간 | 완료 (06 결정 — 불요, 2026-05-02): DataCollector 머신 운영 종료. D3 datacollector 항목 모두 DGX 흡수 또는 불요 처리. DGX 측 calibrate·flow 검증은 06 V2 prod 검증으로 통합 |
| 2 | TODO-O3 미완 — orin/interactive_cli/ prod 검증 (flow 0~5 완주 + hil_inference 50-step). 04 G2 verification_queue 통합. SSH connection timed out — 네트워크 연결 후 처리 필요 | O3 NEEDS_USER_VERIFICATION (2026-05-02) | 중간 | 완료 (07 O1, orin/interactive_cli/ flow 0~5 SSH_AUTO PASS + hil_inference PHYS_REQUIRED BACKLOG, 2026-05-04): deploy PASS, venv/cusparseLt PASS, menu walkthrough flow 0~2 정상. hil_inference 50-step SO-ARM live 는 07 #9 게이트 4 PHYS_REQUIRED 통합. |
| 3 | TODO-X3 미완 — dgx/interactive_cli/ prod 검증 (flow 0~5 완주 + smoke_test 동의 + ckpt 케이스). 04 X3·T1·T2 verification_queue 통합. devPC 정적 검증·deploy 완료. DGX 실물 SSH 검증 대기 | X3 NEEDS_USER_VERIFICATION (2026-05-02) | 중간 | 완료 (07 D2, dgx/interactive_cli/ 학습 mode 회귀 검증 PASS — preflight 5단계·save_dummy·smoke_test·ckpt 4건 분기·G-4 단발 종료 전 항목 자동 검증 PASS, 2026-05-04) |


---

## [06_dgx_absorbs_datacollector](history/06_dgx_absorbs_datacollector.md)

> 목표: DataCollector 책임을 DGX 가 흡수 — 3-노드 (devPC + DGX + Orin) 재정의 + DGX 시연장 직접 이동 운영
> 작성: 2026-05-02 | 완료: 2026-05-03 (자동화 영역) / Phase 3 BACKLOG 이관

| # | 항목 | 발견 출처 | 우선순위 | 상태 |
|---|------|-----------|----------|------|
| 1 | TODO-V1 — DGX 시연장 이동 후 SO-ARM·카메라 직결 하드웨어 검증 (USB·dialout·v4l2·find-port·find-cameras·check_hardware.sh 5-step, 총 6 항목) | wrap 시점 사용자 무시 결정 (B-3, 2026-05-03) | 중간 | 미완 — 환경 의존 (DGX 시연장 이동 가능 시 처리). devPC 정적 검증 PASS. 04 BACKLOG #7·#8·#9 + 05 D3 통합 대상이었으나 DGX 흡수 후 일부만 V1 으로 재정의 |
| 2 | TODO-V2 — dgx/interactive_cli/ 수집 mode flow 0~7 완주 검증 (calibrate·record·HF Hub push·G-4 학습 전환 prompt·BACKLOG #14 실물, 총 12 항목) | wrap 시점 사용자 무시 결정 (B-3, 2026-05-03) | 중간 | 미완 — 환경 의존. devPC 정적 검증 PASS (py_compile·ruff·bash -n·G-4 인계 체인·H-(b) rsync 제거). 04 BACKLOG #14 (env_check.py NoneType) 실물 진단 통합 |
| 3 | TODO-V3 — dgx/interactive_cli/ 학습 mode 회귀 검증 (preflight·smoke_test 5~15분·save_dummy·ckpt 케이스 4건·G-4 단발 종료, 총 10 항목). 05 X3 통합 | wrap 시점 사용자 무시 결정 (B-3, 2026-05-03) | 중간 | 미완 — 환경 의존. devPC 정적 검증 17/17 PASS. 05 X3 (smoke_test·save_dummy·ckpt 케이스) 자연 흡수. 학교 WiFi 차단 가능 항목 (svla_so100_pickplace 다운로드) 다른 네트워크 권고 |
| 4 | sync_ckpt_dgx_to_orin.sh 신규 작성 — 본 spec 결정 H-(b) 후 차기 사이클 (07_leftarmVLA) 위임. ckpt 전송 (DGX → Orin rsync) 책임 명확화 | X2·X3 wrap 시점 결정 (2026-05-02) | 중간 | 완료 (06 사이클 중 작성, 07 T3 검증 — sync_ckpt PASS, 2026-05-04): dry-run PASS + 실 실행 PASS (DGX→devPC→Orin 906MB, safetensors 헤더 OK). Orin `/home/laba/smolvla/orin/checkpoints/07_pilot_2k/002000/` 7파일 확인. |
| 5 | datacollector 머신 (smallgaint) 회수 또는 다른 용도 재활용 결정 — 본 spec 자산 legacy 이관 후 머신 자체 미사용 상태 | wrap 시점 (2026-05-02) | 낮음 | 미완 — 사용자 운영 결정 |
| 6 | M3 인계 — `.claude/skills/lerobot-reference-usage/SKILL.md` L111 의 `docs/storage/legacy/CLAUDE_pre-subagent.md` 경로 갱신 (실제 경로: `legacy/01_pre_subagent_workflow/CLAUDE_pre-subagent.md`). Category A 영역 — reflection 시점 메인 + 사용자 승인 후 처리 | L1·M3 grep 결과 (2026-05-02) | 낮음 | 완료 (07 W1 Read 확인, 이미 올바른 경로 `docs/storage/legacy/01_pre_subagent_workflow/CLAUDE_pre-subagent.md` 반영 확인 — 변경 불요, 2026-05-03) |
| 7 | M3 잔재 — `docs/storage/lerobot_upstream_check/04_dgx_lerobot_diff.md`·`05_datacollector_lerobot_diff.md` 색인 누락 (M3 code-tester Rec) | M3 code-tester (2026-05-02) | 낮음 | 완료 (07 W2 갱신, 2026-05-03): `99_lerobot_upstream_Tracking.md` 에 디렉터리 파일 색인 섹션 신설. 04·05 두 파일 모두 등록 + 05 는 DataCollector legacy 이관에 따른 역사 기록 보존 사유 명시. |
| 8 | spec 본문 `setup_env.sh` ↔ 실제 `setup_train_env.sh` 파일명 오기재 — 본 spec 본문은 그대로 보존 (역사적 결정), 차기 사이클 spec 작성 시 정확한 파일명 사용 | X5 task-executor 발견 (2026-05-03) | 낮음 | 미완 — 메타 |

---

## [07_e2e_pilot_and_cleanup](07_e2e_pilot_and_cleanup.md)

> 목표: 팔만 시연장에 달면 즉시 데이터수집·학습·추론 한 사이클 가능한 도구 완비 + datacollector 잔재 정리 + e2e 파이프라인 1회 실 검증
> 작성: 2026-05-03

| # | 항목 | 발견 출처 | 우선순위 | 상태 |
|---|------|-----------|----------|------|
| 1 | settings.json allow 의 redundant `Bash(...:* )` 패턴 ~80건 + datacollector 잔재 5건 (`ssh datacollector:*` 등) 일괄 정리 — `"Bash"` 광역 토큰 추가 후 모두 redundant. 가독성·롤백 편의 위해 즉시 삭제 X. deny-only 모델 안정 운영 확인 후 본 사이클 wrap 시 또는 별도 사이클 처리 | settings.json deny-only 전환 (2026-05-03) | 낮음 | 완료 (07 wrap reflection 제안 #5, 2026-05-04): 80 redundant Bash(...) 패턴 일괄 제거. allow 9 items (Bash 광역 + 비-Bash 도구). deny 64 유지. _comment 갱신 |
| 2 | PreToolUse hook 에 Bash matcher 추가 — `curl\|bash`·`wget\|sh`·`bash <(curl)` 등 shell metachar 포함 위험 패턴 차단 정규식 + Category A Bash 우회 차단 (예: `> .claude/`, `>> docs/reference/` 류). claude-code-guide 검증 결과 deny 패턴은 metachar 포함 시 매칭 X. 본 사이클 deny 64 의 한계 보완. 사이클 07 wrap 시 또는 별도 사이클 | settings.json 패치 시 발견 (2026-05-03 16:16, ANOMALIES 07-#1 후속) | 중간 | 미완 — wrap 트리거 |
| 3 | setup_train_env.sh §3-c 정리 — D5 extras 통합 후 §3-c 의 개별 pip install (pynput, pyserial, deepdiff, feetech-servo-sdk) 이 §3 lerobot[hardware,feetech] 와 중복. torchcodec 별도 인덱스 처리는 유지 필요. datasets/pandas/pyarrow/av/jsonlines 는 lerobot[training→dataset] 체인으로 커버. 중복 라인 제거로 §3-c 를 torchcodec 전용으로 슬림화 | D5 task-executor 발견 (2026-05-03) | 낮음 | 미완 — 07 wrap 또는 차기 cleanup 트리거 |
| 4 | cameras.json 데이터 연결 — `_run_find_cameras_split` 이 저장한 str path (`/dev/videoN`) 를 record.py 또는 다른 사용처가 실제로 읽도록 통합. | D6 code-tester R2 (2026-05-03) | 중간 (08_leftarmVLA 진입 시 트리거 가능) | 완료 (D12, 2026-05-03): _load_configs_for_record() helper 신설 + flow6_record() configs_dir 인자 추가. _validate_camera_indices() int\|str 확장. mode.py _run_collect_flow() 에서 configs_dir 전달. |
| 5 | `_get_streamable_video_devices` cv2 사전 스캔 비용 — 카메라 수 × ~1초 (device open + read). 현재 `_run_find_cameras_split` 진입 시 baseline + baseline_restored 총 2회 호출. 사용 장비가 늘어나면 (>4 device) 대기 시간 증가. 캐싱 또는 timeout 단축 패턴 검토 후보 (08_leftarmVLA 카메라 3대 환경 진입 시 트리거). | D8 task-executor 발견 (2026-05-04) | 낮음 (08 트리거 시 중간) | 미완 |
| 6 | lerobot extras 누락 패턴 3회 반복 — pyserial (D4) → deepdiff (D8 reported, D5 fix 이후도 보고) 2회. extras transitive 의존성이 예상과 다르게 동작하는 경우 또는 기존 venv 미재설치 환경에서 발생. reflection 후보: "extras install 후 venv 재설치 의무" 절차 명문화, 또는 `setup_train_env.sh` §5 검증 블록에 critical extras import 체크 추가. | D8 task-executor 분석 (2026-05-04) | 낮음 | 미완 — reflection 후보 |
| 7 | `orin/scripts/run_python.sh` `set -euo pipefail` 의 `-u` 플래그 버그 — venv activate 스크립트 내부에서 `$LD_LIBRARY_PATH` unset 참조 시 exit 1 발생. 현재 우회: `export LD_LIBRARY_PATH=''` 사전 실행 또는 venv 직접 activate. 영구 fix 후보: activate 직전 `set +u` + activate 직후 `set -u` 복원, 또는 `${LD_LIBRARY_PATH:-}` 패턴. Category B 영역 (`orin/scripts/`) — 다음 사이클 처리 권장. | O5 prod-test-runner 발견 (2026-05-04) | 중간 | 미완 |
| 8 | `scripts/deploy_orin.sh --delete` 가 Orin-only 디렉터리 삭제 — devPC 에 `orin/checkpoints/` 미존재 시 rsync --delete 로 Orin 측 `~/smolvla/orin/checkpoints/` 전체 삭제됨 (O5 prod-test 에서 T3 ckpt 삭제 후 복구 필요). fix: rsync exclude 패턴에 `checkpoints/` 추가 (calibration/ 제외 패턴 참조). 우선순위: 중간. | O5 prod-test-runner 발견 (2026-05-04) | 중간 | 미완 |
| 9 | 07 게이트 4 PHYS_REQUIRED 통합 — 시연장 이동 또는 DGX/Orin SO-ARM 직결 환경에서 walkthrough 완주 검증 대기: (a) DGX: D1-[D-1~D-4]·D3·D4-[D4-2]·D6-[D6-1]·D7-[D7-1~D7-2]·D8-[D8-1~D8-2] SO-ARM+카메라 직결 검증, (b) Orin: O1-[O1-1~O1-3] check_hardware first-time/resume + hil_inference 50-step live, O4-[O4-1] 카메라 자동 발견 + hil_inference dry-run. 참고: 사용자 walkthrough (2026-05-04) 에서 DGX env_check 항목 1~5 SSH_AUTO PASS 확인. 시연장 이동 시 일괄 처리 권장. | W5 통합 정리 (2026-05-03) | 중간 (시연장 이동 트리거 시) | 미완 — PHYS_REQUIRED 이관 |
| 10 | transfer 후 학습 진입 prompt UX 강화 — transfer (HF Hub / 로컬) 완료 직후 "이제 학습 진입할 수 있습니다" 명시 안내 추가. 현재는 G-4 학습 분기 prompt 가 있으나 transfer 결과 표시 후 곧바로 분기로 넘어가 사용자가 상황을 파악하기 어려움. flow 7 transfer.py + mode.py G-4 진입 직전 안내 삽입 권장. | D10 G4 (2026-05-03) | 중간 | 미완 |
| 11 | 학습 mode 진입 시 기존 record 산출물 vs 새 데이터 분기 명확화 — 학습 mode 에서 이미 수집한 로컬 데이터 경로를 직접 지정할 수 있는 분기 제공. 현재는 "HF Hub repo_id 만 입력" 패턴이라 오프라인 로컬 데이터 학습 시 사용자 혼란 가능. training.py 또는 mode.py 학습 분기에서 "로컬 경로 / HF Hub ID" 선택 prompt 추가 검토. | D10 G4 (2026-05-03) | 중간 | 미완 |
| 12 | Orin 측 hil_inference 진입 안내 강화 — ckpt 전송 (T3: sync_ckpt_dgx_to_orin.sh) 완료 후 "다음: ssh orin → main.sh → hil_inference mode 선택" 안내 출력 추가. 현재 sync_ckpt 완료 후 사용자가 다음 단계를 직접 파악해야 함. dgx/scripts/sync_ckpt_dgx_to_orin.sh 완료 후 안내 또는 dgx/interactive_cli 의 T3 완료 메시지에 Orin 진입 절차 1줄 추가. 08_leftarmVLA 트리거 후 처리 권장. | D10 G4 (2026-05-03) | 중간 | 미완 |
| 13 | 각 flow 단계 "왜 이 단계 필요한지" 1줄 안내 추가 — 신규 사용자 친화. 각 flow 헤더 (flow 0~7) 에 단계 목적을 1줄로 명시. 예: "flow 3 — 텔레오퍼레이션: 로봇이 지시를 따라 이동할 수 있는지 확인하고 시연 데이터를 기록합니다." 현재는 단계 이름만 있고 목적 설명이 없어 처음 사용자는 각 단계의 역할을 파악하기 어려움. | D10 G4 (2026-05-03) | 낮음 | 미완 |
| 14 | Ctrl+C 종료 시 cleanup 안내 — 각 flow 에서 KeyboardInterrupt 발생 시 "USB 점유 해제·임시 파일 확인" 안내 출력. 현재 단순 "[flow N] 취소됨." 출력만 있고 사후 처리 안내 없음. 특히 lerobot-record 중단 시 임시 episode 파일 (data/ 하위 partial episode) 과 USB 장치 해제 확인이 필요할 수 있음. | D10 G4 (2026-05-03) | 낮음 | 미완 |
| 15 | deploy_dgx.sh 가 dgx/interactive_cli/configs/ports.json·cameras.json placeholder 덮어쓰는 문제 — 04 BACKLOG #3 (orin/config) + 07 BACKLOG #8 (deploy_orin --delete) 와 같은 패턴. 사용자 환경 보호 위해 rsync exclude 또는 별도 정책 필요. precheck 옵션 1 다시 진행으로 우회 가능 단 영구 fix 권장. | D12 walkthrough 발견 (2026-05-03) | 중간 | 완료 (07 D13 Part B, 2026-05-03): deploy_dgx.sh rsync 에 `--exclude 'interactive_cli/configs/*.json'` 추가. precheck 옵션 2 cameras.json null 시 streamable fallback 도 D13 Part A 로 함께 처리 |
| 16 | flow7 transfer.py HF_TOKEN 미설정 시 즉석 입력 prompt 강화 — 현재는 "HuggingFace 인증 정보 없음 → 인증 설정 후 다시 선택" 안내만 출력하고 (1) 로컬 저장만 fallback. 즉석 토큰 입력 prompt 추가 시 walkthrough 1회 흐름 안에서 HF Hub 업로드 가능. flow7 _check_hf_token False 분기에서 "지금 토큰 입력하시겠습니까? [y/N]" prompt → input → os.environ['HF_TOKEN'] 즉석 export 후 재진행 옵션 추가 검토. 현 우회: 프로젝트 루트 `.env` 파일 + main.sh 자동 source (07 walkthrough 후속 ad-hoc 처리 완료). | 07 walkthrough 후속 (2026-05-04 HF Hub push 검증 시) | 낮음 | 미완 |
| 17 | 본 사이클 walkthrough 가 spec 본문에 명시되지 않은 ad-hoc 변경 2건 발생 — (a) 프로젝트 루트 `.env` 파일 신규 + `.gitignore` 패턴 추가 (.env, .env.*, !.env.example) + `.env.example` 템플릿 신규, (b) `dgx/interactive_cli/main.sh` + `orin/interactive_cli/main.sh` 1.5 블록 추가 (PROJECT_ROOT/.env 자동 source). 사용자 즉석 요청 + 본 사이클 wrap 우선이라 즉시 적용. reflection 후보: spec Phase 1 합의 시 walkthrough 중 ad-hoc 변경 처리 정책 명문화 (별도 todo 등록 vs 즉시 적용 + 메모). | 07 walkthrough ad-hoc (2026-05-04) | 낮음 | 완료 (07 walkthrough, 2026-05-04 — 변경 자체는 즉시 처리, 정책 명문화는 reflection 후보) |
