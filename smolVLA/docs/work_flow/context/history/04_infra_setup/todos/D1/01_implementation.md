# TODO-D1 — DataCollector 노드 정체 + 디렉터리 신규

> 작성: 2026-05-01 14:18 | task-executor | cycle: 1

## 사전 점검 결과

**orin/pyproject.toml extras 분석**:
- `smolvla`: transformers==5.3.0, num2words, accelerate — DataCollector 에서 제외 (추론 X)
- `hardware`: pynput, pyserial, deepdiff — DataCollector 에서 필요 (SO-ARM 제어)
- `feetech`: feetech-servo-sdk, pyserial, deepdiff — DataCollector 에서 필요 (Feetech 서보)
- `zmq`: pyzmq — DataCollector 에서 불필요 (lekiwi 로봇 전용)

**lerobot upstream pyproject [project.optional-dependencies] 키 확인**:
- `dataset`: datasets, pandas, pyarrow, av-dep, jsonlines — record 에 필요
- `training`: lerobot[dataset] + accelerate + wandb — DataCollector 제외 (학습 DGX)
- `hardware`: pynput-dep + pyserial-dep + deepdiff-dep
- `core_scripts`: dataset + hardware + viz (viz=rerun-sdk)
- `feetech`: feetech-servo-sdk + pyserial-dep + deepdiff-dep
- `smolvla`: transformers + num2words + accelerate — DataCollector 제외
- `intelrealsense`: pyrealsense2 — 선택적 (RealSense 카메라 사용 시)
- `evaluation`: av-dep 만 — DataCollector 제외 (eval 불필요)
- DataCollector 권장 extras: `record` (dataset 상당) + `hardware` + `feetech`

**04_devnetwork.md SSH 패턴 추출**:
- Host alias / HostName (IP 직접 기재) / User / Port 22 / IdentityFile ~/.ssh/id_ed25519 / ServerAliveInterval 30 / ServerAliveCountMax 5
- DHCP soft 고정 환경 — IP 변경 시 config HostName 수동 업데이트 패턴 확인

**05_orin_venv_setting.md venv 패턴 추출**:
- venv 이름 컨벤션: `.hylion_arm` (orin), `.arm_finetune` (dgx)
- 디렉터리 안에 hidden venv — `~/smolvla/orin/.hylion_arm`
- rsync 시 `--exclude '.hylion_arm'` 패턴
- setup_env.sh 절 구조: §0 시스템 패키지 → §1 venv 생성 → §2 lerobot editable → §3 torch → §4 LD_LIBRARY_PATH 패치 → §5 nvcc PATH → §6 검증

**08_orin_structure.md / 09_dgx_structure.md 절 패턴 확인**:
- §0 본 문서의 위치 → §1 디렉터리 트리 → §2 핵심 컴포넌트 책임 표 → §3 마일스톤별 책임 매트릭스 → §4 외부 의존성 → §5 마이그레이션 계획 → §6 후속 TODO 트리거 → §7 변경 이력 표
- 09 에서는 study DOD 5개 절 (노드 정체 / venv / 디렉터리 / 시연장 배치 / devPC 네트워크) 을 핵심으로 재구성

## 산출물

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `docs/storage/09_datacollector_setup.md` | 신규 | DataCollector 노드 설계 결정 문서 (§0~§7) |
| `docs/work_flow/context/history/04_infra_setup/20260501_1418_task_datacollector_setup.md` | 신규 | history 기록 |

## 적용 룰

- CLAUDE.md Hard Constraints Category A: docs/reference/ 미변경 ✓
- CLAUDE.md Hard Constraints Category C: 새 디렉터리 생성 (datacollector/) 동의 사용자로부터 사전 확보 ✓ (2026-05-01 14:18 awaits_user 답변)
- lerobot-reference-usage 스킬: lerobot upstream pyproject.toml extras 명세 직접 확인 후 subset 구성 ✓
- lerobot-upstream-check 스킬: datacollector/lerobot/ 옵션 B 원칙 명시, 05_datacollector_lerobot_diff.md TODO-D2 신규 의무 명시 ✓
- Coupled File Rule (해당 없음): 본 study 에서 코드 파일 미작성 — pyproject.toml / setup_env.sh / lerobot/ 은 TODO-D2 의 책임
- 07/08 패턴 미러: §0 + §1~§5 + §6 향후 작업 + §7 변경 이력 표 구성 ✓

## 변경 내용 요약

