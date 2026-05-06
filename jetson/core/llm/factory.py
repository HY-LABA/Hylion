from __future__ import annotations

from jetson.core.llm.base import LLMBackend
from jetson.core.llm.groq_llm import GroqLLMBackend
from jetson.core.llm.offline_stub import OfflineStubLLMBackend


def build_llm_backend(online: bool) -> LLMBackend:
	"""Pick LLM backend based on network state.

	Step 3 wires Groq → online and the offline stub → offline.
	Step 5 will swap online=False to OllamaLLMBackend.
	"""
	if online:
		return GroqLLMBackend()
	return OfflineStubLLMBackend()
