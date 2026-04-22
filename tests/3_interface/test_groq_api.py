from pathlib import Path
import json
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from jetson.cloud.groq_client import GroqCallResult, GroqClient, build_action_json_from_stt


class _FakeMessage:
	def __init__(self, content: str):
		self.content = content


class _FakeChoice:
	def __init__(self, content: str):
		self.message = _FakeMessage(content)


class _FakeResponse:
	def __init__(self, content: str):
		self.choices = [_FakeChoice(content)]


class _FakeCompletions:
	def __init__(self, fail_count: int = 0, content: str = '{"intent":"chat"}'):
		self._fail_count = fail_count
		self._content = content
		self.calls = 0

	def create(self, **kwargs):
		self.calls += 1
		if self._fail_count > 0:
			self._fail_count -= 1
			raise RuntimeError("temporary_failure")
		return _FakeResponse(self._content)


class _FakeChat:
	def __init__(self, completions):
		self.completions = completions


class _FakeGroqClient:
	def __init__(self, completions):
		self.chat = _FakeChat(completions)


def test_request_chat_completion_retries_then_succeeds():
	completions = _FakeCompletions(fail_count=1, content='{"intent":"chat"}')
	client = _FakeGroqClient(completions)

	api = GroqClient(client=client)
	result = api.request_chat_completion(
		system_prompt="return json",
		user_text="안녕",
		retries=2,
		retry_delay_sec=0.0,
	)

	assert result.ok is True
	assert '"intent":"chat"' in result.content
	assert completions.calls == 2


def test_request_chat_completion_client_unavailable(monkeypatch):
	monkeypatch.delenv("GROQ_API_KEY", raising=False)

	api = GroqClient(client=None)
	result = api.request_chat_completion(system_prompt="x", user_text="y")

	assert result.ok is False
	assert result.error == "groq_client_unavailable"


class _FakeWrapper:
	def __init__(self, result: GroqCallResult):
		self._result = result

	def request_chat_completion(self, **kwargs):
		return self._result


def _valid_action_payload(intent: str = "move") -> str:
	payload = {
		"action_id": "tmp",
		"timestamp": "2026-01-01T00:00:00Z",
		"session_id": "tmp",
		"schema_version": "1.0",
		"source": "stt",
		"network_online": True,
		"intent": intent,
		"target_object": "none",
		"reply_text": "네! 하이리온이 도와드릴게요.",
		"requires_smolvla": intent == "pick_place",
		"requires_bhl": intent in {"move", "stop"},
		"gait_cmd": "walk_forward" if intent == "move" else "none",
		"state_current": "WALKING" if intent == "move" else "TALKING",
		"safety_allowed": True,
		"fallback_policy": "none",
	}
	return json.dumps(payload, ensure_ascii=False)


def test_build_action_json_from_stt_success_move_defaults_gait():
	result = GroqCallResult(
		ok=True,
		content=_valid_action_payload(intent="move"),
	)
	wrapper = _FakeWrapper(result)

	action = build_action_json_from_stt(
		client=wrapper,
		stt_text="앞으로 가",
		session_id="sess-001",
		system_prompt="json only",
	)

	assert action["network_online"] is True
	assert action["intent"] == "move"
	assert action["gait_cmd"] == "walk_forward"
	assert action["requires_bhl"] is True
	assert action["source"] == "stt"


def test_build_action_json_from_stt_fallback_on_invalid_json():
	result = GroqCallResult(ok=True, content="not-a-json")
	wrapper = _FakeWrapper(result)

	action = build_action_json_from_stt(
		client=wrapper,
		stt_text="테스트",
		session_id="sess-err",
		system_prompt="json only",
	)

	assert action["network_online"] is False
	assert action["intent"] == "unknown"
	assert action["fallback_policy"] == "cloud_invalid_or_schema_fail_then_local_fail"


def test_build_action_json_from_stt_cloud_fail_local_success():
	cloud = _FakeWrapper(GroqCallResult(ok=False, content="", error="timeout"))
	local = _FakeWrapper(GroqCallResult(ok=True, content=_valid_action_payload(intent="chat")))

	action = build_action_json_from_stt(
		client=cloud,
		local_client=local,
		stt_text="안녕 하이리온",
		session_id="sess-local",
		system_prompt="json only",
	)

	assert action["intent"] == "chat"
	assert action["network_online"] is False
	assert action["fallback_policy"] == "local_llm"
