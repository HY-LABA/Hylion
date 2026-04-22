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
