from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math
from typing import List, Optional, Tuple
import wave


DEFAULT_SAMPLE_RATE = 44100
DEFAULT_CHANNELS = 1
DEFAULT_SAMPLE_WIDTH_BYTES = 2


def _pcm16_to_samples(pcm_bytes: bytes) -> List[int]:
	if len(pcm_bytes) % 2 != 0:
		raise ValueError("PCM16 byte length must be even")
	return [int.from_bytes(pcm_bytes[i : i + 2], byteorder="little", signed=True) for i in range(0, len(pcm_bytes), 2)]


def _samples_to_pcm16(samples: List[int]) -> bytes:
	return b"".join(int(s).to_bytes(2, byteorder="little", signed=True) for s in samples)


def _rms_pcm16(pcm_bytes: bytes) -> int:
	samples = _pcm16_to_samples(pcm_bytes)
	if not samples:
		return 0
	mean_square = sum(s * s for s in samples) / len(samples)
	return int(math.sqrt(mean_square))


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
				default_samplerate=float(raw["default_samplerate"]),
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


def _write_wav(path: Path, pcm_bytes: bytes, samplerate: int, channels: int) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)

	with wave.open(str(path), "wb") as wf:
		wf.setnchannels(channels)
		wf.setsampwidth(DEFAULT_SAMPLE_WIDTH_BYTES)
		wf.setframerate(samplerate)
		wf.writeframes(pcm_bytes)


def record_to_wav(
	output_path: str,
	# parameters
	duration_sec: float = 3.0,
	preferred_keyword: Optional[str] = "USB",
	samplerate: int = DEFAULT_SAMPLE_RATE,
	channels: int = DEFAULT_CHANNELS,
) -> str:
	"""Record fixed-duration audio and store it as 16-bit PCM WAV."""
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

	path = Path(output_path)
	_write_wav(path, recording.tobytes(), samplerate, channels)

	return str(path)


def read_wav_mono16(input_path: str) -> Tuple[bytes, int]:
	"""Read WAV and return mono 16-bit PCM bytes with samplerate."""
	with wave.open(str(input_path), "rb") as wf:
		channels = wf.getnchannels()
		sample_width = wf.getsampwidth()
		sample_rate = wf.getframerate()
		frames = wf.readframes(wf.getnframes())

	if sample_width != DEFAULT_SAMPLE_WIDTH_BYTES:
		raise ValueError("Only 16-bit PCM WAV is supported")

	if channels == 1:
		return frames, sample_rate

	# Convert multi-channel PCM to mono for simple VAD scoring.
	if channels != 2:
		raise ValueError("Only mono/stereo WAV is supported")

	samples = _pcm16_to_samples(frames)
	mono_samples = []
	for i in range(0, len(samples), 2):
		mono_samples.append(int((samples[i] + samples[i + 1]) / 2))

	return _samples_to_pcm16(mono_samples), sample_rate


def detect_speech_segments(
	pcm_mono16: bytes,
	sample_rate: int,
	frame_ms: int = 30,
	rms_threshold: int = 400,
	min_speech_ms: int = 250,
	min_silence_ms: int = 300,
) -> List[Tuple[float, float]]:
	"""Return [(start_sec, end_sec)] speech segments by RMS threshold.

	This is a lightweight VAD policy used for Phase 2 before Whisper integration.
	"""
	if sample_rate <= 0:
		raise ValueError("sample_rate must be > 0")
	if frame_ms <= 0:
		raise ValueError("frame_ms must be > 0")

	bytes_per_sample = DEFAULT_SAMPLE_WIDTH_BYTES
	frame_samples = int(sample_rate * frame_ms / 1000)
	frame_bytes = frame_samples * bytes_per_sample
	if frame_bytes <= 0:
		return []

	min_speech_frames = max(1, int(min_speech_ms / frame_ms))
	min_silence_frames = max(1, int(min_silence_ms / frame_ms))

	segments: List[Tuple[float, float]] = []
	in_speech = False
	speech_start_frame = 0
	speech_frames = 0
	silence_run = 0

	total_frames = len(pcm_mono16) // frame_bytes
	for i in range(total_frames):
		chunk = pcm_mono16[i * frame_bytes : (i + 1) * frame_bytes]
		rms = _rms_pcm16(chunk)
		is_speech = rms >= rms_threshold

		if is_speech:
			if not in_speech:
				in_speech = True
				speech_start_frame = i
				speech_frames = 0
				silence_run = 0
			speech_frames += 1
			silence_run = 0
		elif in_speech:
			silence_run += 1
			if silence_run >= min_silence_frames:
				if speech_frames >= min_speech_frames:
					start_sec = (speech_start_frame * frame_samples) / sample_rate
					end_frame = speech_start_frame + speech_frames
					end_sec = (end_frame * frame_samples) / sample_rate
					segments.append((start_sec, end_sec))
				in_speech = False
				speech_frames = 0
				silence_run = 0

	if in_speech and speech_frames >= min_speech_frames:
		start_sec = (speech_start_frame * frame_samples) / sample_rate
		end_frame = speech_start_frame + speech_frames
		end_sec = (end_frame * frame_samples) / sample_rate
		segments.append((start_sec, end_sec))

	return segments
