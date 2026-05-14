# Gesture 시스템 — 작업 핸드오프 (Jetson AI 캐치업용)

> **작성**: 2026-05-14
> **목적**: DGX 측에서 진행한 gesture 시스템 작업 현황을 Jetson(brain) 측 AI 세션이 이어받아 계속할 수 있도록 정리.
> **이 파일 위치**: DGX `~/smolvla/dgx/docs/gesture_handoff.md` = Jetson `~/smolvla/orin/gesture/GESTURE_HANDOFF.md` (양쪽 동일 내용)
> **함께 읽을 문서**:
> - `~/smolvla/orin/gesture/gestures_jetson_setup_prompt.md` — Jetson wrapper 구현 가이드 (이미 §1~§9 참조됨)
> - DGX `~/smolvla/dgx/docs/gestures.md` — 전체 아키텍처 / 안전 원칙 (Jetson 에는 없을 수 있음)

---

## 0. 목표 (한 줄)

DGX 에서 우측 SO-ARM 팔로 제스처(인사 등)를 녹화 → Jetson 으로 sync → **Jetson 의 brain(coordinator.py)이 사용자 명령을 받아 gesture 로 분류하면 그 제스처를 우측 팔로 재생**.

```
[DGX]  record_gesture.sh        [rsync]      [Jetson]  coordinator.py (brain)
  우측 팔 teleop 녹화      ───────────────>     STT → LLM intent 분류
  (1회/gesture)                                  └─ intent=="gesture" → play_gesture.sh <name>
                                                       └─ lerobot-replay → 우측 follower
```

VLA/ACT 추론 없음 — lerobot 의 record/replay 만 사용. 우측 팔 전담 (좌측은 SmolVLA inference 용, 건드리지 않음).

---

## 1. 현재 진행 상황 (2026-05-14 기준)

| Phase | 상태 | 비고 |
|---|---|---|
| **A. 우측 팔 셋업** | ✅ 완료 | DGX 에서 포트 식별 + follower/leader 캘리브 + teleop 검증 |
| **B. gesture 녹화** | ✅ 진행중 | `wave_hello`(208 frames), `wave_hello_2`(236 frames) 녹화 완료. 추가 녹화는 DGX 에서 언제든 가능 |
| **C. Jetson sync** | ✅ 완료 | 두 gesture + follower 캘리브 Jetson 으로 sync 됨 (md5 일치 확인) |
| **D-build. wrapper** | ✅ 완료 | Jetson `play_gesture.sh` + `check_gesture_ready.sh` 구축, dry-run exit code 검증 완료 |
| **D-test. 실 replay** | ⏸ **대기** | 우측 follower 가 아직 DGX 에 연결됨. Jetson 에 연결해야 실 검증 가능 |
| **E. coordinator 통합** | ⬜ **미시작** | 작업 지점 파악 완료 (아래 §5). **이 핸드오프의 핵심 남은 작업** |

---

## 2. 핵심 경로 / 자원

### DGX 측 (녹화 전담)
- 우측 follower 포트: `/dev/serial/by-id/usb-1a86_USB_Single_Serial_5AE6082773-if00`
- 우측 leader 포트: `/dev/serial/by-id/usb-1a86_USB_Single_Serial_5AE6056701-if00`
- 캘리브: `~/smolvla/.hf_cache/lerobot/calibration/{robots/so_follower,teleoperators/so_leader}/rightarm_test_{follower,leader}.json`
- gesture 원본: `~/smolvla/dgx/gestures/{wave_hello, wave_hello_2}/`
- 스크립트: `~/smolvla/dgx/scripts/{record_gesture.sh, sync_gesture_to_orin.sh, read_wrist_roll.py}`

### Jetson 측 (재생 전담)
- venv: `~/smolvla/orin/.hylion_arm` (Python 3.10, lerobot **0.5.2** — DGX 와 동일 버전)
- wrapper: `~/smolvla/orin/scripts/{play_gesture.sh, check_gesture_ready.sh}` ← **이미 구축됨, dry-run 검증 완료**
- gesture 데이터: `~/smolvla/orin/gestures/{wave_hello, wave_hello_2}/`
- 캘리브: `~/.cache/huggingface/lerobot/calibration/robots/so_follower/rightarm_test_follower.json`
  - ⚠️ Jetson 은 HF_HOME **미설정** → lerobot 이 `~/.cache/huggingface` 기본값 사용. `~/smolvla/.hf_cache` 아님!
