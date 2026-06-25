"""jetson/core/hardcoding_coordinator.py — 시나리오 하드코딩 coordinator.

실행:
    cd ~/Hylion
    python3 -m jetson.core.hardcoding_coordinator

흐름:
    웨이크워드 감지 → 인사 → 발화 감지 루프 → 시나리오 스텝 매칭 → TTS + gesture
    6번 스텝("쉬고 있어") 이후 웨이크워드 대기 상태로 복귀.
"""
from __future__ import annotations

import os
import subprocess
import threading
import time
from pathlib import Path
from time import sleep

PROJECT_ROOT   = Path(__file__).resolve().parents[2]
GESTURE_DIR    = PROJECT_ROOT / "jetson" / "arm" / "gestures"
PLAY_SH        = GESTURE_DIR / "play_gesture.sh"
PLAY_BOTH_SH   = GESTURE_DIR / "play_both_wave.sh"
LIVE_AUDIO_DIR = PROJECT_ROOT / "data" / "episodes"
LIVE_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

RECORD_SEC          = 5.0
SPEECH_RMS_THRESHOLD = 350
PREFERRED_KEYWORD   = "P5HD"
SAMPLE_RATE         = 44100


# ── 시나리오 정의 ──────────────────────────────────────────────────────────────
# keywords: 하나라도 포함되면 매칭. reply: TTS 멘트. gesture: 아래 _run_gesture 참조.
SCENARIOS: list[dict] = [
    {
        "id": 1,
        "keywords": ["인사해", "관객"],
        "reply": (
            "안녕하세요! 저는 한양대 라바랩실의 하이리온이에요! "
            "이렇게 만나게 돼서 정말 반가워요!"
        ),
        "gesture": "both_wave",
    },
    {
        "id": 2,
        "keywords": ["자기소개"],
        "reply": (
            "나는 애국한양 민주경영 라바랩실의 사고뭉치를 맡고 있는 하이리온이야! "
            "내 이름이 뭐라고?"
        ),
        "gesture": "wave_hello",
    },
    {
        "id": 3,
        "keywords": ["기분", "사람들 앞", "서니"],
        "reply": (
            "하산해서 행당산 밑으로 내려오니 공기가 참 상쾌하고 좋다! "
            "이렇게 많은 사람들 앞은 처음이라 쑥스럽네. "
            "성래 너는 많이 긴장돼 보여!"
        ),
        "gesture": None,
    },
    {
        "id": 4,
        "keywords": ["목이 마르", "음료수", "마시고 싶"],
        "reply": "알겠어 앞에 보이는 음료수를 줄게!",
        "gesture": "pick_object_left",
    },
    {
        "id": 5,
        "keywords": ["인형", "탁자"],
        "reply": "내 친구 미니 하이리온이야!",
        "gesture": "wave_hello",
    },
    {
        "id": 6,
        "keywords": ["쉬고 있어", "쉬어"],
        "reply": "알겠어 쉬고 있을게!",
        "gesture": "wave_hello",
        "end": True,   # 이 스텝 후 웨이크워드 대기로 복귀
    },
]

GREETING_TEXT = "네, 말씀하세요!"


# ── gesture 실행 ───────────────────────────────────────────────────────────────

def _run_gesture(gesture: str | None) -> None:
    """gesture 를 백그라운드 스레드에서 실행 (비블로킹)."""
    if not gesture:
        return

    def _exec() -> None:
        if gesture == "both_wave":
            cmd = ["bash", str(PLAY_BOTH_SH)]
            env = None
        elif gesture == "wave_hello":
            cmd = ["bash", str(PLAY_SH), "wave_hello"]
            env = None
        elif gesture == "pick_object_left":
            cmd = ["bash", str(PLAY_SH), "pick_object"]
            env = dict(os.environ)
            env["FOLLOWER_PORT"] = "/dev/so_arm_left"
            env["FOLLOWER_ID"]   = "leftarm_test_follower"
        else:
            print(f"[Gesture] 알 수 없는 gesture: {gesture}")
            return

        print(f"[Gesture] {gesture} 실행 중...")
        result = subprocess.run(cmd, env=env, capture_output=False)
        print(f"[Gesture] {gesture} 완료 (rc={result.returncode})")

    threading.Thread(target=_exec, daemon=True).start()


