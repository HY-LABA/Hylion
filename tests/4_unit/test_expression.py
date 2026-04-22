from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from jetson.expression import microphone


class _FakeArray:
	def __init__(self, payload: bytes):
		self._payload = payload

	def tobytes(self) -> bytes:
		return self._payload


class _FakeSoundDevice:
	def __init__(self):
		self._devices = [
			{"name": "builtin mic", "max_input_channels": 1, "default_samplerate": 16000},
			{"name": "USB Audio Device", "max_input_channels": 1, "default_samplerate": microphone.DEFAULT_SAMPLE_RATE},
		]

	def query_devices(self):
		return self._devices

	def rec(self, frames, samplerate, channels, dtype, device):
		assert frames > 0
		assert samplerate == microphone.DEFAULT_SAMPLE_RATE
		assert channels == 1
		assert dtype == "int16"
		assert device == 1
		return _FakeArray(b"\x00\x00" * frames)

	def wait(self):
		return None


def test_choose_preferred_input_device_usb(monkeypatch):
	fake_sd = _FakeSoundDevice()
	monkeypatch.setitem(sys.modules, "sounddevice", fake_sd)

	selected = microphone.choose_preferred_input_device("USB")

	assert selected is not None
	assert selected.index == 1
	assert "USB" in selected.name


def test_record_to_wav_creates_file(monkeypatch, tmp_path):
	fake_sd = _FakeSoundDevice()
	monkeypatch.setitem(sys.modules, "sounddevice", fake_sd)

	output = tmp_path / "sample.wav"
	result = microphone.record_to_wav(
		output_path=str(output),
		duration_sec=1.0,
		preferred_keyword="USB",
		samplerate=microphone.DEFAULT_SAMPLE_RATE,
		channels=1,
	)

	assert result == str(output)
	assert output.exists()
	assert output.stat().st_size > 44  # WAV header + PCM data


def _samples_to_pcm16(samples):
	# Little-endian signed 16-bit PCM.
	return b"".join(int(s).to_bytes(2, byteorder="little", signed=True) for s in samples)


def test_detect_speech_segments_finds_middle_voice():
	sr = 16000
	frame_ms = 20
	frame_samples = int(sr * frame_ms / 1000)

	# 10 silence frames + 20 speech frames + 10 silence frames.
	quiet = [0] * frame_samples
	voice = [3000] * frame_samples

	all_samples = []
	for _ in range(10):
		all_samples.extend(quiet)
	for _ in range(20):
		all_samples.extend(voice)
	for _ in range(10):
		all_samples.extend(quiet)

	pcm = _samples_to_pcm16(all_samples)
	segments = microphone.detect_speech_segments(
		pcm_mono16=pcm,
		sample_rate=sr,
		frame_ms=frame_ms,
		rms_threshold=400,
		min_speech_ms=200,
		min_silence_ms=200,
	)

	assert len(segments) == 1
	start, end = segments[0]
	assert 0.15 <= start <= 0.30
	assert 0.50 <= end <= 0.80


def test_detect_speech_segments_ignores_short_noise():
	sr = 16000
	frame_ms = 20
	frame_samples = int(sr * frame_ms / 1000)

	quiet = [0] * frame_samples
	burst = [3000] * frame_samples

	# Short burst: 3 frames (=60ms), below min_speech_ms=200.
	all_samples = []
	for _ in range(8):
		all_samples.extend(quiet)
	for _ in range(3):
		all_samples.extend(burst)
	for _ in range(8):
		all_samples.extend(quiet)

	pcm = _samples_to_pcm16(all_samples)
	segments = microphone.detect_speech_segments(
		pcm_mono16=pcm,
		sample_rate=sr,
		frame_ms=frame_ms,
		rms_threshold=400,
		min_speech_ms=200,
		min_silence_ms=200,
	)

	assert segments == []
