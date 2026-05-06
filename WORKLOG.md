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
