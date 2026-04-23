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
