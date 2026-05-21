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
| task 1 | "Pick up the blue and yellow doll and place it on the left side of the table" — 목표 **200 ep** (2026-05-18 100→200 조정) |
| task 2 | "Hand the yellow can to the person" — 목표 **200 ep** (2026-05-18 100→200 조정) |
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
| 인혁이형 | 흰색 옷 (4차) / 검은 상의 + 흰 바지 (8차) | 카메라 화각에 적당히 들어옴. 동일 인물이라도 차수별 옷차림 명시 (vision robustness) |
| 성래 | (좌석 위치 기반) | **화각에서 잘 안 보이는 위치에 앉아있음** — 시각적 구분 약함 |
| 승민이 | 회색 상의 + 검은 바지 (12차) | task 1 시연자 (operator) — 화각 밖. 12차 첫 등장. *승민 전여친 랩실 = 본인 환경* |
| (추후 추가) | — | — |

### 규칙 (공통)

- **instruction 은 동일** — orientation / person 은 instruction 에 안 들어감. pick-place·hand-over 동작이 이들과 무관하게 같으므로, *물리적 다양성* 일 뿐 모델이 instruction 으로 구분할 대상 아님
- **차수별로 한 조합** — 한 수집 차수 = 한 orientation (+ task 2 는 한 person). 시연 중 일관 유지 + 로그 추적 명확
- 각 차수 로그 entry 에 `orientation: ...` (task 2 는 추가로 `person: ...`) 명시
- 목표: task 별로 앞/뒤 + 사람 대략 균형

### 3. 추가 다양화 영역 (2026-05-18 도입 — 8차부터 적용)

vision encoder 의 *task-irrelevant 변동 invariance* 학습 목적. 차수당 *의식적 다양화*:

| 다양화 차원 | 가능 값 | 의도 |
|---|---|---|
| **위치분포** (물체 시작 위치) | `좌` / `우` / `중앙` / `혼합 (예: 3,3,4)` | spatial generalization. task1 의 "테이블 왼쪽" instruction grounding 학습 보강. 차수 내 비율로 명시 |
| **조명** | `default` (기본 시연장 조명) / `오전 자연광` / `오후 자연광` / `저녁 형광등 only` / 기타 | vision encoder 의 color/lighting invariance 학습 |
| **배경** | `clean` / `주변 사람` / `테이블 위 잡동사니` / 기타 | task-irrelevant feature 무시 학습 |

**중요**: 1~7차 (2026-05-15 수집분) 은 다양화 영역 *미명시* — 빈 칸 또는 `-` 표기. 8차부터 적용.

### 4. 시연자 다양화 — task 1 도 적용 (2026-05-18 도입)

기존 시연자 칼럼이 task 2 전용이었으나, *task 1 도 시연자 다양성 변수*. 8차부터 task 1 수집 시도 `person` 칼럼 채움. 1~7차의 task 1 시연자 (본인) 는 *사후 분류 X* — 빈 칸 유지.

---

## 현재 누적 상태

### 차수별 상세

> 칼럼 안내: `위치분포`, `조명`, `배경` 은 2026-05-18 도입 — 1~7차는 빈 칸 (`-`). 8차부터 채움.

| 차수 | 날짜 | task | 모드 | +ep | ep index | orientation | person | 위치분포 | 조명 | 배경 | 누적 T1 | 누적 T2 | 누적 합 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2026-05-15 | 1 (doll) | FRESH | 10 | 0~9 | front (얼굴) | — | - | - | - | 10 | 0 | 10 |
| 2 | 2026-05-15 | 1 (doll) | RESUME | 20 | 10~29 | front (얼굴) | — | - | - | - | 30 | 0 | 30 |
| 3 | 2026-05-15 | 1 (doll) | RESUME | 20 | 30~49 | back (뒤통수) | — | - | - | - | 50 | 0 | 50 |
| 4 | 2026-05-15 | 2 (can) | RESUME | 10 | 50~59 | front (문양) | 인혁이형 (흰옷) | - | - | - | 50 | 10 | 60 |
| 5 | 2026-05-15 | 2 (can) | RESUME | 10 | 60~69 | front (문양) | 성래 (화각 외) | - | - | - | 50 | 20 | 70 |
| 6 | 2026-05-15 | 2 (can) | RESUME | 20 | 70~89 | front (문양) | 성래 (화각 외) | - | - | - | 50 | 40 | 90 |
| 7 | 2026-05-15 | 2 (can) | RESUME | 20 | 90~109 | back (성분표시) | 성래 (화각 외) | - | - | - | 50 | 60 | 110 |
| 8 | 2026-05-18 14:59 | 2 (can) | RESUME | 20 | 110~129 | back (성분표시) | 인혁이형 (검은상의·흰바지) | 캔 카메라 중앙 (1~7차 좌측에서 변경) | 형광등 | 승민 전여친 랩실 (인혁이형이 카메라에 꽉 차게 앉아있음) | 50 | 80 | 130 |
| 9 | 2026-05-18 15:13 | 2 (can) | RESUME | 20 | 130~149 | back (성분표시) | 인혁이형 (검은상의·흰바지, 화각 안) | 캔 카메라 좌측 (1~7차 위치 복귀) | 형광등 | 승민 전여친 랩실 (인혁이형이 카메라에 꽉 차게 앉아있음) | 50 | 100 | 150 |
| 10 | 2026-05-18 15:34 | 2 (can) | RESUME | 20 | 150~169 | back (성분표시) | 인혁이형 (검은상의·흰바지, 화각 밖) | 캔 카메라 좌측 (계획 중앙→실행 좌측, 9차와 동일) | 형광등 | 승민 전여친 랩실 (인혁이형 자리 비움 → 배경만) | 50 | 120 | 170 |
| 11 | 2026-05-18 15:53 | 2 (can) | RESUME | 20 | 170~189 | front (문양) | 인혁이형 (검은상의·흰바지, 화각 밖) | 캔 카메라 좌측 (9·10차와 동일) | 형광등 | 승민 전여친 랩실 (인혁이형 자리 비움 → 배경만) | 50 | 140 | 190 |
| 12 | 2026-05-18 16:30 | 1 (doll) | RESUME | 20 | 190~209 | front (얼굴) | 승민이 (회색상의·건색바지, 화각 밖 — operator) | 인형 시작 위치 좌측 일관 고정 | 형광등 | 승민 전여친 랩실 (텅 빈 배경) | 70 | 140 | 210 |
| 13 | 2026-05-18 18:25 | 1 (doll) | RESUME | 20 | 210~229 | back (뒤통수) | 인혁이형 (검은상의·흰바지, 화각 밖 — operator) | 인형 시작 위치 좌측 일관 고정 (12차와 동일) | 형광등 | 승민 전여친 랩실 (텅 빈 배경) | 90 | 140 | 230 |
| 14 | 2026-05-18 18:37 | 1 (doll) | RESUME | 20 | 230~249 | back (뒤통수) | 인혁이형 (검은상의·흰바지, 화각 밖 — operator) | 인형 시작 위치 좌측 일관 고정 (13차와 동일) | 형광등 | 승민 전여친 랩실 (텅 빈 배경) | 110 | 140 | 250 |
| 15 | 2026-05-18 21:04 | 1 (doll) | RESUME | 20 | 250~269 | front (얼굴) | 인혁이형 (검은상의·흰바지, 화각 밖 — operator) | 인형 시작 위치 좌측 일관 고정 (12·13·14차와 동일) | 형광등 | 승민 전여친 랩실 (텅 빈 배경) | 130 | 140 | 270 |
| 16 | 2026-05-18 21:12 | 1 (doll) | RESUME | 20 | 270~289 | back (뒤통수) | 인혁이형 (검은상의·흰바지, 화각 밖 — operator) | 인형 시작 위치 좌측 일관 고정 (13·14차와 동일) | 형광등 | 승민 전여친 랩실 (텅 빈 배경) | 150 | 140 | 290 |
| 17 | 2026-05-18 21:22 | 2 (can) | RESUME | 20 | 290~309 | **front (문양)** | 인혁이형 (검은상의·흰바지, 화각 밖 — receiver 자리 비움) | 캔 좌측 (9·10·11차와 동일) | 형광등 | 승민 전여친 랩실 (배경만) | 150 | **160** | **310** |

