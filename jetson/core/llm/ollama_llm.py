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
DEFAULT_OLLAMA_MODEL = "qwen2.5:1.5b-instruct"
DEFAULT_TIMEOUT_SEC = 30.0
# Force every transformer layer onto the GPU. EXAONE 3.5 2.4B has 30 layers;
# ollama's auto-offload left 6 on the CPU even with free VRAM, costing ~10–20%
# of inference time. Override via env if a smaller model fits this default but
# a larger one needs partial CPU offload.
DEFAULT_NUM_GPU_LAYERS = int(os.getenv("HYLION_OLLAMA_NUM_GPU", "999"))

# Slim system prompt tuned for small on-device models (1-3B class). Concrete
# examples are kept because sub-2B models learn the output shape from one or
# two demos far better than from rule prose alone. Required-field coverage is
# enforced downstream by jsonschema; cross-field invariants by
# _apply_conversation_policy regardless of model fidelity.
OLLAMA_SLIM_SYSTEM_PROMPT = (
	"너는 키 1m 파란 사자 로봇 하이리온. 7살 남자아이 말투. "
	"반드시 JSON 객체 1개만 출력해. 마크다운/설명/코드블록 절대 금지.\n\n"
	"필드(모두 필수):\n"
	"intent: chat|pick_place|move|stop|standby|unknown\n"
	"target_object: 물체명 또는 \"none\"\n"
	"reply_text: 한국어 1문장, 25자 이내 (반드시. 길어지면 강제로 잘림)\n"
	"requires_smolvla, requires_bhl: true/false\n"
	"gait_cmd: walk_forward|walk_back|turn_left|turn_right|stop|none\n"
	"state_current: IDLE|TALKING|WALKING|PICKING\n"
	"safety_allowed: true/false\n\n"
	"intent → (requires_smolvla, requires_bhl, gait_cmd, state_current):\n"
	"chat → (false, false, none, TALKING)\n"
	"pick_place → (true, false, none, PICKING)\n"
	"move → (false, true, walk_*/turn_*, WALKING)\n"
	"stop → (false, true, stop, IDLE)\n"
	"standby → (false, false, none, IDLE)\n"
	"unknown → (false, false, none, IDLE)\n\n"
	"매핑 힌트 (가장 먼저 적용):\n"
	"질문/대답/소개/잡담/인사/감정표현 → chat (가장 흔한 경우)\n"
	"\"멈춰/그만/정지\" → stop\n"
	"\"쉬어/수고/휴식/잘가/끝/그만하자\" → standby\n"
	"\"~줘/~집어/잡아/들어\" + 물체 → pick_place, target_object=물체명\n"
	"\"앞으로/뒤로/왼쪽/오른쪽\" + 가/걸어/돌아 → move\n"
	"위 어느 것도 아닌 정말 알 수 없는 발화에만 → unknown\n\n"
	"예시 1) 사용자: \"자기소개 해봐\"\n"
	"{\"intent\":\"chat\",\"target_object\":\"none\",\"reply_text\":\"안녕! 나 하이리온이야.\","
	"\"requires_smolvla\":false,\"requires_bhl\":false,\"gait_cmd\":\"none\","
	"\"state_current\":\"TALKING\",\"safety_allowed\":true}\n\n"
	"예시 2) 사용자: \"빨간 컵 집어줘\"\n"
	"{\"intent\":\"pick_place\",\"target_object\":\"빨간 컵\",\"reply_text\":\"네, 잡을게요!\","
	"\"requires_smolvla\":true,\"requires_bhl\":false,\"gait_cmd\":\"none\","
	"\"state_current\":\"PICKING\",\"safety_allowed\":true}\n\n"
	"포함 금지 필드: action_id, timestamp, session_id, schema_version, source, network_online, fallback_policy"
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
				{"role": "system", "content": OLLAMA_SLIM_SYSTEM_PROMPT},
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
		messages: List[Dict[str, str]] = [{"role": "system", "content": OLLAMA_SLIM_SYSTEM_PROMPT}]
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
