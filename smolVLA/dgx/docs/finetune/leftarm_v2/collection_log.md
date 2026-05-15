# leftarm_v2 — 데이터 수집 로그

> **목적**: `BaboGaeguri/leftarm_v2` 데이터셋의 수집 차수별 실행 기록 — 명령 / 결과 / 관찰 / 이슈.
> **운영**: 차수마다 "수집 차수 로그" 에 entry 추가. 이슈는 "발견된 이슈 / 후속" 에 누적.
> **자매 문서**: [../data_collection.md](../data_collection.md), [../camera_and_codec.md](../camera_and_codec.md), [../backlog.md](../backlog.md). 설정·래퍼는 [dgx/finetune/leftarm_v2/](../../../finetune/leftarm_v2/).

---

## 데이터셋 개요

| 항목 | 값 |
|---|---|
| repo_id | `BaboGaeguri/leftarm_v2` |
| 성격 | 멀티태스크 pick-and-place (단일 dataset, instruction 별 수집) |
| task 1 | "Pick up the blue and yellow doll and place it on the left side of the table" — 목표 100 ep |
| task 2 | "Hand the yellow can to the person" — 목표 100 ep |
| fps | 30 |
| 카메라 | top 480×640 (rotation -90, MJPG), wrist 640×480 (MJPG) |
| 코덱 | `h264_nvenc` (GPU NVENC — leftarm_v1 의 libsvtav1 에서 변경, [camera_and_codec.md §3](../camera_and_codec.md) 근거) |
| episode_time_s / reset_time_s | 60 (상한) / 15 |

---

## 수집 컨벤션

2026-05-15 도입. **vision robustness 용 다양성** — 물체·환경이 어떤 모습이든 task 를 수행할 수 있게.

### 1. 물체 앞/뒷면 (task 1, task 2 공통)

| 물체 | 앞면 (front) | 뒷면 (back) |
|---|---|---|
| 인형 (task 1) | 얼굴이 카메라에 보이게 | 뒤통수가 카메라에 보이게 |
| 캔 (task 2) | 문양이 카메라에 보이게 | 성분표시가 카메라에 보이게 |

### 2. 사람 정보 (task 2 전용)

task 2 instruction (`Hand the yellow can to the person`) 에 "the person" 이 등장 — 받는 사람의 외형(옷·신체) 이 시연마다 다르면 모델이 "어떤 사람이든 건넨다" 를 학습 (vision robustness).

차수별로 한 사람으로 통일하고 로그에 식별 정보 (이름 + 옷차림 등 시각적 구분점) 기록.

**현재 등록 인물**:
| 식별자 | 시각적 구분 | 비고 |
|---|---|---|
| 인혁이형 | 흰색 옷 | 카메라 화각에 적당히 들어옴 |
| 성래 | (좌석 위치 기반) | **화각에서 잘 안 보이는 위치에 앉아있음** — 시각적 구분 약함 |
| (추후 추가) | — | — |

### 규칙 (공통)

- **instruction 은 동일** — orientation / person 은 instruction 에 안 들어감. pick-place·hand-over 동작이 이들과 무관하게 같으므로, *물리적 다양성* 일 뿐 모델이 instruction 으로 구분할 대상 아님
- **차수별로 한 조합** — 한 수집 차수 = 한 orientation (+ task 2 는 한 person). 시연 중 일관 유지 + 로그 추적 명확
- 각 차수 로그 entry 에 `orientation: ...` (task 2 는 추가로 `person: ...`) 명시
- 목표: task 별로 앞/뒤 + 사람 대략 균형

---

## 현재 누적 상태

### 차수별 상세

