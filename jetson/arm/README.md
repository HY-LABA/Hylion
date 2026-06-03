# jetson/arm

SO-ARM101 팔 제어 레이어. gesture 데이터 저장 및 재생을 담당한다.

```
arm/
├── data/                            # LeRobotDataset 포맷 gesture 데이터
│   ├── wave_hello/                  # 오른팔 wave 동작 (1번)
│   ├── wave_hello_2/                # 양팔 wave 동작 (2번)
│   └── pick_object/                 # 물건 집기 동작
│                                    # (HuggingFace BaboGaeguri/leftarm_v2 마지막 에피소드)
│       ├── data/chunk-000/
│       │   └── file-000.parquet    # 프레임별 action 데이터 (6 motor × N frames)
│       └── meta/
│           ├── info.json           # fps, total_frames, action motor 이름 목록
│           ├── stats.json          # action 컬럼 통계 (min/max/mean/std)
│           ├── tasks.parquet       # 태스크 설명 레이블
│           └── episodes/
│               └── chunk-000/
│                   └── file-000.parquet  # 에피소드 메타 (길이, 청크 위치)
│
├── gestures/                        # gesture 재생 실행 파일
│   ├── play_gesture.sh              # 진입점: gesture 1회 재생
│   │                                #   venv 활성화 → pre-check → LD_LIBRARY_PATH → replay
│   │                                #   exit 0=성공 / 2=인자오류 / 3=환경 / 4=데이터 / 5=포트 / 1=실패
│   ├── play_both_wave.sh            # 양팔 동시 wave 재생 (wave_hello_2 × 좌우)
│   ├── replay_gesture.py            # 1회성 재생 CLI (play_gesture.sh 가 호출)
│   ├── gesture_replay_core.py       # 재생 공유 라이브러리
│   │                                #   ensure_ld_library_path() : cusparselt 경로 보정
│   │                                #   load_episode()           : parquet → action 리스트
│   │                                #   connect_arm()            : SO101 follower 연결
│   │                                #   replay_episode()         : 30fps send_action 루프
│   └── gesture_daemon.py            # 상주 데몬 (coordinator 통합용)
│                                    #   lerobot + 팔 연결을 warm 상태로 유지 → cold-start 제거
│                                    #   Unix 소켓(/tmp/hylion_gesture.sock)으로 명령 수신
│                                    #   프로토콜: play <name> / ping / status / shutdown
│
└── utils/                           # 유틸리티 스크립트
    ├── check_gesture_ready.sh       # 재생 전 5단계 사전점검 (모터 미구동)
    │                                #   venv → replay_gesture.py → pyarrow → info.json → 캘리브 → 포트
    └── fetch_hf_gesture.py          # HuggingFace 데이터셋 → gesture 포맷 변환
                                     #   지정 repo의 마지막(또는 특정) 에피소드만 다운로드
                                     #   frame_index / episode_index 재정규화 후 data/ 에 저장
```

## 파일 간 의존 관계

```
play_gesture.sh
  ├─ utils/check_gesture_ready.sh     (사전점검)
  └─ gestures/replay_gesture.py       (재생)
       └─ gestures/gesture_replay_core.py

gesture_daemon.py  (coordinator → gesture_client.py 가 기동)
  └─ gestures/gesture_replay_core.py

fetch_hf_gesture.py  (독립 실행)
  └─ 결과물을 data/ 에 저장
```

## 환경 변수

| 변수 | 기본값 | 설명 |
|---|---|---|
| `FOLLOWER_PORT` | `/dev/serial/by-id/usb-...-5AE6082773-if00` | follower 시리얼 포트 |
| `FOLLOWER_ID` | `rightarm_test_follower` | 캘리브레이션 파일명 |
| `ORIN_GESTURES_ROOT` | `~/Hylion/jetson/arm/data` | gesture 데이터 루트 |
| `JETSON_VENV` | `~/smolvla/orin/.hylion_arm` | lerobot venv 경로 |

## 캘리브레이션 파일 위치

`~/.cache/huggingface/lerobot/calibration/robots/so_follower/<FOLLOWER_ID>.json`
