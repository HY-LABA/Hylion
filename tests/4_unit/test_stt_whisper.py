from pathlib import Path
import sys
import types


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from jetson.core.stt import local_whisper
from jetson.core.stt.base import STTResult, build_input_event


class _FakeWhisperModel:
    def __init__(self, model_size: str, device: str = "cpu"):
        self.model_size = model_size
        self.device = device

    def transcribe(self, wav_path: str, language=None, fp16=False):
        assert wav_path.endswith(".wav")
        return {"text": "안녕 하이리온", "language": language or "ko"}


def test_transcribe_wav_with_mocked_model(monkeypatch, tmp_path):
    fake_module = types.ModuleType("whisper")
    fake_module.load_model = lambda model_size, device="cpu": _FakeWhisperModel(model_size, device)
    monkeypatch.setitem(sys.modules, "whisper", fake_module)
    local_whisper._MODEL_CACHE.clear()

    wav_file = tmp_path / "sample.wav"
    wav_file.write_bytes(b"RIFF....WAVE")

    result = local_whisper.transcribe_wav(
        str(wav_file), model_size="small", language="ko", device="cpu"
    )

    assert result.text == "안녕 하이리온"
    assert result.language == "ko"


def test_build_input_event_has_required_fields():
    result = STTResult(text="컵 집어줘", language="ko")
    event = build_input_event(result, session_id="sess-001")

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