| 차수 | 날짜 | task | 모드 | +ep | ep index | orientation | person | 누적 T1 | 누적 T2 | 누적 합 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2026-05-15 | 1 (doll) | FRESH | 10 | 0~9 | front (얼굴) | — | 10 | 0 | 10 |
| 2 | 2026-05-15 | 1 (doll) | RESUME | 20 | 10~29 | front (얼굴) | — | 30 | 0 | 30 |
| 3 | 2026-05-15 | 1 (doll) | RESUME | 20 | 30~49 | back (뒤통수) | — | 50 | 0 | 50 |
| 4 | 2026-05-15 | 2 (can) | RESUME | 10 | 50~59 | front (문양) | 인혁이형 (흰옷) | 50 | 10 | 60 |
| 5 | 2026-05-15 | 2 (can) | RESUME | 10 | 60~69 | front (문양) | 성래 (화각 외) | 50 | 20 | 70 |
| 6 | 2026-05-15 | 2 (can) | RESUME | 20 | 70~89 | front (문양) | 성래 (화각 외) | 50 | 40 | 90 |
| 7 | 2026-05-15 | 2 (can) | RESUME | 20 | 90~109 | back (성분표시) | 성래 (화각 외) | 50 | 60 | **110** |

### Orientation 합계

| task | 누적 / 목표 | front | back |
|---|---|---|---|
| task 1 (doll) | 50 / 100 | 30 (차 1·2) | 20 (차 3) |
| task 2 (can) | 60 / 100 | 40 (차 4·5·6) | 20 (차 7) |
| **전체** | **110 / 200** (59,752 frames) | 70 | 40 |

### Person 합계 (task 2 전용)

| person | front | back | 합계 | 해당 차수 |
|---|---|---|---|---|
| 인혁이형 (흰옷) | 10 | 0 | 10 | 차 4 |
| 성래 (화각 외) | 30 | 20 | 50 | 차 5·6·7 |
| **합계** | 40 | 20 | **60 / 100** | — |

> 1~4차 (2026-05-15 컨벤션 도입 전) 의 orientation·person 은 사용자가 사후 분류한 값으로 채움. 5차부터는 시연 시점에 명시 + 일관 유지.

마지막 갱신: 2026-05-15 — 2차 orientation **back → front** 정정 (사용자가 file-001.mp4 확인 결과 얼굴이 보임). 3차 (file-002) 는 미확인, 사용자 원본 메시지 "10(앞).20(뒤),20(뒤)" 기준 back 유지.

---

## 수집 차수 로그

### 1차 — 2026-05-15 · task 1 · 10 episodes · FRESH · **orientation: front (얼굴)**

**명령**:
```bash
python run_record.py record --task 1 --episodes 10
```
(dry-run 으로 명령 미리 확인 후 실행. FRESH 모드 — dataset 신규 생성.)

**결과**:

| 항목 | 값 |
|---|---|
| 수집 episodes | 10 (index 0~9) |
| 총 frames | 6158 |
| 평균 episode 길이 | 616 frames ≈ **20.5초** |
| episode 별 길이 | 585 / 690 / 599 / 562 / 668 / 758 / 508 / 553 / 612 / 623 |
| 재녹화 (`←`) | episode 1 (2회), episode 4 (2회), episode 7 (1회) — 시연 불만족분 폐기 |
| 비디오 크기 | top `file-000.mp4` **4.9 MB** / wrist `file-000.mp4` **20 MB** |
| Hub push | ✅ 성공 — 5 파일, 26.3 MB 업로드 |
| 종료 | ✅ 클린 (disconnect 크래시 없음 — leftarm_v1 과 대비) |

**코덱 — h264_nvenc 첫 적용**:
- `Using video codec: h264_nvenc` 확인
- `Auto-inserting h264_mp4toannexb bitstream filter` 로그 — h264 를 mp4 컨테이너에 넣을 때 정상 동작
- libsvtav1 (leftarm_v1) → h264_nvenc 전환 이유: CPU 인코딩 병목 회피, Walking RL 미가동 ([camera_and_codec.md §3](../camera_and_codec.md))

**관찰 / 이슈**:

