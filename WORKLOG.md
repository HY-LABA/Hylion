# Worklog

이 파일은 이 워크스페이스에서 진행하는 검증, 수정, 푸시 과정을 계속 기록하는 용도다.

## 사용 규칙

- 새 작업을 시작할 때 현재 목표를 짧게 적는다.
- 실행한 명령과 결과를 핵심만 기록한다.
- 코드 변경이 있으면 수정한 파일과 이유를 적는다.
- 실패한 시도는 원인과 다음 조치를 같이 남긴다.
- 푸시가 끝나면 커밋 해시와 원격 반영 여부를 적는다.

## 고정 인수인계 프로토콜 (Windows <-> Jetson)

- 이 파일(`WORKLOG.md`)을 단일 workload 기준 파일로 사용한다.
- Windows에서 작업 후 `git push` 하기 직전에 반드시 아래를 기록한다.
  - 오늘 변경 요약
  - 테스트 결과
  - 수정 파일 목록
  - 다음 환경에서 바로 할 일
- Jetson에서 `git pull` 직후 반드시 이 파일 최신 항목부터 읽고 이어서 작업한다.
- Jetson에서 작업 후 `git push` 직전에 동일 형식으로 기록한다.
- Windows에서 `git pull` 직후 동일하게 읽고 작업을 이어간다.

### Push 전 체크리스트 (공통)

- `git status --short` 확인
- `WORKLOG.md` 기록 업데이트
- 테스트 결과 기록 (성공/실패 모두)
- `git add -A && git commit && git push`

## 진행 기록

### 2026-04-21

- 마이크 검증 파일 `tests/mic_test2.wav`를 `tests/`로 이동함.
- Jetson 마이크 검증을 수행함.
- `jetson/expression/microphone.py`의 샘플레이트 흐름을 44.1kHz 기준으로 단순화함.
- `tests/4_unit/test_expression.py`를 새 기준에 맞게 조정함.
- 단위 테스트 `2 passed` 확인함.
- 생성된 WAV 파일 `data/episodes/target_smoke.wav`를 확인함.
- `git commit` 및 `git push origin ε1` 완료함.

### workflow 규칙 추가 (2026-04-21 22:55)

- WORKLOG.md 파일 신규 생성
- memories/git.md에 workflow 규칙 추가
  - `git push` 전에 작업 기록
  - `git pull` 후 기록 파일 읽고 흐름 파악

### 2026-04-22

- Windows 환경에서 `git pull origin ε1` 수행: `Already up to date` 확인.
- 현재 로컬 진행 상태(아직 미푸시):
  - `jetson/expression/microphone.py`: VAD 단계(무음 분리) 로직 추가 및 Python 3.14 호환 보정(`audioop` 제거)
  - `tests/4_unit/test_expression.py`: VAD 테스트 2건 추가
  - `docs/07_non_ros2_pipeline_master_plan.md`: Phase 2 진행 체크 갱신
- 로컬 테스트 결과: `tests/4_unit/test_expression.py` 4 passed.
- 다음 pull 환경(Jetson)에서 이어서 할 일:
  - 최신 변경 pull
  - TARGET 재검증(마이크 녹음 + VAD 동작)
  - 이상 없으면 push 전 본 파일 업데이트 후 푸시

### 2026-04-22 (추가 진행)

- `git pull origin ε1` 재확인: `Already up to date`.
- Phase 2 추가 구현(DEV):
  - `jetson/expression/stt_whisper.py` 추가
    - faster-whisper 기반 `transcribe_wav()`
    - `input_event` 변환용 `build_input_event()`
  - `tests/4_unit/test_stt_whisper.py` 추가
  - `jetson/expression/microphone.py`의 VAD 로직 Python 3.14 호환으로 보정(`audioop` 제거)
- DEV 테스트 결과:
  - `python -m pytest tests/4_unit/test_expression.py tests/4_unit/test_stt_whisper.py -q`
  - `6 passed`
- 현재 상태: DEV 구현 완료, Jetson TARGET 검증 및 push 대기

### 2026-04-22 (fallback 제거)

- 사용자 요청에 따라 microphone 쪽 샘플레이트 폴백을 제거 방향으로 정리함.
- `jetson/expression/microphone.py`
  - `default_samplerate` 메타데이터를 암묵적 기본값 없이 읽도록 정리함.
  - `record_to_wav()`는 더 이상 샘플레이트 재시도를 하지 않음.
- 로컬 테스트 결과:
  - `python -m pytest tests/4_unit/test_expression.py tests/4_unit/test_stt_whisper.py -q`
  - `6 passed`
- 다음 Jetson TARGET 확인 포인트:
  - 고정 마이크/고정 샘플레이트로 실제 녹음만 검증
  - 필요 시 샘플레이트는 호출부에서 명시적으로 넣기

### 2026-04-22 (다음 단계 5-step 확정)

- Jetson TARGET에서 다음 순서로 진행하기로 확정:
  1. `git pull origin ε1`
  2. microphone 녹음 + VAD 동작 확인
  3. whisper 전사 확인
  4. STT 결과 `input_event` 생성 확인
  5. `WORKLOG.md` 업데이트 후 `git push`
- 목적:
  - DEV unit test와 별개로 TARGET 실환경 검증 흐름 고정
  - Windows <-> Jetson 교대 시 같은 절차 재사용

### 2026-04-22 (Jetson TARGET 5-step 실행 결과)

- Step 1. `git pull`:
  - `Fast-forward` 반영 완료 (`7de5236 -> e8a181e`)
- Step 2. microphone 녹음 + VAD:
  - 1차 녹음(`data/episodes/target_smoke.wav`)은 RMS가 낮아(`max=139`) VAD 구간 검출 실패
  - 2차 재녹음(`data/episodes/target_smoke_voice.wav`)에서 VAD 구간 검출 확인
    - `rms_threshold=400`: `[(4.68, 4.95)]`
    - `rms_threshold=100`: `[(1.26, 2.16), (3.87, 4.98)]`
- Step 3. whisper 전사:
  - 초기 실패: `faster-whisper` 미설치
  - 조치: `python -m pip install faster-whisper`
  - 재실행 결과: 전사 성공 (`"마이크 테스트 마이크 테스트"`)
- Step 4. `input_event` 생성/검증:
  - 초기 샘플은 `input_text=''`로 strict schema 검증 실패 가능성 확인
  - `jsonschema` 설치 후 strict 검증으로 재확인
  - 재녹음 샘플 기준 `input_event` 검증 성공 (`ok`)
- 실행한 검증 명령(요약):
  - Python one-liner로 `record_to_wav -> detect_speech_segments -> transcribe_wav -> build_input_event -> validate_payload` 순차 실행
- 수정/생성 파일:
  - 수정: `data/episodes/target_smoke.wav` (재녹음)
  - 생성: `data/episodes/target_smoke_voice.wav`
  - 수정: `WORKLOG.md` (본 기록)
- 남은 할 일:
  - push 여부 결정 전, 샘플 WAV(`data/episodes/*`)를 커밋에 포함할지 정책 확정
  - 포함 정책 확정 후 `git add/commit/push`

## 다음 기록 형식

- 날짜
- 한 줄 요약
- 실행한 검증 명령
- 수정한 파일
- 결과
- 남은 할 일

### 2026-04-22 (Phase 3 리팩토링 정렬: schema/LLM fallback/source)

### 2026-04-22 (Phase 4 coordinator 실동작 루프 + standby intent 반영)

- 한 줄 요약:
  - mock 입력 대신 실제 마이크->Whisper->Groq 경로를 표준으로 사용하는 `coordinator.py`를 구현하고, 대화 종료용 `standby` intent 및 자동 대기 복귀 흐름을 추가했다.
- 실행한 검증 명령:
  - `python3 -m pytest tests/3_interface/test_groq_api.py -q`
  - `python3 -m jetson.core.coordinator --help`
- 수정한 파일:
  - `jetson/core/coordinator.py`
  - `jetson/cloud/groq_client.py`
  - `configs/schemas/action.schema.json`
  - `jetson/core/brain/llm_pipeline.py`
  - `tests/3_interface/test_groq_api.py`
  - `WORKLOG.md`
- 결과:
  - `coordinator.py`에서 실마이크 녹음(`record_to_wav`) -> Whisper STT(`transcribe_wav`) -> 실 Groq 호출(`build_action_json_from_stt`) 루프 구현
  - 실행 전 `GROQ_API_KEY`/네트워크 체크 및 실제 Groq API probe 추가
  - 요청대로 터미널에 `INPUT_JSON`/`ACTION_JSON` 출력 추가
  - chat 의도는 루프 유지, 대화 종료 키워드 감지 시 `intent=standby`로 전환
  - `pick_place`/`move`/`stop` 이후 자동 `ACTION_JSON (AUTO-STANDBY)` 출력 및 대기 모드 복귀
  - action schema의 `intent` enum에 `standby` 추가
  - 인터페이스 테스트에 conversation-end -> standby 케이스 추가 후 `7 passed`
- 남은 할 일:
  - Jetson에서 실제 마이크 장치 연결 상태로 `python3 -m jetson.core.coordinator` 실주행 검증
  - executor 실연동(arm/bhl) 시 현재 mock route 출력을 실제 호출로 치환

- 한 줄 요약:
  - `groq_client.py`를 동적 스키마 프롬프트 + Cloud->Local->Offline fallback 구조로 정렬하고, `source`를 `stt` 기준으로 스키마/코드/테스트 일치시킴.
- 실행한 검증 명령:
  - `python -m pytest tests/3_interface/test_groq_api.py -q`
- 수정한 파일:
  - `jetson/cloud/groq_client.py`
  - `configs/schemas/action.schema.json`
  - `tests/3_interface/test_groq_api.py`
  - `docs/07_non_ros2_pipeline_master_plan.md`
  - `WORKLOG.md`
- 결과:
  - 인터페이스 테스트 `5 passed`.
  - action schema `source` enum에 `stt` 포함.
  - action JSON 생성 시 `source=stt`로 통일.
  - Cloud 실패 시 LocalLLM 시도, 이후 Offline 안전 fallback 동작.
- 남은 할 일 (Jetson TARGET):
  - 실 API 키/네트워크로 Cloud 경로 검증.
  - LocalLLMClient 실제 구현 전까지 Offline fallback reason 로그 확인.
  - STT 실입력(chat/move/pick_place/stop) 4케이스 변환 결과를 WORKLOG에 추가.

### 2026-04-22 (Jetson pull 후 바로 실행할 다음 단계)

- 목적:
  - Jetson에서 `git pull` 직후 바로 이어서 검증하고, 결과를 다시 WORKLOG에 남길 수 있게 순서를 고정한다.
