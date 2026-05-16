# dgx/finetune/ — 데이터셋별 fine-tune 사이클 설정·래퍼

각 하위 폴더 = 하나의 dataset 의 "수집 → 학습 → 추론" 사이클 단위. `dgx/docs/finetune/` (how-to 가이드) 와 구분 — 본 디렉터리는 *그 데이터셋의 실제 설정값 + 실행 래퍼* 를 보관한다.

## 구조

```
dgx/finetune/
├── README.md
├── leftarm_v1/                       # 동결 — 구 task "Pick up the doll and reach forward" (40 ep)
│   └── config/{base,record,train}_config.yaml   # frozen 기록 (스크립트 없음)
└── leftarm_v2/                       # 본 era 작업 대상 — 2 task pick-and-place (realplaying.md M1·M2)
    ├── _lib.py                        # run_*.py 공용 헬퍼
    ├── check_port_and_camera_index.py # ① 포트·카메라 인덱스 찾기 (lerobot-find-port/cameras)
    ├── run_teleop.py                  # ② 셋업 검증 — lerobot-teleoperate (데이터 저장 X)
    ├── run_record.py                  # ③ 데이터 수집 — lerobot-record
    ├── run_train.py                   # ④ 학습 — lerobot-train 래퍼
    ├── convert_to_image.py            # ⑤ video dataset → image dataset 변환 (M1.5 OOM 대응)
    ├── experiments/                   # M1.5 — 학습 OOM 진단 실험 스크립트·절차 문서
    │   ├── cleanup_helper.sh          # 학습 전 환경 정리 헬퍼 (VSCode/Claude/Firefox kill + 메모리 검증)
    │   └── exp_a_cleanup_attempt3.md  # 실험 A: cleanup 강화 + 시도 3 절차 + 결과 양식
    └── config/
        ├── base_config.yaml           # 셋업 컨텍스트
        ├── record_config.yaml         # 수집 job 파라미터
        └── train_config.yaml          # 학습 job 파라미터 (M2 — 현재 [TBD-M2] skeleton)
```

## config 3-파일 분할

| 파일 | 성격 | 내용 |
|---|---|---|
| `base_config.yaml` | **셋업 컨텍스트** (record·teleop·train 공용) | 식별(`name`·`hf_repo_id`·`status`), 저장 위치(`paths`), 계정(`accounts`: hf_user·wandb), **물리 셋업(`robot`·`teleop`·`cameras`)**, `calibration`(파일 위치·메타), `hardware`(포트·카메라 인덱스) |
| `record_config.yaml` | **수집 job** | `dataset`(fps·episode_time_s·vcodec·tags 등 `--dataset.*`), `record_opts`(display_data·play_sounds), `tasks`(instruction·episode 배분) |
| `train_config.yaml` | **학습 job** | policy_path·method(lora/full)·하이퍼파라미터 — M2 spec 에서 확정 |

> `robot`/`teleop`/`cameras`/`calibration`/`hardware` 는 record·teleop 이 공유하는 *물리 셋업* — train 은 미사용. record_config 는 순수 "무엇을·어떻게 수집할지" 만.

## 안정값 vs 세션값 — 둘 다 yaml 직접 입력

| | 내용 |
|---|---|
| **안정값** | dataset `repo_id`·instruction, 카메라 녹화 파라미터(rotation·fourcc·해상도), robot/teleop type·id, 하이퍼파라미터, 저장 위치·계정 — yaml 에 그대로 |
| **세션 의존값** (`base_config.hardware`) | USB 포트 `/dev/ttyACM*`, 카메라 `/dev/videoN` 인덱스 — enumeration 의존이라 부팅·재연결마다 변동. **yaml 에 직접 입력**하되, 확인 전엔 `null` → run_*.py 가 **무조건 에러** |

> ⚠️ `hardware` 는 env 변수 메커니즘도 fallback 도 아니다. `check_port_and_camera_index.py` 로 확인한 값을 매 세션 `base_config.yaml` 에 직접 갱신한다. `null` = 미확인 → 에러 (잘못된 값으로 조용히 실행되는 사고 방지).

> 📌 **`base_config.yaml` 은 `deploy_dgx.sh` 동기화 대상에서 제외**된다 (hardware 섹션이 DGX 로컬 세션값이라 repo 의 `null` 템플릿이 덮어쓰지 않도록). DGX 에서 직접 갱신한 값은 배포에도 보존된다. 반대로 안정값 필드(`robot`/`teleop`/`cameras`/`calibration`/`paths`/`accounts`)를 repo 에서 고쳤다면 그 파일만 수동 rsync 해야 DGX 에 반영된다.

## 워크플로우 (leftarm_v2)

```
① python check_port_and_camera_index.py    # 포트·카메라 인덱스 찾기
   → 결과를 config/base_config.yaml 의 hardware 섹션에 직접 입력
② python run_teleop.py                      # 셋업 검증 (calibration·포트·카메라·모터 정합)
③ python run_record.py record --task N --episodes M   # 데이터 수집 (차수별)
```

모든 스크립트: venv 활성화 후 (`source ~/smolvla/dgx/.arm_finetune/bin/activate`) `leftarm_v2/` 에서 실행. `--dry-run` 으로 명령만 미리 확인 가능.
