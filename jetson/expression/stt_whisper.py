from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4


_MODEL_CACHE: Dict[str, Any] = {}

# parameters: defaults tuned for Jetson with CUDA available.
# On startup we try GPU float16 first, then fall back to CPU int8 if CUDA / cuDNN
# isn't available so the pipeline still works on developer laptops.
DEFAULT_MODEL_SIZE = "base"
DEFAULT_DEVICE = "cuda"
DEFAULT_COMPUTE_TYPE = "float16"
CPU_FALLBACK_COMPUTE_TYPE = "int8"


@dataclass(frozen=True)
class STTResult:
    text: str
    language: str


def _get_model(
    model_size: str = DEFAULT_MODEL_SIZE,
    compute_type: str = DEFAULT_COMPUTE_TYPE,
    device: str = DEFAULT_DEVICE,
) -> Any:
    cache_key = f"{model_size}:{compute_type}:{device}"
    if cache_key in _MODEL_CACHE:
        return _MODEL_CACHE[cache_key]

    try:
        from faster_whisper import WhisperModel
    except Exception as exc:
        raise RuntimeError(
            "faster-whisper is not installed. Install it on TARGET Ubuntu environment first."
        ) from exc

    try:
        model = WhisperModel(model_size, device=device, compute_type=compute_type)
        print(f"[STT] loaded faster-whisper '{model_size}' on {device} ({compute_type})")
    except Exception as exc:
        if device == "cpu" and compute_type == CPU_FALLBACK_COMPUTE_TYPE:
            raise
        print(f"[STT] {device}/{compute_type} unavailable ({exc}); falling back to cpu/{CPU_FALLBACK_COMPUTE_TYPE}")
        cache_key = f"{model_size}:{CPU_FALLBACK_COMPUTE_TYPE}:cpu"
        if cache_key in _MODEL_CACHE:
            return _MODEL_CACHE[cache_key]
        model = WhisperModel(model_size, device="cpu", compute_type=CPU_FALLBACK_COMPUTE_TYPE)
        print(f"[STT] loaded faster-whisper '{model_size}' on cpu ({CPU_FALLBACK_COMPUTE_TYPE})")

    _MODEL_CACHE[cache_key] = model
    return model


def transcribe_wav(
    wav_path: str,
    model_size: str = DEFAULT_MODEL_SIZE,
    language: Optional[str] = "ko",
    compute_type: str = DEFAULT_COMPUTE_TYPE,
    device: str = DEFAULT_DEVICE,
) -> STTResult:
    path = Path(wav_path)
    if not path.exists():
        raise FileNotFoundError(f"WAV file not found: {path}")

    model = _get_model(model_size=model_size, compute_type=compute_type, device=device)

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