- 다음 실행 순서:
  1. `git pull origin ε1`
  2. `python3 -m pip install -U pip`
  3. `python3 -m pip install groq jsonschema faster-whisper pytest`
  4. `python3 -m pytest tests/3_interface/test_groq_api.py -q`
  5. `GROQ_API_KEY` 설정 후 STT 텍스트 4케이스(`chat`, `move`, `pick_place`, `stop`)를 `build_action_json_from_stt()`로 확인
  6. 결과 JSON에서 아래 항목 확인
     - `intent`
     - `gait_cmd`
     - `requires_smolvla`
     - `requires_bhl`
     - `source == stt`
     - `fallback_policy`
  7. Cloud 실패 상황도 1회 확인
     - 키 제거 또는 네트워크 차단
     - LocalLLM 실패 시 offline fallback 반환 확인
  8. 검증 결과를 WORKLOG에 추가
  9. 이상 없으면 다음 단계(Phase 4 coordinator)로 진행
- Jetson에서 기록할 핵심 결과:
  - 실행한 명령
  - 통과/실패 여부
  - 실패 시 에러 메시지
  - 실제 반환 JSON 예시 1개 이상
  - 다음 환경에서 할 일

### 2026-04-22 (실행 단계 검증 결과)

- 한 줄 요약:
  - WORKLOG 마지막 단계들을 실제 환경에서 순차 실행했고, Groq 인터페이스 테스트와 STT 4케이스 매핑, 오프라인 fallback까지 확인했다.
- 실행한 검증 명령:
  - `git pull origin ε1`
  - `python3 -m pip install -U pip`
  - `python3 -m pip install groq jsonschema faster-whisper pytest`
  - `python3 -m pip install -U pytest`
  - `python3 -m pytest tests/3_interface/test_groq_api.py -q`
  - Python one-liner로 `build_action_json_from_stt()` 4케이스 검증
  - `env -u GROQ_API_KEY` 상태로 오프라인 fallback 1회 검증
- 수정한 파일:
  - `WORKLOG.md`
- 결과:
  - `git pull origin ε1`: 이미 업데이트 상태
  - 기존 pytest 6.2.5는 anyio 플러그인과 충돌해 초기 실패했으나, pytest 9.0.3으로 업그레이드 후 `tests/3_interface/test_groq_api.py`가 `5 passed`
  - STT 4케이스 결과:
    - `chat` -> `intent=chat`, `gait_cmd=none`, `requires_smolvla=False`, `requires_bhl=False`, `source=stt`, `fallback_policy=none`
    - `move` -> `intent=move`, `gait_cmd=walk_forward`, `requires_smolvla=False`, `requires_bhl=True`, `source=stt`, `fallback_policy=none`
    - `pick_place` -> `intent=pick_place`, `gait_cmd=none`, `requires_smolvla=True`, `requires_bhl=False`, `source=stt`, `fallback_policy=none`
    - `stop` -> `intent=stop`, `gait_cmd=stop`, `requires_smolvla=False`, `requires_bhl=True`, `source=stt`, `fallback_policy=none`
  - 오프라인 fallback 확인:
    - `GROQ_API_KEY` 제거 시 `intent=unknown`, `source=stt`, `fallback_policy=cloud_fail_local_not_ready`, `network_online=False`
- 남은 할 일:
  - 실제 `GROQ_API_KEY`/네트워크 조합에서 재검증이 필요하면 Jetson 환경에서 1회 더 확인
  - 다음 단계로 Phase 4 coordinator 진입 전 현재 변경분(`data/episodes/*`, 기존 작업 내역) 커밋 여부를 정리

### 2026-04-22 (Phase 4 coordinator 실동작 루프 + standby intent 반영)

- 한 줄 요약:
  - mock 입력 대신 실제 마이크->Whisper->Groq 경로를 표준으로 사용하는 `coordinator.py`를 구현하고, 대화 종료용 `standby` intent 및 자동 대기 복귀 흐름을 추가했다.
- 실행한 검증 명령:
  - `python3 -m pytest tests/3_interface/test_groq_api.py -q`
  - `python3 -m jetson.core.coordinator --help`
- 수정한 파일:
  - `jetson/core/coordinator.py`
  - `jetson/cloud/groq_client.py`
  - `configs/schemas/action.schema.json`
  - `jetson/core/brain/llm_pipeline.py`
  - `tests/3_interface/test_groq_api.py`
  - `WORKLOG.md`
- 결과:
  - `coordinator.py`에서 실마이크 녹음(`record_to_wav`) -> Whisper STT(`transcribe_wav`) -> 실 Groq 호출(`build_action_json_from_stt`) 루프 구현
  - 실행 전 `GROQ_API_KEY`/네트워크 체크 및 실제 Groq API probe 추가
  - 요청대로 터미널에 `INPUT_JSON`/`ACTION_JSON` 출력 추가
  - chat 의도는 루프 유지, 대화 종료 키워드 감지 시 `intent=standby`로 전환
  - `pick_place`/`move`/`stop` 이후 자동 `ACTION_JSON (AUTO-STANDBY)` 출력 및 대기 모드 복귀
  - action schema의 `intent` enum에 `standby` 추가
  - 인터페이스 테스트에 conversation-end -> standby 케이스 추가 후 `7 passed`
- 남은 할 일:
  - Jetson에서 실제 마이크 장치 연결 상태로 `python3 -m jetson.core.coordinator` 실주행 검증
  - executor 실연동(arm/bhl) 시 현재 mock route 출력을 실제 호출로 치환

### 2026-04-22 (Phase 4 coordinator Jetson 테스트 완료)

- 한 줄 요약:
  - 대화 종료 하드코딩 제거 + Groq 프롬프트 기반 분류 + intent별 키워드 슬롯 추가
  - 마이크 녹음 시작 시점 표시 강화
  - 실제 음성으로 전체 파이프라인 테스트
- 실행한 검증 명령:
  - `python3 -m pytest tests/3_interface/test_groq_api.py -q`
  - `python3 -m jetson.core.coordinator`
- 수정한 파일:
  - `jetson/core/coordinator.py`
  - `jetson/cloud/groq_client.py`
  - `WORKLOG.md`
- 결과:
  - 하드코딩 종료 키워드 로직을 제거
  - LLM이 프롬프트 규칙으로 대화 종료를 판단해 standby로 분류
  - 요청대로 intent별 키워드 강제 분류용 빈 템플릿 칸을 프롬프트에 추가
  - 녹음 타이밍 알 수 있게 START/STOP 메시지를 추가
  - 실제 테스트 결과 정상 작동

### 2026-04-23 (chat lip-sync 연결 정리)

- 한 줄 요약:
  - `coordinator.py`의 `intent == chat` 경로에 TTS/입술동기화 루프를 연결하고, 스피커 부재 시에도 duration만큼 서보가 움직이도록 fallback 구조를 정리했다.
- 수정한 파일:
  - `jetson/core/coordinator.py`
  - `jetson/expression/speaker.py`
  - `jetson/expression/mouth_servo.py`
  - `WORKLOG.md`
- 결과:
  - chat intent 발생 시 `reply_text`를 받아 음성 파일을 생성하고 재생하는 동안 Pin 33의 MG90S 서보가 동작하도록 연결됨
  - 오디오 재생 실패 시에도 `time.sleep(duration)` fallback으로 입술 동작 시간 보장
  - chat 응답이 끝나면 기존 흐름대로 대기 모드로 복귀함
- 남은 할 일:
  - Jetson Ubuntu 실환경에서 실제 마이크/STT/LLM/chat lip-sync smoke test 수행
  - 테스트 결과와 로그를 이 파일에 추가한 뒤 `git push` 진행

### 2026-04-23 (push 완료)

- 커밋 해시:
  - `3653953` (`Add chat lip-sync speaker flow`)
- 원격 반영:
  - `origin/ε1` 푸시 완료
- 비고:
  - 현재 코드는 chat intent에서 TTS 생성 -> 오디오 재생 -> MG90S Pin 33 서보 lipsync -> 대기 모드 복귀 흐름으로 연결됨
  - 스피커 부재 시에도 playback 실패를 잡아서 duration만큼 sleep fallback이 동작함

### 2026-04-23 (Jetson 테스트 완료)

- mouth_servo.py가 PMW를 직접 생성하는 것이 아니라 High/Low로 출력하도록 되어 있어 Jetson에서 지속적으로 오류 발생
  - check_mouth_servo.py에서 했듯이 PMW 직접 생성으로 코드 수정

- 테스트 결과 성공. 정상적으로 작동함.

### 2026-04-23 (all-intent reply 음성+입술동기화 확장)

- 한 줄 요약:
  - chat 전용이던 speaker/lipsync 호출을 모든 intent 공통으로 확장해서, `reply_text`가 있으면 항상 먼저 말하고(입술동기화), non-chat 작업 후에는 standby 안내 멘트도 다시 말하도록 정리함.
- 수정한 파일:
  - `jetson/core/coordinator.py`
- 결과:
  - 공통 helper `_speak_reply_if_any()` 추가
  - 모든 `action_json` 처리 직후 `before_<intent>` 단계에서 reply 출력
  - `pick_place`/`move`/`stop` 등 non-chat intent는 executor route 수행 후, auto-standby action의 reply를 `after_<intent>` 단계에서 추가 출력
  - `chat` intent는 reply 출력 후 기존처럼 chat loop 유지
- 남은 할 일:
  - Jetson 실환경에서 시나리오 검증
    - 예: "컵 집어줘" -> 사전 안내 멘트(lipsync) -> executor route -> 완료 멘트(lipsync) -> standby 복귀
  - 커밋/푸시는 사용자 직접 수행

### 2026-04-23 (wake word 자동 트리거 전환)

- 한 줄 요약:
  - `coordinator.py`의 `input()` 블로킹을 제거하고, `openwakeword` 기반 wake word 대기 루프로 바꾸었으며, 감지 후 마이크를 닫고 0.5초 바톤 터치 지연을 준 뒤 STT/LLM 파이프라인으로 넘어가게 정리했다.
- 수정한 파일:
  - `jetson/expression/wake_word.py`
  - `jetson/core/coordinator.py`
  - `jetson/expression/mouth_servo.py`
  - `WORKLOG.md`
- 결과:
  - Plan A: ALSA `plughw` + 16kHz 요청으로 OS 리샘플링 우선 시도
  - Plan B: 실패 시 44.1kHz로 열고 `audioop` 또는 `numpy`로 16kHz 다운샘플링
  - wake word 감지 직후 오디오 스트림을 즉시 닫고 `time.sleep(0.5)` 후 반환하도록 구현
  - coordinator 최상단 실행 블록에 `KeyboardInterrupt` + `finally` 정리 경로 추가
  - 종료 시 wake word 스트림과 GPIO cleanup을 보장하도록 정리함
- 남은 할 일:
  - Jetson Ubuntu 실환경에서 wake word 실제 감지/오인식/복귀 동작 smoke test
  - 필요 시 wake word 모델명/threshold/device keyword를 환경변수로 조정

### 2026-04-23 (wake word 모델 재설정 + chat loop 정리)


