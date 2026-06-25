from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple
from uuid import uuid4

from jetson.core.client import gesture_registry


SCHEMA_VERSION = "1.0"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ACTION_SCHEMA_PATH = PROJECT_ROOT / "configs" / "schemas" / "action.schema.json"


# =============================================================================
# Harness contract (Step 1 responsibility map)
#
# The LLM emits only 4 "judgment" fields. The harness derives the rest:
# intent-driven fields (requires_smolvla / state_current /
# safety_allowed), the keyword-detected gesture_name, and injects the metadata
# fields. Keeping the model's output surface this small is the core reliability
# lever for the 1.5B offline model: fewer fields to fill = fewer ways to be
# wrong, and cross-field invariants become impossible to violate because the
# model never sees those fields.
# =============================================================================
CORE_FIELDS = ("intent", "target_object", "reply_text", "gait_cmd")
VALID_INTENTS = ("chat", "pick_place", "move", "stop", "standby", "unknown")
# action.schema.json's gait enum is walk_forward/turn_left/stop/none. `stop` is
# harness-derived, so the only gait values the model ever chooses are these two.
MOVE_GAITS = ("walk_forward", "turn_left")

# intent -> derived state_current (schema enum: IDLE/TALKING/MANIPULATING/WALKING/EMERGENCY)
_INTENT_STATE = {
	"chat": "TALKING",
	"pick_place": "MANIPULATING",
	"move": "WALKING",
	"stop": "IDLE",
	"standby": "IDLE",
	"unknown": "IDLE",
}

# Fallback reply when the model truncates reply_text away (common on the 1.5B
# model when the rest of the JSON is otherwise valid).
_DEFAULT_REPLY = {
	"chat": "응, 듣고 있어!",
	"pick_place": "응, 잡아볼게!",
	"move": "씩씩하게 갈게!",
	"stop": "멈췄어!",
	"standby": "그럼 쉬고 있을게!",
	"unknown": "무슨 말인지 잘 모르겠어요. 다시 말씀해 주시겠어요?",
}

# Step 3: hard keyword overrides.
# Safety-critical intents must NOT depend on model fidelity, so the rule lives
# in code and runs after the LLM call. "멈춰" forcing `stop` is a guarantee, not
# a hint the 1.5B model might miss. Applied by apply_hard_overrides().
HARD_INTENT_OVERRIDES: Dict[str, Tuple[str, ...]] = {
	"stop": ("멈춰", "멈춰줘", "그만", "정지", "스톱"),
	"standby": ("쉬어", "수고", "휴식", "잘가", "그만하자", "끝났어", "쉬고 있어"),
}

# Gesture keyword overrides.
# A gesture is NOT an intent — it rides along on a `chat` turn as a side-effect.
# When the user is chatting and says a gesture keyword, the harness fills the
# derived `gesture_name` field while leaving intent == "chat", so the right arm
# plays the gesture and the conversation continues uninterrupted. Same code-side
# longest-match pattern as HARD_INTENT_OVERRIDES — the LLM never sees this, which
# keeps gesture triggering deterministic and the 1.5B prompt untouched.
# Keys must be valid registry gesture names (see gesture_registry); a key that
# points at an unsynced gesture is simply never matched (detect_gesture re-checks
# the registry). Add a gesture's keywords here when it is synced to the Jetson.
GESTURE_KEYWORD_OVERRIDES: Dict[str, Tuple[str, ...]] = {
	"wave_hello": ("인사해", "인사 해", "인사하"),
	"wave_hello_2": ("손 흔들", "흔들어", "손 인사"),
}


# =============================================================================
# Step 4: layered system prompts
#
# Online (Groq 8B) and offline (Ollama 1.5B) share one skeleton:
#   [페르소나] -> [임무] -> [출력 필드] -> [intent 판단 규칙] -> [출력 예시]
# They differ only in verbosity. Neither prompt mentions the derived/injected
# fields or the JSON schema — the harness owns those, so spending tokens on them
# would only invite the model to fill fields whose answers we discard.
# =============================================================================
_PERSONA = (
	"너는 키 1미터의 귀여운 파란 사자 휴머노이드 로봇 '하이리온(HYlion)'이야. "
	"용맹하고 따뜻한 라이온 하트, 가장 온도가 높다는 푸른 불꽃을 닮은 갈기로 주변을 따뜻하게 밝히지. "
	"한양대를 가꾸는 가드너가 취미고, 학생들의 사랑을 받아 더 귀여워졌어. "
	"말투는 씩씩하고 따뜻하고 용기 있는 7살 남자아이 같아."
)

