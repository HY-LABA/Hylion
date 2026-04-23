from __future__ import annotations

import os
import subprocess
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from jetson.expression.mouth_servo import MouthServoController

try:
    from mutagen.mp3 import MP3  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - runtime dependency in target environment
    MP3 = None

try:
    from gtts import gTTS  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - runtime dependency in target environment
    gTTS = None

# parameters
PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPLY_AUDIO_DIR = PROJECT_ROOT / "data" / "reply"
DEFAULT_CLOVA_SPEAKER = "ara"
DEFAULT_CLOVA_TTS_API_URL = "https://naveropenapi.apigw.ntruss.com/tts-premium/v1/tts"
DEFAULT_CLOVA_TTS_TIMEOUT_SEC = 15.0
DEFAULT_PIPER_STUB_FILENAME = "piper_stub.wav"


def _estimate_duration_from_text(reply_text: str) -> float:
    text = reply_text.strip()
    if not text:
        return 0.6
    return max(0.8, len(text) * 0.085)


def _timestamped_filename(extension: str) -> str:
    return f"reply_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}{extension}"


@dataclass(frozen=True)
class ClovaTTSConfig:
    # parameters
    speaker: str = DEFAULT_CLOVA_SPEAKER
    save_dir: Path = REPLY_AUDIO_DIR
    api_url: str = DEFAULT_CLOVA_TTS_API_URL
    timeout_sec: float = DEFAULT_CLOVA_TTS_TIMEOUT_SEC


class ClovaTTS:
    def __init__(self, config: Optional[ClovaTTSConfig] = None) -> None:
        self.config = config or ClovaTTSConfig()
        self.client_id = os.getenv("NAVER_CLIENT_ID")
        self.client_secret = os.getenv("NAVER_CLIENT_SECRET")
        if not self.client_id or not self.client_secret:
            raise RuntimeError("NAVER_CLIENT_ID and NAVER_CLIENT_SECRET must be set in the environment")

    def synthesize_reply_audio(self, reply_text: str, output_dir: Optional[Path] = None) -> Path:
        text = reply_text.strip()
        if not text:
            raise ValueError("reply_text is empty")

        save_dir = output_dir or self.config.save_dir
        os.makedirs(save_dir, exist_ok=True)

        mp3_path = save_dir / _timestamped_filename(".mp3")
        body = urlencode(
            {
                "speaker": self.config.speaker,
                "text": text,
                "format": "mp3",
                "speed": "0",
                "pitch": "0",
                "volume": "0",
            }
        ).encode("utf-8")

        request = Request(
            self.config.api_url,
            data=body,
            headers={
                "X-NCP-APIGW-API-KEY-ID": self.client_id,
                "X-NCP-APIGW-API-KEY": self.client_secret,
            },
            method="POST",
        )

        with urlopen(request, timeout=self.config.timeout_sec) as response:
            audio_bytes = response.read()

        if not audio_bytes:
            raise RuntimeError("Clova TTS returned empty audio payload")

        mp3_path.write_bytes(audio_bytes)
        return mp3_path

    def get_audio_duration_sec(self, audio_path: Path, reply_text: str = "") -> float:
        if MP3 is None:
            raise RuntimeError("mutagen is not installed. Install mutagen in the runtime environment.")
        return max(0.0, float(MP3(str(audio_path)).info.length))

    def play_audio_blocking(self, audio_path: Path, duration_sec: float) -> None:
        subprocess.run(["mpg123", "-q", str(audio_path)], check=True)

    def speak_with_lipsync(
        self,
        reply_text: str,
        *,
        cleanup_after_play: bool = False,
        servo_pin: int = 33,
    ) -> float:
        if not reply_text.strip():
            return 0.0

        audio_path = self.synthesize_reply_audio(reply_text)
        duration = self.get_audio_duration_sec(audio_path, reply_text=reply_text)

        stop_event = threading.Event()
        servo = MouthServoController(pin=servo_pin)

        def _audio_worker() -> None:
            try:
                self.play_audio_blocking(audio_path, duration_sec=duration)
            except Exception as exc:
                print(f"[FaceSpeaker] audio playback failed -> fallback sleep ({exc})")
                # Preserve lip-sync timing even if playback fails.
                time.sleep(duration)
            finally:
                stop_event.set()

        def _servo_worker() -> None:
            try:
                # Duration comes from the generated MP3 metadata, so the servo motion
                # length stays aligned with the actual spoken audio length.
                servo.run_lipsync_for_duration(duration_sec=duration, stop_event=stop_event)
            except Exception as exc:
                print(f"[FaceSpeaker] servo playback failed -> fallback audio-only ({exc})")
                stop_event.set()

        audio_thread = threading.Thread(target=_audio_worker, name="clova-audio", daemon=True)
        servo_thread = threading.Thread(target=_servo_worker, name="clova-servo", daemon=True)

        start_ts = time.monotonic()
        audio_thread.start()
        servo_thread.start()

        audio_thread.join()
        servo_thread.join()
        elapsed = time.monotonic() - start_ts

        if cleanup_after_play:
            servo.cleanup()

        return elapsed