- 한 줄 요약:
  - OpenWakeWord의 기본 모델만 지원 가능 (커스텀 "hey hylion" 불가) -> "hey google"로 변경
  - Chat loop 중 intent=standby면 바로 대기모드 복귀, non-chat 작업 후만 auto-standby 발행으로 정리
  - 코드 중복(PROJECT_ROOT) 제거 및 가독성 개선
- 수정한 파일:
  - `.env`: HYLION_WAKEWORD_MODEL을 "hey hylion" -> "hey google"로 변경
  - `jetson/core/coordinator.py`:
    - PROJECT_ROOT 중복 정의 제거 + import 정리
    - standby intent 처리 분기 추가 (LLM 분류된 standby면 바로 탈출)
    - auto-standby 발행 로직만 non-chat 경로에 남김
    - 중복 "Waiting for wake word..." 제거
- Wake word 상황 설명:
  - OpenWakeWord는 사전 학습된 모델만 사용 가능 (hey google, hey mycroft, hey siri, alexa, ok google 등)
  - "hey hylion" 커스텀 모델을 사용하려면: OpenWakeWord 문서 참고해 모델 학습 -> .pt 파일 생성 -> 경로를 .env에 지정 필요
  - 현재는 "hey google"으로 설정해 바로 테스트 가능
- Chat loop 동작:
  - intent == "chat": 루프 유지 (마이크 재대기)
  - intent == "standby": 바로 chat mode 탈출, wake word 대기 복귀
  - 기타 intent (pick_place, move, stop 등): executor route 실행 -> auto-standby 발행 -> 탈출
- 남은 할 일:
  - Jetson에서 `python3 -m jetson.core.coordinator` 실행 후 "hey google" 감지 테스트
  - Chat loop에서 standby 분기 동작 확인

### 2026-04-23 (custom Hey_Hyleon ONNX 연동)

- 한 줄 요약:
  - OpenWakeWord를 기본 내장 키워드가 아닌 커스텀 ONNX 모델(`Hey_Hyleon.onnx`) 경로 로드 방식으로 전환하고, 민감도 threshold를 `WAKE_WORD_THRESHOLD` 환경 변수로 제어 가능하게 반영함.
- 수정한 파일:
  - `jetson/expression/wake_word.py`
  - `jetson/core/coordinator.py`
  - `WORKLOG.md`
- 결과:
  - 모델 경로 우선순위: `WAKE_WORD_MODEL_PATH` -> `HYLION_WAKEWORD_MODEL` -> 기본값(`checkpoints/wakeword/Hey_Hyleon.onnx`)
  - 모델 파일이 없으면 즉시 명확한 에러 메시지로 실패하도록 보호 로직 추가
  - `WAKE_WORD_THRESHOLD`(기본 0.5) 환경변수로 민감도 실시간 조절 가능
  - custom ONNX 사용에 맞춰 wakeword inference 기본 프레임워크를 `onnx`로 설정
  - Plan A(16k ALSA plughw) -> Plan B(44.1k + Python resample) 로직 유지
  - wake word 감지 후 stream close + `time.sleep(0.5)` 바톤 터치 로직 유지
  - coordinator 종료 시 `wakeword_listener.close()`와 `cleanup_gpio()`를 각각 try/except로 보호해 finally cleanup 안정성 보강
- 확인 사항:
  - 모델 파일 존재 확인: `checkpoints/wakeword/Hey_Hyleon.onnx`
- 남은 할 일:
  - Jetson에서 `WAKE_WORD_MODEL_PATH` 미설정 상태 기본 경로 로드 확인
  - `WAKE_WORD_THRESHOLD` 값(예: 0.35/0.5/0.7) 별 오인식/미인식 trade-off 측정

### 2026-04-23 (auto-standby 직후 즉시 재트리거 수정)

- 한 줄 요약:
  - 작업 완료 후 auto-standby에서 wake word가 너무 빨리 다시 열려 잔향/마지막 발화에 반응하던 문제를 non-chat 경로에만 짧은 cooldown으로 해결함.
- 수정한 파일:
  - `jetson/core/coordinator.py`
  - `WORKLOG.md`
- 결과:
  - `HYLION_WAKEWORD_AUTO_STANDBY_COOLDOWN_SEC` 환경변수 추가 (기본값 `1.5`초)
  - `intent == "standby"` 경로는 그대로 즉시 wake-word 대기로 복귀
  - `pick_place` / `move` / `stop` 등 non-chat 작업 후 auto-standby를 말한 뒤에만 cooldown을 적용하고 재무장함
  - coordinator 종료 시 `wakeword_listener.close()`와 `cleanup_gpio()` cleanup 로직은 그대로 안전하게 유지됨
- 원인 설명:
  - 작업 완료 멘트가 끝난 직후 바로 wake-word listener가 재가동되면서, 마지막 음성/echo/마이크 바닥잡음이 wake trigger로 다시 잡히는 현상
- 남은 할 일:
  - Jetson에서 auto-standby 후 실제 재트리거 여부 확인
  - 필요 시 `HYLION_WAKEWORD_AUTO_STANDBY_COOLDOWN_SEC` 값을 1.0~2.5초 범위로 조정

### 2026-04-23 (chat->standby 재트리거 역전 이슈 수정)

- 한 줄 요약:
  - auto-standby는 안정적이지만 chat에서 standby로 종료될 때만 키워드 없이 재기동되던 문제를, chat-standby 전용 cooldown + wake model state reset으로 보정함.
- 수정한 파일:
  - `jetson/core/coordinator.py`
  - `jetson/expression/wake_word.py`
  - `.env`
  - `WORKLOG.md`
- 결과:
  - `HYLION_WAKEWORD_CHAT_STANDBY_COOLDOWN_SEC`(기본 1.2s) 추가
  - `intent == "standby"` 경로에서 wakeword 재무장 전에 chat-standby cooldown 적용
  - wakeword listener 재진입 시 `openwakeword` 모델의 내부 상태를 가능한 경우 `reset()`으로 초기화
  - `.env`를 custom wakeword 기준으로 정렬
    - `WAKE_WORD_MODEL_PATH=checkpoints/wakeword/Hey_Hyleon.onnx`
    - `WAKE_WORD_THRESHOLD=0.5`
    - `HYLION_WAKEWORD_CHAT_STANDBY_COOLDOWN_SEC=1.2`
    - `HYLION_WAKEWORD_AUTO_STANDBY_COOLDOWN_SEC=1.5`
- 원인 설명:
  - chat 종료 발화 직후 바로 listener를 재무장하면, 잔향/노이즈 + 모델의 temporal state 영향으로 early trigger가 발생할 수 있음
- 남은 할 일:
  - Jetson 실환경에서 chat 종료("이제 대기해") 후 키워드 없이 재트리거되는지 재확인
  - 필요 시 chat-standby cooldown을 1.2 -> 1.6초로 상향

### 2026-04-23 (공유 가능한 runtime env로 전환)

- 한 줄 요약:
  - 비민감 wakeword 설정을 `.env`에서 추적 가능한 `configs/runtime.env`로 이동해 push/pull 동기화 가능하게 정리함.
- 수정한 파일:
  - `configs/runtime.env` (신규)
  - `jetson/core/coordinator.py`
  - `.env`
  - `WORKLOG.md`
- 결과:
  - `configs/runtime.env`에 공유 설정 저장
    - `WAKE_WORD_MODEL_PATH`
    - `WAKE_WORD_THRESHOLD`
    - `HYLION_WAKEWORD_CHAT_STANDBY_COOLDOWN_SEC`
    - `HYLION_WAKEWORD_AUTO_STANDBY_COOLDOWN_SEC`
  - coordinator 환경 로드 순서 정리
    1) `configs/runtime.env` (git 추적, 공통값)
    2) `.env` (로컬 override, 선택)
  - env 로드 이후에 cooldown 상수를 계산하도록 순서 수정하여 값 반영 누락 가능성 제거
  - `.env`는 로컬 override 안내 주석만 남김
- 남은 할 일:
  - Jetson에서 pull 후 `.env` 없이도 동일 값으로 동작하는지 1회 확인

### 2026-04-23 (runtime env 사용 철회, 코드 파라미터로 복귀)

- 한 줄 요약:
  - 사용자 요청에 따라 wakeword/coordinator 런타임 설정을 다시 코드 내부 parameters 섹션으로 고정하고, env 기반 공유 설정 구조를 철회함.
- 수정한 파일:
  - `jetson/core/coordinator.py`
  - `jetson/expression/wake_word.py`
  - `.env`
  - `WORKLOG.md`
- 결과:
  - `coordinator.py`에서 `configs/runtime.env`/`.env` 자동 로드 로직 제거
  - cooldown 파라미터를 코드 상수로 복귀
    - `AUTO_STANDBY_COOLDOWN_SEC = 1.5`
    - `CHAT_STANDBY_COOLDOWN_SEC = 1.2`
  - `wake_word.py`의 모델/threshold/오디오 fallback 파라미터를 env 읽기 대신 코드 상수로 복귀
  - `configs/runtime.env` 파일 제거
  - `.env`는 로컬 비밀값(예: API key) 용도 안내만 유지
- 남은 할 일:
  - 필요시 이후 튜닝은 코드 parameters 값 직접 수정 방식으로 진행

### 2026-04-23 (runtime tuning table 문서화 + reply audio 저장 위치 정리)

- 한 줄 요약:
  - wakeword/STT/coordinator 전체 튜닝 파라미터를 단일 표로 문서화하고, reply용 음성 파일 저장 위치와 보존 정책을 코드 기준으로 명확히 정리함.
- 수정한 파일:
  - `docs/09_runtime_tuning_table.md` (신규)
  - `WORKLOG.md`
- 결과:
  - wakeword, coordinator, STT 튜닝 항목(현재값/권장범위/효과/부작용/우선순위) 표 추가
  - 현장 테스트용 quick matrix 추가
  - reply audio 저장 위치 정리
    - Ubuntu/Jetson 기준 `/tmp/hylion_tts`
    - 파일명 `reply_<timestamp>.mp3` 또는 fallback `reply_<timestamp>.wav`
  - 현재 구현은 재생 후 자동 삭제를 하지 않음을 문서에 명시
- 남은 할 일:
  - 필요 시 `speaker.py`에 재생 후 자동 삭제 정책 추가 검토

### 2026-04-23 (speaker 실음성 TTS + data/reply 저장 경로 전환)

- 한 줄 요약:
  - `speaker.py`의 무음 fallback 생성을 제거하고, gTTS(ko)로 실제 한국어 MP3를 생성해 `data/reply/reply.mp3`로 저장/재생하도록 교체함.
- 수정한 파일:
  - `jetson/expression/speaker.py`
  - `WORKLOG.md`
