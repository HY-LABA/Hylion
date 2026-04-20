import json
import uuid
from datetime import datetime
from groq import Groq

from hylion_perception import perceive_environment
from hylion_soarm import call_lerobot_act_model, apply_inverse_kinematics

# Initialize Groq client (Uses GROQ_API_KEY from ~/.bashrc)
client = Groq()

# HYlion Action Schema (minimal, top-level)
system_prompt = """You are the AI brain of the 'HYlion' physical robot.
You must output ONLY a valid JSON object matching the HYlion Action schema.
Do not include any conversational text outside the JSON.

Required fields:
- action_id
- timestamp
- session_id
- source
- network_online
- intent
- target_object
- reply_text
- requires_smolvla
- requires_bhl
- gait_cmd
- state_current
- safety_allowed
- fallback_policy

Rules:
- intent is one of chat, pick_place, move, stop, unknown.
- Do not output nested motion_cmd, perception, or so_arm_control blocks.
- For pick_place, set requires_smolvla=true, requires_bhl=false, gait_cmd=stop, state_current=MANIPULATING.
- For move, set requires_bhl=true.
- reply_text must always be non-empty.
"""


def reason_with_llm(user_input, detections, chat_history):
    perception_context = f"""
Current camera detections:
{json.dumps(detections, indent=2)}

User command: \"{user_input}\"
"""

    full_prompt = system_prompt + "\n" + perception_context

    messages = chat_history.copy()
    if not messages or messages[-1]["role"] != "user":
        messages.append({"role": "user", "content": full_prompt})
    else:
        messages[-1] = {"role": "user", "content": full_prompt}

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        llm_output = response.choices[0].message.content
        return json.loads(llm_output)

    except Exception as e:
        print(f"❌ LLM Error: {e}")
        return None


def normalize_action_json(action_json, user_input, detections):
    if not isinstance(action_json, dict):
        action_json = {}

    if "intent" not in action_json:
        action_low = (action_json.get("action") or action_json.get("behavior") or user_input).lower()
        if "pick" in action_low or "grab" in action_low or "lift" in action_low:
            action_json["intent"] = "pick_place"
        elif "move" in action_low or "go" in action_low:
            action_json["intent"] = "move"
        elif "stop" in action_low:
            action_json["intent"] = "stop"
        elif "speak" in action_low or "talk" in action_low or "hello" in action_low:
            action_json["intent"] = "chat"
        else:
            action_json["intent"] = "unknown"

    if not action_json.get("target_object") and action_json.get("intent") == "pick_place" and detections:
        action_json["target_object"] = detections[0].get("class", "unknown")
    if not action_json.get("target_object"):
        action_json["target_object"] = "unknown"

    if not action_json.get("reply_text"):
        if action_json.get("intent") == "pick_place":
            action_json["reply_text"] = f"Okay, I will pick up the {action_json['target_object']}."
        elif action_json.get("intent") == "move":
            action_json["reply_text"] = "Moving to the requested location."
        elif action_json.get("intent") == "stop":
            action_json["reply_text"] = "Stopping now."
        else:
            action_json["reply_text"] = "I am ready."

    action_json["requires_smolvla"] = bool(action_json.get("intent") == "pick_place")
    action_json["requires_bhl"] = bool(action_json.get("intent") == "move")
    action_json["gait_cmd"] = action_json.get("gait_cmd") or ("stop" if action_json.get("intent") == "pick_place" else "none")
    action_json["state_current"] = action_json.get("state_current") or (
        "MANIPULATING" if action_json.get("intent") == "pick_place"
        else "WALKING" if action_json.get("intent") == "move"
        else "TALKING"
    )
    action_json["safety_allowed"] = bool(action_json.get("safety_allowed", True))
    action_json["fallback_policy"] = action_json.get("fallback_policy") or (
        "smolvla" if action_json.get("intent") == "pick_place" else "precoded"
    )
    action_json.setdefault("session_id", "sess_unknown")
    action_json.setdefault("source", "mic")
    action_json.setdefault("network_online", True)

    for legacy_key in ["motion_cmd", "perception", "confidence", "emotion", "state", "tts_text"]:
        action_json.pop(legacy_key, None)

    return action_json


def validate_action_json(action_json):
    issues = []

    intent = action_json.get("intent")

    if intent == "pick_place":
        if not action_json.get("target_object") or action_json.get("target_object") == "None":
            action_json["target_object"] = "unknown"
            issues.append("⚠️ target_object was None, set to 'unknown'")

        action_json["requires_smolvla"] = True
        action_json["requires_bhl"] = False
        action_json["gait_cmd"] = "stop"
        action_json["state_current"] = "MANIPULATING"
        if not action_json.get("reply_text"):
            action_json["reply_text"] = f"Okay, I will pick up the {action_json['target_object']}."

    if action_json.get("state_current") == "MANIPULATING" and action_json.get("gait_cmd") != "stop":
        action_json["gait_cmd"] = "stop"
        issues.append("⚠️ State=MANIPULATING forces gait_cmd=stop")

    if intent != "pick_place":
        action_json["requires_smolvla"] = False
        if action_json.get("state_current") not in ["EMERGENCY", "WALKING"]:
            action_json["state_current"] = "TALKING" if intent == "chat" else "IDLE"
        if action_json.get("gait_cmd") not in ["none", "stop", "walk_forward", "turn_left"]:
            action_json["gait_cmd"] = "none"

    return issues


def chat_with_hylion():
    print("="*60)
    print("🤖 HYlion Brain v2.0 is ONLINE (LLM orchestration only)")
    print("="*60)
    print("Type your message (or 'quit'/'exit' to stop)")
    print("="*60)

    chat_history = [{"role": "system", "content": system_prompt}]

    while True:
        print("\n📸 [Sensing environment...]")
        detections, frame = perceive_environment(use_camera=True)

        if detections:
            print(f"   ✅ Detected {len(detections)} object(s)")
        else:
            print("   ⚠️ No objects detected")

        user_input = input("\n[You]: ").strip()

        if user_input.lower() in ["quit", "exit"]:
            print("\n🛑 Shutting down HYlion brain... Goodbye!")
            break
        if not user_input:
            continue

        print("\n🧠 [LLM reasoning...]")
        chat_history.append({"role": "user", "content": user_input})

        action_json = reason_with_llm(user_input, detections, chat_history)
        if not action_json:
            print("❌ LLM failed to generate valid JSON")
            continue

        action_json = normalize_action_json(action_json, user_input, detections)
        issues = validate_action_json(action_json)
        for issue in issues:
            print(issue)

        action_json["action_id"] = str(uuid.uuid4())
        action_json["timestamp"] = datetime.utcnow().isoformat() + "Z"
        action_json.setdefault("session_id", "sess_unknown")
        action_json.setdefault("source", "mic")
        action_json.setdefault("network_online", True)

        print("\n" + "-"*60)
        print(f"🔊 [Robot says]: {action_json.get('reply_text', '(silent)')}")
        print("-"*60)
        print(json.dumps(action_json, indent=2))

        chat_history.append({"role": "assistant", "content": json.dumps(action_json)})


if __name__ == "__main__":
    chat_with_hylion()
