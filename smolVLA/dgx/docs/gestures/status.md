# 현황 스냅샷 (DGX SmolVLA / leftarm_v1)

> **최종 갱신**: 2026-05-13
> **목적**: 데이터 수집·학습 진행 상황을 한 화면에서 파악. 가이드 문서가 *어떻게 하는지* 라면 본 문서는 *지금 어디까지 와있는지*.
> **자매 문서**: [README.md](../README.md) (환경), [data_collection.md](data_collection.md) (수집 가이드), [training.md](training.md) (학습 가이드), [gestures.md](gestures.md) (gesture 시스템), [backlog.md](backlog.md) (오픈 항목)

---

## 1) 환경

| 항목 | 상태 |
|---|---|
| 노드 구조 | DGX Spark **단일 노드** (수집 + 학습 + Hub push 통합. DataCollector 노드는 2026-05-03 부로 종료) |
| venv | `~/smolvla/dgx/.arm_finetune` (PyTorch 2.10.0+cu130, lerobot editable) |
| HF cache | `/home/laba/smolvla/.hf_cache/` (Walking RL 와 격리) |
| HF user | `BaboGaeguri` (`hf auth login` 완료) |
| Walking RL 동시 가동 | ⚠ 본 학습은 **잔여 자원만 사용** — preflight 통과 후 진행 원칙 |
| `peft` 패키지 | 현 venv 에 **수동 설치 완료**. setup_finetune_env.sh 자동화는 [backlog](backlog.md) 🔥 항목 |

---

## 2) 하드웨어 배치

### 양팔 배치 현황 (2026-05-13)

본 프로젝트는 SO-101 **양팔** 환경입니다. 좌·우 follower + leader 각각 1쌍 (총 4 devices) 물리 배치 완료.

| 팔 | 역할 | 캘리브레이션 | 사용 시스템 |
|---|---|---|---|
| **좌측** | SmolVLA 학습·추론 전담 | ✅ 완료 (2026-05-11) — `leftarm_test_follower`, `leftarm_test_leader` | `leftarm_v1` dataset, SmolVLA fine-tune |
| **우측** | Gesture 전담 | ⬜ **미수행** — 녹화 전 1회 필요. id 규약: `rightarm_test_follower`, `rightarm_test_leader` | [gesture 시스템](gestures.md) |

### 좌측 팔 직전 확인 값 (2026-05-11 기준 — 우측 팔 추가 후 enumeration 변동 가능)

| 디바이스 | 포트 / 인덱스 | 식별자 |
|---|---|---|
| SO-ARM follower (좌) | `/dev/ttyACM0` | serial `5B42138563`, id `leftarm_test_follower` |
| SO-ARM leader (좌)   | `/dev/ttyACM1` | serial `5B42138566`, id `leftarm_test_leader` |
| Top camera (YJX-C5) | `/dev/video0` | `width=480, height=640, rotation=-90, MJPG@30fps` |
| Wrist camera (Innomaker U20CAM-720P) | `/dev/video2` | `width=640, height=480, MJPG@30fps` |

### 우측 팔 (미확인 — 사용자 가용 시 1회 lerobot-find-port 필요)

| 디바이스 | 포트 / 인덱스 | 식별자 |
|---|---|---|
| SO-ARM follower (우) | ⬜ 미확인 | serial 미기록, id `rightarm_test_follower` (계획) |
| SO-ARM leader (우)   | ⬜ 미확인 | serial 미기록, id `rightarm_test_leader` (계획) |

> **enumeration 안정성 권고**: 4 devices 환경에서는 `/dev/ttyACM*` 번호가 부팅마다 변동 가능. serial 기반 udev rule (`/dev/so_arm_left_follower` 등 고정 심볼릭) 채택을 [backlog](backlog.md) 신규 항목으로 검토 권장.

캐리브레이션 파일 위치: `${HF_HOME}/lerobot/calibration/{robots/so_follower,teleoperators/so_leader}/<id>.json`.

---

## 3) 데이터셋 현황

### `BaboGaeguri/leftarm_v1`

| 항목 | 값 |
|---|---|
| Task instruction | `"Pick up the doll and reach forward"` |
| Episodes (누적) | **40 / 100** (목표) |
| Frames | **21,352** (평균 ~17.8s / episode) |
| FPS | 30 |
| Tasks | 1 |
| Tags | `smolvla, so101, leftarm, doll, hylion` |
| 로컬 경로 | `/home/laba/smolvla/.hf_cache/lerobot/BaboGaeguri/leftarm_v1/` |
| HF Hub | https://huggingface.co/datasets/BaboGaeguri/leftarm_v1 (public) |
| 수집 차수 진행 | 1차 (10) → 2차 resume (30 추가 → 40) 완료. 3~6차 미진행 |

### 수집 인시던트 (이력)

