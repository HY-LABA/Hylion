from pathlib import Path
import sys
import types


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from jetson.expression import stt_whisper


class _FakeSegment:
    def __init__(self, text: str):
        self.text = text


class _FakeInfo:
    def __init__(self, language: str):
        self.language = language


class _FakeWhisperModel:
    def __init__(self, model_size: str, compute_type: str = "int8"):
        self.model_size = model_size
        self.compute_type = compute_type

    def transcribe(self, wav_path: str, language=None, vad_filter=True):
        assert wav_path.endswith(".wav")
        assert vad_filter is True
        segments = [_FakeSegment("안녕"), _FakeSegment("하이리온")]
        info = _FakeInfo(language or "ko")
        return segments, info


def test_transcribe_wav_with_mocked_model(monkeypatch, tmp_path):
    fake_module = types.ModuleType("faster_whisper")
    fake_module.WhisperModel = _FakeWhisperModel
    monkeypatch.setitem(sys.modules, "faster_whisper", fake_module)

    wav_file = tmp_path / "sample.wav"
    wav_file.write_bytes(b"RIFF....WAVE")

    result = stt_whisper.transcribe_wav(str(wav_file), model_size="small", language="ko")

    assert result.text == "안녕 하이리온"
    assert result.language == "ko"


def test_build_input_event_has_required_fields():
    result = stt_whisper.STTResult(text="컵 집어줘", language="ko")
    event = stt_whisper.build_input_event(result, session_id="sess-001")

    required = [
        "event_id",
        "timestamp",
        "session_id",
        "source",
        "schema_version",
        "input_text",
        "language",
    ]
    for key in required:
        assert key in event

    assert event["session_id"] == "sess-001"
    assert event["input_text"] == "컵 집어줘"
    assert event["source"] == "stt"
