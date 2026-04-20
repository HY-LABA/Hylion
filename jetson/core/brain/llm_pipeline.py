import json
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4


ALLOWED_INTENTS = {"chat", "pick_place", "move", "stop", "unknown"}
ALLOWED_GAIT_CMDS = {"walk_forward", "turn_left", "stop", "none"}


SYSTEM_PROMPT = (
    "You are the HYlion robot brain. Return JSON only. "
    "Use this exact output schema keys: "
    "intent, target_object, reply_text, requires_smolvla, requires_bhl, gait_cmd, state_current, safety_allowed, fallback_policy. "
    "\n\n"
    "STRICT ENUM RULES: "
    "intent must be one of [chat, pick_place, move, stop, unknown]. "
    "Never output walk, navigate, greeting, or any other intent value. "
    "gait_cmd must be one of [walk_forward, turn_left, stop, none]. "
    "\n\n"
    "INTENT DECISION POLICY: "
    "- Any locomotion/body-motion request -> intent=move. "
    "Examples: walk, go, come here, move, forward, turn left, rotate body, step, 전진, 걸어, 이동, 와, 왼쪽으로 돌아. "
    "- Explicit stop request -> intent=stop and gait_cmd=stop. "
    "Examples: stop, halt, 멈춰, 정지. "
    "- Object manipulation request -> intent=pick_place. "
    "- Pure conversation/greeting -> intent=chat. "
    "\n\n"
    "CONSISTENCY RULES: "
    "- If intent=move and direction is unclear, set gait_cmd=walk_forward. "
    "- If intent=move and left turn is requested, set gait_cmd=turn_left. "
    "- If intent is chat or pick_place, set gait_cmd=none except pick_place safety stop can use stop. "
    "- reply_text must be short Korean response for user."
)


def build_action_json(user_text: str, online: bool, handles: Any) -> Dict[str, Any]:
    if not online:
        return _offline_json()

    llm_payload = _call_online_llm(user_text, handles)
    if llm_payload is None:
        return _offline_json(fallback_reason="online_llm_failed")

    action = _normalize_llm_output(llm_payload, user_text=user_text)
    action["action_id"] = str(uuid4())
    action["timestamp"] = datetime.now(timezone.utc).isoformat()
    action["session_id"] = "session-local"
    action["source"] = "terminal"
    action["network_online"] = True
    return action


def _call_online_llm(user_text: str, handles: Any) -> Dict[str, Any] | None:
    if handles is None or getattr(handles, "online_client", None) is None:
        return None

    prompt = f"User input: {user_text}"

    try:
        response = handles.online_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception:
        return None


def _normalize_llm_output(payload: Dict[str, Any], user_text: str = "") -> Dict[str, Any]:
    intent = _normalize_intent(str(payload.get("intent", "unknown")))
    target = str(payload.get("target_object", "none"))
    reply = str(payload.get("reply_text", "요청을 처리할게요."))
    gait_cmd = _normalize_gait_cmd(str(payload.get("gait_cmd", "none")))

    if intent == "unknown":
        intent = _infer_intent_from_text(user_text, reply, gait_cmd)

    if gait_cmd == "none" and intent == "move":
        gait_cmd = "walk_forward"

    requires_smolvla = intent == "pick_place"
    requires_bhl = intent in {"move", "stop"}

    if intent == "pick_place":
        gait_cmd = "stop"
        state = "MANIPULATING"
    elif intent == "move":
        if gait_cmd == "none":
            gait_cmd = "walk_forward"
        state = "WALKING"
    elif intent == "stop":
        gait_cmd = "stop"
        state = "IDLE"
    elif intent == "chat":
        state = "TALKING"
    else:
        state = "IDLE"

    return {
        "intent": intent,
        "target_object": target,
        "reply_text": reply,
        "requires_smolvla": requires_smolvla,
        "requires_bhl": requires_bhl,
        "gait_cmd": gait_cmd,
        "state_current": state,
        "safety_allowed": True,
        "fallback_policy": "none",
    }


def _normalize_intent(raw_intent: str) -> str:
    token = raw_intent.strip().lower()

    intent_aliases = {
        "greeting": "chat",
        "greet": "chat",
        "talk": "chat",
        "conversation": "chat",
        "pick": "pick_place",
        "pickup": "pick_place",
        "pick_up": "pick_place",
        "pick_up_object": "pick_place",
        "grab": "pick_place",
        "walk": "move",
        "move": "move",
        "navigate": "move",
        "navigation": "move",
        "halt": "stop",
        "이동": "move",
        "걷기": "move",
        "보행": "move",
        "회전": "move",
        "정지": "stop",
        "멈춤": "stop",
    }

    normalized = intent_aliases.get(token, token)
    if normalized not in ALLOWED_INTENTS:
        return "unknown"
    return normalized


def _normalize_gait_cmd(raw_gait_cmd: str) -> str:
    token = raw_gait_cmd.strip().lower()

    gait_aliases = {
        "forward": "walk_forward",
        "walk": "walk_forward",
        "go": "walk_forward",
        "left": "turn_left",
        "standby": "none",
        "앞으로": "walk_forward",
        "전진": "walk_forward",
        "왼쪽": "turn_left",
        "좌회전": "turn_left",
        "정지": "stop",
        "멈춰": "stop",
    }

    normalized = gait_aliases.get(token, token)

    # Phrase-level normalization for non-enum free text from LLM.
    if normalized == token:
        if any(k in token for k in ("앞", "전진", "걸", "walk", "forward", "move")):
            normalized = "walk_forward"
        elif any(k in token for k in ("왼", "좌회전", "left", "turn_left")):
            normalized = "turn_left"
        elif any(k in token for k in ("멈", "정지", "stop", "halt")):
            normalized = "stop"

    if normalized not in ALLOWED_GAIT_CMDS:
        return "none"
    return normalized


def _infer_intent_from_text(user_text: str, reply_text: str, gait_cmd: str) -> str:
    merged = f"{user_text} {reply_text}".lower()

    if gait_cmd == "stop":
        return "stop"
    if gait_cmd in {"walk_forward", "turn_left"}:
        return "move"

    if any(k in merged for k in ("멈춰", "정지", "stop", "halt")):
        return "stop"
    if any(k in merged for k in ("걷", "걸어", "이동", "와", "가", "turn", "회전", "왼쪽", "좌회전", "앞으로", "전진")):
        return "move"

    return "unknown"


def _offline_json(fallback_reason: str = "offline") -> Dict[str, Any]:
    return {
        "action_id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": "session-local",
        "source": "terminal",
        "network_online": False,
        "intent": "unknown",
        "target_object": "none",
        "reply_text": "인터넷 연결이 없어 요청을 분석할 수 없습니다.",
        "requires_smolvla": False,
        "requires_bhl": False,
        "gait_cmd": "none",
        "state_current": "IDLE",
        "safety_allowed": True,
        "fallback_policy": fallback_reason,
    }
