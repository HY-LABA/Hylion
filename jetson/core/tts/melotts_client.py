"""HTTP client for the MeloTTS daemon (services/tts_server/server.py).

Lives in Hylion's main venv (torch 2.5). Talks to the daemon over loopback HTTP
so coordinator never imports heavy ML libs that need torch 2.8 / torchaudio.
Same speak_with_lipsync(...) signature as expression.speaker.Speaker so the
coordinator can swap backends transparently via build_tts_backend().
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import subprocess
import threading
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)


# parameters
DEFAULT_HOST = os.getenv("HYLION_TTS_HOST", "http://127.0.0.1:8001")
DEFAULT_TIMEOUT_SEC = 30.0
DEFAULT_REPLY_DIR = Path(__file__).resolve().parents[3] / "data" / "reply"


def _ensure_reply_dir() -> Path:
	candidates = [DEFAULT_REPLY_DIR, Path("/tmp/hylion_reply")]
	for cand in candidates:
		try:
			cand.mkdir(parents=True, exist_ok=True)
			probe = cand / ".write_test"
			probe.touch(); probe.unlink()
			return cand
		except Exception:
			continue
	fallback = Path("/tmp/hylion_reply")
	fallback.mkdir(parents=True, exist_ok=True)
	return fallback


def _wav_duration_sec(wav_path: str) -> float:
	with contextlib.closing(wave.open(wav_path, "rb")) as fh:
		frames = fh.getnframes()
		rate = fh.getframerate()
		return frames / float(rate) if rate else 0.0


def _play_wav_blocking(wav_path: str, pulse_sink: Optional[str] = None) -> bool:
	if not Path(wav_path).exists():
		logger.error("audio file not found: %s", wav_path)
		return False
	env = os.environ.copy()
	if pulse_sink and pulse_sink != "default":
		env["PULSE_SINK"] = pulse_sink
	try:
		result = subprocess.run(
			["aplay", "-q", wav_path],
			capture_output=True,
			timeout=300,
			env=env,
		)
		if result.returncode != 0:
			logger.error("aplay failed: %s", result.stderr.decode(errors="replace"))
			return False
		return True
	except FileNotFoundError:
		logger.error("aplay not installed (apt install alsa-utils)")
		return False
	except subprocess.TimeoutExpired:
		logger.error("aplay timed out")
		return False


def _find_usb_audio_sink() -> Optional[str]:
	try:
		result = subprocess.run(
			["pactl", "list", "short", "sinks"],
			capture_output=True,
			text=True,
			timeout=5,
		)
		if result.returncode != 0:
			return None
		for line in result.stdout.strip().splitlines():
			parts = line.split("\t")
			if len(parts) >= 2 and "usb" in parts[1].lower():
				return parts[1]
	except Exception:
		return None
	return None


class MeloTTSSpeaker:
	"""TTS backend that fetches WAV from the local MeloTTS daemon.

	Mirrors expression.speaker.Speaker.speak_with_lipsync(...) so it can be a
	drop-in replacement when build_tts_backend(is_online=False) is selected.
	"""

	def __init__(
		self,
		host: str = DEFAULT_HOST,
		timeout_sec: float = DEFAULT_TIMEOUT_SEC,
		device: str = "default",
		enable_lipsync: bool = True,
	) -> None:
		self.host = host.rstrip("/")
		self.timeout_sec = timeout_sec
		self.enable_lipsync = enable_lipsync
		self._reply_dir = _ensure_reply_dir()
		usb = _find_usb_audio_sink()
		self.device = usb or device
		self.last_audio_file: Optional[str] = None
		logger.info("MeloTTSSpeaker initialized (host=%s, sink=%s)", self.host, self.device)

	def _post_synthesize(self, text: str, speed: float = 1.0) -> Optional[bytes]:
		body = json.dumps({"text": text, "speed": speed}).encode("utf-8")
		req = urllib.request.Request(
			f"{self.host}/synthesize",
			data=body,
			headers={"Content-Type": "application/json"},
			method="POST",
		)
		try:
			with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
				return resp.read()
		except urllib.error.URLError as exc:
			logger.error("MeloTTS daemon unreachable: %s", exc)
			return None
		except Exception as exc:
			logger.error("MeloTTS request failed: %s", exc)
			return None

	def warm_up(self, timeout_sec: float = 60.0) -> bool:
		"""Tell daemon to load the model now (blocking). Idempotent.

		Coordinator calls this in offline mode at startup so the first user-
		facing turn doesn't pay the ~22s cold-load cost. In online mode it is
		intentionally NOT called so the daemon stays at ~40 MB.
		"""
		req = urllib.request.Request(
			f"{self.host}/warmup",
			data=b"",
			headers={"Content-Type": "application/json"},
			method="POST",
		)
		try:
			with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
				body = resp.read().decode("utf-8")
			logger.info("MeloTTS daemon warm-up: %s", body)
			return True
		except urllib.error.URLError as exc:
			logger.error("MeloTTS warm-up failed (daemon unreachable): %s", exc)
			return False
		except Exception as exc:
			logger.error("MeloTTS warm-up failed: %s", exc)
			return False

	def unload(self, timeout_sec: float = 5.0) -> bool:
		"""Tell daemon to drop model references. PyTorch's allocator caches host
		RAM so RSS doesn't fully fall — this mostly clears CUDA cache. To fully
		reclaim RAM, restart the daemon (systemctl restart hylion-tts)."""
		req = urllib.request.Request(
			f"{self.host}/unload",
			data=b"",
			headers={"Content-Type": "application/json"},
			method="POST",
		)
		try:
			with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
				body = resp.read().decode("utf-8")
			logger.info("MeloTTS daemon unload: %s", body)
			return True
		except Exception as exc:
			logger.error("MeloTTS unload failed: %s", exc)
			return False

	def synthesize_reply_audio(
		self,
		reply_text: str,
		# remaining kwargs accepted for parity with Speaker; mostly Clova-specific.
		speaker: Optional[str] = None,
		voice: Optional[str] = None,
		pitch: Optional[int] = None,
		rate: Optional[int] = None,
		speed: Optional[int] = None,
		volume: Optional[int] = None,
		audio_format: Optional[str] = None,
		emotion: Optional[int] = None,
		emotion_strength: Optional[int] = None,
	) -> Optional[str]:
		if not reply_text or not reply_text.strip():
			return None

		# Map Clova-style speed (-5..+5) to MeloTTS multiplier (0.5..2.0).
		# Default 1.0 if not provided.
		melo_speed = 1.0
		if isinstance(speed, (int, float)) and speed != 0:
			melo_speed = max(0.5, min(2.0, 1.0 + float(speed) * 0.05))

		audio_bytes = self._post_synthesize(reply_text, speed=melo_speed)
		if not audio_bytes:
			return None

		ts_ms = int(time.time() * 1000)
		out_path = self._reply_dir / f"reply_{ts_ms}.wav"
		out_path.write_bytes(audio_bytes)
		self.last_audio_file = str(out_path)
		logger.info("offline TTS saved: %s (%d bytes)", out_path, len(audio_bytes))
		return str(out_path)

	def get_audio_duration_sec(self, audio_file: str) -> float:
		try:
			return _wav_duration_sec(audio_file)
		except Exception as exc:
			logger.warning("duration probe failed: %s", exc)
			return 0.0

	def play_audio_blocking(self, audio_file: str) -> bool:
		return _play_wav_blocking(audio_file, pulse_sink=self.device)

	def speak_with_lipsync(
		self,
		reply_text: str,
		mouth_servo=None,
		speaker: Optional[str] = None,
		voice: Optional[str] = None,
		pitch: Optional[int] = None,
		rate: Optional[int] = None,
		speed: Optional[int] = None,
		volume: Optional[int] = None,
		audio_format: Optional[str] = None,
		emotion: Optional[int] = None,
		emotion_strength: Optional[int] = None,
	) -> float:
		if not reply_text or not reply_text.strip():
			return 0.0

		start = time.time()
		audio_file = self.synthesize_reply_audio(
			reply_text=reply_text,
			speaker=speaker, voice=voice, pitch=pitch, rate=rate, speed=speed,
			volume=volume, audio_format=audio_format, emotion=emotion,
			emotion_strength=emotion_strength,
		)
		if not audio_file:
			# Fallback: estimate duration from text length so the servo at least moves.
			est = len(reply_text) / 10.0
			time.sleep(est)
			return time.time() - start

		duration = self.get_audio_duration_sec(audio_file)
		if duration <= 0:
			duration = len(reply_text) / 10.0

		lipsync_thread = None
		if self.enable_lipsync and mouth_servo is not None:
			try:
				stop_event = threading.Event()
				lipsync_thread = threading.Thread(
					target=mouth_servo.run_lipsync_for_duration,
					args=(duration, stop_event),
					daemon=True,
				)
				lipsync_thread.start()
			except Exception as exc:
				logger.warning("lipsync thread failed to start: %s", exc)
				lipsync_thread = None

		self.play_audio_blocking(audio_file)

		if lipsync_thread and lipsync_thread.is_alive():
			lipsync_thread.join(timeout=duration + 1.0)

		return time.time() - start
