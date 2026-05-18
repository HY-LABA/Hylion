# 추가 조치 백로그 (DGX SmolVLA 워크플로우)

> **목적**: 데이터 수집 / 학습 진행 중 발견된 "지금 당장은 아니지만 나중에 정리할 것" 들을 모아두는 곳. 자매 문서: [data_collection.md](data_collection.md), [training.md](training.md).
> **운영 원칙**: 작업 끝나면 해당 항목을 **[ ]** → **[x]** 표시. 항목 추가 시 발견 일자 / 트리거 / 영향 명시.

---

## 우선순위 표기

| 표기 | 의미 |
|---|---|
| 🔥 | High — 다음 학습 / 데이터 수집 세션 진입 전 처리 권장 |
| ⚙️ | Medium — 워크플로우 안정화 후 처리 |
| 💡 | Low — 개선 / 정리 / nice-to-have |

---

## 환경 / 설정

### ⚙️ [ ] v4l2-utils 사전 설치 확인 / check_hardware.sh 안내 강화

- **발견**: 2026-05-11, data_collection.md §2 카메라 노드 매핑 시 `v4l2-ctl --list-devices` 사용
- **트리거**: 현재 사용자 시스템엔 설치돼 있어 OK 였지만, 새 환경에서는 누락 가능 (`apt install v4l-utils`)
- **조치**: [check_hardware.sh](../scripts/check_hardware.sh) 에 `v4l2-ctl` 존재 여부 체크 + 미설치 시 `sudo apt install v4l-utils` 안내 출력
- **영향**: 시연장 이동 / 새 노드 셋업 시 카메라 매핑 단계에서 헤매지 않음

---

## 데이터 수집

### ⚙️ [ ] 그리퍼 (id=6) 모터 overload 방지 — 시연 패턴 가이드 추가

- **발견**: 2026-05-11, 2차 resume 수집 중 episode 39 (40번째) 종료 시 모터 6번 overload 로 disconnect() 크래시
- **트리거**: 장시간 연속 수집 + 그리퍼가 인형을 꽉 잡은 상태로 episode 종료 → 누적 열 + 지속 전류 → Feetech 펌웨어가 overload 플래그 set
- **조치**: data_collection.md §5-3 (수집 중 키 조작) 다음에 "**시연 시 모터 보호 패턴**" 절 신설. 권장 패턴:
  - episode 끝낼 때 그리퍼 살짝 열고 자연스러운 자세로 종료
  - 인형을 꽉 잡지 않고 grip force 적당히
  - 20 episodes 마다 1~2분 휴식 (모터 발열 식히기)
  - 100 episodes 풀 수집 시 중간에 USB 사이클 한 번
- **영향**: 다음 resume 차수 (60, 80, 100) 진입 전 알아두면 같은 크래시 회피 가능

### ⚙️ [ ] dataset_repos.json 에 leftarm_v1 등록

- **발견**: 2026-05-11, 수집 완료된 dataset 의 메타가 [dgx/config/dataset_repos.json](../config/dataset_repos.json) 에 반영 안 됨
- **트리거**: 현재 placeholder (`example_dataset`) 만 있음
- **조치**: `leftarm_v1` 항목 추가:
  ```json
  {
    "name": "leftarm_v1",
    "hf_hub": { "repo_id": "${HF_USER}/leftarm_v1", "private": false },
    "active_method": "hf_hub",
    "task": "Pick up the doll and reach forward",
    "episodes": 40,
    "frames": 21352,
    "collected_at": "2026-05-11"
  }
  ```
- **영향**: 다른 스크립트 / 사용자가 dataset 메타를 조회할 때 일관된 출처

### 💡 [ ] Orphaned rerun viewer 프로세스 자동 정리

- **발견**: 2026-05-11, htop 에서 이전 lerobot-record/teleoperate 세션의 rerun viewer 4개가 살아있음 (RES 3.4 GB 누적). disconnect 크래시 시 cleanup 누락 추정
- **트리거**: `--display_data=true` 가 spawn 하는 rerun_sdk/rerun_cli/rerun 프로세스가 부모 lerobot 종료 시 (특히 비정상 종료) 정리 안 됨
- **조치**: `data_collection.md` §0 또는 `training.md` §0-5 에 "세션 시작 전 rerun 정리" 한 줄 추가:
  ```bash
  pkill -f "rerun_sdk/rerun_cli/rerun" 2>/dev/null || true
  pkill ffplay 2>/dev/null || true
  ```