- **2026-05-11**: 1차 instruction 변경 — "left/right" 구분 불가 → `"Pick up the doll and reach forward"` 로 재시작 (이전 10 episodes dataset 삭제 후 fresh)
- **2026-05-11**: 2차 resume 종료 시 그리퍼 (motor id=6) overload 로 `disconnect()` 크래시 → push_to_hub 자동 skip. 로컬 episodes 는 안전, 수동 `LeRobotDataset(...).push_to_hub(...)` 로 복구 ([memory: lerobot_push_hub_crash_recovery](../../.claude/projects/-home-laba/memory/project_lerobot_push_hub_crash_recovery.md))

### `dgx/config/dataset_repos.json`

⚠ 현재 placeholder (`example_dataset`) 만 등록됨. `leftarm_v1` 메타 반영은 [backlog](backlog.md) ⚙ 항목.

---

## 4) 학습 현황

### 완료된 run

| Run ID | 날짜 | 설정 | Steps | 산출물 | 비고 |
|---|---|---|---|---|---|
| `leftarm_v1_explore_2026-05-11_17-01-25` | 2026-05-11 | 초기 시도 | — | 체크포인트 없음 | num_workers=8 시스템 메모리 100% 도달 → 강제 중지 |
| `leftarm_v1_explore_2026-05-11_17-04-20` | 2026-05-11 | **LoRA all-linear r=16** | **500** | `checkpoints/000250/`, `000500/`, `last/` | adapter 46MB. wandb 활성. 의도된 5000 step 미완 (조기 중단) |

### 활성 체크포인트

```
~/smolvla/dgx/outputs/leftarm_v1_explore_2026-05-11_17-04-20/checkpoints/last/pretrained_model/
├── adapter_config.json          # LoRA r=16, 17개 target_modules (q/k/v/o_proj, fc1/2, gate/up/down, action_*, state_proj, lm_head, proj)
├── adapter_model.safetensors    # 46 MB — adapter weights 만
├── config.json
├── policy_pre/postprocessor.json + .safetensors
└── train_config.json
```

**주의**: LoRA adapter 만 저장됨 (base 가중치 없음). Inference 호출 시 [backlog ⚙ "LoRA adapter inference 명령 검증"](backlog.md) 항목 미해결 — 첫 실 추론 전 lerobot 의 adapter 자동 로딩 확인 필요.

### 학습 stage / 자원 정책 정리

- 권장 첫 시도: **LoRA all-linear r=16** (training.md §2 결론)
- preflight 시나리오: `s1` (35GB) 통과 시 OK. 실제 LoRA all-linear 메모리 ~35-40GB
- batch_size=16, num_workers=8 (Walking RL 미가동 시), save_freq=250

---

## 5) 다음 단계 (제안)

### 5-1. 데이터 수집 재개 (40 → 60+)

- 차수 표 ([data_collection.md §5-2](data_collection.md)): 다음은 **3차 resume (+20, 누적 60)**
- 명령: 기존 §5-2 명령에서 `--dataset.num_episodes=20`, `--resume=true`, `--dataset.root=${HF_HOME}/lerobot/${HF_USER}/leftarm_v1`
- 시연 패턴 권장 ([backlog](backlog.md) ⚙): 그리퍼 살짝 열고 종료 / 20 episodes 마다 휴식 / 100 풀 수집 시 USB 사이클
- 세션 시작 전: `pkill -f "rerun_sdk/rerun_cli/rerun"` (orphan viewer 정리), `bash dgx/scripts/check_hardware.sh`

### 5-2. 학습 재시도 (40 episodes, full 5000 steps)

- num_workers `8 → 4` 로 낮춤 ([backlog 🔥](backlog.md) "num_workers 가이드라인")
- rerun orphan 사전 정리 후 시작
- wandb run name 표준화: `leftarm_v1_lora-all-r16_2026-05-13` 같은 패턴
- 5000 step 완주 → §5-2 inference 검증 → 성공률 ≥ 60% 면 60+ episodes 추가 수집

### 5-3. Inference 검증 경로

- LoRA adapter 케이스에서 `--policy.path` 인자가 lerobot 에서 어떻게 해석되는지 확인 ([backlog ⚙](backlog.md))
- 첫 실 추론에서는 follower 동작 범위 사전 제한 / safe pose 부터 시작

---

## 6) 오픈 백로그 요약 ([backlog.md](backlog.md) 참조)