1. ⚠️ **FPS warning 여전히 발생 — h264_nvenc 가 명확히 해결 못함**
   - episode 0~6: 각 episode 시작 시 1회씩 warmup 경고 (1.4~3.3 Hz) 후 추가 경고 없음 → 30 Hz 회복 추정
   - episode 7~9: **지속적 18~30 Hz 경고 다수** — steady-state 가 sub-30Hz
   - leftarm_v1 의 libsvtav1 (20~29 Hz) 대비 **명확한 개선 없음** — 오히려 후반 episode 에서 불안정
   - 가설: 인코더 종류 문제가 아니라 카메라 입력 / record loop 의 다른 병목 가능성. **추가 관찰 필요** (→ 후속 항목)

2. `Corrupt JPEG data: 11 extraneous bytes before marker 0xd9` — 1회 출력. USB MJPG 카메라에서 흔한 프레임 디코드 경고, **cosmetic** (해당 프레임만 영향, 학습 무관)

3. **비디오 크기 불균형** — wrist (20 MB) 가 top (4.9 MB) 의 약 4배. 동일 픽셀 수 (480×640 ↔ 640×480) 인데 차이 큼. wrist 카메라(그리퍼 근접뷰)가 모션/디테일이 많아 압축률이 낮은 것으로 추정. 이상 징후는 아님 — 기록만.

4. ⚠️ **task instruction 이 spatial reference 로 변경됨**
   - 현재 task 1: "...place it **on the left side of the table**"
   - leftarm_v1 에서 "left/right" 공간 참조가 시연장 환경 (카메라-물체 근접) 에서 모호해 "reach forward" 로 바꿨던 이력 있음
   - leftarm_v2 는 별도 셋업이라 사용자 판단이지만, **카메라에 "테이블 왼쪽" 이 명확히 grounding 되는지 확인 필요**. 안 되면 같은 모호성 사고 재발 위험
   - task 2 "Hand the yellow can to the person" 도 사람 위치 의존 — 일관성 확인 필요

**검증**:
```
jq '{total_episodes, total_frames, fps}' \
  ~/smolvla/.hf_cache/lerobot/BaboGaeguri/leftarm_v2/meta/info.json
→ total_episodes: 10, total_frames: 6158, fps: 30 ✅
```

---

### 2차 — 2026-05-15 · task 1 · +20 episodes (ep 10~29) · RESUME · **orientation: front (얼굴)**

> 정정 (2026-05-15): 처음 사용자 메시지 "10(앞).20(뒤),20(뒤)" 기준 back 으로 기록했으나, file-001.mp4 확인 결과 얼굴이 보여 front 로 정정.

> 콘솔 로그는 50,000자 제한으로 부분만 확인 (ep 10~19 구간). 본 entry 는 **dataset 실제 상태 (episode parquet) 기준**.

**명령**: `python run_record.py record --task 1 --episodes 20`

| 항목 | 값 |
|---|---|
| 추가 episodes | 20 (index 10~29) |
| 누적 episodes | 30 |
| 추가 frames | 10,449 (평균 522 ≈ **17.4초**) |
| 비디오 청크 | top/wrist 각 `file-001` |

**관찰**:
- FPS warning 1차와 동일 패턴 (warmup 1.2~1.7 Hz → steady 21~30 Hz)
- ⚠️ **`Corrupt JPEG data` 경고 다수** — episode 경계에서 연속 출력 (ep 10 reset 직후 6연속). 1차 1회 → 2차 다수로 증가
- 재녹화 (`←`) 부분 로그상 ep 10, ep 15 각 1회

### 3차 — 2026-05-15 · task 1 · +20 episodes (ep 30~49) · RESUME · **orientation: back (뒤통수)**

> 콘솔 로그는 50,000자 제한으로 부분만 확인 (ep 30~39 구간). 본 entry 는 **dataset 실제 상태 기준**.

**명령**: `python run_record.py record --task 1 --episodes 20`

| 항목 | 값 |
|---|---|
| 추가 episodes | 20 (index 30~49) |
| 누적 episodes | **50** (Hub `hub_episodes: 50` 확인) |
| 추가 frames | 9,264 (평균 463 ≈ **15.4초**) |
| 비디오 청크 | top/wrist 각 `file-002` |
| Hub push | ✅ `last_modified: 2026-05-15T01:53:46Z` |
| 종료 | ✅ 클린 (Hub 동기화 완료) |