- 결과:
  - `synthesize_reply_audio()`:
    - `gTTS(text=reply_text, lang="ko")`로 실제 음성 생성
    - 저장 전 `os.makedirs(save_dir, exist_ok=True)` 수행
    - 저장 경로를 프로젝트 내부 `data/reply/reply.mp3`로 고정
  - `get_audio_duration_sec()`:
    - `mutagen.mp3.MP3`로 정확한 재생 길이(초) 추출
  - `play_audio_blocking()`:
    - Linux `mpg123 -q <file>` 기반 재생으로 정리
  - `speak_with_lipsync()`:
    - 오디오 재생 실패 시 duration 기반 `time.sleep()` fallback 유지
    - 동일 duration을 서보 스레드에 전달해 lipsync 시간 정합 유지
- 남은 할 일:
  - Jetson 런타임에 `gTTS`, `mutagen`, `mpg123` 설치/가용성 확인

### 2026-04-23 (온라인/오프라인 하이브리드 라우팅 리팩토링)

- 한 줄 요약:
  - wake word 직후 네트워크 상태를 확인해 online이면 Groq + ClovaTTS, offline이면 LocalLLM 스텁 + PiperTTS 스텁으로 분기하는 하이브리드 구조를 추가함.
- 수정한 파일:
  - `jetson/core/brain/network_probe.py`
  - `jetson/core/coordinator.py`
  - `jetson/expression/speaker.py`
  - `docs/09_runtime_tuning_table.md`
  - `WORKLOG.md`
- 결과:
  - `is_online()`를 가벼운 socket reachability probe로 정리
    - 8.8.8.8:53
    - 1.1.1.1:53
    - www.google.com:443
    - www.naver.com:443
  - `speaker.py`
    - 온라인: `ClovaTTS`
    - 오프라인: `PiperTTS` 스텁
    - Clova 기본 speaker 파라미터를 `ara`로 고정
    - NAVER API 인증키는 `os.getenv("NAVER_CLIENT_ID")`, `os.getenv("NAVER_CLIENT_SECRET")`로만 읽음
    - mp3 생성 후 `mutagen`으로 duration 추출, `mpg123` 재생, 실패 시 `time.sleep(duration)` fallback 유지
    - reply 오디오 저장 위치를 `Hylion/data/reply/`로 유지하면서 timestamp 파일로 누적 저장
  - `coordinator.py`
    - wake word 감지 직후 네트워크 상태를 확인하고 turn 단위로 backend를 선택
    - online이면 `GroqClient` + `ClovaTTS`
    - offline이면 `LocalLLM` 스텁 + `PiperTTS` 스텁
    - online 준비 실패 시 안전하게 offline stub으로 fallback
- 남은 할 일:
  - Jetson에서 NAVER API 키 설정 후 ClovaTTS 실제 발화 테스트
  - 오프라인 스텁은 이후 Piper TTS 실제 구현 시 교체

### 2026-04-24 (07 master plan 문서 최신 진행상태 동기화)

- 한 줄 요약:
  - `WORKLOG.md` 최신 진행 내역(웨이크워드 안정화, 하이브리드 라우팅, Clova/Piper, TTS+lipsync 반영)을 `docs/07_non_ros2_pipeline_master_plan.md`에 반영해 체크리스트/스냅샷/시나리오를 최신화함.
- 수정한 파일:
  - `docs/07_non_ros2_pipeline_master_plan.md`
  - `WORKLOG.md`
- 결과:
  - 기준일/상태를 2026-04-24 기준으로 업데이트
  - Phase 4에 wakeword 안정화 + online/offline 분기 완료 항목 추가
  - Phase 5에서 TTS/speaker adapter 항목을 완료로 갱신
  - 현재 경계 조건을 "Clova TARGET 검증 필요 / Piper-LocalLLM 스텁" 상태로 명확화
  - 구조도와 데이터 경로 설명에 wakeword/network_probe/TTS+lipsync 단계 반영
  - 장애 시나리오를 네트워크/Cloud 실패를 함께 다루는 형태로 갱신
- 남은 할 일:
  - Jetson에서 Clova 실키 기반 발화 검증 결과를 07/WORKLOG에 추가
  - Piper TTS 및 LocalLLM 실구현 시 해당 체크리스트 항목 업데이트

### 2026-05-04 (STT GPU 가속 — faster-whisper → openai-whisper 백엔드 교체)

- 한 줄 요약:
  - Jetson Orin Nano Super 8GB에서 STT를 GPU(cuDNN 9 + CUDA 12.6)로 돌리기 위해 백엔드를 `faster-whisper`(CTranslate2 의존, aarch64 CUDA wheel 부재)에서 `openai-whisper`(PyTorch 기반, smolvla 문서가 검증한 NVIDIA JP 6.0 wheel 재사용)로 교체. `jetson/expression/.venv` 신규 venv 구축.
- 수정한 파일:
  - `jetson/expression/stt_whisper.py`
  - `tests/4_unit/test_stt_whisper.py`
  - `WORKLOG.md`
  - (시스템) `~/.bashrc` — ROS2 source 두 줄 삭제 (앞으로도 ROS2 미사용)
- 결과:
  - venv 위치 `jetson/expression/.venv` (virtualenv 21.2.4 사용 — `python3-venv` apt 미설치 회피)
  - 설치 패키지:
    - `torch 2.5.0a0+872d972e41.nv24.08` (NVIDIA JP 6.0 wheel — `developer.download.nvidia.com/compute/redist/jp/v61/pytorch/`)
    - `nvidia-cusparselt-cu12 0.8.1` (시스템 미등록 → venv `activate`에 LD_LIBRARY_PATH fallback 추가)
    - `numpy 1.26.4` (`<2` 고정 — torch 2.5.0a0 ABI)
    - `openai-whisper 20250625`, `tiktoken`, `numba`, `pytest`
  - 시스템 의존성(libopenblas/openmpi/omp)은 이미 설치돼있어 sudo apt 단계 스킵
  - smolvla `setup_env.sh` 절차를 그대로 따라가 환경 일관성 유지 (lerobot 부분만 제외)
- 코드 변경 요지:
  - `stt_whisper.py`
    - `from faster_whisper import WhisperModel` → `import whisper`
    - 외부 API (`STTResult`, `transcribe_wav`, `build_input_event`) 시그니처 그대로 유지 → `coordinator.py` 변경 불필요
    - `compute_type="float16"` → openai-whisper의 `fp16=True` 매핑, cpu fallback도 동일 흐름
    - `vad_filter` 인자 제거 (openai-whisper 내장 no-speech 검출 사용)
    - 캐시 키에서 compute_type 분리, device만 캐시 키로 사용
  - `test_stt_whisper.py`
    - mock 대상을 `faster_whisper.WhisperModel` → `whisper.load_model`로 교체
    - segments+info dict → `{"text": ..., "language": ...}` dict 형태로 fake 응답 변경
    - 단위 테스트 2/2 PASSED (PYTHONPATH ROS2 오염 제거 후)
- 검증:
  - `import torch; torch.cuda.is_available()` → True, cuDNN 90300, CUDA 텐서 연산 OK
  - `whisper.load_model('base', device='cuda')` 로딩 OK
  - 실제 샘플 `data/episodes/live_20260422_203303.wav` → "안녕 넌 누구야?" (ko), 4.79초 (모델 로딩 포함, GPU 메모리 439MB)
  - 단위 테스트 `tests/4_unit/test_stt_whisper.py` 2 passed
- 결정 기록:
  - 다른 후보(D1 ctranslate2 소스 빌드 / D3 whisper.cpp / D4 CPU 유지)를 두고, **smolvla 문서와 동일 환경 컨벤션 유지**가 가장 중요하다는 사용자 판단으로 D2(openai-whisper) 선택
  - 트레이드오프: 추론 속도/메모리 약간 손해, 환경 재현성·다른 모델(smolVLA 등)과의 venv 통합 가능성 확보
  - smolVLA 동시 적재 시 메모리 전략은 smolVLA 모델 확정 후 측정해서 다시 판단 (현재는 둘 다 상주가 가장 빠른 옵션)
- 남은 할 일:
  - smolVLA 모델 확정 후 메모리 budget 재측정, 필요 시 패턴 A/C로 전환 (서비스 추상화는 그때 도입)
  - `data/reply/` root 소유 디렉터리 정리 (사용자 권한으로 이전)
  - 미사용 패키지(`faster-whisper`, `ctranslate2`, `av`, `onnxruntime`) 정리 검토 (~300MB)
  - `scripts/deploy_jetson.sh`가 venv activate 가정하도록 정비 검토

### 2026-05-05 (프로젝트 전체 흐름도 문서화 + 코디네이터 정리)

- 한 줄 요약:
  - 현재 동작 기준으로 프로젝트 전체 모듈/파일 구조와 런타임 데이터 흐름을 도식화한 문서 추가. 동시에 코디네이터의 STT warm-up과 wake_word listener를 단일 경로로 단순화한 변경분(이전 세션 잔여)을 같이 정리해 push.
- 수정/추가 파일:
  - `docs/09_project_flow_overview.md` (신규) — ASCII 흐름도 + 모듈 트리 + Mermaid flowchart, 빈 스텁 영역(`perception`, `arm`, `safety`, `scenarios`, `state_machine/fsm.py`, `nuc/bhl`, `comm/{nuc,orin}`, `comm/mock_bridge.py`)을 ❌ 표시로 명시
  - `jetson/core/coordinator.py` — 시작 시 `warm_up_stt()` 호출 추가, 기본 whisper 모델 `base` → `small`, 기동 배너 정리, `WakeWordActivation.source` 출력 제거
  - `jetson/expression/stt_whisper.py` — `warm_up()` 공개 함수 추가, `DEFAULT_MODEL_SIZE` `base` → `small`
  - `jetson/expression/wake_word.py` — Plan A/Plan B 이중 디바이스 경로 제거, 단일 device_keyword/sample_rate로 단순화 (44.1kHz 캡처 → 16kHz Python 리샘플 단일 경로)
  - `jetson/expression/requirements.txt` (신규) — venv 재현용 의존성 명세 (PyTorch JP6.0 wheel + openai-whisper + openwakeword + Jetson.GPIO 등)
  - `WORKLOG.md`
- 결과:
  - `coordinator.py main()` 진입 시 whisper small 모델을 즉시 GPU 로드 → 첫 발화 지연 제거
  - wake word 코드 라인 수 감소, 분기 로그도 한 줄로 정리
- 메모(저장소 위생):
  - `data/episodes/*.wav`, `data/reply/*.mp3`, root의 `Error`(0B 파일)은 이번 커밋에 포함하지 않음. `.gitignore` 의 `.mp3`/`.wav` 룰이 와일드카드(`*.mp3`/`*.wav`)가 빠져있어 untracked로 보이는 상태 — 다음 세션에서 gitignore 보강 필요.
- 다음 환경에서 할 일:
  - `.gitignore` 의 `.mp3`/`.wav` → `*.mp3`/`*.wav` 보강 + `data/episodes/`, `data/reply/`, root `Error` 처리 결정
  - whisper `small` 모델로 GPU/지연 측정 재확인 후 모델 사이즈 확정
  - SMOLVLA/BHL 라우팅(_route_action) 실제 구현 진입점 결정

