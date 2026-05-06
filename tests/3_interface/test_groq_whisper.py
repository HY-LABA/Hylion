from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest

from jetson.core.stt.groq_whisper import GroqWhisperBackend


class _FakeTranscription:
    def __init__(self, text: str):
        self.text = text


class _FakeAudioTranscriptions:
    def __init__(self, text: str = "안녕 하이리온"):
        self._text = text
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return _FakeTranscription(self._text)


class _FakeAudio:
    def __init__(self, transcriptions: _FakeAudioTranscriptions):
        self.transcriptions = transcriptions


class _FakeGroqClient:
    def __init__(self, text: str = "안녕 하이리온"):
        self.audio = _FakeAudio(_FakeAudioTranscriptions(text=text))


def test_transcribe_calls_audio_endpoint_with_expected_args(tmp_path):
    wav_file = tmp_path / "sample.wav"
    wav_file.write_bytes(b"RIFFxxxxWAVEfake")

    fake_client = _FakeGroqClient(text="컵 집어줘")
    backend = GroqWhisperBackend(client=fake_client)

    result = backend.transcribe(str(wav_file))

    assert result.text == "컵 집어줘"
    assert result.language == "ko"

    calls = fake_client.audio.transcriptions.calls
    assert len(calls) == 1
    call = calls[0]
    assert call["model"] == "whisper-large-v3-turbo"
    assert call["language"] == "ko"
    filename, payload = call["file"]
    assert filename == "sample.wav"
    assert payload == b"RIFFxxxxWAVEfake"


def test_transcribe_per_call_language_overrides_default(tmp_path):
    wav_file = tmp_path / "sample.wav"
    wav_file.write_bytes(b"RIFFxxxxWAVE")

    fake_client = _FakeGroqClient(text="hello")
    backend = GroqWhisperBackend(client=fake_client, language="ko")

    result = backend.transcribe(str(wav_file), language="en")

    assert result.language == "en"
    assert fake_client.audio.transcriptions.calls[0]["language"] == "en"


def test_transcribe_missing_file_raises(tmp_path):
    backend = GroqWhisperBackend(client=_FakeGroqClient())
    with pytest.raises(FileNotFoundError):
        backend.transcribe(str(tmp_path / "no_such.wav"))


def test_warm_up_without_api_key_raises(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    backend = GroqWhisperBackend()
    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        backend.warm_up()


def test_factory_returns_groq_whisper_when_online():
    from jetson.core.stt.factory import build_stt_backend

    backend = build_stt_backend(online=True, language="ko")
    assert isinstance(backend, GroqWhisperBackend)
    assert backend.name == "groq-whisper-large-v3-turbo"


def test_factory_returns_local_whisper_when_offline():
    from jetson.core.stt.factory import build_stt_backend
    from jetson.core.stt.local_whisper import LocalWhisperBackend

    backend = build_stt_backend(online=False, model_size="small", language="ko")
    assert isinstance(backend, LocalWhisperBackend)
    assert backend.name == "local-whisper-small"