ONLINE_SYSTEM_PROMPT = (
	f"{_PERSONA}\n\n"
	"[임무] 사용자의 음성 입력 텍스트를 분석해서, 아래 4개 필드만 담은 JSON 객체 1개로만 응답해. "
	"마크다운·코드블록·부연 설명은 절대 금지야.\n\n"
	"[출력 필드 — 4개 전부 필수]\n"
	"- intent: chat | pick_place | move | stop | standby | unknown 중 하나\n"
	"- target_object: intent가 pick_place일 때 집을 물체 이름, 그 외에는 \"none\"\n"
	"- reply_text: 사용자가 들을 한국어 음성 대사. 하이리온의 성격을 담아 1~2문장의 완전한 문장으로 작성해.\n"
	"- gait_cmd: intent가 move일 때만 walk_forward 또는 turn_left, 그 외에는 \"none\"\n\n"
	"[intent 판단 규칙]\n"
	"- 사용자가 너에게 말을 거는 거의 모든 일상 발화는 chat이야. 질문·자기소개 요청·잡담·인사·감정 표현·칭찬·부탁이 아닌 말 → 전부 chat.\n"
	"- \"~줘 / 집어 / 잡아 / 들어\" + 물체 → pick_place, target_object에 물체 이름\n"
	"- \"앞으로 / 왼쪽으로\" + 가/걸어/돌아 → move\n"
	"- 멈추거나 정지하라는 지시 → stop\n"
	"- 대화를 마무리·종료하려는 의도 (대화 맥락까지 보고 판단) → standby\n"
	"- unknown은 STT가 깨져서 뜻을 전혀 알 수 없는 소리일 때만 써. 말뜻을 이해했다면, 네가 직접 할 수 없는 부탁이어도 chat이야. "
	"평범한 질문이나 잡담은 절대 unknown이 아니야. "
	"unknown일 때 reply_text는 \"무슨 말인지 잘 모르겠어요. 다시 말씀해 주시겠어요?\"로 작성해.\n\n"
	"[출력 예시]\n"
	'사용자: "자기소개 해봐"\n'
	'{"intent":"chat","target_object":"none","reply_text":"안녕! 나는 한양대를 지키는 파란 사자 하이리온이야!","gait_cmd":"none"}\n'
	'사용자: "노래 불러줄래?"\n'
	'{"intent":"chat","target_object":"none","reply_text":"노래는 아직 서툴지만 너랑 얘기하는 건 좋아!","gait_cmd":"none"}\n'
	'사용자: "오늘 기분이 어때?"\n'
	'{"intent":"chat","target_object":"none","reply_text":"난 오늘도 너랑 얘기해서 신나!","gait_cmd":"none"}\n'
	'사용자: "물병 좀 집어줘"\n'
	'{"intent":"pick_place","target_object":"물병","reply_text":"좋아, 물병을 멋지게 잡아볼게!","gait_cmd":"none"}\n'
	'사용자: "왼쪽으로 돌아"\n'
	'{"intent":"move","target_object":"none","reply_text":"왼쪽으로 씩씩하게 돌게!","gait_cmd":"turn_left"}\n'
	'사용자: "앞으로 걸어가"\n'
	'{"intent":"move","target_object":"none","reply_text":"씩씩하게 앞으로 갈게!","gait_cmd":"walk_forward"}'
)

