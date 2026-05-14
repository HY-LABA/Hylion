from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from jetson.core.llm.groq_llm import GroqClient
from jetson.core.llm.prompt import (
	apply_hard_overrides,
	assemble_action,
	derive_full_action,
	extract_core,
)


# --------------------------------------------------------------------------
# GroqClient transport: retry / unavailable
# --------------------------------------------------------------------------
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


# --------------------------------------------------------------------------
# Harness contract: extract_core (LLM JSON -> 4-field core)
# --------------------------------------------------------------------------
def test_extract_core_keeps_only_contract_fields_and_drops_extras():
	# An old-style payload with derived/injected fields the model shouldn't emit.
	content = (
		'{"intent":"move","target_object":"none","reply_text":"갈게!",'
		'"gait_cmd":"walk_forward","requires_bhl":false,"state_current":"IDLE",'
		'"action_id":"junk"}'
	)
	core = extract_core(content)
	assert set(core.keys()) == {"intent", "target_object", "reply_text", "gait_cmd"}
	assert core["intent"] == "move"
	assert core["gait_cmd"] == "walk_forward"


def test_extract_core_backfills_missing_fields_and_clamps_bad_intent():
	core = extract_core('{"intent":"banana"}')
	assert core["intent"] == "unknown"
	assert core["target_object"] == "none"
	assert core["reply_text"] == ""
	assert core["gait_cmd"] == "none"


# --------------------------------------------------------------------------
# Harness contract: apply_hard_overrides (Step 3 keyword rules in code)
# --------------------------------------------------------------------------
def test_apply_hard_overrides_forces_stop_regardless_of_model():
	assert apply_hard_overrides("그냥 멈춰", "chat") == "stop"


def test_apply_hard_overrides_forces_standby():
	assert apply_hard_overrides("이제 수고했어 쉬어", "chat") == "standby"


def test_apply_hard_overrides_passes_through_when_no_keyword():
	assert apply_hard_overrides("앞으로 걸어가", "move") == "move"


# --------------------------------------------------------------------------
# Harness derive layer: derive_full_action (4 fields -> 15-field schema object)
# --------------------------------------------------------------------------
def test_derive_full_action_move_keeps_valid_gait_and_sets_bhl():
	action = derive_full_action(
		{"intent": "move", "target_object": "none", "reply_text": "갈게!", "gait_cmd": "turn_left"},
		session_id="sess-1",
		network_online=True,
		fallback_policy="groq",
	)
	assert action["intent"] == "move"
	assert action["gait_cmd"] == "turn_left"
	assert action["requires_bhl"] is True
	assert action["requires_smolvla"] is False
	assert action["state_current"] == "WALKING"
	assert action["source"] == "stt"


def test_derive_full_action_pick_place_derives_smolvla_and_state():
	action = derive_full_action(
		{"intent": "pick_place", "target_object": "빨간 컵", "reply_text": "잡을게!", "gait_cmd": "none"},
		session_id="sess-2",
		network_online=True,
		fallback_policy="groq",
	)
	assert action["requires_smolvla"] is True
	assert action["requires_bhl"] is False
	assert action["gait_cmd"] == "none"
	assert action["state_current"] == "MANIPULATING"
	assert action["target_object"] == "빨간 컵"


def test_derive_full_action_stop_forces_gait_stop():
	action = derive_full_action(
		{"intent": "stop", "target_object": "none", "reply_text": "멈췄어!", "gait_cmd": "walk_forward"},
		session_id="sess-3",
		network_online=False,
		fallback_policy="ollama",
	)
	assert action["gait_cmd"] == "stop"
	assert action["requires_bhl"] is True
	assert action["state_current"] == "IDLE"


def test_derive_full_action_move_clamps_out_of_enum_gait():
	# Schema gait enum has no walk_back; an out-of-enum direction must not break
	# schema validation — it falls back to walk_forward.
	action = derive_full_action(
		{"intent": "move", "target_object": "none", "reply_text": "갈게!", "gait_cmd": "walk_back"},
		session_id="sess-4",
		network_online=True,
		fallback_policy="groq",
	)
	assert action["gait_cmd"] == "walk_forward"


def test_derive_full_action_backfills_empty_reply_text():
	action = derive_full_action(
		{"intent": "chat", "target_object": "none", "reply_text": "", "gait_cmd": "none"},
		session_id="sess-5",
		network_online=True,
		fallback_policy="groq",
	)
	assert len(action["reply_text"]) >= 1


# --------------------------------------------------------------------------
# Harness entry point: assemble_action (raw text -> validated action)
# --------------------------------------------------------------------------
def test_assemble_action_happy_path():
	content = '{"intent":"chat","target_object":"none","reply_text":"안녕!","gait_cmd":"none"}'
	action = assemble_action(
		content,
		stt_text="안녕 하이리온",
		session_id="sess-a",
		network_online=True,
		fallback_policy="groq",
	)
	assert action["intent"] == "chat"
	assert action["network_online"] is True
	assert action["fallback_policy"] == "groq"


def test_assemble_action_invalid_json_falls_back():
	action = assemble_action(
		"not-a-json",
		stt_text="테스트",
		session_id="sess-b",
		network_online=True,
		fallback_policy="groq",
	)
	assert action["intent"] == "unknown"
	assert action["fallback_policy"] == "groq_parse_fail"


def test_assemble_action_applies_hard_override_after_parse():
	# Model mis-classifies "멈춰" as chat; the harness keyword rule corrects it.
	content = '{"intent":"chat","target_object":"none","reply_text":"응?","gait_cmd":"none"}'
	action = assemble_action(
		content,
		stt_text="하이리온 멈춰",
		session_id="sess-c",
		network_online=False,
		fallback_policy="ollama",
	)
	assert action["intent"] == "stop"
	assert action["gait_cmd"] == "stop"
	assert action["requires_bhl"] is True