DataCollector 노드의 설계를 확정하고 `docs/storage/09_datacollector_setup.md` 에 문서화하였다. 사용자 답변 (별도 PC 신규 구매, Ubuntu 22.04 LTS, `smolVLA/datacollector/` 위치, pyproject.toml 신규 작성, HF Hub + rsync 양방향 지원) 을 모두 반영하였다. lerobot upstream extras 키를 직접 확인하여 DataCollector 에 필요한 최소 subset (record + hardware + feetech, smolvla·training 제외) 을 결정하였다.

orin·dgx 와 동일한 형제 패턴을 유지하면서, Jetson 제약이 없는 x86_64 Ubuntu 환경이므로 표준 PyTorch wheel 사용 가능 사실을 명시하였다. SSH 설정 / rsync deploy 패턴 / HF Hub 업로드 시나리오를 04_devnetwork.md 패턴 미러로 정의하였다. 시연장 배치 시 DHCP 변동·인터넷 격리 리스크를 기존 BACKLOG 02 #1 과 연결하여 명시하였다.

## code-tester 입장에서 검증 권장 사항

- study 타입 — 코드 단위 테스트 X
- **문서 일관성 검증**:
  - §1~§5 절 구성이 study DOD 5개 항목 (노드 정체·venv·디렉터리·시연장 배치·devPC 네트워크) 을 모두 포함하는지 확인
  - §0 + §6 + §7 이 07/08 패턴과 일관성 있는지 확인
- **사실 정확성 검증**:
  - lerobot upstream extras 키 (dataset / hardware / feetech / smolvla 등) 가 `docs/reference/lerobot/pyproject.toml` 와 일치하는지 확인
  - venv 이름 컨벤션 (.hylion_collector) 이 05_orin_venv_setting.md 패턴과 일관성 있는지 확인
  - SSH ~/.ssh/config 패턴이 04_devnetwork.md §5 와 일관성 있는지 확인
- **패턴 미러 검증**:
  - 디렉터리 구조가 §3 orin/ 형제 패턴과 일관성 있는지 확인
  - coupled file 05_datacollector_lerobot_diff.md 필요성이 TODO-D2 에 명시되었는지 확인

## 본 사이클 자연 해소 BACKLOG / 명시

- BACKLOG 04 #2 (.archive 컨벤션): run_teleoperate.sh → datacollector/scripts/ 최종 이동 시점을 TODO-D2 로 명시. 자연 해소 경로 확정.
- BACKLOG 02 #1 (DHCP 예약): DataCollector 도 동일 카테고리, §4.1 에서 사용자 책임으로 명시. 프로젝트 DHCP 정책 일관성 유지.

## 잔여 리스크 / SKILL_GAP

- DataCollector 구매 전이므로 실제 IP·호스트명·유저명은 미확정 (§1-3 에 placeholder 로 기록)
- 시연장 WiFi 환경 미확인 — HF Hub 접근 가능 여부 사전 테스트 필요 (§4-2 명시)
- SKILL_GAP 없음 — lerobot upstream extras 직접 확인 완료

## TODO-D2 입력 사양

다음 사양을 기반으로 TODO-D2 (실제 셋업 실행) 진행:

- **pyproject.toml 신규 작성**: extras = record (dataset 상당) + hardware + feetech. smolvla·training·evaluation 제외. entrypoint 9개 (eval·train 제외).
- **setup_env.sh 신규 작성**: orin/scripts/setup_env.sh 패턴 미러. Jetson 제약 제거 (cusparseLt 처리 X, redist URL X). 표준 `pip install torch torchvision` 사용.
- **lerobot curated subset**: 옵션 B 원칙 (파일 변경 X, entrypoint 만 정리). 신규 coupled file `docs/storage/lerobot_upstream_check/05_datacollector_lerobot_diff.md` 신규 작성 의무.
- **venv 이름**: `.hylion_collector`
- **디렉터리 구조**: §3-2 트리 그대로 실행 (README.md, pyproject.toml, lerobot/, scripts/, tests/, config/, data/)
- **run_teleoperate.sh 최종 이동**: `docs/storage/others/run_teleoperate.sh.archive` → `datacollector/scripts/run_teleoperate.sh`

## 검증 필요 (다음 단계)

- code-tester: study 라 코드 검증 X — 산출물 일관성 + 패턴 미러 + 사실 정확성 위주
- 특히 lerobot extras 키 추출이 upstream pyproject.toml 과 정확히 일치하는지 교차 검증 권장