OFFLINE_SYSTEM_PROMPT = (
	"너는 키 1m 파란 사자 로봇 하이리온. 씩씩한 7살 남자아이 말투.\n"
	"JSON 객체 1개만 출력. 마크다운·설명·코드블록 금지.\n\n"
	"필드 4개 (전부 필수):\n"
	"intent: chat|pick_place|move|stop|standby|unknown\n"
	"target_object: 물체 이름 또는 \"none\"\n"
	"reply_text: 한국어 1문장, 25자 이내\n"
	"gait_cmd: walk_forward|turn_left|none\n\n"
	"intent 판단:\n"
	"- 사용자가 말을 걸면 거의 다 chat. 질문·인사·자기소개·잡담·감정 표현 → 전부 chat.\n"
	"- \"~줘/집어/잡아/들어\" + 물체 → pick_place\n"
	"- \"앞으로/왼쪽\" + 가/걸어/돌아 → move\n"
	"- \"멈춰/정지\" → stop\n"
	"- 대화 끝내려는 말 → standby\n"
	"- unknown은 STT가 깨져 뜻을 알 수 없는 소리일 때만. 말뜻을 이해했으면 못 하는 부탁이어도 chat. 평범한 질문은 unknown 아님.\n\n"
	"예시)\n"
	'사용자: "자기소개 해봐"\n'
	'{"intent":"chat","target_object":"none","reply_text":"안녕! 나 하이리온이야.","gait_cmd":"none"}\n'
	'사용자: "노래 불러줄래?"\n'
	'{"intent":"chat","target_object":"none","reply_text":"노래는 서툴러도 얘기는 좋아!","gait_cmd":"none"}\n'
	'사용자: "오늘 기분 어때?"\n'
	'{"intent":"chat","target_object":"none","reply_text":"난 오늘 신나!","gait_cmd":"none"}\n'
	'사용자: "물병 좀 집어줘"\n'
	'{"intent":"pick_place","target_object":"물병","reply_text":"응, 잡을게!","gait_cmd":"none"}\n'
	'사용자: "왼쪽으로 돌아"\n'
	'{"intent":"move","target_object":"none","reply_text":"왼쪽으로 돌게!","gait_cmd":"turn_left"}\n'
	'사용자: "앞으로 가"\n'
	'{"intent":"move","target_object":"none","reply_text":"앞으로 갈게!","gait_cmd":"walk_forward"}'
)


def load_action_schema_content(schema_path: Path = DEFAULT_ACTION_SCHEMA_PATH) -> str:
	"""Load action schema text. Kept for callers that still want the raw schema."""
	return schema_path.read_text(encoding="utf-8")


# =============================================================================
# Step 2: harness derive layer
# =============================================================================
def apply_hard_overrides(stt_text: str, intent: str) -> str:
	"""Step 3: force safety-critical intents from keywords, ignoring model output.

	Runs after the LLM call so a mis-classified "멈춰" can still be corrected to
	`stop`. Longest matching keyword wins, so "그만하자" (standby) beats the
	shorter "그만" (stop) substring. Returns the (possibly overridden) intent.
	"""
	text = stt_text.strip()
	best_kw = ""
	best_intent = intent
	for forced_intent, keywords in HARD_INTENT_OVERRIDES.items():
		for kw in keywords:
			if kw in text and len(kw) > len(best_kw):
				best_kw = kw
				best_intent = forced_intent
	return best_intent


def extract_core(content: str) -> Dict[str, Any]:
	"""Parse the LLM response down to the 4-field core contract.

	Tolerant by design: unexpected extra fields are dropped, missing fields are
	backfilled with safe defaults, an out-of-enum intent collapses to `unknown`.
	Raises only when the response is not a JSON object at all.
	"""
	payload = json.loads(content)
	if not isinstance(payload, dict):
		raise ValueError("llm_response_not_object")

	intent = str(payload.get("intent", "unknown")).strip()
	if intent not in VALID_INTENTS:
		intent = "unknown"

	return {
		"intent": intent,
		"target_object": str(payload.get("target_object", "none") or "none").strip(),
		"reply_text": str(payload.get("reply_text", "") or "").strip(),
		"gait_cmd": str(payload.get("gait_cmd", "none") or "none").strip(),
	}


def detect_gesture(stt_text: str, intent: str) -> str:
	"""Code-side keyword -> gesture_name mapping, run after the LLM call.

	Gestures are a side-effect of conversation, never a standalone command, so
	they only fire on a `chat` turn — a non-chat intent yields "none". Longest
	matching keyword wins (same tie-break as apply_hard_overrides). The chosen
	gesture must still exist in the registry, otherwise it collapses to "none"
	so the executor route is simply skipped instead of failing at the wrapper.
	"""
	if intent != "chat":
		return "none"
	text = stt_text.strip()
	best_kw = ""
	best_gesture = "none"
	for gesture_name, keywords in GESTURE_KEYWORD_OVERRIDES.items():
		for kw in keywords:
			if kw in text and len(kw) > len(best_kw):
				best_kw = kw
				best_gesture = gesture_name
	if best_gesture != "none" and not gesture_registry.is_valid_gesture(best_gesture):
		return "none"
	return best_gesture