### Orientation 합계

> 2026-05-18 목표 조정: task 당 100 → **200 ep**. 전체 200 → **400 ep**. 사유: researcher 추정 (300~500ep) 의 중간 영역 진입으로 데이터 부족 가설 통계 신뢰도 ↑ + camera mismatch 확신 영역 도달 (자세한 근거는 [learning_log1.md §이관 1 — 2A/2B 패스 구조 변경 이력](../../../../prof_computer/docs/leftarm_v2/learning_log1.md) 또는 본 사이클 대화).

| task | 누적 / 목표 | front | back |
|---|---|---|---|
| task 1 (doll) | 150 / **200** | 70 (차 1·2·12·15) | 80 (차 3·13·14·16) |
| task 2 (can) | 160 / **200** | 80 (차 4·5·6·11·17) | 80 (차 7·8·9·10) |
| **전체** | **310 / 400** (164,332 frames) | 150 | 160 |

### Person 합계 (task 2 receiver)

| person | front | back | 합계 | 해당 차수 (화각 위치) |
|---|---|---|---|---|
| 인혁이형 (4차 흰옷, 8·9·10·11·17차 검은상의·흰바지) | 50 | 60 | 110 | 차 4 (F·안), 차 8·9 (B·안), 차 10 (B·**밖**), 차 11·17 (F·**밖**) |
| 성래 (화각 외) | 30 | 20 | 50 | 차 5·6·7 |
| **합계** | 80 | 80 | **160 / 200** | — |

### Person 합계 (task 1 시연자 — 12차부터 명시, §4 컨벤션)

| 시연자 | front | back | 합계 | 해당 차수 |
|---|---|---|---|---|
| 본인 (1~3차, 사후 분류 X) | 30 | 20 | 50 | 차 1·2·3 (시연자 정보 미명시) |
| 승민이 (회색상의·검은바지, 화각 밖) | 20 | 0 | 20 | 차 12 (F·**operator**) |
| 인혁이형 (검은상의·흰바지, 화각 밖) | 20 | 60 | 80 | 차 13·14·16 (B·**operator**), 차 15 (F·**operator**) — task2 receiver 역할과 다른 *operator* 역할 |
| **합계** | 70 | 80 | **150 / 200** | — |

> 1~4차 (2026-05-15 컨벤션 도입 전) 의 orientation·person 은 사용자가 사후 분류한 값으로 채움. 5차부터는 시연 시점에 명시 + 일관 유지.

마지막 갱신: 2026-05-18 — **17차 추가 = 오늘 마감 (10 차수 +200ep, 110→310)**. task2 140→160 (**80% 마일스톤**), 전체 310/400 (77.5%). task2 80F/80B 균등 도달 (격차 해소). 11차↔17차 task2 front 인혁 화각밖 2-batch doubling 완성. + 조명 컬럼 "낮 (형광등)" → "형광등" 정합성 정정 (시간 컬럼이 시간대 제공, 8·9·10차는 낮이었으나 11~17차는 저녁이라 "낮" 부적합).

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

### ⚙️ [x] 2026-05-18 — 11차 시도 1 Feetech 모터 통신 크래시 (ep 170 첫 frame), 데이터 영향 0 (즉시 crash)

- **발견**: 2026-05-18 15:39. task 2 11차 (`--episodes 20`) 시작 직후 `Recording episode 170` 메시지 1초 후 image writer 대기 → 즉시 Stop recording → `ConnectionError: Failed to sync read 'Present_Position' ... [TxRxResult] There is no status packet!` (5차와 동일 에러)
- **영향**: **데이터 무결성 영향 0** — episode 170 frame 한번도 못 읽고 crash → 0 episode 저장. info.json 170 그대로, file-010 미생성, Hub push 도 "No files have been modified since last commit. Skipping" 로 클린 종료. 5차와 달리 *롤백 불필요*
- **맥락**: 8·9·10차 연속 3 배치 (~20분 시연 / 60ep) 후 4분 휴식 → 11차 시도. 누적 발열 또는 휴식 중 모터 idle state 진입이 원인으로 추정
- **조치**:
  1. follower 보드 전원 사이클 (사용자 직접)
  2. by-id 매핑 재확인 — ACM 변동 없음 (follower=ACM1, leader=ACM0 유지)
  3. `run_teleop.py` 실행 → 60 Hz steady, NORM 값 정상 출력, ConnectionError 재발 없음 → **모터 회복 확인**
  4. 11차 본 수집 재시도
- **메모리 참조**: [SO-ARM debugging](../../../.claude/projects/-home-laba/memory/project_smolvla_so_arm_debugging.md) — power cycle 외 reset 불가
- **5차와 비교**: 5차는 ep 60 정상 후 ep 61 시점 crash → 1 episode 저장 후 롤백 필요했음. 11차는 ep 170 첫 시도 즉시 crash → 0 episode, 롤백 불필요. *연속 배치 3개 후* 라는 공통점 — 차수 사이 휴식이 더 길었어야 했을 가능성. 향후 4 연속 배치 회피 권장

### ⚙️ [x] 2026-05-18 — 13차 시도 1 중 SO-ARM 물리적 분리 → 사용자 의도적 Ctrl-C, ep 210·211 단독 저장 후 롤백

- **발견**: 2026-05-18 16:34. task 1 13차 (`--episodes 20`) 시작 직후 ep 210 (16:33:19→36 정상 저장) · ep 211 (16:33:44→16:34:03 정상 저장) · ep 212 (16:34:11 시작) 진행 중 SO-ARM 모터 보드/마운트가 물리적으로 분리되어 사용자가 Ctrl-C 로 의도적 중단. record_loop 즉시 종료, Hub push 단계 진입 전 process killed
- **영향**:
  - 로컬 dataset: ep 210·211 저장됨 → total_episodes 210→212 (의도치 않은 상태)
  - data/chunk-000/file-012.parquet (42 KB) + videos/{top,wrist}/.../file-012.mp4 (1.1·3.5 MB) 신규 생성
  - meta/episodes/file-012.parquet **미생성** (lerobot 이 meta 배치 갱신 임계점 못 채움) → dataset 이미 부분 불완전 상태
  - Hub: 12차 push (210) 상태 그대로 → 로컬/Hub mismatch
- **조치** (5차 절차 준용):
  1. 로컬 파일 3개 삭제: `data/chunk-000/file-012.parquet` + `videos/observation.images.top/chunk-000/file-012.mp4` + `videos/observation.images.wrist/chunk-000/file-012.mp4`
  2. `meta/info.json` 정정: total_episodes 212→210, total_frames 117155→116113, splits.train "0:212"→"0:210"
  3. Hub 정합: push 전 종료라 Hub=210 그대로 → **추가 작업 불필요** (5차 때는 push 일어났어서 Hub 정정 필요했음)
  4. `meta/stats.json` 은 ep 210·211 기여 포함된 채 stale 잔존 (2/212 = ~1% 오차) → 14차 진입 시 lerobot 이 자연 갱신 예상, 미정정
  5. SO-ARM 물리 마운트 재고정 → 텔레옵 sanity → 13차 재시도
- **메모리 참조**: [lerobot push_hub crash recovery](../../../.claude/projects/-home-laba/memory/project_lerobot_push_hub_crash_recovery.md)
- **5·11차와 비교**:
  | 차수 | 원인 | 저장 ep | Hub 영향 | 처리 |
  |---|---|---|---|---|
  | 5 | Feetech 통신 | 1 (ep 60) | 1 ep push 됨 | 로컬+Hub 롤백 |
  | 11 시도 1 | Feetech 통신 | 0 | 없음 | 처리 불필요 |
  | **13 시도 1** | **물리 분리 (Ctrl-C)** | **2 (ep 210·211)** | 없음 | **로컬만 롤백** |
- **재발 방지**: SO-ARM 마운트·케이블 *수집 전* 점검 (특히 wrist mount, gripper 케이블, base 고정). 차수 사이 5분 휴식 시 마운트 시각 점검 1초만 들이기

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