### 2026-05-06 (하이브리드 online/offline 리팩터 — 설계 단계)

- 한 줄 요약:
  - 현재 wake(offline) → STT(offline whisper) → LLM(online Groq) 의 환경 혼합 구조를, 웨이크워드 직후 `is_online()` 1회 측정으로 STT/LLM/TTS 백엔드를 일괄 선택하는 깨끗한 양 갈래 구조로 재설계. 코드 구현 전 설계 문서 + 결정사항을 먼저 정리.
- 수정/추가 파일:
  - `docs/10_hybrid_online_offline_refactor_plan.md` (신규 327줄 → +1줄, 무료 티어 정보 추가)
  - `.gitignore` — `.mp3`/`.wav` → `*.mp3`/`*.wav` 와일드카드 보정 + `data/sessions/` → `data/sessions/*`
  - `WORKLOG.md`
- 주요 결정사항:
  - **모듈 구조**: `jetson/core/stt/` 와 `jetson/core/llm/` 패키지 신설 (사용자 요청대로 `core` 안에 위치). 각 패키지는 `base.py`(Protocol+dataclass), `factory.py`, 백엔드별 1파일.
  - **온라인 STT**: Groq `whisper-large-v3-turbo` (속도 우선, 한국어 large-v3와 사실상 동일). 무료 티어로 충분 (20 RPM, 28.8K audio sec/day). LLM과 별도 버킷이라 같은 API 키로 둘 다 호출해도 안 겹침.
  - **오프라인 LLM**: Ollama + `exaone3.5:2.4b` Q4_K_M (~1.5GB, LG 한국어 native, 30-40 tok/s on Orin Nano). 엔드포인트는 Jetson 내부 `127.0.0.1:11434` 데몬, systemd로 부팅 자동기동.
  - **오프라인 TTS**: Coqui XTTS-v2 + 보유 중인 CLOVA child voice mp3 (`ndain_final_test.mp3` 등)를 voice cloning reference로 사용. 메모리 빠듯해서 LLM/TTS 순차 사용 패턴(ollama keep_alive=0) 검토 필요.
  - **online 측정 빈도**: outer 루프(웨이크워드 활성화) 직후 1회만. inner 채팅 루프에서는 재측정 X. 호출 실패 시 1회 즉석 재프로브 후 강등.
  - **warm-up 정책**: 부팅 시 `is_online()` 결과로 한쪽만 로드 (8GB 시스템에서 양쪽 적재 비현실적). 강등 시 lazy load.
- Jetson 환경 확인:
  - 모델: NVIDIA Jetson Orin Nano Engineering Reference Developer Kit Super
  - JetPack 6.x (R36 release), CUDA 12.6
  - RAM 7.4 GiB 공유 (현재 사용 2.6GB / 가용 4.5GB), 스왑 3.7 GiB
- 보유 자산 확인:
  - CLOVA voice mp3 8개 (root 위치) — 그 중 child voice (`ndain`/`nhajun`/`nara`/`ngaram`) 4개를 오프라인 TTS reference clip으로 활용 예정.
- 다음 환경에서 할 일 (구현 단계 진입):
  - 단계 1: `core/stt/`, `core/llm/`, `core/network.py` 디렉토리 골격 생성 (빈 껍데기 + Protocol)
  - 단계 2: 기존 `expression/stt_whisper.py` → `core/stt/local_whisper.py` 이전, `cloud/groq_client.py` 분해해서 `core/llm/{prompt,groq_llm}.py`로 분배 (기능 변화 0)
  - 단계 3: `coordinator.py` 평탄화 — `_build_turn_services` / inner-loop if online / `LocalLLM` 더미 클래스 제거, 백엔드 메서드 호출로 통일 (여전히 기능 변화 0)
  - 단계 4 이후: Groq Whisper 백엔드 신규 구현 → Ollama 백엔드 신규 구현 → graceful degradation → 오프라인 TTS

### 2026-05-06 (단계 1~3 — 백엔드 추상화 리팩터, 기능 변화 0)

- 한 줄 요약:
  - STT/LLM을 `core/stt/`, `core/llm/` 패키지로 분해하고 `STTBackend`/`LLMBackend` Protocol 도입. coordinator는 `_build_turn_services` 한 곳에서 백엔드를 고르고 inner 루프는 `stt_backend.transcribe()` / `llm_backend.build_action()` 한 줄씩으로 평탄화. 동작은 이전과 byte-identical.
- 실행한 검증 명령:
  - `python3 -m pytest tests/4_unit/test_stt_whisper.py tests/3_interface/test_groq_api.py -q` → 9 passed
  - `python3 -m pytest tests/4_unit tests/3_interface tests/5_integration tests/2_hw_connection -q` → 14 passed
  - `python3 -m jetson.core.coordinator --help` → 정상 출력
  - `python3 -c "from jetson.core.brain.network_probe import is_online; ..."` → shim OK
- 신규 파일:
  - `jetson/core/network.py` (network_probe 이전)
  - `jetson/core/stt/{__init__.py, base.py, local_whisper.py, factory.py}`
  - `jetson/core/llm/{__init__.py, base.py, prompt.py, groq_llm.py, offline_stub.py, factory.py}`
- 삭제 파일:
  - `jetson/expression/stt_whisper.py` (→ `core/stt/local_whisper.py` + `core/stt/base.py`)
  - `jetson/cloud/groq_client.py` (→ `core/llm/{prompt,groq_llm}.py`)
- 수정 파일:
  - `jetson/core/coordinator.py` — `LocalLLM` 더미 클래스 삭제, online/offline if 분기 제거, 백엔드 메서드 호출로 평탄화. `_build_turn_services` 시그니처에 `whisper_model_size`/`whisper_language` 추가
  - `jetson/core/brain/network_probe.py` — `core.network`로 re-export 하는 thin shim (legacy `brain_main.py` 보호용)
  - `tests/4_unit/test_stt_whisper.py` — import 경로를 `core.stt.local_whisper` + `core.stt.base`로 갱신
  - `tests/3_interface/test_groq_api.py` — import 경로를 `core.llm.groq_llm` + `core.llm.prompt`로 갱신
- 주요 인터페이스:
  - `STTBackend.transcribe(wav_path, *, language=None) -> STTResult`
  - `STTBackend.warm_up()`
  - `LLMBackend.build_action(stt_text, *, session_id, history, in_chat_mode) -> dict(ACTION_JSON)`
  - `LLMBackend.warm_up()`
  - 팩토리: `build_stt_backend(online, *, model_size, language)`, `build_llm_backend(online)`
- 현재 백엔드 매핑 (변경 무):
  - online → `LocalWhisperBackend` + `GroqLLMBackend` + Clova TTS  ※ 단계 4에서 STT만 GroqWhisper로 교체 예정
  - offline → `LocalWhisperBackend` + `OfflineStubLLMBackend` (기존 LocalLLM 클래스 동일 reply) + offline TTS
- 코드량 변화: 508줄 삭제 / 60줄 net 추가 (+ 신규 패키지 11파일은 untracked → commit 시 추가)
- 다음 환경에서 할 일:
  - **단계 4** — `core/stt/groq_whisper.py` 신규 구현 (Groq audio.transcriptions, `whisper-large-v3-turbo`), 팩토리에서 online=True 시 GroqWhisperBackend 반환하도록 교체. 한국어 인식률/지연 실측.

### 2026-05-06 (단계 4 — Groq Whisper online STT)

- 한 줄 요약:
  - online STT를 `whisper-large-v3-turbo`로 라이브. `GroqWhisperBackend` 신규 + 팩토리 분기 추가. 실 음성 4초 wav 한 개로 엔드투엔드 검증, 로컬 whisper(CUDA) 4.79s 대비 **0.63s**(약 7-8배 빠름) 확인.
- 실행한 검증 명령:
  - `python3 -m pytest tests/3_interface/test_groq_whisper.py tests/3_interface/test_groq_api.py tests/4_unit/test_stt_whisper.py -q` → 15 passed
  - `python3 -c "...GroqWhisperBackend().transcribe('data/episodes/live_20260422_203303.wav')..."` → 0.632s, "안녕 넌 누구야?" (ko)
  - `python3 -m jetson.core.coordinator --help` → 정상
- 신규 파일:
  - `jetson/core/stt/groq_whisper.py` — `GroqWhisperBackend(model='whisper-large-v3-turbo', language='ko', timeout_sec=30.0)`. Groq SDK `client.audio.transcriptions.create()` 호출, `(filename, bytes)` 튜플로 업로드, 결과의 `.text`만 추출
  - `tests/3_interface/test_groq_whisper.py` — fake Groq client으로 SDK 호출 인자 검증 + 팩토리 분기 검증 (6 tests)
- 수정 파일:
  - `jetson/core/stt/factory.py` — online=True → `GroqWhisperBackend`, online=False → `LocalWhisperBackend` 으로 분기
  - `WORKLOG.md`
- 측정값 (Jetson Orin Nano Super 8GB, JP6.x, GROQ_API_KEY 설정):
  - `warm_up()`: 0.530s (SDK 임포트 + Groq() 인스턴스 생성)
  - `transcribe()` first call: 0.632s (4초 WAV, 한국어, network round-trip 포함)
  - 전사 결과 정확도: 사람이 들은 발화와 동일
- 결정/관찰:
  - Groq SDK 1.2.0이 venv에 이미 있어 추가 설치 불필요
  - STT와 LLM은 같은 `GROQ_API_KEY` 공유, 모델별 별도 rate limit 버킷 → 한도 안 겹침
  - 무료 티어 한도(20 RPM, 28.8K audio sec/day)로 일상 사용 충분, 실측 호출당 ~5 audio sec 소모
- 남은 할 일:
  - **단계 5** — Ollama + `exaone3.5:2.4b` 백엔드 신규 (`core/llm/ollama_llm.py`), 팩토리 offline=True → OllamaLLMBackend 교체. JSON 모드 schema 통과 검증.
  - 단계 6 — coordinator inner-loop graceful degradation (네트워크 예외 시 즉석 재프로브 + 강등)
  - 단계 7 — 오프라인 TTS (XTTS-v2 + CLOVA child clip)

### 2026-05-06 (단계 5 — Ollama + EXAONE 3.5 2.4B 오프라인 LLM 라이브)

- 한 줄 요약:
  - offline 경로의 stub LLM을 실제 Ollama + `exaone3.5:2.4b`로 교체. 슬림 prompt + intent 기반 backfill + cross-field policy로 한국어 schema-conformant ACTION_JSON 안정 생성. 6/6 케이스 성공, 평균 ~9.7s/turn (워밍 후 ~8.8s).
