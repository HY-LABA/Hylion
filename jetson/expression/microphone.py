from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import wave


@dataclass(frozen=True)
class AudioInputDevice:
	index: int
	name: str
	max_input_channels: int
	default_samplerate: float


def list_input_devices() -> List[AudioInputDevice]:
	"""Return available input-capable audio devices.

	This step only discovers devices. Recording is implemented in a later step.
	"""
	try:
		import sounddevice as sd
	except Exception:
		return []

	devices = []
	for idx, raw in enumerate(sd.query_devices()):
		channels = int(raw.get("max_input_channels", 0))
		if channels <= 0:
			continue

		devices.append(
			AudioInputDevice(
				index=idx,
				name=str(raw.get("name", f"device-{idx}")),
				max_input_channels=channels,
				default_samplerate=float(raw.get("default_samplerate", 16000.0)),
			)
		)

	return devices


def choose_preferred_input_device(preferred_keyword: Optional[str] = "USB") -> Optional[AudioInputDevice]:
	"""Pick a preferred input device.

	Priority:
	1) First device whose name contains preferred_keyword (case-insensitive)
	2) First available input device
	"""
	devices = list_input_devices()
	if not devices:
		return None

	if preferred_keyword:
		keyword = preferred_keyword.lower()
		for dev in devices:
			if keyword in dev.name.lower():
				return dev

	return devices[0]


def format_device_table(devices: List[AudioInputDevice]) -> str:
	if not devices:
		return "No input audio devices found"

	lines = ["index | channels | samplerate | name", "----- | -------- | ---------- | ----"]
	for dev in devices:
		lines.append(f"{dev.index} | {dev.max_input_channels} | {int(dev.default_samplerate)} | {dev.name}")
	return "\n".join(lines)


def record_to_wav(
	output_path: str,
	duration_sec: float = 3.0,
	preferred_keyword: Optional[str] = "USB",
	samplerate: int = 16000,
	channels: int = 1,
) -> str:
	"""Record fixed-duration audio and store it as 16-bit PCM WAV.

	This keeps Phase 2 simple: one-shot capture without VAD or streaming.
	"""
	if duration_sec <= 0:
		raise ValueError("duration_sec must be > 0")
	if channels <= 0:
		raise ValueError("channels must be > 0")

	device = choose_preferred_input_device(preferred_keyword=preferred_keyword)
	if device is None:
		raise RuntimeError("No input audio device available")

	try:
		import sounddevice as sd
	except Exception as exc:
		raise RuntimeError("sounddevice is not available") from exc

	frames = int(duration_sec * samplerate)
	recording = sd.rec(
		frames,
		samplerate=samplerate,
		channels=channels,
		dtype="int16",
		device=device.index,
	)
	sd.wait()

	pcm_bytes = recording.tobytes()
	path = Path(output_path)
	path.parent.mkdir(parents=True, exist_ok=True)

	with wave.open(str(path), "wb") as wf:
		wf.setnchannels(channels)
		wf.setsampwidth(2)
		wf.setframerate(samplerate)
		wf.writeframes(pcm_bytes)

	return str(path)
