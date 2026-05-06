from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from jetson.core.llm.prompt import build_action_json_from_stt


@dataclass(frozen=True)
class GroqCallResult:
	ok: bool
	content: str
	error: Optional[str] = None


class GroqClient:
	"""Thin Groq API wrapper with timeout/retry policy."""

	def __init__(self, client: Optional[Any] = None) -> None:
		self._client = client

	def _get_or_create_client(self) -> Optional[Any]:
		if self._client is not None:
			return self._client

		if not os.getenv("GROQ_API_KEY"):
			return None

		try:
			from groq import Groq
		except Exception:
			return None

		self._client = Groq()
		return self._client

	def request_chat_completion(
		self,
		# parameters
		system_prompt: str,
		user_text: str,
		model: str = "llama-3.1-8b-instant",
		temperature: float = 0.2,
		retries: int = 2,
		retry_delay_sec: float = 0.4,
		timeout_sec: Optional[float] = 15.0,
		json_mode: bool = True,
		history: Optional[List[Dict[str, str]]] = None,
	) -> GroqCallResult:
		client = self._get_or_create_client()
		if client is None:
			return GroqCallResult(ok=False, content="", error="groq_client_unavailable")

		messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
		if history:
			messages.extend(history)
		messages.append({"role": "user", "content": user_text})

		last_error: Optional[str] = None
		max_attempts = max(1, retries + 1)

		for attempt in range(max_attempts):
			try:
				kwargs = {
					"model": model,
					"messages": messages,
					"temperature": temperature,
				}
				if json_mode:
					kwargs["response_format"] = {"type": "json_object"}
				if timeout_sec is not None:
					kwargs["timeout"] = timeout_sec

				response = client.chat.completions.create(**kwargs)
				content = response.choices[0].message.content or ""
				return GroqCallResult(ok=True, content=str(content))
			except Exception as exc:
				last_error = str(exc)
				if attempt < (max_attempts - 1):
					time.sleep(retry_delay_sec)

		return GroqCallResult(ok=False, content="", error=last_error or "groq_call_failed")


class GroqLLMBackend:
	"""LLMBackend adapter that emits ACTION_JSON dicts via GroqClient."""

	def __init__(self, model: str = "llama-3.1-8b-instant", client: Optional[GroqClient] = None) -> None:
		self.name = f"groq-{model}"
		self._model = model
		self._client = client or GroqClient()

	def warm_up(self) -> None:
		probe = self._client.request_chat_completion(
			system_prompt='Return JSON only: {"ok": true}',
			user_text="연결 점검",
			retries=0,
			retry_delay_sec=0.0,
			timeout_sec=10.0,
			json_mode=True,
		)
		if not probe.ok:
			raise RuntimeError(f"Groq API connection failed: {probe.error}")

	def build_action(
		self,
		stt_text: str,
		*,
		session_id: str,
		history: List[Dict[str, str]],
		in_chat_mode: bool,
	) -> Dict[str, Any]:
		return build_action_json_from_stt(
			client=self._client,
			stt_text=stt_text,
			session_id=session_id,
			history=history,
			in_chat_mode=in_chat_mode,
		)