**관찰**:
- FPS warning 동일 패턴 지속 — h264_nvenc 가 FPS 문제 해결 못함 **3차까지 재확인**
- 확인된 부분 로그 (ep 30~39) 에는 `Corrupt JPEG` 경고 없음 — 2차와 대비. 단 로그 truncate 라 전체 미확인 (inconclusive)
- episode 경계에 ep 34 즈음 한 번 `12.3 Hz` / ep 39 `14.9 Hz` 같은 중간 dip 관찰

**⚠️ episode 길이 단축 추세 (3 data points)**:

| 차수 | 평균 episode 길이 |
|---|---|
| 1차 | 20.5초 |
| 2차 | 17.4초 |
| 3차 | 15.4초 |

→ 매 차수 짧아짐. 시연 숙달일 수도 있으나 **3연속 하락 추세** — task 완료 trajectory 가 너무 짧아져 핵심 동작 (집기→이동→놓기) 이 누락되고 있지 않은지 영상 확인 필요.

**검증**:
```
jq '{total_episodes, total_frames}' ~/smolvla/.hf_cache/lerobot/BaboGaeguri/leftarm_v2/meta/info.json
→ total_episodes: 50, total_frames: 25871 ✅   |   hub_episodes: 50 ✅
```

---

### 4차 — 2026-05-15 · task 2 (can) 첫 배치 · +10 episodes (ep 50~59) · RESUME · **orientation: front (문양)** · **person: 인혁이형 (흰색 옷)**

> task 2 첫 수집. 콘솔 로그는 50,000자 제한으로 부분만 확인 (ep 50~54 구간). 본 entry 는 **dataset 실제 상태 기준**.

**명령**: `python run_record.py record --task 2 --episodes 10`
**instruction**: `Hand the yellow can to the person`
**orientation / person**: front (캔 문양이 카메라에 보이게) · 인혁이형 (흰색 옷)

| 항목 | 값 |
|---|---|
| 추가 episodes | 10 (index 50~59) |
| 누적 episodes | **60** (task 1: 50 / task 2: 10) — Hub `hub_episodes: 60` 확인 |
| 추가 frames | 6,449 (평균 645 ≈ **21.5초**) |
| Hub push | ✅ `last_modified: 2026-05-15T02:30:15Z` |
| 종료 | ✅ 클린 |

**관찰**:
- FPS warning 동일 패턴 (warmup 1.1~1.7 Hz → steady 21~30 Hz). h264_nvenc — task 2 에서도 동일
- 확인된 부분 로그 (ep 50~54) 에 `Corrupt JPEG` 경고 없음
- 재녹화 (`←`) 부분 로그상 ep 54 1회
- **episode 길이 21.5초** — task 1 후반 (3차 15.4초) 보다 **길다**. task 2 가 새 task 라 아직 시연 미숙 → task 1 1차 (20.5초) 와 비슷한 "초보 길이". 사용자가 확인한 "반복 숙달 → 단축" 패턴과 일관 (task 2 도 차수 진행하며 짧아질 것으로 예상)

**검증**:
```
jq '{total_episodes, total_frames, total_tasks}' ~/smolvla/.hf_cache/lerobot/BaboGaeguri/leftarm_v2/meta/info.json
→ total_episodes: 60, total_frames: 32320, total_tasks: 2 ✅   |   hub_episodes: 60 ✅
```

---

## 발견된 이슈 / 후속

### 💡 [ ] FPS sub-30Hz — dataset 무결성 영향 없음 확인됨, polish 항목으로 격하