- brain coordinator: `/home/laba/Hylion/jetson/core/coordinator.py` ← **Phase E 작업 대상**
- LLM 분류 레이어: `/home/laba/Hylion/jetson/core/llm/` (`prompt.py`, `groq_llm.py`, `ollama_llm.py`, `factory.py`, `base.py`)

### 우측 follower robot.id
- `rightarm_test_follower` (follower), `rightarm_test_leader` (leader)
- `/dev/ttyACMx` 번호는 부팅마다 바뀌므로 **항상 by-id 시리얼 경로 사용**

---

## 3. play_gesture.sh / check_gesture_ready.sh (D-build 산출물)

이미 Jetson `~/smolvla/orin/scripts/` 에 배치 + chmod +x + dry-run 검증 완료.

**play_gesture.sh 인터페이스:**
```
Usage: bash play_gesture.sh <gesture_name>
Exit: 0=성공(disconnect overload cosmetic 포함), 2=인자오류, 3=환경, 4=데이터/캘리브, 5=포트, 1=재생실패
Stdout: 한 줄 요약 "[play_gesture] <name>: frames=N, elapsed=Ns, rc=N"
```

**env override (기본값 hardcoded):**
- `FOLLOWER_PORT` (기본 `/dev/serial/by-id/usb-1a86_USB_Single_Serial_5AE6082773-if00`)
- `FOLLOWER_ID` (기본 `rightarm_test_follower`)
- `ORIN_GESTURES_ROOT` (기본 `~/smolvla/orin/gestures`)
- `JETSON_VENV` (기본 `~/smolvla/orin/.hylion_arm`)

**dry-run 검증 결과 (팔 미연결 상태):**
- `check_gesture_ready.sh wave_hello` → exit 5 (포트만 없음 — venv/lerobot/데이터/캘리브 4단계는 통과)
- `play_gesture.sh nonexistent_gesture` → exit 4
- `play_gesture.sh Bad-Name` → exit 2

---

## 4. 알려진 이슈 / 주의사항

### 4-1. wrist_roll dead zone (중요)
이 SO-ARM 의 wrist_roll(motor 5)은 진짜 무한 회전이 아니라 ~350° 한계. 인코더가 wraparound (raw 2400→4095→0→1800) 하며 `(1800, 2400)` raw 구간이 dead zone(mech stop). lerobot 은 wrist_roll 을 full-turn 으로 하드코딩(range 0-4095)해서 이 dead zone 을 모름.
- **녹화 시 wrist_roll 을 안전 위치(~1500 raw)에 고정**하고 안 건드림 (wave 는 wrist_flex 로). DGX `read_wrist_roll.py` 로 raw 값 확인 가능.
- dead zone 진입 시 → 모터 overload.

### 4-2. disconnect overload = cosmetic
lerobot-record/replay 가 동작 정상 완료 후 `disconnect()` → `disable_torque` 단계에서 모터 overload error register 때문에 non-zero exit 하는 경우가 있음. 재생 자체는 완료된 상태.
- `play_gesture.sh` 가 이미 이걸 감지(`"Replaying episode"` + `"Overload error"` + `"in disconnect"` 패턴) → exit 0 으로 처리. coordinator 가 매번 실패로 오인하지 않도록.

### 4-3. 전원 cycle
record/replay 전 우측 follower 보드 **전원 cycle (off→5s→on)** 권장 — 이전 동작에서 남은 모터 error state 클리어. USB 는 안 빼도 됨.

### 4-4. 좌측 팔 격리
좌측 팔(`leftarm_test_*`, 시리얼 5B42...)은 SmolVLA 학습용. **절대 건드리지 말 것** — 캘리브/데이터셋/좌표계 무효화 위험. gesture 시스템은 우측 팔(5AE...) 전담.

### 4-5. SSH 비대화형 venv
Jetson SSH 비대화형 세션은 `~/.bashrc` 안 읽음 → venv activate 누락. `play_gesture.sh` 는 이미 venv activate 를 명시적으로 함.

---

## 5. 남은 작업

### Phase D-test (우측 follower 를 Jetson 에 물리 연결 후)

1. 우측 follower USB 를 DGX → Jetson 으로 이동 (leader 는 녹화 전용이라 안 옮겨도 됨)
2. Jetson 에서 `lerobot-find-port` 또는 `ls /dev/serial/by-id/` 로 확인 — by-id 경로는 시리얼(5AE6082773) 기반이라 그대로 유효
3. 우측 follower 전원 cycle
4. dry-run: `bash ~/smolvla/orin/scripts/check_gesture_ready.sh wave_hello` → exit 0 기대 (이제 포트도 있으니)
5. 실 재생 (빈 공간, 사용자 입회): `bash ~/smolvla/orin/scripts/play_gesture.sh wave_hello`
   - 우측 팔이 인사 동작 재생하면 ✅ D-test 통과
   - 첫 프레임 jerk 시 → follower 를 녹화 시작 자세(home pose)와 비슷하게 두고 재시도