### 8차 — 2026-05-18 14:59 · task 2 (can) · +20 episodes (ep 110~129) · RESUME · **orientation: back (성분표시)** · **person: 인혁이형 (검은 상의 + 흰 바지)**

> 3일 휴지 후 첫 세션. 8차부터 신규 다양화 칼럼 (조명·배경) 적용 — 위치분포는 본 세션 *고려안함*. 인혁이형 (기존 인물, 4차 흰옷 ↔ 8차 검은상의+흰바지로 옷차림 변동).

> 사전 점검 완료 (2026-05-18 14:30~14:40):
> - 포트 변동 확인 → base_config hardware 갱신: follower `/dev/ttyACM2` → `/dev/ttyACM1` (serial 5B42138563), leader `/dev/ttyACM1` → `/dev/ttyACM0` (serial 5B42138566). 카메라 인덱스 (top=0, wrist=2) 변동 없음 — lerobot-find-cameras + ffmpeg MJPG 캡처로 매핑 검증
> - `run_teleop.py` 로 모터·캘리브·카메라 정합 검증 — 59 Hz steady, 양쪽 모터 응답 OK

**명령**: `python run_record.py record --task 2 --episodes 20`
**instruction**: `Hand the yellow can to the person`
**orientation / person**: back (캔 성분표시가 카메라에 보이게) · 인혁이형 (검은 상의 + 흰 바지)

| 차원 | 값 |
|---|---|
| 위치분포 | **캔이 카메라 화면 중간에 위치** (그동안 1~7차는 좌측에 치우쳐져 있었음 — 8차가 첫 중앙 시도) |
| 조명 | 형광등 |
| 배경 | 승민 전여친 랩실 (인혁이형이 카메라에 꽉 차게 앉아있음) |

**계획 근거**:
- task 2 현재 F40/B20 — back 부족분(+80) 이 front(+60) 보다 커서 back 우선
- **인혁이형 현재 10F/0B (강한 편향) → back 미수집 보강 시급**
- 옷차림 변화 (4차 흰옷 → 8차 검은상의·흰바지) → 동일 인물 다양 외형 데이터 (vision encoder 의 인물 invariance 학습 보강)

| 항목 | 값 |
|---|---|
| 추가 episodes | 20 (index 110~129) |
| 누적 episodes | **130** (task 1: 50 / task 2: 80, F40/B40) — info.json 확인 |
| 추가 frames | 10,935 (평균 547 ≈ **18.2초**) |
| 비디오 청크 | top/wrist 각 `file-007` 신규 (file-000~006 은 이전 차수 누적) |
| Hub push | ✅ 클린 (54.8 MB 신규 업로드, parquet + mp4 chunk-000 갱신) |
| 종료 | ✅ 클린 (top/wrist/follower/leader 순차 disconnect, Hub push 완료, Exiting) |

**관찰**:
- FPS warning 기존 패턴 동일 (steady 20~29 Hz, warmup spike 1.1 Hz 1회 — ep 129 시작 시점). h264_nvenc 8차도 일관, 폴리시 안에서 frame drop 없음 (이전 50ep 점검과 동일 메커니즘 추정)
- **episode 길이 18.2초** — 7차 17.9초 / 6차 17.8초 와 거의 동일 → **task 2 가 ~18초 plateau 안정 유지** (시연 숙달 후 정상값)
- **Feetech 통신 크래시 0회** — 5차 ConnectionError 재발 없음. 3일 휴지 후 첫 세션이지만 모터·통신 안정
- `Corrupt JPEG data` 경고 로그 범위 내 미관측 (전체 로그 확인 시 다를 수 있음)
- **인혁이형 옷차림 변화 첫 적용** — 동일 인물 같은 task·orientation 인데 4차(흰옷) ↔ 8차(검은상의·흰바지) 외형 다양화. vision encoder 의 person identity invariance 학습 자산
- **인물이 카메라에 꽉 찬 화각** — task 2 instruction `Hand the yellow can to the person` 의 "the person" 이 시각적으로 명확히 grounding 되는 첫 데이터. 5차 entry 의 *성래 화각 외 → instruction grounding 약화 우려* 와 정반대 케이스로, person grounding 다양성 (화각 외 ↔ 꽉 참) 양극 데이터 확보

---

### 9차 — 2026-05-18 15:13 · task 2 (can) · +20 episodes (ep 130~149) · RESUME · **orientation: back (성분표시)** · **person: 인혁이형 (검은 상의 + 흰 바지)**

> 8차 직후 연속 진행. 동일 인물·동일 orientation·동일 옷차림으로 **위치분포만 변화** (8차 중앙 → 9차 좌측 치우침 = 1~7차 기존 위치 복귀). 위치분포 변수 단독 효과 측정용 데이터 쌍 형성.

**명령**: `python run_record.py record --task 2 --episodes 20`
**instruction**: `Hand the yellow can to the person`
**orientation / person**: back (캔 성분표시가 카메라에 보이게) · 인혁이형 (검은 상의 + 흰 바지)

| 차원 | 값 |
|---|---|
| 위치분포 | **캔이 좌측에 치우쳐서 위치** (1~7차 기존 위치 — 8차 중앙 직후 복귀) |
| 조명 | 형광등 |
| 배경 | 승민 전여친 랩실 (인혁이형이 카메라에 꽉 차게 앉아있음) |

**계획 근거**:
- 8차 (중앙) 와 *위치분포만 다른 짝* — 이외 모든 조건 동일 (task / orientation / person / 옷차림 / 조명 / 배경)
- 학습 시 위치분포 단일 변수 효과 / robustness 비교 가능한 통제된 데이터 쌍

| 항목 | 값 |
|---|---|
| 추가 episodes | 20 (index 130~149) |
| 누적 episodes | **150** (task 1: 50 / task 2: 100, F40/B60) — info.json 확인 |
| 추가 frames | 11,392 (평균 569 ≈ **19.0초**) |
| 비디오 청크 | top/wrist 각 `file-008` 신규 |
| Hub push | ✅ 클린 (56.9 MB 신규 업로드) |
| 종료 | ✅ 클린 (top/wrist/follower/leader 순차 disconnect, Hub push 완료, Exiting) |

**관찰**:
- FPS warning 동일 패턴 (steady 23~29 Hz 범위). 8차와 일관
- **episode 길이 19.0초** — 8차 18.2초 / 7차 17.9초 대비 약간 증가. *위치분포 (캔 좌측) 가 reach trajectory 를 살짝 길게 만드는 효과* 가설 (좌측 = follower 시작자세 대비 도달 거리 약간 멀 수 있음). 단일 차수 차이라 noise 일 수도 — 추후 추세 확인
- **Feetech 통신 크래시 0회** — 8차 직후 연속 진행에도 모터 안정
- 카메라·모터 disconnect 클린, Hub push 4분 만에 완료 (56.9 MB)
- task 2 **누적 100 episodes 도달** — 200ep 목표의 50% 마일스톤. front 40 / back 60 으로 back 우세 (계획대로 진행)

---

### 10차 — 2026-05-18 15:34 · task 2 (can) · +20 episodes (ep 150~169) · RESUME · **orientation: back (성분표시)** · **person: 인혁이형 (검은 상의 + 흰 바지, 화각 밖)**

> 8·9차 직후 연속 진행. 동일 인물·동일 옷차림 유지, **person 화각 위치 변경** (8·9차 화각 안 → 10차 화각 밖). 5차 entry 의 *성래 화각 외 → instruction grounding 약화 우려* 를 같은 인물 양쪽 케이스 보유로 해결하는 controlled 실험 진입.

> ⚠️ 계획 변경: 원래 계획은 *front · 캔 중앙* 이었으나 실행 시 **back · 캔 좌측** 으로 진행됨. 그 결과 **9차 ↔ 10차 = 화각 가시성 단일 변수 변동 pair** (orientation back·위치분포 좌측·옷차림 동일, 화각 안↔밖만 변동) 가 자연스럽게 형성됨 — 오히려 더 깨끗한 통제 디자인. F/B 격차는 늘어났지만 (40F/80B), 11차 front 로 균형 회복 가능.

