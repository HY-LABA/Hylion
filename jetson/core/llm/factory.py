from __future__ import annotations

from jetson.core.llm.base import LLMBackend
from jetson.core.llm.groq_llm import GroqLLMBackend
from jetson.core.llm.ollama_llm import OllamaLLMBackend


def build_llm_backend(online: bool) -> LLMBackend:
	"""Pick LLM backend based on network state.

	online → Groq llama-3.1-8b-instant (cloud, free tier).
	offline → Ollama qwen2.5:1.5b-instruct (on-device, JSON-mode constrained).
	"""
	if online:
		return GroqLLMBackend()
	return OllamaLLMBackend()
