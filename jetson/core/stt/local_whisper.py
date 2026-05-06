from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from jetson.core.stt.base import STTResult


_MODEL_CACHE: Dict[str, Any] = {}

# Defaults tuned for Jetson with CUDA available. On startup we try GPU first,
# then fall back to CPU if CUDA isn't available so the pipeline still works on
# developer laptops. compute_type is kept as a parameter for API compatibility:
# "float16" → fp16 path on GPU (default openai-whisper behavior on cuda),
# "int8" / others → fp32 path (openai-whisper does not support int8 quantization).
DEFAULT_MODEL_SIZE = "small"
DEFAULT_DEVICE = "cuda"
DEFAULT_COMPUTE_TYPE = "float16"
CPU_FALLBACK_COMPUTE_TYPE = "int8"


def _get_model(
    model_size: str = DEFAULT_MODEL_SIZE,
    compute_type: str = DEFAULT_COMPUTE_TYPE,
    device: str = DEFAULT_DEVICE,
) -> Any:
    cache_key = f"{model_size}:{device}"
    if cache_key in _MODEL_CACHE:
        return _MODEL_CACHE[cache_key]

    try:
        import whisper
    except Exception as exc:
        raise RuntimeError(
            "openai-whisper is not installed. Install it on TARGET Ubuntu environment first."
        ) from exc

    try:
        model = whisper.load_model(model_size, device=device)
        print(f"[STT] loaded openai-whisper '{model_size}' on {device} ({compute_type})")
    except Exception as exc:
        if device == "cpu":
            raise
        print(f"[STT] {device} unavailable ({exc}); falling back to cpu")
        cache_key = f"{model_size}:cpu"
        if cache_key in _MODEL_CACHE:
            return _MODEL_CACHE[cache_key]
        model = whisper.load_model(model_size, device="cpu")
        print(f"[STT] loaded openai-whisper '{model_size}' on cpu ({CPU_FALLBACK_COMPUTE_TYPE})")

    _MODEL_CACHE[cache_key] = model
    return model


def warm_up(
    model_size: str = DEFAULT_MODEL_SIZE,
    compute_type: str = DEFAULT_COMPUTE_TYPE,
    device: str = DEFAULT_DEVICE,
) -> None:
    """Eagerly load the whisper model so the first transcribe_wav call is fast."""
    _get_model(model_size=model_size, compute_type=compute_type, device=device)


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

    use_fp16 = compute_type == "float16" and getattr(model, "device", None) is not None and "cuda" in str(model.device)
    result = model.transcribe(
        str(path),
        language=language,
        fp16=use_fp16,
    )

    merged_text = str(result.get("text", "")).strip()
    detected_lang = str(result.get("language", language or "unknown"))

    return STTResult(text=merged_text, language=detected_lang)


class LocalWhisperBackend:
    """STTBackend wrapping openai-whisper. CUDA when available, CPU fallback."""

    def __init__(
        self,
        model_size: str = DEFAULT_MODEL_SIZE,
        language: str = "ko",
        compute_type: str = DEFAULT_COMPUTE_TYPE,
        device: str = DEFAULT_DEVICE,
    ) -> None:
        self.name = f"local-whisper-{model_size}"
        self._model_size = model_size
        self._language = language
        self._compute_type = compute_type
        self._device = device

    def warm_up(self) -> None:
        warm_up(model_size=self._model_size, compute_type=self._compute_type, device=self._device)

    def transcribe(self, wav_path: str, *, language: Optional[str] = None) -> STTResult:
        return transcribe_wav(
            wav_path,
            model_size=self._model_size,
            language=language or self._language,
            compute_type=self._compute_type,
            device=self._device,
        )
