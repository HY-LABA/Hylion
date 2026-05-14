# dgx/gestures — Replay 용 trajectory 저장소

> SmolVLA / ACT 학습 데이터와 **별개** 의, 트리거 기반 고정 동작 (인사·절·포인팅 등) 용 단일 episode trajectory 저장 위치.
> 가이드: [../docs/gestures.md](../docs/gestures.md)
> 녹화: [../scripts/record_gesture.sh](../scripts/record_gesture.sh)

---

## 디렉터리 구조

```text
dgx/gestures/
├── README.md                    # 본 문서
├── <gesture_name>/              # record_gesture.sh 가 생성. snake_case 이름
│   ├── meta/
│   │   ├── info.json            # total_episodes=1, total_frames=N, fps=30, features
│   │   ├── stats.json
│   │   ├── tasks.parquet
│   │   └── episodes/...
│   └── data/chunk-000/file-000.parquet  # action / observation.state 컬럼만 (video 없음)
└── <other_gesture>/...
```

`leftarm_v1` (학습 dataset) 과 어떻게 다른가:

| 항목 | `leftarm_v1` (학습용) | `gestures/<name>` (replay 용) |
|---|---|---|
| 위치 | `${HF_HOME}/lerobot/${HF_USER}/leftarm_v1/` | `dgx/gestures/<name>/` (HF cache 밖) |
| Episodes | 40~100 | **1** |
| 카메라 / 비디오 | 2대 (top, wrist) | **없음** (motors only) |
| HF Hub push | true | **false** (로컬 전용) |
| 길이 | ~17s × N | ~5s × 1 |
| 용도 | SmolVLA fine-tune | `lerobot-replay` 로 그대로 재생 |

---

## 운영 규칙

1. **하나의 gesture = 하나의 디렉터리 = 하나의 episode**. 변형 (예: 빠른 wave vs 느린 wave) 은 `wave_fast`, `wave_slow` 로 분리 — episode index 로 구분하지 말 것
2. **이름 규약**: snake_case, 첫 글자 소문자, 영문/숫자/언더스코어만 (`wave_hello`, `bow_short`, `point_left`)
3. **재캘리브레이션 금지**: 본 디렉터리의 trajectory 는 모두 `${FOLLOWER_ID}` 캘리브레이션의 좌표계 위에 있음. 재캘리브하면 전부 무효
4. **rsync 제외 X**: 본 디렉터리는 rsync 배포 대상 (DGX → Jetson). [../scripts/sync_gesture_to_orin.sh](../scripts/sync_gesture_to_orin.sh) 가 처리
5. **우측 팔 전용** (2026-05-13~): 좌측은 SmolVLA `leftarm_v1` / 학습·추론 전담. 본 디렉터리의 모든 trajectory 는 `rightarm_test_follower` 캘리브레이션 좌표계. 좌측 팔로 녹화 시 env override (`FOLLOWER_ID=leftarm_test_follower ...`) 가능하지만 그러면 좌측 SmolVLA inference 와 USB 충돌하므로 권장 X — 자세한 분담은 [../docs/gestures.md §0-1](../docs/gestures.md#0-1-본-시스템-적용-현황--양팔-배치-2026-05-13-기준)

---

## 참조

- [../docs/gestures.md](../docs/gestures.md) — 녹화·재생 가이드
- [../docs/gestures_jetson_setup_prompt.md](../docs/gestures_jetson_setup_prompt.md) — Jetson 측 replay 구현용 AI 프롬프트
- [../scripts/record_gesture.sh](../scripts/record_gesture.sh)
- [../scripts/sync_gesture_to_orin.sh](../scripts/sync_gesture_to_orin.sh)
