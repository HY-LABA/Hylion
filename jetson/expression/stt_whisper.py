from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4


_MODEL_CACHE: Dict[str, Any] = {}


@dataclass(frozen=True)
class STTResult:
    text: str
    language: str


def _get_model(model_size: str = "small", compute_type: str = "int8") -> Any:
    cache_key = f"{model_size}:{compute_type}"
    if cache_key in _MODEL_CACHE:
        return _MODEL_CACHE[cache_key]

    try:
        from faster_whisper import WhisperModel
    except Exception as exc:
        raise RuntimeError(
            "faster-whisper is not installed. Install it on TARGET Ubuntu environment first."
        ) from exc

    model = WhisperModel(model_size, compute_type=compute_type)
    _MODEL_CACHE[cache_key] = model
    return model


def transcribe_wav(
    wav_path: str,
    model_size: str = "small",
    language: Optional[str] = "ko",
    compute_type: str = "int8",
) -> STTResult:
    path = Path(wav_path)
    if not path.exists():
        raise FileNotFoundError(f"WAV file not found: {path}")

    model = _get_model(model_size=model_size, compute_type=compute_type)

    segments, info = model.transcribe(
        str(path),
        language=language,
        vad_filter=True,
    )

    text_parts = []
    for segment in segments:
        chunk = str(getattr(segment, "text", "")).strip()
        if chunk:
            text_parts.append(chunk)

    merged_text = " ".join(text_parts).strip()
    detected_lang = str(getattr(info, "language", language or "unknown"))

    return STTResult(text=merged_text, language=detected_lang)


def build_input_event(
    stt_result: STTResult,
    session_id: str,
    source: str = "stt",
    schema_version: str = "1.0",
    confidence: Optional[float] = None,
) -> Dict[str, Any]:
    event: Dict[str, Any] = {
        "event_id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "source": source,
        "schema_version": schema_version,
        "input_text": stt_result.text,
        "language": stt_result.language,
    }

    if confidence is not None:
        event["confidence"] = confidence

    return event
