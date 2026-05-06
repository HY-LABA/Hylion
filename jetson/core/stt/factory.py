from __future__ import annotations

from jetson.core.stt.base import STTBackend
from jetson.core.stt.local_whisper import DEFAULT_MODEL_SIZE, LocalWhisperBackend


def build_stt_backend(
    online: bool,
    *,
    model_size: str = DEFAULT_MODEL_SIZE,
    language: str = "ko",
) -> STTBackend:
    """Pick STT backend based on network state.

    Step 3 returns LocalWhisperBackend on both branches so behavior matches the
    pre-refactor pipeline. Step 4 will swap online=True to GroqWhisperBackend.
    """
    # online branch will be replaced by GroqWhisperBackend in step 4.
    return LocalWhisperBackend(model_size=model_size, language=language)
