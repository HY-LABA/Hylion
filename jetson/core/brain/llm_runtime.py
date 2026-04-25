import os
from dataclasses import dataclass
from typing import Optional, Any


@dataclass
class RuntimeHandles:
    online_client: Optional[Any]
    offline_client: Optional[Any]


class LLMRuntime:
    """Loads online/offline LLM handles once at startup."""

    def __init__(self) -> None:
        self._online_client = None
        self._offline_client = None

    def initialize(self) -> RuntimeHandles:
        self._online_client = self._init_groq_client()
        self._offline_client = self._init_offline_client()
        return RuntimeHandles(
            online_client=self._online_client,
            offline_client=self._offline_client,
        )

    def _init_groq_client(self) -> Optional[Any]:
        if not os.getenv("GROQ_API_KEY"):
            return None

        try:
            from groq import Groq  # Imported lazily to avoid hard dependency at startup.

            return Groq()
        except Exception:
            return None

    def _init_offline_client(self) -> Optional[Any]:
        # Placeholder for future on-device model loading.
        # Example: llama.cpp, vLLM, or local runtime wrapper.
        return None