- **영향**: 메모리 / CPU 낭비 방지. 본 학습 / 수집에는 직접 영향 없지만 누적되면 부담

### 🔥 [ ] base_config.yaml hardware.{follower,leader}_port — `/dev/ttyACMx` → **시리얼 by-id 경로**로 전환

- **발견**: 2026-05-18 — 하루 동안 `/dev/ttyACMx` 매핑이 3회 변동
  - 13:50 (3일 휴지 후): follower ACM2→ACM1, leader ACM1→ACM0 → base_config 갱신
  - 20:48 (Orin 추론 후 재연결): follower ACM1↔ACM0 swap, leader ACM0↔ACM1 swap → base_config 또 갱신
  - 매 swap 마다 새 세션 진입 시 텔레옵·수집 명령이 잘못된 포트로 실행될 위험
- **트리거**: USB enumeration 순서는 부팅·USB 이벤트·외부 디바이스 연결 (Orin 추론용 케이블 이동 등) 에 따라 swap 가능. 시리얼 번호는 보드별 고유라 안정. `/dev/serial/by-id/` 심볼릭 링크는 udev 가 시리얼로 생성해서 *재부팅·재연결에도 유효*
- **현재 컨벤션**: `base_config.yaml` 의 `hardware.follower_port` / `hardware.leader_port` 가 `/dev/ttyACMx` 직접 표기 → 매 swap 마다 사용자 수동 갱신 필요. *null=에러* 가드는 있지만 *잘못된 ACM 으로 가리킨 경우* 는 잡지 못함 (예: ACM1 에 leader 가 있을 때 follower_port=ACM1 로 적혀있어도 통신 시도 → calibration mismatch / 모터 ID 충돌로 늦게 발견)
- **권장 컨벤션** (메모리 [project_smolvla_arm_serial_mapping](../../../.claude/projects/-home-laba/memory/project_smolvla_arm_serial_mapping.md) §How to apply 일관):
  ```yaml
  hardware:
    follower_port: /dev/serial/by-id/usb-1a86_USB_Single_Serial_5B42138563-if00
    leader_port:   /dev/serial/by-id/usb-1a86_USB_Single_Serial_5B42138566-if00
    camera_top_index: 0     # 카메라는 hub 위치 기반이라 enumeration 변동 적음 — 유지
    camera_wrist_index: 2
  ```
  - 좌측 팔 시리얼 (현재 base_config 대상): follower `5B42138563`, leader `5B42138566`
  - 우측 팔 시리얼 (gesture 작업용): follower `5AE6082773`, leader `5AE6056701`
- **시리얼 확인 방법** (한 줄):
  ```bash
  ls -la /dev/serial/by-id/ | grep USB_Single_Serial
  # 결과 예: usb-1a86_USB_Single_Serial_5B42138563-if00 -> ../../ttyACM0
  #         (시리얼 → 현재 ttyACMx 매핑 한눈에)
  ```
  - 또는 `lerobot-find-port` (인터랙티브 — 케이블 뽑았다 꽂아 매핑 확정)
  - 부팅마다 변동 가능한 ACM 번호 대신 *시리얼이 진실의 원천*
- **조치**:
  1. `dgx/finetune/leftarm_v2/config/base_config.yaml` 의 `hardware.follower_port` / `leader_port` 를 by-id 경로로 교체
  2. `_lib.py` 의 `get_hardware` 가 by-id 경로도 정상 처리하는지 검증 (`os.path.expanduser` + `Path` 만 거치므로 그대로 동작 예상)
  3. (선택) `check_port_and_camera_index.py` 가 시리얼 ↔ ACM 매핑을 출력하도록 보강
  4. `base_config.yaml` 주석 갱신: "`/dev/ttyACMx` 직접 표기는 swap 위험" 안내 추가