# ── 키워드 매칭 ────────────────────────────────────────────────────────────────

def _match_scenario(text: str) -> dict | None:
    """STT 텍스트에서 시나리오 스텝을 찾아 반환. 없으면 None."""
    normalized = text.strip().lower()
    for step in SCENARIOS:
        for kw in step["keywords"]:
            if kw in normalized:
                return step
    return None


# ── 메인 ──────────────────────────────────────────────────────────────────────

def main() -> None:
    from datetime import datetime

    from jetson.core.stt import build_stt_backend
    from jetson.expression.microphone import record_to_wav, wav_has_speech
    from jetson.expression.mouth_servo import MouthServoController, cleanup_gpio
    from jetson.expression.speaker import DEFAULT_CLOVA_SPEAKER, build_tts_backend
    from jetson.expression.wake_word import build_wake_word_listener

    print("[Init] 초기화 중...")
    wakeword_listener = build_wake_word_listener()
    stt = build_stt_backend(online=True, language="ko")
    tts = build_tts_backend(is_online=True, speaker=DEFAULT_CLOVA_SPEAKER,
                            tts_provider="clova")
    servo = MouthServoController(pin=7)
    print(f"[Init] 완료. MouthServo available={servo.is_available}")

    try:
        while True:
            # ── 웨이크워드 대기 ────────────────────────────────────────────────
            print("\n[Standby] 웨이크워드 대기 중...")
            activation = wakeword_listener.wait_for_wake_word()
            print(f"[Wake] label={activation.label}, score={activation.score:.3f}")

            # ── 인사 ──────────────────────────────────────────────────────────
            print(f"[TTS] {GREETING_TEXT}")
            tts.speak_with_lipsync(GREETING_TEXT, mouth_servo=servo,
                                   speaker=DEFAULT_CLOVA_SPEAKER)

            # ── 발화 감지 루프 ─────────────────────────────────────────────────
            silent_turns = 0
            while True:
                wav_path = str(
                    LIVE_AUDIO_DIR
                    / f"hc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
                )
                print(f"[Mic] {RECORD_SEC:.0f}초 녹음...")
                record_to_wav(wav_path, duration_sec=RECORD_SEC,
                              preferred_keyword=PREFERRED_KEYWORD,
                              samplerate=SAMPLE_RATE)

                has_speech, peak_rms = wav_has_speech(
                    wav_path, rms_threshold=SPEECH_RMS_THRESHOLD)
                print(f"[Mic] peak_rms={peak_rms}, has_speech={has_speech}")

                if not has_speech:
                    silent_turns += 1
                    print(f"[STT] 발화 없음 → 무음 턴 {silent_turns}")
                    if silent_turns >= 3:
                        print("[Mode] 무음 3턴 → 웨이크워드 대기로 복귀")
                        break
                    continue

                silent_turns = 0
                stt_result = stt.transcribe(wav_path)
                transcript = stt_result.text.strip() if stt_result else ""
                print(f"[STT] \"{transcript}\"")

                if not transcript:
                    continue

                step = _match_scenario(transcript)
                if step is None:
                    print("[Match] 매칭 없음 — 계속 듣는 중")
                    continue

                print(f"[Match] 스텝 {step['id']} 매칭: {transcript!r}")

                # gesture 먼저 시작 (비동기)
                _run_gesture(step.get("gesture"))

                # TTS 재생 (블로킹 — gesture 와 동시 진행)
                reply = step["reply"]
                print(f"[TTS] {reply}")
                tts.speak_with_lipsync(reply, mouth_servo=servo,
                                       speaker=DEFAULT_CLOVA_SPEAKER)

                if step.get("end"):
                    print("[Mode] 시나리오 종료 → 웨이크워드 대기로 복귀")
                    sleep(1.0)
                    break

    except KeyboardInterrupt:
        print("\n[종료] 사용자 중단")
    finally:
        if wakeword_listener is not None:
            try:
                wakeword_listener.close()
            except Exception:
                pass
        cleanup_gpio()
        print("[종료] 완료")


if __name__ == "__main__":
    main()
