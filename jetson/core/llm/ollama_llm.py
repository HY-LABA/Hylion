from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional
from urllib import error as urlerror
from urllib import request as urlrequest

from jetson.core.llm.prompt import (
	OFFLINE_SYSTEM_PROMPT,
	assemble_action,
	offline_action_json,
)


# Default Ollama daemon listens on localhost; override via env if a separate
# host is used. We don't expect a remote host in Hylion since the daemon runs
# on the same Jetson, but keep the hook for testability.
DEFAULT_OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
DEFAULT_OLLAMA_MODEL = "qwen2.5:1.5b-instruct"
DEFAULT_TIMEOUT_SEC = 30.0
# Force every transformer layer onto the GPU. EXAONE 3.5 2.4B has 30 layers;
# ollama's auto-offload left 6 on the CPU even with free VRAM, costing ~10–20%
# of inference time. Override via env if a smaller model fits this default but
# a larger one needs partial CPU offload.
DEFAULT_NUM_GPU_LAYERS = int(os.getenv("HYLION_OLLAMA_NUM_GPU", "999"))

class OllamaLLMBackend:
	"""LLMBackend that talks to a local Ollama daemon over HTTP.

	Uses /api/chat with format='json' so the model is constrained to emit a
	single JSON object that we then validate against action.schema.json.
	"""

	def __init__(
		self,
		model: str = DEFAULT_OLLAMA_MODEL,
		host: str = DEFAULT_OLLAMA_HOST,
		timeout_sec: float = DEFAULT_TIMEOUT_SEC,
		num_ctx: int = 1536,
		num_predict: int = 80,
		temperature: float = 0.0,
	) -> None:
		self.name = f"ollama-{model}"
		self._model = model
		self._host = host.rstrip("/")
		self._timeout_sec = timeout_sec
		self._num_ctx = num_ctx
		self._num_predict = num_predict
		self._temperature = temperature

	def warm_up(self) -> None:
		"""Pre-load model + system-prompt KV cache so the first real turn is fast.

		Ollama's default keep_alive is 5 min, which can expire during wake-word
		standby — pinning to 30 min keeps the model resident across that gap.
		Passing the real system prompt and format=json front-loads prefill and
		json-grammar setup that would otherwise hit the first user turn.
		"""
		body = {
			"model": self._model,
			"messages": [
				{"role": "system", "content": OFFLINE_SYSTEM_PROMPT},
				{"role": "user", "content": "ok"},
			],
			"stream": False,
			"format": "json",
			"keep_alive": "30m",
			"options": {
				"num_ctx": self._num_ctx,
				"num_predict": 1,
				"temperature": 0.0,
				"num_gpu": DEFAULT_NUM_GPU_LAYERS,
			},
		}
		# A successful 200 response is enough; we don't care about the content.
		self._post_json("/api/chat", body)

	def build_action(
		self,
		stt_text: str,
		*,
		session_id: str,
		history: List[Dict[str, str]],
		in_chat_mode: bool,
	) -> Dict[str, Any]:
		messages: List[Dict[str, str]] = [{"role": "system", "content": OFFLINE_SYSTEM_PROMPT}]
		if history:
			messages.extend(history)
		messages.append({"role": "user", "content": stt_text})

		body = {
			"model": self._model,
			"messages": messages,
			"stream": False,
			"format": "json",
			"keep_alive": "30m",
			"options": {
				"temperature": self._temperature,
				"num_ctx": self._num_ctx,
				"num_predict": self._num_predict,
				"num_gpu": DEFAULT_NUM_GPU_LAYERS,
			},
		}

		try:
			response = self._post_json("/api/chat", body)
		except Exception as exc:
			print(f"[OllamaLLM] request failed: {exc}")
			return offline_action_json(session_id, "ollama_request_failed")

		content = ""
		if isinstance(response, dict):
			message = response.get("message")
			if isinstance(message, dict):
				content = str(message.get("content", "") or "")

		if not content:
			print("[OllamaLLM] empty response content")
			return offline_action_json(session_id, "ollama_empty_content")

		# extract_core -> apply_hard_overrides -> derive_full_action -> validate,
		# all behind one call; assemble_action never raises.
		return assemble_action(
			content,
			stt_text=stt_text,
			session_id=session_id,
			network_online=False,
			fallback_policy="ollama",
		)

	def _post_json(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
		url = f"{self._host}{path}"
		data = json.dumps(body, ensure_ascii=False).encode("utf-8")
		req = urlrequest.Request(
			url,
			data=data,
			headers={"Content-Type": "application/json"},
			method="POST",
		)
		try:
			with urlrequest.urlopen(req, timeout=self._timeout_sec) as resp:
				payload = resp.read()
		except urlerror.URLError as exc:
			raise RuntimeError(f"ollama_unreachable: {exc}") from exc

		try:
			return json.loads(payload.decode("utf-8"))
		except Exception as exc:
			raise RuntimeError(f"ollama_invalid_json_response: {exc}") from exc
