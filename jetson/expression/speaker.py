from __future__ import annotations

import shutil
import subprocess
import tempfile
import threading
import time
import wave
from pathlib import Path
from typing import Optional

from jetson.expression.mouth_servo import MouthServoController

try:
    from gtts import gTTS  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - optional dependency in offline/dev environments
    gTTS = None


def _estimate_duration_from_text(reply_text: str) -> float:
    text = reply_text.strip()
    if not text:
        return 0.6
    # Rough Korean/English mixed speech estimate for fallback.
    return max(0.8, len(text) * 0.085)


def _create_silent_wav(output_path: Path, duration_sec: float, sample_rate: int = 16000) -> Path:
    duration_sec = max(0.1, duration_sec)
    num_frames = int(sample_rate * duration_sec)
    with wave.open(str(output_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * num_frames)
    return output_path


def synthesize_reply_audio(reply_text: str, output_dir: Optional[Path] = None) -> Path:
    """Create TTS audio for reply text. Returns path to generated wav or mp3."""
    if output_dir is None:
        output_dir = Path(tempfile.gettempdir()) / "hylion_tts"
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_name = f"reply_{int(time.time() * 1000)}"

    if gTTS is not None:
        mp3_path = output_dir / f"{safe_name}.mp3"
        tts = gTTS(text=reply_text, lang="ko")
        tts.save(str(mp3_path))
        return mp3_path

    wav_path = output_dir / f"{safe_name}.wav"
    estimated = _estimate_duration_from_text(reply_text)
    return _create_silent_wav(wav_path, estimated)


def get_audio_duration_sec(audio_path: Path) -> float:
    """Get duration from wav directly, or fallback to ffprobe when available."""
    suffix = audio_path.suffix.lower()
    if suffix == ".wav":
        with wave.open(str(audio_path), "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            if rate <= 0:
                return 0.0
            return frames / float(rate)

    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        cmd = [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return max(0.0, float(result.stdout.strip()))

    raise RuntimeError(f"Cannot parse non-wav duration without ffprobe: {audio_path}")


def play_audio_blocking(audio_path: Path) -> None:
    """Play audio using aplay for wav, ffplay for mp3/wav, and block until finished."""
    suffix = audio_path.suffix.lower()

    if suffix == ".wav" and shutil.which("aplay"):
        subprocess.run(["aplay", str(audio_path)], check=True)
        return

    ffplay = shutil.which("ffplay")
    if ffplay:
        subprocess.run(
            [ffplay, "-nodisp", "-autoexit", "-loglevel", "error", str(audio_path)],
            check=True,
        )
        return

    raise RuntimeError("No playback backend found (aplay/ffplay).")


def speak_with_lipsync(
    reply_text: str,
    *,
    cleanup_after_play: bool = False,
    servo_pin: int = 33,
) -> float:
    """
    Run two-thread lip-sync.

    Thread 1: audio playback (with fallback sleep on playback failure)
    Thread 2: mouth servo random movement for exact duration
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
            # Keep timing contract even without speaker hardware.
            time.sleep(duration)
        finally:
            stop_event.set()

    def _servo_worker() -> None:
        try:
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
