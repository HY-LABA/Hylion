from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib import error as urlerror
from urllib import request as urlrequest
from uuid import uuid4

from jetson.core.llm.prompt import (
	_apply_conversation_policy,
	_offline_action_json,
	_parse_and_validate_action_json,
)


# Default Ollama daemon listens on localhost; override via env if a separate
# host is used. We don't expect a remote host in Hylion since the daemon runs
# on the same Jetson, but keep the hook for testability.
DEFAULT_OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
DEFAULT_OLLAMA_MODEL = "exaone3.5:2.4b"
DEFAULT_TIMEOUT_SEC = 30.0

# Slim system prompt tuned for small on-device models (EXAONE 2.4B). The full
# schema is intentionally NOT injected — it ~doubles prompt size and small
# models tend to copy schema field names verbatim into output. Required-field
# coverage is checked downstream by jsonschema; cross-field consistency is
# enforced by _apply_conversation_policy regardless of model fidelity.
OLLAMA_SLIM_SYSTEM_PROMPT = (
	"너는 키 1미터의 귀여운 파란색 사자 휴머노이드 로봇 하이리온이야. "
	"사용자 발화를 듣고 반드시 아래 JSON 객체 하나만 출력해. 마크다운/설명 금지.\n\n"
	"[필수 출력 필드 — 이것만 출력]\n"
	"- intent: chat | pick_place | move | stop | standby | unknown\n"
	"- target_object: 잡으려는 물체명 또는 \"none\"\n"
	"- reply_text: 7살 어린 남자아이 말투 한국어 1~2문장\n"
	"- requires_smolvla: true (intent=pick_place) / false\n"
	"- requires_bhl: true (intent=move 또는 stop) / false\n"
	"- gait_cmd: walk_forward | walk_back | turn_left | turn_right | stop | none\n"
	"- state_current: IDLE | TALKING | WALKING | PICKING\n"
	"- safety_allowed: true / false\n\n"
	"[규칙]\n"
	"- intent=pick_place → requires_smolvla=true, requires_bhl=false, gait_cmd=none\n"
	"- intent=move → requires_smolvla=false, requires_bhl=true, gait_cmd 지정\n"
	"- intent=stop → requires_smolvla=false, requires_bhl=true, gait_cmd=stop\n"
	"- intent=chat → requires_smolvla=false, requires_bhl=false, gait_cmd=none\n"
	"- intent=standby → 모두 false/none, state_current=IDLE\n"
	"- 사용자가 대화 종료 의도(쉬어/수고/휴식 등)면 intent=standby\n"
	"- \"멈춰\" → intent=stop\n"
	"- 의미 불명 → intent=unknown, reply_text=\"무슨 말인지 잘 모르겠어요. 다시 말씀해 주시겠어요?\"\n\n"
	"[출력 금지 필드 — 절대 포함하지 마]\n"
	"action_id, timestamp, session_id, schema_version, source, network_online, fallback_policy"
)


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
		num_ctx: int = 2048,
		num_predict: int = 150,
		temperature: float = 0.2,
	) -> None:
		self.name = f"ollama-{model}"
		self._model = model
		self._host = host.rstrip("/")
		self._timeout_sec = timeout_sec
		self._num_ctx = num_ctx
		self._num_predict = num_predict
		self._temperature = temperature

	def warm_up(self) -> None:
		"""Load the model into memory by issuing a 1-token generation."""
		body = {
			"model": self._model,
			"messages": [{"role": "user", "content": "ok"}],
			"stream": False,
			"options": {"num_predict": 1, "temperature": 0.0},
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
		messages: List[Dict[str, str]] = [{"role": "system", "content": OLLAMA_SLIM_SYSTEM_PROMPT}]
		if history:
			messages.extend(history)
		messages.append({"role": "user", "content": stt_text})

		body = {
			"model": self._model,
			"messages": messages,
			"stream": False,
			"format": "json",
			"options": {
				"temperature": self._temperature,
				"num_ctx": self._num_ctx,
				"num_predict": self._num_predict,
			},
		}

		try:
			response = self._post_json("/api/chat", body)
		except Exception as exc:
			print(f"[OllamaLLM] request failed: {exc}")
			return _offline_action_json(session_id=session_id, reason="ollama_request_failed")

		content = ""
		if isinstance(response, dict):
			message = response.get("message")
			if isinstance(message, dict):
				content = str(message.get("content", "") or "")

		if not content:
			print("[OllamaLLM] empty response content")
			return _offline_action_json(session_id=session_id, reason="ollama_empty_content")

		try:
			action = _parse_and_validate_action_json(
				content,
				session_id=session_id,
				network_online=False,
				fallback_policy="ollama",
			)
			return _apply_conversation_policy(action)
		except Exception as exc:
			print(f"[OllamaLLM] schema validation failed: {exc}")
			return _offline_action_json(session_id=session_id, reason="ollama_invalid_schema")

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