- 실행한 검증 명령:
  - `curl -fsSL https://ollama.com/install.sh | sh` (사용자 별도 터미널)
  - `sudo systemctl enable --now ollama`
  - `ollama pull exaone3.5:2.4b` (~1.6 GB Q4_K_M)
  - `python3 -m pytest tests/3_interface tests/4_unit tests/5_integration tests/2_hw_connection -q` → 27 passed
  - 엔드투엔드 6 케이스 (안녕/컵/이동/정지/standby/지식질문) → fallback 0건, 모두 정확 분류, 평균 9.69s
- 신규 파일:
  - `jetson/core/llm/ollama_llm.py` — `OllamaLLMBackend(model='exaone3.5:2.4b', host='http://127.0.0.1:11434', num_ctx=2048, num_predict=150)`, urllib HTTP /api/chat 호출, 슬림 system prompt 내장
  - `tests/3_interface/test_ollama_llm.py` — 7 tests (성공 path / 히스토리 / 요청 실패 / JSON 깨짐 / 메시지 누락 / 팩토리 분기)
- 수정 파일:
  - `jetson/core/llm/factory.py` — offline=True → `OllamaLLMBackend` (이전 stub 제거)
  - `jetson/core/llm/prompt.py`:
    - `_apply_conversation_policy` 확장 — standby뿐 아니라 pick_place/move/stop/chat/unknown 모두 cross-field 강제 정규화
    - `_backfill_required_defaults` 신규 — 모델이 boolean/enum 필드 빠뜨려도 intent 기반 기본값으로 schema 통과
  - `jetson/core/coordinator.py` — `_startup_warm_up()` 추가 (§F5 정책: online=Groq probe만, offline=local whisper + Ollama 모델 모두 미리 로드)
  - `WORKLOG.md`
- 삭제 파일:
  - `jetson/core/llm/offline_stub.py` — Ollama가 자체 fallback(`_offline_action_json`)을 가지므로 dead code
- 측정값 (Jetson Orin Nano Super 8GB, JP6.x, GPU 100%):
  - 모델 로드 (warm_up): 4.95s
  - 첫 콜드 turn: ~14s
  - 워밍 후 turn: 7.7~10.7s (한국어 1~2문장 응답, num_predict=150 캡)
  - 메모리: 2.7GB → 5.0GB (델타 +2.3GB; 가용 4.5GB → 2.2GB)
  - prompt eval: 76~542ms (445 토큰), 가장 큰 비용은 generation 18 tok/s
- 최적화 적용 비교:
  - full schema 주입 (1,038 prompt tokens) → 평균 21.0s/turn
  - **슬림 prompt (445 tokens) + num_predict=150** → 평균 9.7s/turn (**2.4배 빠름**)
- 남은 한계:
  - 8-10s/turn은 빠르진 않지만 graceful degradation 용도로 수용 가능
  - 더 줄이려면 (a) 더 작은 모델 (gemma2:2b, qwen2.5:1.5b) 한국어 평가 필요, (b) `format=json` 제약 생성 오버헤드 측정 — JSON 모드 끄고 직접 파싱 시도 등
- 다음 환경에서 할 일:
  - **단계 6** — coordinator inner-loop graceful degradation (transcribe/build_action 실패 시 즉석 `is_online()` 재프로브 + 백엔드 일시 강등 + 1회 재시도)
  - 단계 7 — 오프라인 TTS (XTTS-v2 + 보유 CLOVA `ndain` child clip을 voice cloning reference로 등록, 메모리 budget 실측)

### 2026-05-06 (단계 7 — 오프라인 TTS via MeloTTS daemon)

- 한 줄 요약:
  - 오프라인 한국어 TTS를 **MeloTTS 데몬 + HTTP 클라이언트** 패턴으로 추가. Hylion 메인 venv (torch 2.5)는 손 안 대고, 별도 venv (`.venv-melotts`, torch 2.8 + torchaudio 2.8 jetson-ai-lab)에 FastAPI 서버를 띄워 loopback HTTP로 통신. Ollama와 동일 패턴.
- 배경 — 시도했다가 막힌 옵션들:
  1. **XTTS-v2** — 동작은 했으나 한국어 voice cloning 품질 매우 낮음 (사용자 평가 "알아듣기 어려움"). 게다가 PyPI torchaudio가 NVIDIA Jetson torch와 ABI 충돌 (undefined symbol `_ZNK5torch8autograd4Node4nameEv`).
  2. **Piper KSS Korean** — pygoruut 비표준 phonemizer 사용으로 mainstream piper-tts 1.4.2가 못 읽음. 공식 한국어 voice는 piper 카탈로그에 0개 (espeak-ng 한국어 G2P 품질이 낮아 학습이 안 됨).
  3. **Kokoro v1.0** — 한국어 voice 부재.
  4. **MeloTTS** ⭐ 채택. 한국어 native 학습, RTF 0.22~0.27x, GPU 0.76 GB.
- 통합 패턴 결정 (옵션 B = daemon):
  - 옵션 A (메인 venv torch 2.8 업그레이드) 대신 옵션 B (daemon HTTP) 채택
  - 이유: smolvla(자체 venv torch 2.5) / NUC bhl(별도 머신) 등 미래 ML 컴포넌트도 모두 IPC 패턴 → **모든 ML 서비스 = 별도 데몬, 코디네이터는 가벼운 오케스트레이션 역할**로 통일
  - HTTP 오버헤드: 1-5ms (전체 응답의 0.1% 미만, 무시 가능)
- 신규 파일:
  - `services/tts_server/server.py` — FastAPI app, GET /health + POST /synthesize, 부팅 시 모델 로드 + warm-up (warm 후 모든 호출 ~1초 미만)
  - `services/tts_server/hylion-tts.service` — systemd unit
  - `services/tts_server/setup.sh` — 재현 가능 venv/모델 설치 스크립트
  - `services/tts_server/README.md` — 운영 문서 (manual launch, systemd, 오프라인 검증, 메모리 footprint, 미래 OpenVoice v2 확장 메모)
  - `services/tts_server/patches/melotts_korean_only.patch` — MeloTTS upstream에 적용할 Korean-only path 패치 (Japanese MeCab / Chinese 의존 import 제거)
  - `jetson/core/tts/__init__.py`
  - `jetson/core/tts/melotts_client.py` — `MeloTTSSpeaker` (HTTP 클라이언트, `expression/speaker.py:Speaker`와 동일한 `speak_with_lipsync()` 시그니처, WAV 재생은 `aplay`)
  - `jetson/expression/.venv-melotts/` (gitignore된 venv) — torch 2.8 + torchaudio 2.8 + coqui-tts deps + MeloTTS
  - `third_party/MeloTTS/` (gitignore) — clone + 패치 적용 상태
  - `data/tts_ref/ndain.wav` (gitignore) — 향후 OpenVoice v2 voice cloning reference clip
- 수정 파일:
  - `jetson/expression/speaker.py` — `build_tts_backend(is_online=False)` 분기 추가 → `MeloTTSSpeaker` 반환. online 분기는 기존 Clova Speaker 그대로
  - `.gitignore` — `third_party/`, `data/tts_ref/` 추가
  - `WORKLOG.md`
- 실행한 검증:
  - 메인 venv torch 그대로 (`2.5.0a0+nv24.08`), 27/27 기존 테스트 통과
  - 데몬 manual 기동 → `/health` ok, `/synthesize` 1.6s에 6.6초 WAV 응답
  - 메인 venv에서 `MeloTTSSpeaker.synthesize_reply_audio()` 3회 호출 → 0.63~0.86s/호출, `data/reply/*.wav`로 저장 정상
  - 오프라인 검증: HF cache 완전(`models--myshell-ai--MeloTTS-Korean` 199MB + `models--kykim--bert-kor-base` 908MB), 합성 시 데몬의 외부 socket 모두 CLOSE-WAIT (잔여) — 새 네트워크 호출 0
- 측정값 (Jetson Orin Nano 8GB):
  - 데몬 메모리 RSS: ~2.0~2.5 GB (모델 + framework + Korean BERT)
  - GPU: 0.76 GB
  - 합성 RTF: 0.22~0.27x (5초 응답 → 1초 합성)
  - 첫 호출 콜드 (BERT 다운 포함, 1회만): ~140s → warm-up에서 처리됨
- 음질 평가 (사용자):
  - 알아들을 수 있음 ✅ — 단계 7 baseline 합격선
  - 다소 "연기 로봇 톤" — 단계 8(별도 작업)에서 OpenVoice v2 추가해서 CLOVA `nhajun` 톤으로 voice clone 예정
- 사용자가 다음에 할 일:
  - (선택) systemd 등록: `sudo cp services/tts_server/hylion-tts.service /etc/systemd/system/ && sudo systemctl enable --now hylion-tts`
  - (선택) 비행기 모드 켜고 `curl POST /synthesize` 한 번 더 → 진짜 오프라인 동작 확인
- 다음 환경에서 할 일:
  - **단계 6** — coordinator inner-loop graceful degradation (STT/LLM/TTS 호출 실패 시 try/except + 즉석 `is_online()` 재프로브 + 백엔드 일시 강등 + 1회 재시도)
  - 단계 8 — OpenVoice v2 추가 (MeloTTS daemon에 tone color converter layer) → CLOVA `nhajun.wav` 톤으로 음성 클론 → 자연스러운 어린아이 voice

### 2026-05-06 (단계 7 보강 — TTS 데몬 lazy-load + /warmup, /unload)

- 한 줄 요약:
  - 사용자 지적("online 모드일 때도 TTS 데몬이 2.3GB 헛점유 중") 반영. 데몬을 lazy-load 패턴으로 전환 — 부팅 직후 RSS 40MB, coordinator가 offline일 때만 `/warmup` 트리거. **online 모드에서 RAM 약 2GB 절약**.
- 실행한 검증:
  - `/warmup` (cold): 22s, RSS 40MB → 2.5GB
  - `/warmup` (idempotent): 0s
  - `/unload`: refs 제거 + cuda cache flush (※ host RSS는 PyTorch allocator 한계로 안 떨어짐 — 진짜 회수하려면 daemon 재시작)
  - `/warmup` (재로드): 4s (BERT cache 살아있음)
  - 메인 venv `MeloTTSSpeaker.warm_up()` / `.unload()` 호출 정상
  - 27/27 기존 테스트 통과
- 수정 파일:
  - `services/tts_server/server.py` — `lifespan` 훅에서 `_load_model()`/`_warm_up_synth()` 제거, threading.Lock으로 idempotent하게 lazy 로드, `POST /warmup` + `POST /unload` 신규, `/synthesize`는 첫 호출에서 자동 warm-up (graceful)
  - `jetson/core/tts/melotts_client.py` — `MeloTTSSpeaker.warm_up()` / `.unload()` 신규
  - `jetson/core/coordinator.py` — `_startup_warm_up()` offline 분기에 MeloTTS warm-up 추가
  - `services/tts_server/README.md` — lazy lifecycle, /warmup/unload 동작, RAM 회수 한계 명시