- **발견**: 2026-05-15 1·2·3차 수집 전반 — record loop sub-30Hz 경고 (warmup 1.2~1.7 Hz → steady 21~30 Hz). h264_nvenc 전환에도 지속 → 인코더가 원인 아님
- **✅ frame drop 검증 완료 (2026-05-15)**: `data/*.parquet` 의 timestamp 간격 전수 분석 결과 — **50 episode 전부 33.33ms 간격, 표준편차 0.00ms, gap 0개**. dataset 내부적으로 완벽히 일관, **누락 frame 없음**
- **핵심 발견**: lerobot 은 `timestamp = frame_index / fps` 로 **이상값을 계산해 저장** (std 0.00 이 증거). 즉 dataset timestamp 로는 loop 가 느렸는지 알 수 없음. FPS warning 의 실제 효과 = 느린 순간 실제 모션이 30fps 보다 듬성 샘플링되지만 lerobot 이 전부 이상적 30fps 로 라벨 → "30fps 라벨이 현실보다 약간 낙관적" 수준
- **학습 영향**: 경미. 50개 episode 전체가 비슷한 ~25-29Hz 로 균일 압축 → policy 가 일관된 시간 표현 학습 가능. episode 간 15/30Hz 가 뒤섞인 게 아니라 안전. **학습 blocker 아님 — 기존 50개 사용 가능**
- **남은 polish (선택, 본 수집/학습 막지 않음)**: 진짜 30fps fidelity 원하면 — `--display_data=false` 비교 / USB 토폴로지 (카메라 2대 hub 경합) / `Corrupt JPEG data` 경고 (USB MJPG 입력단 불안정) 점검. 우선순위 낮음

### ⚠️ [ ] task instruction 의 spatial-reference 모호성 점검

- **발견**: 2026-05-15. task 1 "left side of the table" / task 2 "to the person"
- **상태**: leftarm_v1 에서 "left/right" 모호성으로 instruction 2회 변경한 이력 — 같은 함정 가능성
- **조치**: 수집 영상을 Rerun / Hub 에서 확인 — 카메라 화면에서 "테이블 왼쪽" 이 시각적으로 명확히 구분되는지. 모호하면 본 수집 (100 ep) 진입 전 instruction 재검토
- **영향**: instruction grounding 이 약하면 멀티태스크 학습 시 task 구분 실패

### 5차 — 2026-05-15 · task 2 (can) · +10 episodes (ep 60~69) · RESUME · **orientation: front (문양)** · **person: 성래 (화각 외)**

> 5차 첫 시도는 모터 크래시로 롤백 (아래 이슈 항목). 본 entry 는 전원 사이클 후 재시도 성공분.

**명령**: `python run_record.py record --task 2 --episodes 10`
**instruction**: `Hand the yellow can to the person`
**orientation / person**: front (캔 문양이 카메라에 보이게) · 성래 (화각에서 잘 안 보이는 위치에 앉음)

| 항목 | 값 |
|---|---|
| 추가 episodes | 10 (index 60~69) |
| 누적 episodes | **70** (task 1: 50 / task 2: 20) — Hub `hub_episodes: 70` |
| 추가 frames | 5,987 (평균 599 ≈ **20.0초**) |
| Hub push | ✅ `last_modified: 2026-05-15T05:23:21Z` |
| 종료 | ✅ 클린 (전원 사이클 후 모터 안정) |
| 재녹화 (`←`) | ep 60 시작 시 3회 (모터 회복 직후 보정 필요했던 듯) |

**관찰**:
- FPS warning 패턴 동일 (warmup → 21~30 Hz steady). h264_nvenc 동일
- **episode 길이 4차 21.5초 → 5차 20.0초** — 시연 숙달
- ⚠️ **성래 화각 외 위치 — instruction grounding 우려**:
  - task 2 instruction "Hand ... to **the person**" 의 사람이 카메라에 거의 안 보임
  - policy 가 "특정 방향으로 팔 뻗기" 만 학습 (사람의 시각적 단서 없이)
  - 단일 deployment 환경에선 작동, but 다른 사람·위치 generalization 약화. 인혁이형 (4차, 화각 내) 과 성래 (5차, 화각 외) 가 시각적으로 다른 만큼 멀티 person 다양성 ↑ 효과는 있음

