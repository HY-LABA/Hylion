from __future__ import annotations

from jetson.core.stt.base import STTBackend
from jetson.core.stt.groq_whisper import GroqWhisperBackend
from jetson.core.stt.local_whisper import DEFAULT_MODEL_SIZE, LocalWhisperBackend


def build_stt_backend(
    online: bool,
    *,
    model_size: str = DEFAULT_MODEL_SIZE,
    language: str = "ko",
) -> STTBackend:
    """Pick STT backend based on network state.

    online → Groq whisper-large-v3-turbo (cloud, ~216x realtime, free tier).
    offline → openai-whisper local (CUDA → CPU fallback).
    """
    if online:
        return GroqWhisperBackend(language=language)
    return LocalWhisperBackend(model_size=model_size, language=language)