**명령**: `python run_record.py record --task 2 --episodes 20`
**instruction**: `Hand the yellow can to the person`
**orientation / person**: back (캔 성분표시가 카메라에 보이게) · 인혁이형 (검은 상의 + 흰 바지, **이번엔 화각 밖**)

| 차원 | 값 |
|---|---|
| 위치분포 | **캔이 좌측에 치우쳐서 위치** (계획은 중앙이었으나 실행 시 변경 — 9차와 동일) |
| 조명 | 형광등 |
| 배경 | 승민 전여친 랩실 (**인혁이형 자리 비움 → 화각 밖 위치, 카메라엔 배경만**) |

**계획 근거**:
- 8·9차와 같은 person·옷차림이되 *화각 위치만 변경* → person grounding 견고성 통제 데이터
- 실행 결과 9차(back·좌·안) ↔ 10차(back·좌·밖) = 화각 가시성 단일 변수 pair → 학습 시 person grounding 견고성 직접 측정 가능

| 항목 | 값 |
|---|---|
| 추가 episodes | 20 (index 150~169) |
| 누적 episodes | **170** (task 1: 50 / task 2: 120, **F40/B80**) — info.json 확인 |
| 추가 frames | 11,709 (평균 585 ≈ **19.5초**) |
| 비디오 청크 | top/wrist 각 `file-009` 신규 |
| Hub push | ✅ 클린 (57.3 MB 신규 업로드) |
| 종료 | ✅ 클린 (top/wrist/follower/leader 순차 disconnect, Hub push 완료, Exiting) |

**관찰**:
- FPS warning 동일 패턴 (steady 20~29 Hz). h264_nvenc 일관
- **episode 길이 19.5초** — 9차 19.0초 → 10차 19.5초 미세 증가. *위치분포 / orientation 동일*, 변수는 *person 화각 밖* 뿐 → person 가시성이 reach trajectory 길이에 영향 줄 가설은 약함. 시연 미세 변동 noise 로 추정
- **Feetech 통신 크래시 0회** — 8·9·10차 연속 모터 안정
- **task 2 F/B 격차 확대** (40F/80B) — 8·9·10차 모두 back 누적. 11차 front 로 균형 회복 권장
- **person 화각 밖 첫 적용 (인혁이형)** — 5차 (성래 화각 외) 와 비슷하지만 *인물·옷차림 다름*. 8·9차 (인혁이형 꽉 참) 와 합쳐 **같은 인물 같은 옷차림 양쪽 화각 케이스** 데이터 보유 → instruction grounding 시각 의존도 측정 자산
- **9차 ↔ 10차 = 화각 가시성 단일 변수 통제 pair 완성** — orientation back, 위치분포 좌측, 옷차림 검은상의·흰바지, 조명·배경 동일. 학습 후 평가 시 직접 비교 가능한 깨끗한 통제 데이터

---

### 11차 — 2026-05-18 15:53 · task 2 (can) · +20 episodes (ep 170~189) · RESUME · **orientation: front (문양)** · **person: 인혁이형 (검은 상의 + 흰 바지, 화각 밖)**

> 시도 2 — 시도 1 모터 크래시 (15:39) → 전원 사이클 + 텔레옵 sanity (15:41) 통과 후 재진입 (15:53 종료). F/B 격차 완화 + 10차 (back·좌·밖) 와 orientation 단독 변동 controlled pair 형성 목적.