### Phase E — coordinator.py 에 gesture intent 통합 (핵심 남은 작업)

**선행 권장**: D-test 완료 후 (play_gesture.sh 가 실제 동작함을 확인한 뒤 wiring).

**E-1. LLM 분류 레이어 (`/home/laba/Hylion/jetson/core/llm/prompt.py`)**
- `VALID_INTENTS` 에 `"gesture"` 추가 (현재: `chat, pick_place, move, stop, standby, unknown`)
- gesture 이름 운반 필드 결정 — 설계 선택지:
  - (a) 신규 5번째 CORE_FIELD `gesture_name` 추가 (현재 `CORE_FIELDS = ("intent","target_object","reply_text","gait_cmd")`)
  - (b) 기존 `target_object` 재사용 (pick_place 가 쓰는 패턴 — 덜 침습적이지만 의미 모호)
  - → 권장: (a) `gesture_name`. `gait_cmd` 가 move 전용 sub-command 인 것과 같은 패턴
- intent→state 매핑에 `gesture` 추가 (state enum: IDLE/TALKING/MANIPULATING/WALKING/EMERGENCY — gesture 는 MANIPULATING 또는 IDLE)
- intent→reply 매핑 추가 (예: `"gesture": "응, 인사할게!"`)
- intent 판단 규칙 추가 (예: `"인사해 / 손 흔들어 / 안녕 → gesture, gesture_name에 해당 동작 이름"`)
- 출력 예시 추가
- 유효 gesture 이름 enum 은 registry 와 동기화 (E-3)

**E-2. 실행 라우팅 (`/home/laba/Hylion/jetson/core/coordinator.py` `_route_action()`)**
- 현재 `_route_action()` 은 전부 mock (print + sleep). `elif intent == "gesture":` 분기 추가
- `subprocess` 로 `/home/laba/smolvla/orin/scripts/play_gesture.sh <gesture_name>` 호출
- exit code 처리: 0=성공, 2/3/4/5/1=실패 → 로그 + (선택) TTS 피드백
- gesture 는 coordinator 의 **첫 실제(non-mock) executor** 가 됨 — 신중히
- USB mutex: gesture replay 중 다른 gesture 호출 거부 또는 직렬화 (현재는 "1 명령 → 1 동작 → 종료" 가정)

**E-3. gesture registry (유효 이름의 single source of truth)**
- LLM 프롬프트의 gesture_name enum 과 실제 사용 가능한 gesture 가 어긋나지 않도록
- 방식: `~/smolvla/orin/gestures/*/meta/info.json` 디렉토리 스캔 (동적) 또는 `registry.json` (정적)
- 현재 사용 가능 gesture: `wave_hello`, `wave_hello_2`

**E-4. End-to-end 검증**
- Jetson 에서 사용자 명령 ("손 흔들어줘") → coordinator STT → LLM intent=gesture, gesture_name=wave_hello → `_route_action` → `play_gesture.sh wave_hello` → 우측 팔 동작
- `jetson/core/llm/eval/` 에 intent eval 하네스 있음 — gesture intent 케이스 추가 가능

---

## 6. gesture 추가 / 갱신 워크플로우 (참고)

새 gesture 가 필요할 때:
1. (DGX) 우측 follower+leader 가 DGX 에 연결된 상태에서 `record_gesture.sh <name>` (전원 cycle + wrist_roll 안전 위치 주의)
2. (DGX) `sync_gesture_to_orin.sh <name>` — Jetson 으로 전송 (env: `ORIN_HOST=orin ORIN_HF_HOME=/home/laba/.cache/huggingface ORIN_GESTURES_ROOT=/home/laba/smolvla/orin/gestures`)
3. (Jetson) registry / 프롬프트 enum 갱신 (E-3)

---

## 7. 메모리 / 컨텍스트 (DGX claude 세션이 저장한 것)

DGX 측 claude auto-memory 에 다음이 저장됨 (Jetson claude 는 별도 메모리지만 참고):
- SO-ARM 시리얼 ↔ 역할 매핑
- SO-ARM 디버깅 교훈 (모터 overload→power cycle, 캘리브 range, env override 버그)
- Jetson 환경 레이아웃
- Hylion brain 아키텍처 (coordinator + llm 레이어)