def derive_full_action(
	core: Dict[str, Any],
	*,
	session_id: str,
	network_online: bool,
	fallback_policy: str,
	source: str = "stt",
	gesture_name: str = "none",
) -> Dict[str, Any]:
	"""Expand the 4-field core into the full 16-field schema object.

	Every non-judgment field is derived from `intent` or injected here, so
	downstream routing never depends on the model filling them. This replaces
	the old _backfill_required_defaults + _apply_conversation_policy pair: there
	is nothing to "correct" because the model never emitted those fields.

	`gesture_name` is a harness-derived field (keyword detection in code, see
	detect_gesture) — not part of the model's core contract. It is already
	gated to chat turns + valid registry names by the caller; passed in here
	only so it lands in the schema object.
	"""
	intent = core["intent"]

	# gait_cmd: only `move` keeps a model-chosen direction; `stop` is fixed;
	# everything else has no gait. An out-of-enum move direction falls back to
	# walk_forward rather than failing schema validation.
	if intent == "move":
		gait_cmd = core["gait_cmd"] if core["gait_cmd"] in MOVE_GAITS else "walk_forward"
	elif intent == "stop":
		gait_cmd = "stop"
	else:
		gait_cmd = "none"

	target_object = core["target_object"] if intent == "pick_place" else "none"
	if not target_object:
		target_object = "none"

	reply_text = core["reply_text"] or _DEFAULT_REPLY.get(intent, "네!")

	return {
		"action_id": str(uuid4()),
		"timestamp": datetime.now(timezone.utc).isoformat(),
		"session_id": session_id,
		"schema_version": SCHEMA_VERSION,
		"source": source,
		"network_online": network_online,
		"intent": intent,
		"target_object": target_object,
		"reply_text": reply_text,
		"requires_smolvla": intent == "pick_place",
		"requires_bhl": intent in {"move", "stop", "pick_place"},
		"gait_cmd": gait_cmd,
		"gesture_name": gesture_name if intent == "chat" else "none",
		# duration_sec: bridge 가 동작을 얼마나 유지할지. 현재는 harness-derived (move=3s 고정).
		# 사용자 요청 강도에 따른 동적 조절은 추후 CORE_FIELDS 에 추가하면서 활성화.
		"duration_sec": 3.0 if intent == "move" else 0.0,
		"state_current": _INTENT_STATE.get(intent, "IDLE"),
		"safety_allowed": True,
		"fallback_policy": fallback_policy,
	}


def validate_action(
	action: Dict[str, Any],
	schema_path: Path = DEFAULT_ACTION_SCHEMA_PATH,
) -> Tuple[bool, str]:
	"""Validate a fully-derived action against action.schema.json."""
	schema = json.loads(schema_path.read_text(encoding="utf-8"))
	try:
		import jsonschema

		jsonschema.validate(instance=action, schema=schema)
		return True, "ok"
	except ImportError:
		missing = [k for k in schema.get("required", []) if k not in action]
		if missing:
			return False, f"missing required fields: {missing}"
		return True, "ok (required-only fallback)"
	except Exception as exc:
		return False, str(exc)


def offline_action_json(
	session_id: str,
	reason: str,
	network_online: bool = False,
) -> Dict[str, Any]:
	"""Last-resort schema-valid action when the LLM response is unusable.

	Built through derive_full_action so it can never itself drift out of schema.
	"""
	return derive_full_action(
		{
			"intent": "unknown",
			"target_object": "none",
			"reply_text": "잠깐 생각이 헝클어졌어요. 다시 한 번 말씀해 주실래요?",
			"gait_cmd": "none",
		},
		session_id=session_id,
		network_online=network_online,
		fallback_policy=reason,
	)


def assemble_action(
	raw_content: str,
	*,
	stt_text: str,
	session_id: str,
	network_online: bool,
	fallback_policy: str,
) -> Dict[str, Any]:
	"""Single entry point both LLM backends use: raw model text -> valid action.

	Pipeline: extract_core -> apply_hard_overrides -> detect_gesture ->
	derive_full_action -> validate_action. Any failure collapses to
	offline_action_json, so the caller is guaranteed a schema-valid dict and
	never has to handle exceptions.
	"""
	try:
		core = extract_core(raw_content)
	except Exception:
		return offline_action_json(session_id, f"{fallback_policy}_parse_fail", network_online)

	core["intent"] = apply_hard_overrides(stt_text, core["intent"])
	gesture_name = detect_gesture(stt_text, core["intent"])
	action = derive_full_action(
		core,
		session_id=session_id,
		network_online=network_online,
		fallback_policy=fallback_policy,
		gesture_name=gesture_name,
	)

	valid, reason = validate_action(action)
	if not valid:
		return offline_action_json(session_id, f"{fallback_policy}_schema_fail:{reason}", network_online)
	return action
