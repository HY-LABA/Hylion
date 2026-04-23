from __future__ import annotations

import subprocess
import threading
import time
import os
from pathlib import Path
from typing import Optional

from jetson.expression.mouth_servo import MouthServoController

try:
    from gtts import gTTS  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - runtime dependency in target environment
    gTTS = None

try:
    from mutagen.mp3 import MP3  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - runtime dependency in target environment
    MP3 = None

# parameters
PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPLY_AUDIO_DIR = PROJECT_ROOT / "data" / "reply"
REPLY_AUDIO_FILENAME = "reply.mp3"


def synthesize_reply_audio(reply_text: str, output_dir: Optional[Path] = None) -> Path:
    """Create Korean TTS audio and return generated MP3 path."""
    text = reply_text.strip()
    if not text:
        raise ValueError("reply_text is empty")

    if gTTS is None:
        raise RuntimeError("gTTS is not installed. Install gTTS in the runtime environment.")

    if output_dir is None:
        output_dir = REPLY_AUDIO_DIR

    os.makedirs(output_dir, exist_ok=True)
    mp3_path = output_dir / REPLY_AUDIO_FILENAME
    tts = gTTS(text=text, lang="ko")
    tts.save(str(mp3_path))
    return mp3_path


def get_audio_duration_sec(audio_path: Path) -> float:
    """Get accurate MP3 duration in seconds using mutagen."""
    if MP3 is None:
        raise RuntimeError("mutagen is not installed. Install mutagen in the runtime environment.")
    return max(0.0, float(MP3(str(audio_path)).info.length))


def play_audio_blocking(audio_path: Path) -> None:
    """Play MP3 on Linux with mpg123 and block until playback completes."""
    subprocess.run(["mpg123", "-q", str(audio_path)], check=True)


def speak_with_lipsync(
    reply_text: str,
    *,
    cleanup_after_play: bool = False,
    servo_pin: int = 33,
) -> float:
    """
    Run two-thread lip-sync using generated Korean TTS audio.

    Thread 1: audio playback (with fallback sleep on playback failure)
    Thread 2: mouth servo movement for the same duration
    """
    if not reply_text.strip():
        return 0.0

    audio_path = synthesize_reply_audio(reply_text)
    duration = get_audio_duration_sec(audio_path)

    stop_event = threading.Event()
    servo = MouthServoController(pin=servo_pin)

    def _audio_worker() -> None:
        try:
            play_audio_blocking(audio_path)
        except Exception as exc:
            print(f"[FaceSpeaker] audio playback failed -> fallback sleep ({exc})")
            # Keep timing contract even without speaker hardware. This preserves
            # lip-sync timing by occupying the audio thread for the same duration.
            time.sleep(duration)
        finally:
            stop_event.set()

    def _servo_worker() -> None:
        try:
            # Servo thread uses the same duration extracted from MP3 metadata,
            # so mouth motion length matches playback length.
            servo.run_lipsync_for_duration(duration_sec=duration, stop_event=stop_event)
        except Exception as exc:
            print(f"[FaceSpeaker] servo playback failed -> fallback audio-only ({exc})")
            stop_event.set()

    audio_thread = threading.Thread(target=_audio_worker, name="face-audio", daemon=True)
    servo_thread = threading.Thread(target=_servo_worker, name="face-servo", daemon=True)

    start_ts = time.monotonic()
    audio_thread.start()
    servo_thread.start()

    audio_thread.join()
    servo_thread.join()
    elapsed = time.monotonic() - start_ts

    if cleanup_after_play:
        # If this process owns Pin 33 alone, cleanup can be enabled safely.
        servo.cleanup()

    return elapsed