- 메모리 비교 (online 평상시):
  - 이전 (eager load): 시스템 2.5 + 코디 1.0 + Ollama 0.3 + TTS **2.3** = **6.1 GB**
  - 이후 (lazy load): 시스템 2.5 + 코디 1.0 + Ollama 0.3 + TTS **0.04** = **3.84 GB**
  - 절약: **~2.3 GB** → 미래 OpenVoice/smolvla 동시 적재 여유 확보
- offline 평상시 메모리는 동일 (어차피 모델 로드해야 함)
- PyTorch host RAM 회수 한계:
  - `/unload` → CUDA cache는 비워지지만 `python` process RSS는 PyTorch allocator가 잡고 있어 안 떨어짐 (알려진 동작)
  - 진짜 RAM 회수: `sudo systemctl restart hylion-tts` (~5초). 단계 6 graceful degradation에서 online 복귀 시 시도해볼 옵션
- 다음 환경에서 할 일:
  - **단계 6** — graceful degradation (STT/LLM/TTS 호출 실패 시 try/except + 재프로브 + 백엔드 일시 강등 + 1회 재시도). offline→online 복귀 시 `MeloTTSSpeaker.unload()` 호출 또는 daemon restart
  - 단계 8 — OpenVoice v2 추가 (CLOVA nhajun voice cloning)

### 2026-05-11 (오프라인 모드 안정화 + LLM/TTS 응답 단축)

- 한 줄 요약:
  - 오프라인 사이클(시작 → wake → STT/LLM/TTS)을 한 번에 정비. (1) `scripts/run_coordinator.sh` 런처 도입으로 venv + LD_LIBRARY_PATH 한 줄 실행. (2) MeloTTS 데몬 systemd 등록(부팅 자동기동). (3) Ollama/Whisper 워밍업 강화 + 출력 메시지 통일. (4) **LLM을 EXAONE 3.5 2.4B → qwen2.5:1.5b-instruct 로 다운사이즈 + 프롬프트 보강**해서 응답 latency 19s → 7~9s. (5) MeloTTS WAV에 sox `pitch +400 tempo 1.05` 후처리로 어린이 톤 근사. (6) fallback 문구 "연결 불안정" 표현 정정.
- 신규 파일:
  - `scripts/run_coordinator.sh` — coordinator 런처. `jetson/expression/.venv` 의 `nvidia/cusparselt/lib` 를 `LD_LIBRARY_PATH` 에 prepend 한 뒤 venv python 으로 `jetson.core.coordinator` 실행. 이전엔 시스템 python3 로 실행하면 `libcusparseLt.so.0` import 실패로 `RuntimeError: openai-whisper is not installed` (오해의 소지가 큰 에러 메시지)가 떴음.
- 수정 파일:
  - `jetson/core/llm/ollama_llm.py`
    - `DEFAULT_OLLAMA_MODEL` `exaone3.5:2.4b` → **`qwen2.5:1.5b-instruct`** (한국어 품질 유지, 1.6GB → 986MB, decode ~2배 빠름). EXAONE 3.5 시리즈에는 공식 1.2B 가 없어 같은 클래스의 다른 패밀리(Qwen)로 교체.
    - `num_ctx` 2048 → **1536** (1024 도 시도했지만 system prompt 잘림 → schema validation 실패 / 500 사이클 발생해서 1536 절충). KV cache 25% 절약.
    - `temperature` 0.2 → **0.0** (greedy).
    - `num_predict` 150 → **80** (reply_text 25자 + JSON 보일러플레이트 ≈ 70 토큰. 모델이 어겨도 강제 cut).
    - `num_gpu=999` (env `HYLION_OLLAMA_NUM_GPU` override) — ollama 자동 offload 가 EXAONE 의 6개 layer 를 CPU 에 두던 것을 모든 layer GPU 로.
    - `warm_up()` — 1-token "ok" 만 보내던 것을 **system_prompt + format=json + keep_alive=30m** 풀 패스로 전환. wake-word 대기 동안 unload 방지 + grammar-constrained decoding 초기화 비용을 startup 에 흡수.
    - `build_action()` 도 `keep_alive=30m` 동봉 (ollama 는 요청마다 keep_alive 가 reset 되는 특성).
    - `OLLAMA_SLIM_SYSTEM_PROMPT` 재작성 — intent → (smolvla, bhl, gait, state) 4필드 1라인 매핑, 매핑 힌트 첫 줄에 "**질문/대답/소개/잡담/인사 → chat**" 명시(qwen이 모든 chat을 unknown으로 떨어뜨리던 회귀 차단), reply_text "**한국어 1문장, 25자 이내 (반드시. 길어지면 강제로 잘림)**" 강조, 마크다운/코드블록 금지 명시, **few-shot 예시 2개** (자기소개=chat, 빨간 컵 집어줘=pick_place) — 작은 모델은 규칙 산문보다 1~2개 demo 로 출력 shape 학습이 효율적.
  - `jetson/core/llm/prompt.py`
    - `_offline_action_json` 의 `reply_text` 를 "지금은 연결 상태가 불안정해서..." → **"잠깐 생각이 헝클어졌어요. 다시 한 번 말씀해 주실래요?"**. 사용자 보고: 네트워크 정상인데 LLM JSON 파싱 실패로 빠진 fallback 이 마치 네트워크 끊김처럼 보인 사고 차단.
  - `jetson/core/coordinator.py`
    - `MAX_HISTORY_TURNS` 10 → **4** (prefill 단축).
    - `_startup_warm_up()` 출력 통일 — STT / LLM / TTS 각 한 줄, prefix 정렬:
      ```
      [Startup] is_online=False
      [Warm-up] STT  whisper-small ... OK
      [Warm-up] LLM  ollama-qwen2.5:1.5b-instruct ... OK
      [Warm-up] TTS  MeloTTS daemon ... OK
      ```
      LLM 라인은 backend `.name` 자동 반영 (모델 교체 시 메시지 자동 갱신). 이전엔 "loading openai-whisper 'small'..." + "[STT] loaded openai-whisper 'small' on cuda (float16)" + "[Warm-up] local whisper OK" 3줄 중복.
  - `jetson/core/stt/local_whisper.py`
    - `warm_up()` — 모델 로드 후 **1초 무음 WAV `model.transcribe()` 까지 실행**. CUDA kernel JIT / cuDNN handle / encoder-decoder 첫-op 비용을 startup 단계에서 흡수 → 첫 발화 STT latency 가 둘째 발화와 동일해짐. `_write_silent_wav()` 헬퍼 추가 (stdlib `wave` 만 사용, 외부 의존성 0).
    - `_get_model()` 정상 path 의 `print` 제거 (coordinator warm-up 출력과 중복). CPU fallback 경고만 유지.
  - `jetson/core/tts/melotts_client.py`
    - **sox pitch+tempo 후처리** — `synthesize_reply_audio()` 가 데몬 WAV 받은 직후 `sox in.wav out.wav pitch +400 tempo 1.05` 호출해 어린이 톤 근사. env `HYLION_TTS_PITCH_CENTS` (default 400, 즉 +4 semitone) / `HYLION_TTS_TEMPO` (default 1.05) 로 런타임 튜닝.
    - `MeloTTSSpeaker.__init__` 가 pitch/tempo 받음, `_apply_voice_postprocess()` 신규. sox 미설치/실패 시 원본 WAV 반환 (graceful).
- 시스템 변경 (코드 외, 운영 측):
  - `sudo cp services/tts_server/hylion-tts.service /etc/systemd/system/`
  - `sudo systemctl daemon-reload && sudo systemctl enable --now hylion-tts`
  - 결과: 부팅 시 데몬 자동 시작, coordinator 재실행 시 데몬 cold-load 없이 즉시 사용.
- 새로 설치한 ollama 모델:
  - `ollama pull qwen2.5:1.5b-instruct` (986MB, Q4_K_M).
- 실행한 검증:
  - 시스템 python3 → venv python 전환 후 `import whisper` / `import torch` / `model.transcribe()` 정상 (이전엔 `libcusparseLt.so.0` 못 찾아서 깨짐).
  - `ss -ltn` 에 8001 (TTS), 11434 (ollama) 둘 다 LISTEN.
  - `bash scripts/run_coordinator.sh` 풀 사이클 동작 (wake → STT → LLM → TTS → 재생).
  - 응답 latency 측정 (INPUT_JSON ↔ ACTION_JSON timestamp 비교):
    - EXAONE 2.4B baseline: 19.5s (자기소개), 12s (짧은 chat).
    - qwen 1.5B + num_ctx 1536 + greedy + 50자 강제: 17.4s (자기소개 55자), 8.9s ("키가 얼마야?" 18자), 7.5s ("이름이 뭐야?" 11자) — **decode 가 토큰 수에 선형**, 짧은 응답일수록 빠름.
    - 25자 강제 + intent=chat 보강은 사용자 다음 측정 예정.
- 측정 메모:
  - 응답 latency ≈ prefill(~6s baseline, 모델 + system_prompt + history) + decode × 토큰수. EXAONE 2.4B → qwen 1.5B 교체로 prefill/decode 둘 다 약 절반.
  - 메모리: qwen 1.5B Q4 ~1GB VRAM (EXAONE 2.4B 1.6GB 대비 ~600MB 절약). baseline 6.0Gi/7.4Gi 사용 중인 Jetson Orin Nano 에서 의미 큼.
  - sox 후처리: ~50~100ms 추가, 메모리 영향 거의 0.
  - OOM 사건 1회: TTS 데몬 cold warmup 직후 검증 명령에서 추가로 torch + ollama 동시 로드 시도 → SIGKILL + X 세션 종료. 데몬은 systemd 가 자동 복구. 이후 검증은 가볍게 진행 (torch import 없이 curl 만).
- 알려진 한계 / 다음 세션:
  - intent="unknown" 잘못 떨어지는 케이스 — qwen 보강 프롬프트로 1차 완화. 추가 사례 발생 시 keyword override 강화 또는 2단계 LLM 호출 고려.
  - 첫 num_ctx 1024 시도 → ollama 500 + system prompt 잘림. 1536 이 한국어 25자 응답 + 4-turn history 의 sweet spot. 더 짜내려면 system prompt 영문 transliteration 또는 단계 분리 필요.
  - 본격 latency 단축: (a) **streaming TTS** — LLM 토큰 받으면서 reply_text partial 추출해 즉시 TTS, 체감 latency ~3s, 반나절 작업. (b) **TensorRT-LLM** 으로 qwen 재컴파일, 2~3배 prefill 단축, 1~2일. 둘 다 별도 단계.
  - voice cloning (CLOVA `nhajun` → OpenVoice v2) — 메모리 budget 검토 후 별도 단계 (계획은 docs/10 에 이미 있음).
- 사용자가 다음에 할 일:
  - `bash scripts/run_coordinator.sh` 다시 돌려 25자 강제 + intent=chat 분류 안정 확인.
  - 만족하면 streaming TTS 또는 voice cloning 으로 진행 결정.