| 우선순위 | 항목 | 영향 |
|---|---|---|
| 🔥 | `setup_finetune_env.sh` 에 `peft` extra 추가 | venv 재구축 시 LoRA 자동 가능 |
| 🔥 | 학습 시 num_workers 가이드라인 (8 → 4) | 시스템 메모리 100% 회피 |
| ⚙ | 그리퍼 overload 방지 시연 패턴 가이드 | 다음 resume 차수 크래시 예방 |
| ⚙ | `dataset_repos.json` 에 `leftarm_v1` 등록 | 메타 일관성 |
| ⚙ | `dgx/runs/05_leftarm/train.sh` 셸 스크립트화 | 학습 명령 재사용성 |
| ⚙ | LoRA adapter inference 명령 검증 | 실기 검증 단계 막힘 방지 |
| ⚙ | v4l2-utils 사전 설치 / check_hardware.sh 안내 | 새 환경 셋업 시 카메라 매핑 |
| ⚙ | 평가 dataset 명명 규칙 + Hub push 정책 | Hub repo 정리 |
| 💡 | 다양한 nice-to-have (rerun orphan 자동 정리, wandb 명명 규칙 등) | 운영 안정성 |

---

## 7) Gesture 시스템 (학습과 별개 트랙)

SmolVLA / ACT 와 무관한 트리거 기반 고정 동작 (인사·절·포인팅 등) 을 위해 lerobot 의 record/replay 메커니즘을 활용한 시스템. 자세한 설계 / 안전 / 운영은 [gestures.md](gestures.md), Jetson 측 구현용 AI 프롬프트는 [gestures_jetson_setup_prompt.md](gestures_jetson_setup_prompt.md).

### 구축 현황 (2026-05-13)

| 항목 | 상태 |
|---|---|
| DGX 측 녹화 환경 | ✅ 완료 — [scripts/record_gesture.sh](../scripts/record_gesture.sh), [scripts/sync_gesture_to_orin.sh](../scripts/sync_gesture_to_orin.sh) |
| DGX 측 저장 디렉터리 | ✅ [gestures/](../gestures/) (README 포함, 빈 상태) |
| 가이드 문서 | ✅ [docs/gestures.md](gestures.md) (전체 흐름·안전·트러블슈팅, 양팔 분담 명시) |
| Jetson 측 구현 프롬프트 | ✅ [docs/gestures_jetson_setup_prompt.md](gestures_jetson_setup_prompt.md) (대기 — Jetson 세션에서 실행) |
| **우측 팔 USB 포트 식별** | ⬜ 미수행 — `lerobot-find-port` × 2 (follower, leader) |
| **우측 팔 캘리브레이션** | ⬜ 미수행 — `run_teleoperate.sh calibrate-follower/-leader` (env: `FOLLOWER_ID=rightarm_test_follower`, `LEADER_ID=rightarm_test_leader`) |
| 실제 gesture 녹화 (`wave_hello` 등) | ⬜ 미수행 (위 우측 캘리브 완료 후) |
| Jetson 측 replay wrapper | ⬜ 미수행 (위 프롬프트로 Jetson Claude Code 에 위임 예정) |
| 첫 실 재생 검증 | ⬜ 미수행 |

### 팔 분담 정책 (확정)

| 팔 | 시스템 | USB 동시성 |
|---|---|---|
| 좌측 | SmolVLA inference (Jetson, 향후) / SmolVLA training dataset 좌표계 보존 | 우측과 다른 포트라 동시 운영 가능 |
| 우측 | Gesture record (DGX) / Gesture replay (Jetson) | 좌측과 무관 |

→ 양팔 환경에서는 좌측 SmolVLA inference + 우측 gesture replay 동시 실행 가능 (USB mutex 영향 X). 이전 단일팔 시나리오의 mutex 제약 자동 해소.

### 다음 트리거 시점

1. **사용자 SO-ARM 가용** → DGX 에서:
   - (1-1) `lerobot-find-port` × 2 → 우측 follower / leader 포트 확인 (4 devices enumeration)
   - (1-2) 우측 팔 캘리브레이션 2회 (`calibrate-follower`, `calibrate-leader` — env 로 우측 id / 포트 지정)
   - (1-3) `bash scripts/record_gesture.sh wave_hello` (스크립트 기본값이 우측 팔로 설정됨)
2. (선택) DGX 에서 빈 공간 trajectory 검증 재생
3. `bash scripts/sync_gesture_to_orin.sh wave_hello` (사전 `ORIN_HF_HOME`, `ORIN_GESTURES_ROOT` export)
4. Jetson 측 Claude Code 세션에서 [gestures_jetson_setup_prompt.md §10](gestures_jetson_setup_prompt.md#10-ai-에이전트용-프롬프트-jetson-측-claude-code-세션에-복붙) 의 프롬프트 복붙 → wrapper 구현
5. 첫 실 재생 검증 (빈 공간, 사용자 입회)

---

## 8) 본 문서 갱신 시점

다음 시점에 본 문서 §3 / §4 / §5 를 갱신:

1. 데이터 수집 차수 종료 시 (episode / frame 카운트)
2. 학습 run 종료 시 (Run ID / checkpoint 위치 / 의미있는 결과)
3. backlog 항목 ✅ 처리 시 (§6 표에서 제거)
4. 환경 / 하드웨어 식별자 변경 시 (시연장 이동 등 — §1, §2)