---

### ⚙️ [x] 2026-05-15 — 5차 시도 중 Feetech 모터 통신 크래시, ep 60 단독 롤백 처리

- **발견**: 2026-05-15 12:04. task 2 5차 (`--episodes 10`) 중 ep 60 정상 저장 후 ep 61 재녹화 시점에 `ConnectionError: [TxRxResult] There is no status packet` — Feetech 모터 응답 없음. record_loop 종료, 종료 직전 Hub push 1회 일어남
- **영향**: 의도한 10개 중 1개 (ep 60) 만 저장됨. 5차 미완료 상태로 dataset 이 61 episodes 가 됨
- **조치**:
  1. file-004 청크 (data/meta/episodes/video) 4개 + meta/info.json 의 total_episodes/frames 를 60/32320 로 롤백
  2. Hub 의 file-004 4개 삭제 + meta/info.json 갱신 + push_to_hub 로 dataset 카드 재생성
  3. follower 보드 전원 사이클 → run_teleop 점검 → 5차 재시도 예정
- **메모리 참조**: [SO-ARM debugging §1](../../../.claude/projects/-home-laba/memory/project_smolvla_so_arm_debugging.md) — Feetech 모터 error register 가 set 되면 캘리브로 못 풀고 power cycle 만이 reset 가능
- **재발 방지**: 차수 사이에 짧은 휴식 (모터 발열 식히기), 그리퍼·wrist 한계 도달 회피

### 6차 — 2026-05-15 · task 2 (can) · +20 episodes (ep 70~89) · RESUME · **orientation: front (문양)** · **person: 성래 (화각 외)**

**명령**: `python run_record.py record --task 2 --episodes 20`
**instruction**: `Hand the yellow can to the person`
**orientation / person**: front · 성래 (5차 동일)

| 항목 | 값 |
|---|---|
| 추가 episodes | 20 (index 70~89) |
| 누적 episodes | **90** (task 1: 50 / task 2: 40) — Hub `hub_episodes: 90` |
| 추가 frames | 10,696 (평균 535 ≈ **17.8초**) |
| Hub push | ✅ `last_modified: 2026-05-15T05:36:53Z` |
| 종료 | ✅ 클린 |

**관찰**:
- FPS warning 동일 패턴
- **episode 길이 단축 지속** — 4차 21.5초 → 5차 20.0초 → 6차 **17.8초**. task 2 도 task 1 처럼 숙달 단축 패턴 확인. 사용자 확인된 정상 패턴

### ⚠️ [ ] episode 길이 3연속 하락 추세 — trajectory 누락 점검

- **발견**: 2026-05-15. 1차 20.5초 → 2차 17.4초 → 3차 15.4초, 매 차수 단축
- **상태**: 시연 숙달이면 정상이나 3연속 하락이라 추세로 봐야 함. task 완료 동작 (집기→이동→놓기) 이 빠르게 끝나며 일부 누락되고 있을 가능성
- **조치**: 후반 차수 (3차 ep 30~49) 영상을 1차와 비교 — trajectory 가 task 를 온전히 담는지
- **영향**: 너무 짧은 / 동작 누락된 episode 는 학습 시 policy 가 불완전한 trajectory 학습

### 7차 — 2026-05-15 · task 2 (can) · +20 episodes (ep 90~109) · RESUME · **orientation: back (성분표시)** · **person: 성래 (화각 외)**

> task 2 첫 back 배치. 5·6차 (성래 front) 와 동일 인물, orientation 만 전환.

**명령**: `python run_record.py record --task 2 --episodes 20`
**instruction**: `Hand the yellow can to the person`
**orientation / person**: back (캔 성분표시가 카메라에 보이게) · 성래 (5·6차 동일)

