#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import uuid
from datetime import datetime
from groq import Groq

from hylion_perception import perceive_environment, pixel_to_robot_coords

class BrainNode(Node):
    def __init__(self):
        super().__init__('brain_node')

        # System prompt for LLM
        self.system_prompt = """
    You are HYlion, an intelligent robot assistant.
    You must output only a valid JSON object that matches the HYlion Action schema.

    Required top-level fields:
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
    - intent must be one of chat, pick_place, move, stop, unknown.
    - Do not output nested motion_cmd, perception, or so_arm_control blocks.
    - For pick_place, set requires_smolvla=true, gait_cmd=stop, state_current=MANIPULATING.
    - For non-pick_place, set requires_smolvla=false and gait_cmd=none.
    - reply_text must always be non-empty.
    """

        # Publishers
        self.action_json_pub = self.create_publisher(String, '/hylion/action_json', 10)
        self.tts_pub = self.create_publisher(String, '/hylion/tts', 10)

        # Subscribers
        self.user_input_sub = self.create_subscription(String, '/hylion/user_input', self.user_input_callback, 10)
        self.perception_sub = self.create_subscription(String, '/hylion/perception', self.perception_callback, 10)

        # State
        self.chat_history = [{"role": "system", "content": self.system_prompt}]
        self.latest_detections = []
        self.pending_action = None

        # Groq client
        self.client = Groq()

        self.get_logger().info('Brain Node initialized')

    def user_input_callback(self, msg):
        user_input = msg.data.strip()
        if not user_input or user_input.lower() in ['quit', 'exit']:
            return

        self.get_logger().info(f'Received user input: {user_input}')

        # LLM reasoning
        action_json = self.reason_with_llm(user_input, self.latest_detections, self.chat_history)
        if not action_json:
            self.get_logger().error('LLM failed to generate JSON')
            return

        # Normalize to internal schema
        action_json = self.normalize_action_json(action_json, user_input, self.latest_detections)

        # Validate and generate SO-ARM commands if needed
        issues = self.validate_action_json(action_json)
        for issue in issues:
            if issue.startswith('⚠️'):
                self.get_logger().warn(issue)
            else:
                self.get_logger().info(issue)

        # Add metadata
        action_json["action_id"] = str(uuid.uuid4())
        action_json["timestamp"] = datetime.utcnow().isoformat() + "Z"
        action_json.setdefault("session_id", "sess_unknown")
        action_json.setdefault("source", "mic")
        action_json.setdefault("network_online", True)

        # Publish action JSON
        json_str = json.dumps(action_json)
        self.action_json_pub.publish(String(data=json_str))
        self.get_logger().info(f'Published action_json: {json_str[:160]}')

        # Publish TTS
        tts_text = action_json.get('tts_text', '')
        if tts_text:
            self.tts_pub.publish(String(data=tts_text))
            self.get_logger().info(f'Published tts: {tts_text}')

        # Update history
        self.chat_history.append({"role": "user", "content": user_input})
        self.chat_history.append({"role": "assistant", "content": json_str})

    def perception_callback(self, msg):
        try:
            self.latest_detections = json.loads(msg.data)
            self.get_logger().info(f'Updated detections: {len(self.latest_detections)} objects')
        except json.JSONDecodeError:
            self.get_logger().error('Failed to parse perception data')

    def reason_with_llm(self, user_input, detections, chat_history):
        perception_context = f"Current camera detections: {json.dumps(detections, indent=2)}\nUser command: \"{user_input}\""
        full_prompt = self.system_prompt + "\n" + perception_context

        messages = chat_history.copy()
        if not messages or messages[-1]["role"] != "user":
            messages.append({"role": "user", "content": full_prompt})
        else:
            messages[-1] = {"role": "user", "content": full_prompt}

        # Try external LLM (Groq); fallback to deterministic local handler
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            llm_output = response.choices[0].message.content
            parsed = json.loads(llm_output)
            self.get_logger().info('LLM response received')
            return parsed
        except Exception as e:
            self.get_logger().warn(f'LLM Error, using local fallback: {e}')

        # Local deterministic parser for quick testing
        return self.local_reasoning(user_input, detections)

    def local_reasoning(self, user_input, detections):
        user_input_lower = user_input.lower()
        action_json = {
            "intent": "unknown",
            "target_object": "unknown",
            "reply_text": "I did not understand. Please repeat.",
            "requires_smolvla": False,
            "requires_bhl": False,
            "gait_cmd": "none",
            "state_current": "IDLE",
            "safety_allowed": True,
            "fallback_policy": "precoded"
        }

        if "pick up" in user_input_lower or "grab" in user_input_lower or "lift" in user_input_lower:
            # pick_place intent
            target_engineered = "unknown"
            target_detection = detections[0] if detections else None
            if target_detection:
                target_engineered = target_detection.get("class", "unknown")

            action_json = {
                "intent": "pick_place",
                "target_object": target_engineered,
                "reply_text": f"Okay, I will pick up the {target_engineered}.",
                "requires_smolvla": True,
                "requires_bhl": False,
                "gait_cmd": "stop",
                "state_current": "MANIPULATING",
                "safety_allowed": True,
                "fallback_policy": "smolvla"
            }

        elif "go to" in user_input_lower or "move" in user_input_lower:
            action_json = {
                "intent": "move",
                "target_object": "location",
                "reply_text": "Moving to the requested location.",
                "requires_smolvla": False,
                "requires_bhl": True,
                "gait_cmd": "walk_forward",
                "state_current": "WALKING",
                "safety_allowed": True,
                "fallback_policy": "precoded"
            }

        else:
            action_json = {
                "intent": "chat",
                "target_object": "unknown",
                "reply_text": "I am observing the environment.",
                "requires_smolvla": False,
                "requires_bhl": False,
                "gait_cmd": "none",
                "state_current": "TALKING",
                "safety_allowed": True,
                "fallback_policy": "precoded"
            }

        return action_json

    def validate_action_json(self, action_json):
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
        return issues

    def normalize_action_json(self, action_json, user_input=None, detections=None):
        # Convert legacy keys to unified schema
        if not isinstance(action_json, dict):
            return {
                "intent": "unknown",
                "target_object": "unknown",
                "reply_text": "Could not parse action JSON.",
                "requires_smolvla": False,
                "requires_bhl": False,
                "gait_cmd": "none",
                "state_current": "IDLE",
                "safety_allowed": True,
                "fallback_policy": "precoded"
            }

        # Legacy field mapping
        if "intent" not in action_json:
            action = action_json.get("action") or action_json.get("behavior")
            if isinstance(action, str):
                action_low = action.lower()
                if "pick" in action_low:
                    action_json["intent"] = "pick_place"
                elif "place" in action_low:
                    action_json["intent"] = "pick_place"
                elif "move" in action_low or "go" in action_low:
                    action_json["intent"] = "move"
                elif "speak" in action_low or "talk" in action_low:
                    action_json["intent"] = "chat"
                else:
                    action_json["intent"] = "unknown"
            else:
                action_json["intent"] = "unknown"

        if "target_object" not in action_json:
            if "object" in action_json:
                action_json["target_object"] = action_json.get("object")
            elif action_json.get("intent") == "pick_place" and detections:
                action_json["target_object"] = detections[0].get("class", "unknown")
            else:
                action_json["target_object"] = "unknown"

        if "reply_text" not in action_json:
            action_json["reply_text"] = action_json.get("tts_text") or action_json.get("utterance") or ""

        if not action_json.get("reply_text"):
            if action_json.get("intent") == "pick_place":
                action_json["reply_text"] = f"Okay, I will pick up the {action_json.get('target_object', 'object')}."
            elif action_json.get("intent") == "move":
                action_json["reply_text"] = "Moving to the requested location."
            else:
                action_json["reply_text"] = "I am ready."

        action_json["requires_smolvla"] = bool(action_json.get("intent") == "pick_place")
        action_json["requires_bhl"] = bool(action_json.get("intent") == "move")
        action_json["gait_cmd"] = action_json.get("gait_cmd", "stop" if action_json.get("intent") == "pick_place" else "none")
        action_json["state_current"] = action_json.get("state_current", "MANIPULATING" if action_json.get("intent") == "pick_place" else "IDLE")
        action_json["safety_allowed"] = bool(action_json.get("safety_allowed", True))
        action_json["fallback_policy"] = action_json.get("fallback_policy", "smolvla" if action_json.get("intent") == "pick_place" else "precoded")

        # Remove legacy nested payloads so published JSON matches the action schema.
        for legacy_key in ["motion_cmd", "perception", "confidence", "emotion", "state", "tts_text"]:
            if legacy_key in action_json:
                action_json.pop(legacy_key, None)

        return action_json


def main(args=None):
    rclpy.init(args=args)
    node = BrainNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
