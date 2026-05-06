from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from jetson.core.stt.base import STTResult


# whisper-large-v3-turbo: ~216x realtime on Groq, $0.04/hour, Korean accuracy
# practically identical to whisper-large-v3 in our use range. See doc 10 §F1.
DEFAULT_GROQ_WHISPER_MODEL = "whisper-large-v3-turbo"


class GroqWhisperBackend:
    """STTBackend that calls Groq's audio.transcriptions API.

    Uses the same GROQ_API_KEY as the LLM backend; STT and LLM are billed/rate-
    limited as separate buckets so they don't compete for the same quota.
    """

    def __init__(
        self,
        model: str = DEFAULT_GROQ_WHISPER_MODEL,
        language: str = "ko",
        client: Optional[Any] = None,
        timeout_sec: float = 30.0,
    ) -> None:
        self.name = f"groq-{model}"
        self._model = model
        self._language = language
        self._client = client
        self._timeout_sec = timeout_sec

    def _get_or_create_client(self) -> Any:
        if self._client is not None:
            return self._client

        if not os.getenv("GROQ_API_KEY"):
            raise RuntimeError("GROQ_API_KEY not set; cannot use Groq Whisper backend")

        try:
            from groq import Groq
        except Exception as exc:
            raise RuntimeError("groq SDK not installed") from exc

        self._client = Groq()
        return self._client

    def warm_up(self) -> None:
        # Nothing to load; just confirm the SDK + API key are available.
        self._get_or_create_client()

    def transcribe(self, wav_path: str, *, language: Optional[str] = None) -> STTResult:
        path = Path(wav_path)
        if not path.exists():
            raise FileNotFoundError(f"WAV file not found: {path}")

        client = self._get_or_create_client()
        lang = language or self._language

        with path.open("rb") as fh:
            transcription = client.audio.transcriptions.create(
                file=(path.name, fh.read()),
                model=self._model,
                language=lang,
                timeout=self._timeout_sec,
            )

        text = str(getattr(transcription, "text", "") or "").strip()
        return STTResult(text=text, language=lang)
