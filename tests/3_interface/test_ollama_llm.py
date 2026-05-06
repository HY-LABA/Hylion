from pathlib import Path
import json
import sys
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from jetson.core.llm.ollama_llm import OllamaLLMBackend


def _valid_action_payload(intent: str = "chat") -> dict:
    return {
        "intent": intent,
        "target_object": "none",
        "reply_text": "안녕! 하이리온이야.",
        "requires_smolvla": intent == "pick_place",
        "requires_bhl": intent in {"move", "stop"},
        "gait_cmd": "walk_forward" if intent == "move" else "none",
        "state_current": "WALKING" if intent == "move" else "TALKING",
        "safety_allowed": True,
    }


def test_build_action_success_validates_and_normalizes_standby():
    backend = OllamaLLMBackend()

    fake_response = {
        "message": {
            "role": "assistant",
            "content": json.dumps(_valid_action_payload(intent="standby")),
        }
    }

    with patch.object(OllamaLLMBackend, "_post_json", return_value=fake_response) as mock_post:
        action = backend.build_action(
            stt_text="이제 쉬어",
            session_id="sess-001",
            history=[],
            in_chat_mode=True,
        )

    mock_post.assert_called_once()
    call_path, call_body = mock_post.call_args[0]
    assert call_path == "/api/chat"
    assert call_body["model"] == "exaone3.5:2.4b"
    assert call_body["format"] == "json"
    assert call_body["stream"] is False
    assert call_body["messages"][0]["role"] == "system"
    assert call_body["messages"][-1]["content"] == "이제 쉬어"

    assert action["intent"] == "standby"
    assert action["state_current"] == "IDLE"
    assert action["requires_smolvla"] is False
    assert action["requires_bhl"] is False
    assert action["gait_cmd"] == "none"
    assert action["network_online"] is False
    assert action["fallback_policy"] == "ollama"


def test_build_action_history_is_threaded_into_messages():
    backend = OllamaLLMBackend()

    fake_response = {
        "message": {"content": json.dumps(_valid_action_payload(intent="chat"))}
    }
    history = [
        {"role": "user", "content": "이전 질문"},
        {"role": "assistant", "content": "이전 답변"},
    ]

    with patch.object(OllamaLLMBackend, "_post_json", return_value=fake_response) as mock_post:
        backend.build_action(
            stt_text="새 질문",
            session_id="sess-hist",
            history=history,
            in_chat_mode=True,
        )

    body = mock_post.call_args[0][1]
    messages = body["messages"]
    assert messages[0]["role"] == "system"
    assert messages[1] == {"role": "user", "content": "이전 질문"}
    assert messages[2] == {"role": "assistant", "content": "이전 답변"}
    assert messages[3] == {"role": "user", "content": "새 질문"}


def test_build_action_falls_back_when_request_fails():
    backend = OllamaLLMBackend()

    with patch.object(OllamaLLMBackend, "_post_json", side_effect=RuntimeError("ollama_unreachable")):
        action = backend.build_action(
            stt_text="안녕",
            session_id="sess-down",
            history=[],
            in_chat_mode=True,
        )

    assert action["intent"] == "unknown"
    assert action["network_online"] is False
    assert action["fallback_policy"] == "ollama_request_failed"
    assert "안전 대기" in action["reply_text"]


def test_build_action_falls_back_when_content_is_invalid_json():
    backend = OllamaLLMBackend()

    fake_response = {"message": {"content": "not-a-json"}}

    with patch.object(OllamaLLMBackend, "_post_json", return_value=fake_response):
        action = backend.build_action(
            stt_text="안녕",
            session_id="sess-bad",
            history=[],
            in_chat_mode=True,
        )

    assert action["intent"] == "unknown"
    assert action["fallback_policy"] == "ollama_invalid_schema"


def test_build_action_falls_back_when_message_missing():
    backend = OllamaLLMBackend()

    fake_response = {"done": True}

    with patch.object(OllamaLLMBackend, "_post_json", return_value=fake_response):
        action = backend.build_action(
            stt_text="안녕",
            session_id="sess-empty",
            history=[],
            in_chat_mode=True,
        )

    assert action["intent"] == "unknown"
    assert action["fallback_policy"] == "ollama_empty_content"


def test_factory_returns_ollama_when_offline():
    from jetson.core.llm.factory import build_llm_backend

    backend = build_llm_backend(online=False)
    assert isinstance(backend, OllamaLLMBackend)
    assert backend.name == "ollama-exaone3.5:2.4b"


def test_factory_returns_groq_when_online():
    from jetson.core.llm.factory import build_llm_backend
    from jetson.core.llm.groq_llm import GroqLLMBackend

    backend = build_llm_backend(online=True)
    assert isinstance(backend, GroqLLMBackend)
