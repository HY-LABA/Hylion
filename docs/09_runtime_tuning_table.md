# HYlion Runtime Tuning Table

This table is for practical tuning of wake-word, STT, and coordinator loop behavior on Jetson.

## 1) Wake-word Tuning (openwakeword)

| Area | Parameter (File) | Current | Suggested Range | Increase Effect | Decrease Effect | Typical Side Effect | Priority |
|---|---|---:|---:|---|---|---|---|
| Detection sensitivity | DEFAULT_WAKEWORD_THRESHOLD (jetson/expression/wake_word.py) | 0.5 | 0.35-0.75 | Fewer false wakes | More responsive to soft speech | Too high misses wake word, too low false positives | High |
| Input chunk size | DEFAULT_WAKEWORD_BLOCK_MS (jetson/expression/wake_word.py) | 80 ms | 40-120 ms | More stable score averaging | Faster reaction latency | Too small may increase jitter | Medium |
| Post-detect baton touch | DEFAULT_BATON_TOUCH_DELAY_SEC (jetson/expression/wake_word.py) | 0.5 s | 0.3-0.8 s | More reliable mic handoff | Faster transition to STT | Too short can cause device-busy race | High |
| Plan A sample rate | DEFAULT_PLAN_A_SAMPLE_RATE (jetson/expression/wake_word.py) | 16000 | keep 16000 | Native model input rate | N/A | Changing can break detection assumptions | Fixed |
| Plan B sample rate | DEFAULT_PLAN_B_SAMPLE_RATE (jetson/expression/wake_word.py) | 44100 | 32000-48000 | Better hardware compatibility | Less CPU on resample | Wrong value can fail device open | Medium |

## 2) TTS / Lipsync Tuning

| Area | Parameter (File) | Current | Suggested Range | Increase Effect | Decrease Effect | Typical Side Effect | Priority |
|---|---|---:|---:|---|---|---|---|
| Clova speaker | DEFAULT_CLOVA_SPEAKER (jetson/expression/speaker.py) | ara | ara / gihyo | Tighter, more child-like Korean voice | Less playful tone | Voice color changes noticeably | High |
| Clova timeout | DEFAULT_CLOVA_TTS_TIMEOUT_SEC (jetson/expression/speaker.py) | 15.0 s | 10-20 s | More tolerant of slow network | Faster failure on API stall | Too low may interrupt synthesis | Medium |
| Reply save dir | REPLY_AUDIO_DIR (jetson/expression/speaker.py) | data/reply | keep path | Keeps generated speech inside project data tree | N/A | Directory growth if files are never cleaned | High |
| Reply filename | timestamped reply_*.mp3 (jetson/expression/speaker.py) | unique per turn | keep unique | Preserves multiple replies for later review | N/A | More disk usage over time | Medium |

## 3) Coordinator State Tuning

| Area | Parameter (File) | Current | Suggested Range | Increase Effect | Decrease Effect | Typical Side Effect | Priority |
|---|---|---:|---:|---|---|---|---|
| Auto-standby rearm gap | AUTO_STANDBY_COOLDOWN_SEC (jetson/core/coordinator.py) | 1.5 s | 1.0-2.5 s | Reduces post-task immediate re-trigger | Faster return to wake-ready | Too low can retrigger from tail audio | High |
| Chat->standby rearm gap | CHAT_STANDBY_COOLDOWN_SEC (jetson/core/coordinator.py) | 1.2 s | 1.0-2.0 s | Reduces retrigger after "go standby" utterance | Faster return to wake-ready | Too low can re-trigger without keyword | High |
| Per-turn mic capture length | --record-sec arg (jetson/core/coordinator.py) | 4.0 s | 2.5-5.0 s | Captures long utterances | Reduces waiting time per turn | Too short clips speech, too long adds latency | High |

## 4) STT (faster-whisper) Tuning

| Area | Parameter (File) | Current | Suggested Options | Speed Impact | Accuracy Impact | Typical Side Effect | Priority |
|---|---|---|---|---|---|---|---|
| Model size | model_size in transcribe_wav (jetson/expression/stt_whisper.py) | small | tiny/base/small | tiny fastest, small slowest | small best, tiny lowest | tiny may miss details/noisy speech | Very High |
| Compute precision | compute_type in transcribe_wav (jetson/expression/stt_whisper.py) | int8 | int8/float16/float32 | int8 usually fastest on CPU | float types can be more stable | device-dependent performance | High |
| Language hint | language in transcribe_wav (jetson/expression/stt_whisper.py) | ko | fixed ko or auto | fixed language is faster | fixed can improve target language | auto adds latency and language drift | Medium |
| VAD filter | vad_filter in model.transcribe (jetson/expression/stt_whisper.py) | True | True/False | True can skip silence and speed decode | True may clip edge words in some cases | False decodes more noise | Medium |
| Model cache reuse | _MODEL_CACHE (jetson/expression/stt_whisper.py) | enabled | keep enabled | Avoids reload overhead | neutral | none | Fixed |

## 5) Suggested Tuning Sequence

1. Keep wake-word threshold at 0.5 and set record-sec to 3.0 for quick turn testing.
2. If false wakes occur, raise threshold by +0.05 steps.
3. If chat->standby retrigger occurs, raise CHAT_STANDBY_COOLDOWN_SEC by +0.2 s.
4. If STT is slow, switch model_size small -> base -> tiny (in that order).
5. Recheck intent quality after each speed change.

## 6) Quick Field Test Matrix

| Case | Command Pattern | What to Observe | Pass Criteria |
|---|---|---|---|
| Wake stability | Wake word only, no command | false wake count in 3 min | 0 false wakes |
| Chat standby stability | "standby" style end phrase | immediate re-trigger after standby | no re-trigger within 5 sec |
| Task standby stability | move/pick_place then auto-standby | re-trigger after completion reply | no re-trigger within 5 sec |
| STT latency | short command (1-2 sec speech) | mic stop to text ready time | under target threshold |
| Intent quality | 10 mixed utterances | intent classification correctness | at least 90% |

## 7) Note on Reply Audio File Storage

Reply audio generated by the ClovaTTS path is stored in the project tree under data/reply.

- On Ubuntu/Jetson: typically Hylion/data/reply
- File pattern: reply_<timestamp>.mp3

Current implementation does not auto-delete these files after playback.
If cleanup is needed, add a post-play delete policy in jetson/expression/speaker.py.