- **영향**:
  - 매 swap 마다 base_config 수동 갱신 → 0 (자동 안정)
  - 잘못된 ACM 으로 가리켜 *런타임 늦게 발견* 되는 사고 회피
  - 같은 base_config 가 다른 노드 (gesture 작업용 우측 팔도 같은 패턴) 에도 그대로 적용 가능
- **위험 / 검토 필요**:
  - lerobot 의 `--robot.port` 인자가 symlink 경로를 정상 resolve 하는지 확인 (대부분 OK 추정, 1차례 dry-run 검증 필요)
  - by-id 경로가 길어 yaml 가독성 약간 ↓ (단 anchor 로 분리해 정리 가능)
- **우선순위 🔥 사유**: 하루에 매핑 3회 swap → 다음 세션 (혹은 Orin 추론 끝나고 돌아올 때마다) 같은 시나리오 반복 예상. 현재 14차까지 진행했으나 향후 15차 이후 동일 swap 으로 시간 낭비 가능

### 💡 [ ] check_hardware.sh 에 카메라 ↔ 노드 매핑 자동 출력 추가

- **발견**: 2026-05-11, data_collection.md §2 에서 `v4l2-ctl --list-devices` 를 별도 실행해서 매핑 확인
- **트리거**: lerobot-find-cameras 만으로는 "어느 카메라가 어느 /dev/videoN 짝꿍을 가지는지" 명확하지 않음 (보조 노드 / 캡처 노드 구분이 사용자 몫)
- **조치**: [check_hardware.sh](../scripts/check_hardware.sh) 의 OpenCV 카메라 발견 단계에서 `v4l2-ctl --list-devices` 출력을 통합 표시
- **영향**: 카메라 매핑 단계 자동화 → 시연장 이동 시 헷갈림 ↓

---

## 학습 / 추론 — DGX 학습 잠정 중단 (2026-05-17)

DGX 학습 backlog 항목들은 *학습 노드 prof_computer 이관* 으로 *현역 backlog 에서 분리*. 보존:

- 학습 / 추론 backlog (역사적 자료): [`../../legacy/train_trial_2026-05-17/docs/backlog_legacy.md`](../../legacy/train_trial_2026-05-17/docs/backlog_legacy.md)
- 종료 사유 + 이관 경로: [`../../legacy/train_trial_2026-05-17/README.md`](../../legacy/train_trial_2026-05-17/README.md)

현 학습 backlog 는 *prof_computer 측에서 재정의* — 본 문서는 *DGX 수집 backlog* 만 누적.

---

## 문서

### 💡 [ ] training.md / data_collection.md 의 명령 패치를 정기적으로 검증

- **발견**: 2026-05-11, 사용자가 실행하면서 발견한 명령 오류들이 여러 개 (mkdir -p 충돌, wandb.entity 잘못 지정, --resume 시 --dataset.root 누락 등)
- **트리거**: 문서의 명령은 작성 시점 ↔ 실행 시점 간 변동 가능 (lerobot upstream 업데이트, 자체 스크립트 변경)
- **조치**: 마일스톤 진입 시점 (예: 본 100 episodes 수집 시작 전, 본 학습 시작 전) 명령 1회 dry-run 검증 — `--steps=1` / `--num_episodes=1` 같은 최소 실행 옵션 활용
- **영향**: 본 작업 중간에 막히는 빈도 ↓

---

## 완료된 항목 (참고용)

### [x] HF Hub 수동 push 절차 정립 (2026-05-11 완료)
- 배경: 2차 수집 종료 시 그리퍼 overload → disconnect() 크래시 → push_to_hub skip
- 조치: `LeRobotDataset(repo_id=..., root=...).push_to_hub(tags=..., private=False)` Python 한 줄로 복구 가능. 이 패턴은 [메모리](../../.claude/projects/-home-laba/memory/project_lerobot_push_hub_crash_recovery.md) 에 저장됨

### [x] data_collection.md instruction 변경 (2026-05-11 완료)
- 배경: 시연장 환경 한계로 "left/right" 구분 불가
- 조치: `"Pick up the doll and reach forward"` 로 변경. 이전 instruction (left/right) 의 테스트 10개 episodes 는 dataset 삭제 후 재시작
