from __future__ import annotations

from jetson.core.llm.base import LLMBackend
from jetson.core.llm.groq_llm import GroqLLMBackend
from jetson.core.llm.ollama_llm import OllamaLLMBackend


def build_llm_backend(online: bool) -> LLMBackend:
	"""Pick LLM backend based on network state.

	online → Groq llama-3.1-8b-instant (cloud, free tier).
	offline → Ollama exaone3.5:2.4b (LG Korean-native, ~1.5GB Q4_K_M, on-device).
	"""
	if online:
		return GroqLLMBackend()
	return OllamaLLMBackend()
