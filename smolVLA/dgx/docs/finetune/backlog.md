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

### 🔥 [ ] setup_finetune_env.sh 에 `peft` extra 추가

- **발견**: 2026-05-11, training.md §2-1 LoRA 학습 첫 실행 시 `ModuleNotFoundError: No module named 'peft'`
- **트리거**: 현재 [setup_finetune_env.sh](../scripts/setup_finetune_env.sh) 의 lerobot 설치가 `lerobot[smolvla]` 만 포함. PEFT (LoRA) 사용 시 필요한 `lerobot[peft]` extra 누락
- **조치**: 스크립트의 lerobot 설치 라인을 `pip install -e ${LEROBOT_SRC}[smolvla,peft]` 로 변경 (또는 별도 라인 추가)
- **영향**: venv 재구축 시 PEFT 자동 설치되어 LoRA 학습 즉시 가능. 현재 venv 에서는 이미 수동 설치 완료 (`pip install -e ~/smolvla/docs/reference/lerobot[peft]`)
- **검증**: 새 venv 만든 뒤 `python -c "import peft; print(peft.__version__)"` 가 동작

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

### 💡 [ ] check_hardware.sh 에 카메라 ↔ 노드 매핑 자동 출력 추가

- **발견**: 2026-05-11, data_collection.md §2 에서 `v4l2-ctl --list-devices` 를 별도 실행해서 매핑 확인
- **트리거**: lerobot-find-cameras 만으로는 "어느 카메라가 어느 /dev/videoN 짝꿍을 가지는지" 명확하지 않음 (보조 노드 / 캡처 노드 구분이 사용자 몫)
- **조치**: [check_hardware.sh](../scripts/check_hardware.sh) 의 OpenCV 카메라 발견 단계에서 `v4l2-ctl --list-devices` 출력을 통합 표시
- **영향**: 카메라 매핑 단계 자동화 → 시연장 이동 시 헷갈림 ↓

---

## 학습

### ⚙️ [ ] dgx/runs/05_leftarm/ 디렉토리 + train.sh 셸 스크립트화

- **발견**: 2026-05-11, [dgx/runs/README.md](../runs/README.md) 에 따르면 마일스톤 진입 시 채우는 구조
- **트리거**: 현재 학습 명령이 training.md 내 코드블록에 있어 매번 복붙. `runs/05_leftarm/train.sh` 로 셸 스크립트화하면 1줄 실행 가능
- **조치**: §5 leftarmVLA 마일스톤 진입 시 ([dgx/runs/README.md](../runs/README.md) 참조 — 구조 가이드 있음):
  - `dgx/runs/05_leftarm/train.sh` — 현재 training.md §2-1 명령 셸 스크립트화 (LoRA all-linear r=16)
  - `dgx/runs/05_leftarm/README.md` — 학습 가이드 (학습 실행 / 모니터링 / 결과 해석)
  - `dgx/runs/05_leftarm/notes.md` — exploratory 결과 / 이슈 / 재실험 메모
- **영향**: 학습 명령 / 인자 재사용성 ↑, 실수 가능성 ↓

### ⚙️ [ ] LoRA adapter inference 명령 검증

- **발견**: 2026-05-11, training.md §5-2 의 inference 명령은 full-FT 체크포인트 가정 (`--policy.path="${OUTPUT_DIR}/checkpoints/last/pretrained_model"`)
- **트리거**: LoRA 학습 결과는 adapter 만 저장됨 (base model 가중치 없음). full-FT 와 inference 호출 방식이 다를 수 있음
- **조치**:
  1. 첫 LoRA 학습 완료 후 `checkpoints/last/` 디렉토리 구조 확인 — LoRA adapter 파일 (예: `adapter_config.json`, `adapter_model.safetensors`) 가 어떻게 저장되는지
  2. lerobot 가 LoRA adapter 자동 로딩 지원하는지 (peft_model.from_pretrained 경로 등) 확인
  3. training.md §5-2 inference 명령을 LoRA 케이스로 갱신
- **영향**: exploratory 학습 후 실기 검증 단계에서 막힘 방지

### 🔥 [ ] 학습 시 시스템 메모리 100% 회피 — num_workers 가이드라인

- **발견**: 2026-05-11, LoRA all-linear 학습 중 System Memory Utilization 이 step 100 이후 100% 도달 → UI lag → 강제 중지
- **트리거**: `num_workers=8` + 큰 video dataset (40 ep, 21K frames) + 다른 프로세스 (rerun ×4, claude code ×21) 합산
- **조치**: training.md §2-1 명령의 `num_workers` 기본값을 `4` 로 낮추고, 학습 직전 권장 명령에 다음 추가:
  ```bash
  pkill -f "rerun_sdk/rerun_cli/rerun" 2>/dev/null || true
  ```
  + training.md §3 (모니터링) 에 `System Memory Utilization` 항목 명시 — 95% 초과 시 즉시 중단 권장
- **영향**: 학습 안정성. 100% 메모리 도달 시 학습 자체는 진행되지만 시스템 UI 응답성 손실

### 💡 [ ] wandb run 비교를 위한 일관된 명명 규칙

- **발견**: 2026-05-11, exploratory 학습이 여러 번 시도되면서 wandb 에 정렬되지 않은 run 들이 누적
- **조치**: `job_name` 패턴을 `<dataset>_<stage>_<rank>_<date>` 형식으로 표준화 (예: `leftarm_v1_lora-all-r16_2026-05-11`). LoRA / S1 / S3 비교 시 정렬 / 필터링 용이
- **영향**: 다음 차수 / 비교 실험 시 wandb dashboard 가독성 ↑

---

## 추론 / 평가

### ⚙️ [ ] 평가 dataset 명명 규칙 + Hub push 정책

- **발견**: training.md §5-2 에서 `leftarm_v1_eval_$(date +%Y%m%d)` 형식으로 evaluation dataset 생성 예시
- **트리거**: eval dataset 이 학습 dataset 과 별도로 Hub 에 쌓이면 repo 가 많아짐. push_to_hub 여부 / 명명 규칙 정리 필요
- **조치**:
  - eval 은 보통 `push_to_hub=false` 권장 (로컬에만 저장)
  - 필요 시 `<train_dataset>_eval_<date>` 명명
  - 또는 별도 organization / branch 로 분리
- **영향**: HF Hub repo 관리 깔끔

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