### 2026-05-11 — BHL Bridge 초안 (Coordinator JSON ↔ BHL UDP)

- 목표: NUC 의 Berkeley Humanoid Lite lowlevel C 컨트롤러를 게임패드 대신
  Jetson coordinator 의 action JSON 으로 제어. `BHL_Bridge_Handoff.md`(인수인계 문서)
  사양에 맞춰 브리지 신규 구현.
- 추가한 파일:
  - `nuc/bhl/bridge.py` — TCP/NDJSON(:9000) 수신 → 13-byte `<Bfff` UDP 패킷
    (`127.0.0.1:10011`, BHL `consts.h:JOYSTICK_PORT`) 송신. cold start(IDLE→RL_INIT
    1.5s→RL_RUNNING 0.1s) 자동 + watchdog 200ms + EMERGENCY/safety_off/intent=stop
    즉시 STOP + TCP 끊김 시 STOP + 재연결 시 cold start 재실행. 모든 TUNE 지점
    주석 마킹 + env 오버라이드 (`BRIDGE_*`).
  - `nuc/bhl/tests/mock_coordinator.py` — 7가지 시나리오
    (walk/turn/emergency/safety_off/bad_json/watchdog/loop).
  - `nuc/bhl/tests/mock_bhl_receiver.py` — UDP 디코드 + 상태 변화 시점만 출력.
  - `nuc/bhl/systemd/hylion-bridge.service` + `hylion-bridge.env.example`
    — 부팅 자동 실행, journald 로깅, EnvironmentFile 로 무재컴파일 튜닝.
  - `nuc/bhl/README.md` — NUC 검증 + 실배포 절차.
  - `nuc/bhl/BHL_Bridge_Handoff.md` — 원본 인수인계 문서(별도 작성분, 같이 커밋).
- BHL 원본 코드 조사로 확정한 사실:
  - 모드 매핑: `command_mode=1→IDLE, 2→RL_INIT, 3→RL_RUNNING, 0→유지`
    (`csrc/real_humanoid.cpp:259-273`).
  - 명령 정규화 범위는 `[-1.0, 1.0]` 으로 추정 (`gamepad.py` 의 `raw/-32768`).
    → `VEL_FORWARD_MPS=0.5`, `VEL_TURN_LEFT_RPS=0.5` 보수적 시작값으로 채택.
  - 양방향 telemetry 패턴은 BHL 측에 없음 (`run_locomotion.py:16` 이 obs를
    UDP 단방향 visualize 만 함). IMU 채널 확장 시 이 패턴 참고.
- 구현 중 발견·수정한 버그:
  - 초안 cold_start 는 mode=2 / mode=3 패킷을 1회씩만 직접 송신했음. 그러나
    20 Hz sender 가 즉시 `STOP_PACKET`(mode=1) 으로 덮어써 C 의 `next_state`
    가 매 패킷마다 `STATE_IDLE` 로 되돌아감 (real_humanoid.cpp:259 가 `mode!=0`
    이면 매번 next_state 갱신). → cold_start 가 `state.current_packet` 자체를
    mode=2/3 패킷으로 바꿔 sender 가 1.5s 동안 같은 모드를 broadcast 하도록 수정.
- 테스트 결과 (NUC 로컬, mock_coordinator + mock_bhl_receiver):
  - cold start: mode=1(idle) → mode=2 × 30패킷 (1.5s @ 20Hz) → mode=3 × 2 (0.1s)
    → mode=0 vx=+0.500 (walk_forward) → mode=1 (stop) — 모두 정확.
  - emergency 시나리오: walk 1건 → EMERGENCY 1건 → 즉시 mode=1.
  - watchdog: walk 1건 송신 후 침묵 → 정확히 200ms 후 sender 가 mode=1 로 전환
    (실측 t=237.601 → t=237.802).
  - bad_json: 깨진 라인 한 줄 → 파싱 에러 로그만 남기고 다음 정상 JSON 수신 정상 처리.
  - TCP 끊김 → STOP + accept 재진입, 재연결 시 cold start 자동 재실행.
- 수정 파일: 위 목록의 신규 파일만. 기존 코드 변경 없음.
- 다음 환경에서 할 일 (NUC 에 실배포):
  1. `nuc/bhl/Berkeley-Humanoid-Lite-Lowlevel-main/` 빌드 (`make run`).
  2. `python -m berkeley_humanoid_lite_lowlevel.policy.rl_controller` 정책 추론.
  3. `python3 bridge.py` 로 검증 보행 1회 — `VEL_FORWARD_MPS` 가 학습 범위 안인지,
     `velocity_y/yaw` 부호가 좌측/좌회전이 양수 맞는지 실로봇 거동으로 확인.
  4. systemd 등록 (`README.md` 4번 항목) 후 전원 재투입으로 자동 기동 확인.
- 미해결:
  - BHL `configs/` 가 비어있어 정책 학습 명령 범위 yaml 확인 불가. 0.5 보수값.
  - `velocity_y` 와 `velocity_yaw` 의 부호 (gamepad.py 기준 +X=좌측/좌회전으로 가정).
  - Jetson coordinator 측 TCP 클라이언트 코드 — 아직 없음, 다음 단계.

### 2026-05-14 (Coordinator LLM 프롬프트 — 하네스 엔지니어링 적용)

- 한 줄 요약:
  - 프롬프트를 "더 좋은 문장 쓰기"가 아니라 모델을 감싸는 하네스 전체 설계로 접근.
    LLM 출력 계약을 4필드로 축소하고 나머지는 코드가 derive/주입, eval 하네스로
    프롬프트를 숫자로 측정하며 3회 반복(69.2% → 76.9% → 80.8%).
- 실행한 검증 명령:
  - `python -m pytest tests/3_interface/ -q` → 28 passed
  - `python -m jetson.core.llm.eval.run_eval --backend offline` → 21/26 (80.8%)
- 핵심 설계 (하네스 책임 맵):
  - LLM 판단 = `intent, target_object, reply_text, gait_cmd` 4필드만.
  - 코드 derive = `requires_smolvla/requires_bhl/state_current/safety_allowed`.
  - 코드 주입 = `action_id/timestamp/session_id/schema_version/source/`
    `network_online/fallback_policy`.
- 수정한 파일:
  - `jetson/core/llm/prompt.py` — 전면 재작성. `extract_core`(LLM JSON→4필드),
    `derive_full_action`(4필드→15필드 스키마 객체), `apply_hard_overrides`
    (키워드 규칙을 프롬프트→코드로 이동, longest-match-wins), `assemble_action`
    (두 백엔드 공통 진입점), 레이어드 `ONLINE/OFFLINE_SYSTEM_PROMPT`.
    낡은 `LocalLLMClient`/`build_action_json_from_stt`/`_apply_conversation_policy`
    경로 제거.
  - `jetson/core/llm/groq_llm.py` `ollama_llm.py` — 둘 다 `assemble_action`
    공통 경로로 통합. `OLLAMA_SLIM_SYSTEM_PROMPT` 삭제(→`OFFLINE_SYSTEM_PROMPT`).
  - `jetson/core/llm/factory.py` — docstring 모델명 정정(exaone→qwen2.5:1.5b).
  - `jetson/core/llm/eval/` — 신규. `cases.jsonl`(26 케이스), `run_eval.py`
    (intent/target/gait 정확도 측정), `__init__.py`.
  - `tests/3_interface/test_groq_api.py` — 신규 API(extract_core/apply_hard_
    overrides/derive_full_action/assemble_action) 기준 재작성.
  - `tests/3_interface/test_ollama_llm.py` — staleness 정정(모델명, fallback_policy
    문자열).
- 구현 중 발견·수정한 버그:
  - `_INTENT_DEFAULT_STATE`가 스키마에 없는 `"PICKING"` 사용 → `MANIPULATING`으로.
  - 오프라인 프롬프트가 스키마에 없는 `walk_back/turn_right` 제시 → 제거.
  - `apply_hard_overrides`의 "그만"이 "그만하자"를 먼저 잡아 standby→stop 오분류
    → longest-match-wins로 수정.
- eval 측정 결과 (오프라인 qwen2.5:1.5b, 26 케이스):
  - 최종 80.8%. stop 4/4·standby 5/5는 `apply_hard_overrides`가 코드로 보장하므로
    모델 정확도와 무관하게 안전. pick_place 4/4.
  - 남은 실패는 chat↔unknown 혼동, 좌/우 방향 혼동 — 1.5B 모델 능력 한계.
    derive 레이어가 스키마 유효성은 100% 보장하므로 잘못돼도 안전한 액션만 방출.
- 남은 할 일:
  - `--backend online`(Groq) eval 측정 — `GROQ_API_KEY` 필요.
  - cases.jsonl 케이스 확충(현재 26개, 작아서 run별 변동 있음).
  - action.schema.json의 gait enum에 `walk_back/turn_right` 추가 여부는
    BHL 속도 범위 확정 후 결정(BHL_Bridge_Handoff.md §11).

### 2026-05-14 (Gesture 실행기 + README 실행법 문서화)

- 한 줄 요약:
  - chat 턴이 키워드 감지된 gesture를 실어오면 coordinator가 우측 SO-ARM에서
    재생하도록 첫 실제 executor 연결. README에 `run_coordinator.sh` 실행법 추가.
- 수정/추가한 파일:
  - `jetson/core/gesture_registry.py` — 신규. 유효 gesture 이름의 single source
    of truth. `~/smolvla/orin/gestures/<name>/meta/info.json` 디렉토리 스캔으로
    발견, 프로세스 캐시. prompt.py 프롬프트 enum과 coordinator 실행 경로가
    드리프트하지 않도록 둘 다 여기서 조회. `ORIN_GESTURES_ROOT` env override.
  - `jetson/core/coordinator.py` — `_play_gesture_if_any` 추가. chat 분기에서
    `gesture_name != "none"` 이면 `play_gesture.sh` 를 blocking subprocess 로
    실행(`PLAY_GESTURE_SCRIPT` env override, 60s timeout). 상속된 `VIRTUAL_ENV`
    를 strip 해서 wrapper 가 자기 venv 를 잡도록 함. gesture 실패는 로그만,
    대화 루프는 절대 안 끊김. mock action 빌더들에 `gesture_name: "none"` 추가.
  - `configs/schemas/action.schema.json` — `gesture_name` 필드 추가(required).
  - `jetson/core/network.py` — `is_online` 에 오프라인 강제 테스트용 주석 라인
    보존(`# return False`).
  - `README.md` — "실행 방법" 섹션 추가. `scripts/run_coordinator.sh`(venv +
    LD_LIBRARY_PATH + coordinator 한 줄 실행)와 `scripts/live_monitor.sh` 안내.
  - `scripts/live_monitor.sh` — 신규 추적. RAM/GPU/프로세스/데몬 상태 1초 갱신.