> ⚠️ 시도 1 실패 incident 는 [발견된 이슈 / 후속 · 2026-05-18 항목](#%EF%B8%8F-x-2026-05-18--11차-시도-1-feetech-모터-통신-크래시-ep-170-첫-frame-데이터-영향-0-즉시-crash) 참조. dataset 영향 0 — info.json 170, file-010 미생성 상태에서 시도 2 시작.

**명령**: `python run_record.py record --task 2 --episodes 20`
**instruction**: `Hand the yellow can to the person`
**orientation / person**: front (캔 문양이 카메라에 보이게) · 인혁이형 (검은 상의 + 흰 바지, **화각 밖**)

| 차원 | 값 |
|---|---|
| 위치분포 | 캔이 좌측에 치우쳐서 위치 (9·10차와 동일) |
| 조명 | 형광등 — 동일 |
| 배경 | 승민 전여친 랩실 (인혁이형 자리 비움 → 배경만, 10차와 동일) |

**계획 근거**:
- task 2 F/B 격차 (40F/80B) → 60F/80B 로 완화 (front 보강)
- 10차 (back·좌·밖) 와 *orientation 단독 변동* = front↔back 단독 효과 측정 controlled pair
- 동일 person·옷차림·화각·위치·조명·배경 유지 → 통제 디자인 일관성 ↑

| 항목 | 값 |
|---|---|
| 추가 episodes | 20 (index 170~189) |
| 누적 episodes | **190** (task 1: 50 / task 2: 140, **F60/B80**) — info.json 확인 |
| 추가 frames | 11,669 (평균 583 ≈ **19.4초**) |
| 비디오 청크 | top/wrist 각 `file-010` 신규 |
| Hub push | ✅ 클린 (59.9 MB 신규 업로드) |
| 종료 | ✅ 클린 (top/wrist/follower/leader 순차 disconnect, Hub push 완료, Exiting) |

**관찰**:
- FPS warning 동일 패턴 (steady 27~29 Hz 범위, 8~10차와 일관)
- **episode 길이 19.4초** — 10차 19.5초 / 9차 19.0초 와 거의 동일. *orientation 단독 변동* 만으로는 trajectory 길이에 거의 영향 없음 확인 (back↔front 동작 구조가 유사하다는 방증)
- **Feetech 통신 크래시 0회 (시도 2 전체)** — 전원 사이클 효과 확인, 시도 1 의 `There is no status packet` 재발 없음. ep 170 첫 frame 통과 = 회복 완전 검증
- **10차 ↔ 11차 = orientation 단일 변수 통제 pair 완성** — person·옷차림·화각·위치·조명·배경 모두 동일 (인혁이형 검은상의·흰바지 화각 밖, 캔 좌측, 낮 형광등, 승민 전여친 랩실). 학습 후 평가 시 back↔front 단독 효과 측정 가능
- **task 2 70% 진행** (140/200) — 잔여 60ep (60F+0B 또는 다른 조합). person 다양성 (인물 3·4명 목표) 잔여분에 집중 필요
- 4 연속 배치 회피 권장 (시도 1 incident 교훈) — 11차 끝낸 지금 task1 진입 / 휴식 권장 시점

---

### 12차 — 2026-05-18 16:30 · task 1 (doll) · +20 episodes (ep 190~209) · RESUME · **orientation: front (얼굴)** · **시연자 (person): 승민이 (회색 상의 + 검은 바지, 화각 밖 — operator)**

> **task 1 첫 진입 (3일 만)** — 3차(2026-05-15) 이후 task1 정체 상태였음. 11차 시도 1 incident 교훈으로 task2 4연속 배치 (8·9·10·11) 후 task1 전환 = 모터 발열 휴식 + balance 회복 동시 달성.

> **시연자 다양화 컨벤션 (§4) 첫 적용** — task1 도 person 칼럼 채움. 1~7차의 task1 시연자는 본인 (사후 분류 X, 빈 칸 유지). 12차부터 명시.

**명령**: `python run_record.py record --task 1 --episodes 20`
**instruction**: `Pick up the blue and yellow doll and place it on the left side of the table`
**orientation / 시연자**: front (인형 얼굴이 카메라에 보이게) · **승민이** (회색 상의 + 검은 바지, 화각 밖 — operator 자리)

| 차원 | 값 |
|---|---|
| 위치분포 | **인형 시작 위치 일관 (좌측 고정)** — 20ep 전체 동일 좌측 위치에서 시작 (사용자 결정) |
| 조명 | 형광등 — 8~11차와 동일 (같은 시연장) |
| 배경 | 승민 전여친 랩실 (승민이도 화각 밖 → 텅 빈 배경, 인혁이형 자리 비움과 유사) |

**계획 근거**:
- **task1 균형 회복** — 50/200 (25%) 으로 task2 (140/200, 70%) 대비 한참 뒤. 12차로 70/200 도달
- **시연자 다양화 첫 정량 데이터** — 1~7차는 시연자 (본인) 정보 없음. 12차 (승민이) 가 *다른 시연자 trajectory 스타일* 첫 기록
- **4연속 배치 회피** — 11차 시도 1 모터 크래시 교훈. task 전환 + 새 시연자 = 모터 발열 회복 시점
- **위치분포 일관 (좌측)** → task1 의 "place it on the left side" instruction grounding 학습 시 시작점 일관성 제공 (좌측 시작 → 좌측 배치 = 짧은 traversal 케이스 데이터)

| 항목 | 값 |
|---|---|
| 추가 episodes | 20 (index 190~209) |
| 누적 episodes | **210** (task 1: 70 / task 2: 140) — info.json 확인 |
| 추가 frames | 10,656 (평균 533 ≈ **17.8초**) |
| 비디오 청크 | top/wrist 각 `file-011` 신규 (top 13.7 MB / wrist 38.3 MB — top 이 8~11차 task2 의 17 MB 보다 작음) |
| Hub push | ✅ 클린 (52.5 MB 신규 업로드) |
| 종료 | ✅ 클린 (top/wrist/follower/leader 순차 disconnect, Hub push 완료, Exiting) |

**관찰**:
- FPS warning 동일 패턴 (steady 22~30 Hz). task1 도 task2 와 동일한 sub-30Hz 거동
- **episode 길이 17.8초** — task1 본인 시연 (1차 20.5초 / 2차 17.4초 / 3차 15.4초) 의 *학습 곡선 중간 영역* 과 일치. 새 시연자 (승민) 초기 batch 가 본인 plateau (15.4초) 보다 살짝 길지만 1차 (20.5초 초보) 보다 짧음 → **시연자 변경 효과 미미**, 본인 학습 곡선 위에 안착
- **top 비디오 크기 13.7 MB** (vs 8~11차 task2 16~17 MB) — task1 의 정적 인형 vs task2 사람 등장으로 motion 적어 압축률 ↑. 정상 패턴
- **Feetech 통신 크래시 0회** — task 전환 + 시연자 휴식 효과로 모터 안정. 11차 시도 1 incident 후 첫 task1 진입에서 무사고
- **새 시연자 trajectory 스타일** — episode 길이만으로는 큰 차이 없음. 실제 trajectory shape (joint velocity profile 등) 은 학습 시 차이 드러날 가능성. 본 batch 가 *시연자 다양성 baseline* 첫 데이터
- **위치분포 일관 (좌측 고정)** — 20ep 전체 같은 시작점 = 모델에 일관된 spatial reference 학습 데이터. 추후 위치분포 mixed 차수와 비교 가능한 baseline

---

### 13차 — 2026-05-18 18:25 · task 1 (doll) · +20 episodes (ep 210~229) · RESUME · **orientation: back (뒤통수)** · **시연자 (person): 인혁이형 (검은 상의 + 흰 바지, 화각 밖 — operator)**

> **시도 2** — 시도 1 (16:33~34) 에서 SO-ARM 물리 분리 → 사용자 Ctrl-C → ep 210·211 단독 저장 후 [롤백 처리](#%EF%B8%8F-x-2026-05-18--13차-시도-1-중-so-arm-물리적-분리--사용자-의도적-ctrl-c-ep-210211-단독-저장-후-롤백). SO-ARM 마운트 재고정 + 텔레옵 sanity (~17:00) 통과 + 시도 1 후 torque ON 잔존도 텔레옵 Ctrl-C 로 cleanup 정상화 후 시도 2 (18:25 종료).

> **12차 ↔ 13차 = orientation + 시연자 2변수 변동 데이터쌍** — 위치분포·옷차림 가정 동일·조명·배경 모두 일관 유지, *orientation (front↔back) + 시연자 (승민↔인혁이형) 만 변동*. 둘 다 task1 operator (화각 밖) 라 화각 시각 차이 없음 → 학습 시 trajectory 스타일·orientation 효과 측정 가능

**명령**: `python run_record.py record --task 1 --episodes 20`
**instruction**: `Pick up the blue and yellow doll and place it on the left side of the table`
**orientation / 시연자**: back (인형 뒤통수가 카메라에 보이게) · **인혁이형** (검은 상의 + 흰 바지, 화각 밖 — operator 자리)

| 차원 | 값 |
|---|---|
| 위치분포 | **인형 시작 위치 일관 (좌측 고정)** — 12차와 동일. 20ep 전체 동일 좌측 위치에서 시작 |
| 조명 | 형광등 — 8~12차와 동일 |
| 배경 | 승민 전여친 랩실 (인혁이형 operator 자리 → 텅 빈 배경, 12차와 유사) |

**계획 근거**:
- **task1 back 잔여 +80** (front 잔여 +50) → back 우선 진입으로 균형 가속
- **시연자 다양화 확장** — 12차 (승민) 에 이어 13차 (인혁이형) 도입 → task1 시연자 2명 도달 (1·2·3차 본인 사후 분류 X 제외)
- **12차 ↔ 13차 controlled pair** — 위치분포·옷차림·조명·배경 동일, orientation+시연자 만 변동 → 학습 시 변수별 효과 측정 자산
- 11차 시도 1 / 13차 시도 1 incident 교훈: 4 연속 배치 회피 + 마운트 사전 점검 강화

| 항목 | 값 |
|---|---|
| 추가 episodes | 20 (index 210~229) |
| 누적 episodes | **230** (task 1: 90 / task 2: 140) — info.json 확인 |
| 추가 frames | 10,573 (평균 528 ≈ **17.6초**) |
| 비디오 청크 | top/wrist 각 `file-012` 신규 (top 11.6 MB / wrist 39.9 MB) |
| Hub push | ✅ 클린 (52.1 MB 신규 업로드, **롤백 후 Hub consistency 동기화로 이전 chunk file-000~011 도 re-upload** — file-list 정합 작업) |
| 종료 | ✅ 클린 (top/wrist/follower/leader 순차 disconnect, Hub push 완료, Exiting 18:24:57) |

**관찰**:
- FPS warning 동일 패턴 (steady 20~30 Hz, warmup spike 1.5~1.6 Hz). 8차~13차 일관
- **episode 길이 17.6초** — 12차 17.8초 / task1 본인 평균 (15.4~20.5초) 와 비슷한 범위. **시연자 변경 효과 episode 길이 측면 미미** (승민 vs 인혁이형 거의 동일)
- **Feetech 통신 크래시 0회 (시도 2 전체)** — SO-ARM 마운트 재고정 후 안정. 시도 1 의 물리 분리 incident 재발 없음
- **마운트 재고정 후 캘리브 정합 OK** — teleop sanity 통과 + 본 수집 20ep 무이슈 → 마운트 재고정이 캘리브 무효화하지 않음 확인
- **12차↔13차 controlled pair 완성** — 위치분포(좌측)·옷차림·조명·배경 동일, orientation(F↔B) + 시연자(승민↔인혁이형) 만 변동. 본 batch 가 *시연자 spillover 효과 + orientation 효과* 측정 자산
- **task1 누적 90/200 (45%)** — 8차 50→70→90 로 task1 진행률 가속 회복
- **Hub 정합 작업** — 롤백 후 첫 push 라 Hub 측 file-list 재정렬 됨 (file-000~011 + file-012 모두 새로 push). 향후 차수는 신규 file-013 만 push 예상

---

### 14차 — 2026-05-18 18:37 · task 1 (doll) · +20 episodes (ep 230~249) · RESUME · **orientation: back (뒤통수)** · **시연자 (person): 인혁이형 (검은 상의 + 흰 바지, 화각 밖 — operator)**

> **13차와 완전 동일 config (Option A — 단순 doubling)** — task1 / back / 인혁이형 operator / 인형 좌측 고정 / 낮 형광등 / 승민 전여친 랩실. 변수 변동 없음 → 새 통제 페어 형성 X. 효과는 *back 보강 + 13차 단독 20ep → 13·14차 누적 40ep 통계 견고화*.

**명령**: `python run_record.py record --task 1 --episodes 20`
**instruction**: `Pick up the blue and yellow doll and place it on the left side of the table`
**orientation / 시연자**: back (인형 뒤통수가 카메라에 보이게) · 인혁이형 (검은 상의 + 흰 바지, 화각 밖 — operator) — 13차와 동일

| 차원 | 값 |
|---|---|
| 위치분포 | 인형 시작 위치 일관 (좌측 고정) — 12·13차와 동일 |
| 조명 | 형광등 — 8~13차와 동일 |
| 배경 | 승민 전여친 랩실 (인혁이형 operator 자리 → 텅 빈 배경) — 13차와 동일 |

**계획 근거**:
- task1 back 잔여 +60 → +40 로 보강 (back 40→60)
- 13차 batch 통계 견고화 (single batch 20ep → 2 batch 40ep) — 동일 setup 내 시연 변동성 노이즈 분리에 유리
- 시연자 다양화는 정체 (인혁이형 batch 2회 연속) — 14차 단독으론 다양성 비추진 (단 doubling 가치로 정당화)

| 항목 | 값 |
|---|---|
| 추가 episodes | 20 (index 230~249) |
| 누적 episodes | **250** (task 1: 110 / task 2: 140) — info.json 확인 |
| 추가 frames | 9,984 (평균 499 ≈ **16.6초**) |
| 비디오 청크 | top/wrist 각 `file-013` 신규 (top 11.1 MB / wrist 37.2 MB) |
| Hub push | ✅ 클린 (48.8 MB 신규 업로드 — 13차 push 후 잔여 정합 작업 일부 추가 동기화) |
| 종료 | ✅ 클린 (top/wrist/follower/leader 순차 disconnect, Hub push 완료, Exiting 18:37:24) |

**관찰**:
- FPS warning 동일 패턴 (steady 25~30 Hz). 13차와 일관
- **episode 길이 16.6초** — 13차 17.6초 → 14차 16.6초로 1초 단축. *같은 시연자 (인혁이형) batch 1→2 시연 숙달* 효과 — 1·2·3차 본인 (20.5→17.4→15.4 → 학습 곡선), 12차 승민 (17.8), 13·14차 인혁이형 (17.6→16.6) 모두 동일 패턴 (시연자별 첫 batch ~17~20초 → 두번째 batch ~16초). **시연자 학습 곡선 일관성 확인**
- **Feetech 통신 크래시 0회** — 7 연속 차수 무사고 (8·9·10·11·12·13·14)
- **task1 누적 110/200 (55%)** — task1 50% 마일스톤 돌파
- **전체 250/400 (62.5%)** — *오늘 하루 (2026-05-18) 7 차수 +140ep 누적*
- 통제 페어 추가 없음 (13차와 동일 config) — 14차 단독 가치는 doubling 통계 + back 보강

---

### 15차 — 2026-05-18 21:04 · task 1 (doll) · +20 episodes (ep 250~269) · RESUME · **orientation: front (얼굴)** · **시연자 (person): 인혁이형 (검은 상의 + 흰 바지, 화각 밖 — operator)**

> **오늘 마감 3 차수 (15·16·17) 첫 차수**. 15·16 = task1 인혁이형 operator (front/back 각 20), 17 = task2 인혁이형 receiver 화각 밖 (front 20). 17차 끝나면 310/400 = 77.5% 도달.

> **포트 swap 갱신 (20:48 직후)** — Orin 추론 후 by-id 재확인 → follower ACM1→ACM0, leader ACM0→ACM1. base_config.yaml hardware 섹션 갱신 완료. backlog 에 by-id 경로 전환 제안 추가 (🔥).

> **12차 ↔ 15차 = 시연자 단일 변수 통제 pair** — 둘 다 task1 / front / 좌측 고정 / 검은상의·흰바지 (12차는 승민 검은상의·건색바지) / 낮 형광등 / 승민 전여친 랩실. **시연자 (승민↔인혁이형) 만 변동**. 새 controlled pair 형성.

**명령**: `python run_record.py record --task 1 --episodes 20`
**instruction**: `Pick up the blue and yellow doll and place it on the left side of the table`
**orientation / 시연자**: front (인형 얼굴이 카메라에 보이게) · 인혁이형 (검은 상의 + 흰 바지, 화각 밖 — operator)

| 차원 | 값 |
|---|---|
| 위치분포 | 인형 시작 위치 일관 (좌측 고정) — 12·13·14차와 동일 |
| 조명 | 형광등 — 일관 |
| 배경 | 승민 전여친 랩실 (인혁이형 operator → 텅 빈 배경) |

**계획 근거**:
- task1 front 50/100 → 70/100 보강 (front 부족분 +50 → +30)
- **12차 ↔ 15차 시연자 단일 변수 페어** = 학습 시 같은 task·동일 조건에서 시연자 trajectory 스타일 차이 효과 측정 자산
- 인혁이형 task1 operator 누적 40→60 (균형 ↑)

| 항목 | 값 |
|---|---|
| 추가 episodes | 20 (index 250~269) |
| 누적 episodes | **270** (task 1: 130 / task 2: 140) — info.json 확인 |
| 추가 frames | 9,505 (평균 475 ≈ **15.8초**) |
| 비디오 청크 | top/wrist 각 `file-014` 신규 (top 9.55 MB / wrist 33.6 MB) |
| Hub push | ✅ 클린 (43.6 MB 신규 업로드, 일부 이전 청크 정합 재push 포함) |
| 종료 | ✅ 클린 (top/wrist/follower/leader 순차 disconnect, Hub push 완료, Exiting 21:03:52) |

**관찰**:
- FPS warning 동일 패턴 (steady 20~30 Hz). 포트 swap 후에도 안정 유지
- **episode 길이 15.8초** — 인혁이형 task1 batch 3 (13차 17.6→ 14차 16.6→ 15차 15.8). **본인 task1 plateau (1차 20.5→3차 15.4) 와 거의 일치**. *시연 숙달 완료 영역 진입* — 차수별 episode 길이 변화로 시연자 학습 완료 신호 포착
- **Feetech 통신 크래시 0회** — 포트 swap 후 첫 record 도 무사고. by-id 매핑 갱신 효과 확인
- **task1 front 50→70 (70%)** — front 부족분 +50 → +30 로 완화
- **12차↔15차 시연자 단일 변수 controlled pair 완성** — 같은 task·orientation·위치·옷차림·조명·배경에서 시연자만 변동. *학습 시 시연자 스타일 효과 분리* 가능 (단 옷차림 약간 다름: 12차 승민 회색상의·건색바지 / 15차 인혁 검은상의·흰바지 — 시각 차이 있으나 둘 다 화각 밖 operator 라 영상에 안 보임 → 차이 의미 없음)
- **시연자 학습 곡선 정리** (모든 시연자 first batch ~17~20초 → 숙달 ~15~16초):
  | 시연자 | batch 1 | batch 2 | batch 3 |
  |---|---|---|---|
  | 본인 (1·2·3차 task1) | 20.5 | 17.4 | 15.4 |
  | 승민 (12차) | 17.8 | — | — |
  | 인혁 (13·14·15차 task1) | 17.6 | 16.6 | 15.8 |
  → 모든 시연자가 batch 3 즈음 ~15~16초 plateau 도달. 새 시연자 도입 시 ~3 batch 후 안정 예상

---

### 16차 — 2026-05-18 21:12 · task 1 (doll) · +20 episodes (ep 270~289) · RESUME · **orientation: back (뒤통수)** · **시연자 (person): 인혁이형 (검은 상의 + 흰 바지, 화각 밖 — operator)**

> **오늘 마감 3 차수 (15·16·17) 중 2번째**. 13·14차 (back 인혁) 와 동일 config = **3번째 doubling batch** (13·14·16차 = 60ep, 같은 setup).

**명령**: `python run_record.py record --task 1 --episodes 20`
**instruction**: `Pick up the blue and yellow doll and place it on the left side of the table`
**orientation / 시연자**: back (인형 뒤통수가 카메라에 보이게) · 인혁이형 (검은 상의 + 흰 바지, 화각 밖 — operator) — 13·14차 동일

| 차원 | 값 |
|---|---|
| 위치분포 | 인형 시작 위치 일관 (좌측 고정) — 12·13·14·15차와 동일 |
| 조명 | 형광등 |
| 배경 | 승민 전여친 랩실 (인혁이형 operator → 텅 빈 배경) |

**계획 근거**:
- task1 back 60/100 → 80/100 (back 잔여 +40 → +20)
- 13·14차 batch 통계 3차 doubling — 동일 setup 60ep 누적으로 task1 back 가장 견고한 영역
- 인혁이형 task1 operator 누적 60→80 (task1 시연자 비중 ↑ — 본인 50 / 승민 20 / 인혁 80)

| 항목 | 값 |
|---|---|
| 추가 episodes | 20 (index 270~289) |
| 누적 episodes | **290** (task 1: 150 / task 2: 140) — info.json 확인 |
| 추가 frames | 8,775 (평균 439 ≈ **14.6초**) |
| 비디오 청크 | top/wrist 각 `file-015` 신규 (top 9.14 MB / wrist 29.8 MB) |
| Hub push | ✅ 클린 (39.4 MB 신규 + 일부 이전 청크 정합 재push) |
| 종료 | ✅ 클린 (top/wrist/follower/leader 순차 disconnect, Exiting 21:11:54) |

**관찰**:
- FPS warning 동일 패턴 (steady 28~30 Hz). 시연 후반 episode 들이 안정 영역
- **episode 길이 14.6초** — 15차 (15.8) plateau 깨고 *더 짧아짐*. 인혁이형 task1 batch 4 = **본인 task1 plateau (15.4초) 추월**:
  | 시연자 | batch 1 | batch 2 | batch 3 | batch 4 |
  |---|---|---|---|---|
  | 본인 (1·2·3차) | 20.5 | 17.4 | 15.4 | — |
  | 인혁 (13·14·15·16차) | 17.6 | 16.6 | 15.8 | **14.6** |
  → 반복 숙달이 본인 plateau 보다 ~1초 빠른 영역 진입 — *첫 사례*
- **Feetech 통신 크래시 0회** — 8·9·10·11·12·13·14·15·16차 = 9 연속 무사고
- **task1 150/200 (75%) — 75% 마일스톤 돌파**. 12차 직전 25% → 16차 75%, 4 차수 만에 50%p 가속
- 13·14·16차 = back 인혁 동일 setup 3-batch doubling 완성 (60ep) → task1 back 가장 견고한 통계 영역

---

### 17차 — 2026-05-18 21:22 · task 2 (can) · +20 episodes (ep 290~309) · RESUME · **orientation: front (캔 문양)** · **person (receiver): 인혁이형 (검은 상의 + 흰 바지, 화각 밖)**

> **오늘 마감 최종 차수 (3 차수 중 3번째)**. 17차 종료로 **310/400 = 77.5% 도달 → 오늘 마감**.

> **front 선택 근거**: task2 잔여 front +40 > back +20 → front 우선으로 80F/80B 균등 도달. **11차와 동일 config doubling** (11차 ep 170~189: task2 front 인혁 화각밖 좌측 — 17차도 동일).

**명령**: `python run_record.py record --task 2 --episodes 20`
**instruction**: `Hand the yellow can to the person`
**orientation / person**: front (캔 문양이 카메라에 보이게) · 인혁이형 (검은 상의 + 흰 바지, 화각 밖 — receiver 자리 비움)

| 차원 | 값 |
|---|---|
| 위치분포 | 캔 좌측 (9·10·11차와 동일) |
| 조명 | 형광등 |
| 배경 | 승민 전여친 랩실 (인혁이형 receiver 자리 비움 → 배경만, 10·11차와 유사) |

**계획 근거**:
- task2 front 잔여 +40 > back +20 → front 우선 (균형 회복)
- **11차 ↔ 17차 = 같은 config doubling** (둘 다 front · 인혁 화각밖 · 좌측) → task2 front 인혁 화각밖 누적 40ep, 통계 견고화
- 10차 ↔ 11·17차 = orientation 단일 변수 페어 유지 (10차 back 1 batch ↔ 11·17차 front 2 batch)
- task2 80F/80B 균등 도달 (현재 60F/80B 격차 해소)
- 전체 290→310 (72.5% → 77.5%)

| 항목 | 값 |
|---|---|
| 추가 episodes | 20 (index 290~309) |
| 누적 episodes | **310** (task 1: 150 / task 2: 160) — info.json 확인 |
| 추가 frames | 9,382 (평균 469 ≈ **15.6초**) |
| 비디오 청크 | top/wrist 각 `file-016` 신규 (top 10.3 MB / wrist 34.5 MB) |
| Hub push | ✅ 클린 (45.4 MB 신규 + 일부 이전 청크 정합 재push) |
| 종료 | ✅ 클린 (top/wrist/follower/leader 순차 disconnect, Exiting 21:21:52) |

**관찰**:
- FPS warning 동일 패턴 (steady 25~30 Hz). 오늘 모든 차수 (8~17) FPS 거동 일관 — h264_nvenc 안정
- **episode 길이 15.6초** — task2 인혁 batch 길이 추세: 4차 21.5 / 8차 18.2 / 9차 19.0 / 10차 19.5 / 11차 19.4 / **17차 15.6**. 6 batch 후 ~16초 plateau 도달 (task1 인혁 batch 4 (14.6) 와 거의 유사). 시연자 task 무관 plateau 수렴
- **Feetech 통신 크래시 0회** — 8~17차 = 10 연속 무사고 (11차 시도 1·13차 시도 1 incident 후 모든 시도 2/이후는 안정)
- **task2 160/200 (80% 마일스톤 돌파)** — 8차 직전 30% → 17차 80%, 오늘 하루 50%p 가속
- **task2 80F/80B 균등 도달** — 11차 ↔ 17차 doubling 으로 격차 완전 해소
- 11차↔17차 = task2 front 인혁 화각밖 좌측 동일 setup 2-batch doubling 완성 (40ep) → task2 front 통계 견고
- **오늘 마감 (2026-05-18) — 10 차수 +200ep 누적**, 전체 310/400 = 77.5%. 잔여 +90ep 는 추후 진행

---

## 다음 차수

현재 task 1 누적 **150/200** (70F/80B, 75%), task 2 누적 **160/200** (80F/80B 균등, 80%). 전체 **310/400 = 77.5%**. 8~17차 완료 (2026-05-18 하루에 **+200ep**, 110→310). **오늘 마감** — 자세한 종합은 아래 [오늘 마감 종합](#오늘-마감-종합--2026-05-18) 참조. 잔여: task1 50 (+30F/+20B) + task2 40 (+20F/+20B) = 90ep. 향후 차수: task1 / task2 어느 쪽이든 50% 미만 남음 (task1 75% / task2 80%). 새 시연자·인물 도입 가치 ↑. 목표 조정 사유: 2026-05-18 — researcher 추정 영역 (300~500ep) 진입 + camera mismatch 확신 영역 도달.

### 오늘 마감 종합 — 2026-05-18

**시작 → 마감**: 110ep → **310ep (+200ep, 10 차수)**. 3일 휴지 후 첫 세션부터 80% 가까이 가속.

**Incident 2건 → 모두 회복**:
| Incident | 원인 | 영향 | 해결 |
|---|---|---|---|
| 11차 시도 1 | Feetech 통신 크래시 (`There is no status packet`) | 0 ep (즉시 crash, 롤백 불필요) | 모터 전원 사이클 → 텔레옵 sanity → 11차 시도 2 성공 |
| 13차 시도 1 | SO-ARM 물리 분리 → 사용자 Ctrl-C | 2 ep 단독 저장 → 5차 절차 준용 롤백 (file-012 삭제 + info.json 정정) | 마운트 재고정 + 텔레옵 + Ctrl-C cleanup 으로 torque release → 13차 시도 2 성공 |

**Controlled pair 4종 형성** (학습 후 평가에 직접 활용):
| Pair | 변동 변수 | 동일 변수 (통제) |
|---|---|---|
| 8차↔9차 (task2) | 위치분포 (중앙↔좌) | back · 화각 안 · 인혁 · 옷차림 · 형광등 · 배경 |
| 9차↔10차 (task2) | 화각 (안↔밖) | back · 좌측 · 인혁 · 옷차림 · 형광등 · 배경 |
| 10차↔11·17차 (task2) | orientation (back↔front) | 화각 밖 · 좌측 · 인혁 · 옷차림 · 형광등 · 배경 (11·17 = doubling) |
| 12차↔15차 (task1) | 시연자 (승민↔인혁) | front · 좌측 · 옷차림 가정 · 형광등 · 배경 |

**Doubling batches**:
- task1 back 인혁 좌측: 13·14·16차 (60ep, 3-batch)
- task1 front 인혁 좌측: 15차 단독 (20ep) — 추후 doubling 여지
- task2 front 인혁 화각밖 좌측: 11·17차 (40ep, 2-batch)
- task2 back 성래 화각 외: 7차 단독 (20ep)
- task2 back 인혁 화각 안 좌측: 9차 단독 (20ep)
- task2 back 인혁 화각 밖 좌측: 10차 단독 (20ep)

**시연자별 학습 곡선** (모든 시연자 batch 3~4 에서 ~15~16초 plateau 수렴):
| 시연자 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| 본인 task1 (1·2·3차) | 20.5 | 17.4 | 15.4 | — |
| 승민 task1 (12차) | 17.8 | — | — | — |
| 인혁 task1 (13·14·15·16차) | 17.6 | 16.6 | 15.8 | **14.6** ← 본인 plateau 추월 |
| 인혁 task2 (4·8·9·10·11·17차) | 21.5 | 18.2 | 19.0 | 19.5 → 19.4 → **15.6** ← 6 batch 후 plateau |

**조명 정정** — 8~17차 모두 "형광등" 으로 통일 (시간 컬럼이 시간대 제공). 8차(14:59)~10차(15:34) 만 낮 시간, 11차(15:53)부터는 점차 저녁이라 "낮 (형광등)" 표기 부정확했음.

**포트 swap 2회** — 13:50 (3일 휴지 후) / 20:48 (Orin 추론 후). by-id 매핑은 안정. backlog 🔥 항목 추가 (by-id 경로로 base_config 전환).

**잔여 90ep / 가설** — task1 +50 (+30F/+20B), task2 +40 (+20F/+20B). 향후 차수 = **새 시연자 / 새 인물 / 다양화 차원 (조명·배경 변화)** 도입이 우선. 인혁이형 task1 80ep + task2 110ep = 190ep 비중 ↑ 라 다양성 확보 시급.

### 50개 시점 점검 — 완료 (2026-05-15)

| 점검 항목 | 결과 |
|---|---|
| FPS sub-30Hz → frame drop? | ✅ **이상 없음** — timestamp 전수 분석, 50 ep 전부 33.33ms 균일, gap 0. dataset 무결. FPS 는 polish 항목으로 격하 |
| instruction grounding ("테이블 왼쪽") | ✅ 사용자 확인 — 카메라 화면에서 명확 |
| episode 길이 3연속 하락 (20.5→17.4→15.4초) | ✅ 사용자 확인 — 반복 숙달로 인한 단축, trajectory 누락 아님 |

→ **3개 항목 모두 clear. task 1 본 수집 계속 진행 가능.**

### 진행 계획 (400ep 목표 기준)

> **명령은 orientation·person 과 무관하게 동일** (`--task N --episodes M`). 시연 시 물체 방향 / 사람 / 위치분포 / 조명 / 배경을 표대로 통제 + 로그 entry 에 기록 (8차부터 신규 다양화 칼럼 적용).

#### Task 1 (doll) — 남은 +150 (50 → 200)

현재 **front 30 / back 20**. 200 ep 시점 100/100 균형 목표 → 추가로 **front +70 / back +80** 필요.

권장 분할 전략 (예시 — 차수당 20ep 기준 ~8 차수):

| 차수 | 명령 | orientation | person | 위치분포 | 조명 | 배경 | task 1 누적 (F/B) |
|---|---|---|---|---|---|---|---|
| 8 | `--task 1 --episodes 20` | **back** | 본인 | 좌/중/우 골고루 | default | clean | 30F/40B = 70 |
| 9 | `--task 1 --episodes 20` | **front** | 본인 | 좌/중/우 골고루 | default | clean | 50F/40B = 90 |
| 10 | `--task 1 --episodes 20` | **back** | 인혁이형 | 좌/우 위주 | default | clean | 50F/60B = 110 |
| 11 | `--task 1 --episodes 20` | **front** | 인혁이형 | 좌/우 위주 | 다른 시간대 | clean | 70F/60B = 130 |
| 12 | `--task 1 --episodes 20` | **back** | 본인 | 중앙 위주 | default | 주변 사람 | 70F/80B = 150 |
| 13 | `--task 1 --episodes 20` | **front** | 새 사람 D | 좌/중/우 골고루 | default | clean | 90F/80B = 170 |
| 14 | `--task 1 --episodes 20` | **back** | 새 사람 D | 좌/우 위주 | default | clean | 90F/100B = 190 |
| 15 | `--task 1 --episodes 10` | **front** | 본인 | 중앙 위주 | default | clean | 100F/100B = **200** ✅ |

→ task 1 최종 (예시): 본인 80 + 인혁이형 40 + 새 사람 D 40 + 본인 추가 40 = 200, F100/B100.

#### Task 2 (can) — 남은 +140 (60 → 200)

현재 **front 40 (인혁이형 10 + 성래 30) / back 20 (성래 20)**. 200 ep 시점 100/100 균형 목표 → 추가로 **front +60 / back +80** 필요.

권장 분할 전략 (예시):

| 차수 | 명령 | orientation | person | 위치분포 | 조명 | 배경 | task 2 누적 |
|---|---|---|---|---|---|---|---|
| 16 | `--task 2 --episodes 20` | **back** | 인혁이형 | 좌/우 위주 | default | clean | 80 (F40/B40) |
| 17 | `--task 2 --episodes 20` | **back** | 새 사람 C (화각 내) | 좌/중/우 골고루 | default | clean | 100 (F40/B60) |
| 18 | `--task 2 --episodes 20` | **front** | 새 사람 C | 좌/중/우 골고루 | default | clean | 120 (F60/B60) |
| 19 | `--task 2 --episodes 20` | **back** | 새 사람 D (화각 내) | 좌/우 위주 | 다른 시간대 | clean | 140 (F60/B80) |
| 20 | `--task 2 --episodes 20` | **front** | 새 사람 D | 좌/중/우 골고루 | default | 주변 사람 | 160 (F80/B80) |
| 21 | `--task 2 --episodes 20` | **front** | 인혁이형 | 좌/우 위주 | default | clean | 180 (F100/B80) |
| 22 | `--task 2 --episodes 20` | **back** | 본인 (수신자 역) | 중앙 위주 | default | clean | **200** (F100/B100) ✅ |

→ task 2 최종 (예시): 인혁이형 50 (F30/B20) + 성래 50 (F30/B20) + 새 사람 C 40 (F20/B20) + 새 사람 D 40 (F20/B20) + 본인 20 (F0/B20) = 200, F100/B100.

> 위 split 은 예시. **인혁이형 back 미수집 + 새 사람 (C·D) 추가 + 본인 task 1 외 시연자 다양화 + 위치분포 의식적 명시** 가 핵심.
>
> 새 사람 추가 시 [수집 컨벤션 §2](#2-사람-정보-task-2-전용) 의 "현재 등록 인물" 표 갱신.
>
> ⚠️ **성래 화각 외 우려**: 5차 entry 참조. 새 사람 (C·D) 추가 시 **화각에 명확히 들어오는 위치** 권장 — instruction grounding 다양성 확보.

### 200ep 시점 중간점검 (권장)

400ep 도달 *전* 에 200ep 시점 (= M1.5 와 동일 데이터 양 × 2) 에서 한번 *중간 학습 + Orin 추론* 권장. 의도:
- 100ep → 200ep 변화에서 *성공률 변동 측정* — 데이터 양 효과 정량화
- 200ep 결과가 0% 정체 → 400ep 까지 가는 *근거 강화*
- 200ep 결과가 유의미 개선 → 400ep 도달 *기대치 calibration*

단 *학습 비용 추가* (8h+) — 본인 결정 영역. 200ep 중간점검 없이 400ep 까지 한 번에 가도 무관.
</content>