class PiperTTS:
    def __init__(self, save_dir: Optional[Path] = None) -> None:
        self.save_dir = save_dir or REPLY_AUDIO_DIR

    def synthesize_reply_audio(self, reply_text: str, output_dir: Optional[Path] = None) -> Path:
        save_dir = output_dir or self.save_dir
        os.makedirs(save_dir, exist_ok=True)
        stub_path = save_dir / DEFAULT_PIPER_STUB_FILENAME
        print("[Offline Mode] Piper TTS 동작 예정 (현재 미구현)")
        stub_path.touch(exist_ok=True)
        return stub_path

    def get_audio_duration_sec(self, audio_path: Path, reply_text: str = "") -> float:
        return _estimate_duration_from_text(reply_text)

    def play_audio_blocking(self, audio_path: Path, duration_sec: float) -> None:
        print("[Offline Mode] Piper TTS 재생 스텁 - 실제 음성은 아직 미구현")
        time.sleep(duration_sec)

    def speak_with_lipsync(
        self,
        reply_text: str,
        *,
        cleanup_after_play: bool = False,
        servo_pin: int = 33,
    ) -> float:
        if not reply_text.strip():
            return 0.0

        audio_path = self.synthesize_reply_audio(reply_text)
        duration = self.get_audio_duration_sec(audio_path, reply_text=reply_text)

        stop_event = threading.Event()
        servo = MouthServoController(pin=servo_pin)

        def _audio_worker() -> None:
            try:
                self.play_audio_blocking(audio_path, duration_sec=duration)
            finally:
                stop_event.set()

        def _servo_worker() -> None:
            try:
                servo.run_lipsync_for_duration(duration_sec=duration, stop_event=stop_event)
            except Exception as exc:
                print(f"[FaceSpeaker] servo playback failed -> fallback audio-only ({exc})")
                stop_event.set()

        audio_thread = threading.Thread(target=_audio_worker, name="piper-audio", daemon=True)
        servo_thread = threading.Thread(target=_servo_worker, name="piper-servo", daemon=True)

        start_ts = time.monotonic()
        audio_thread.start()
        servo_thread.start()

        audio_thread.join()
        servo_thread.join()
        elapsed = time.monotonic() - start_ts

        if cleanup_after_play:
            servo.cleanup()

        return elapsed


def build_tts_backend(is_online: bool, speaker: str = DEFAULT_CLOVA_SPEAKER) -> ClovaTTS | PiperTTS:
    if is_online:
        return ClovaTTS(ClovaTTSConfig(speaker=speaker))
    return PiperTTS()


def speak_with_lipsync(
    reply_text: str,
    *,
    online: bool = True,
    speaker: str = DEFAULT_CLOVA_SPEAKER,
    cleanup_after_play: bool = False,
    servo_pin: int = 33,
) -> float:
    backend = build_tts_backend(is_online=online, speaker=speaker)
    return backend.speak_with_lipsync(
        reply_text,
        cleanup_after_play=cleanup_after_play,
        servo_pin=servo_pin,
    )