| 항목 | 값 |
|---|---|
| 추가 episodes | 20 (index 90~109) |
| 누적 episodes | **110** (task 1: 50 / task 2: 60) — Hub `hub_episodes: 110` |
| 추가 frames | 10,749 (평균 537 ≈ **17.9초**) |
| reset_time_s | **7** (기존 15 → 7 로 단축 — 시연 숙달 반영, runtime-only 라 dataset 일관성 영향 없음) |
| Hub push | ✅ `last_modified: 2026-05-15T05:51:07Z` |
| 종료 | ✅ 클린 |

**관찰**:
- FPS warning 동일 패턴 — h264_nvenc 7차 차수 동안 일관
- **episode 길이 17.9초** — 6차 17.8초와 사실상 동일. task 2 가 ~18초 plateau 에 도달한 것으로 보임 (task 1 의 15.4초 plateau 와 별개)
- back orientation 첫 시연 — 성분표시 면이 카메라에 노출되도록 캔 회전 유지. 시연 동작 자체는 front 와 동일 (pick → hand over)

---

## 다음 차수

현재 task 1 누적 **50/100**, task 2 누적 **60/100** (전체 110/200).

### 50개 시점 점검 — 완료 (2026-05-15)

| 점검 항목 | 결과 |
|---|---|
| FPS sub-30Hz → frame drop? | ✅ **이상 없음** — timestamp 전수 분석, 50 ep 전부 33.33ms 균일, gap 0. dataset 무결. FPS 는 polish 항목으로 격하 |
| instruction grounding ("테이블 왼쪽") | ✅ 사용자 확인 — 카메라 화면에서 명확 |
| episode 길이 3연속 하락 (20.5→17.4→15.4초) | ✅ 사용자 확인 — 반복 숙달로 인한 단축, trajectory 누락 아님 |

→ **3개 항목 모두 clear. task 1 본 수집 계속 진행 가능.**

### 진행 계획

> **명령은 orientation·person 과 무관하게 동일** (`--task N --episodes M`). 시연 시 물체 방향 / 사람을 표대로 통제 + 로그 entry 에 기록.

#### Task 1 (doll) — 남은 +50

현재 **front 30 / back 20**. 100 ep 시점 50/50 균형 목표 → 추가로 **front +20 / back +30** 필요.

| 차수 (예시) | 명령 | orientation | task 1 누적 (F/B) |
|---|---|---|---|
| ? | `--task 1 --episodes 20` | **back** (뒤통수) | 30F/40B = 70 |
| ? | `--task 1 --episodes 20` | **front** (얼굴) | 50F/40B = 90 |
| ? | `--task 1 --episodes 10` | **back** (뒤통수) | 50F/50B = **100** ✅ |

#### Task 2 (can) — 남은 +40

현재 **front 40 (인혁이형 10 + 성래 30) / back 20 (성래 20)**. 7차로 back 진입. 50/50 균형까지 **back +30 / front +10** 필요.

| 차수 (예시) | 명령 | orientation | person | task 2 누적 |
|---|---|---|---|---|
| ? | `--task 2 --episodes 20` | **back** (성분표시) | 인혁이형 | 80 (F40/B40) |
| ? | `--task 2 --episodes 10` | **back** (성분표시) | (새 사람 C) | 90 (F40/B50) |
| ? | `--task 2 --episodes 10` | **front** (문양) | (새 사람 C) | **100** (F50/B50) ✅ |

→ task 2 최종 (예시): 인혁이형 30 (F10/B20) + 성래 50 (F30/B20) + C 20 (F10/B10) = 100, F50/B50.

> 위 split 은 예시. **인혁이형 back 미수집 + 새 사람 추가** 두 가지가 핵심 — 사람×orientation cross 다양성 확보.
>
> 새 사람 추가 시 [수집 컨벤션 §2](#2-사람-정보-task-2-전용) 의 "현재 등록 인물" 표 갱신.
>
> ⚠️ **성래 화각 외 우려**: 5차 entry 참조. 새 사람 (C) 추가 시 **화각에 명확히 들어오는 위치**로 두면 instruction grounding 다양성 확보 측면에서 더 유리.
</content>
