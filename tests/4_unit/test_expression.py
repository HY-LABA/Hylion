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
			{"name": "USB Audio Device", "max_input_channels": 1, "default_samplerate": 48000},
		]

	def query_devices(self):
		return self._devices

	def rec(self, frames, samplerate, channels, dtype, device):
		assert frames > 0
		assert samplerate == 16000
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
		samplerate=16000,
		channels=1,
	)

	assert result == str(output)
	assert output.exists()
	assert output.stat().st_size > 44  # WAV header + PCM data
