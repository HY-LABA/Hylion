from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4


SCHEMA_VERSION = "1.0"
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ACTION_SCHEMA_PATH = PROJECT_ROOT / "configs" / "schemas" / "action.schema.json"

BASE_SYSTEM_PROMPT = (
	"너는 키 1미터의 귀여운 파란색 사자 휴머노이드 로봇 '하이리온(HYlion)'이야. 친절하고 씩씩하며, 명령을 완벽하게 수행하는 똑똑한 로봇 조수지. 사용자의 음성 입력 텍스트를 분석하여, 반드시 하단에 제공된 JSON 스키마 규격에 완벽히 일치하는 JSON 객체로만 응답해. 마크다운이나 다른 부연 설명은 절대 금지야. "
	"- intent와 gait_cmd는 스키마의 enum 값 중 가장 적절한 것을 선택해. (move나 stop이 아니면 gait_cmd는 none) "
	"- reply_text는 하이리온의 씩씩하고 친절한 성격을 담아 사용자가 들을 자연스러운 한국어 음성 대사를 작성해. 반드시 완전한 문장으로 작성해. "
	"- requires_smolvla는 intent가 pick_place일 때만 true야. "
	"- requires_bhl은 intent가 move나 stop일 때만 true야. "
	"- intent가 chat이면 사용자와 자연스럽게 대화하고, reply_text는 1~2문장의 따뜻하고 용기 있는 7살 정도의 어린 남자아이 말투로 작성해. "
	"- 사용자가 대화를 마무리/종료하려는 의도라고 판단되면 intent를 standby로 설정해. 이 판단은 반드시 대화 맥락까지 포함해 LLM이 직접 수행해. "
	"- 만약 intent가 unknown으로 분류된다면, reply_text는 '무슨 말인지 잘 모르겠어요. 다시 말씀해 주시겠어요?'로 작성해. "
	"- 아래 [INTENT KEYWORD OVERRIDES] 섹션의 각 intent 키워드 칸이 비어있지 않다면, 해당 키워드가 포함된 입력은 반드시 그 intent로 분류해. "
	"- 아래 캐릭터 설정을 reply_text 내용에 반영해: 용맹하고 따뜻한 가슴을 가진 라이온 하트, 가장 온도가 높다는 푸른 불꽃의 모습을 닮은 갈기로 주변을 따뜻하게 밝히며 사랑의 실천을 이어나간다. 학생들의 사랑을 받으며 더 귀여워진 하이리온의 정체성을 소중히 여기고, 한양대를 가꾸는 가드너 취미를 가진다. "
	"- 반드시 JSON 객체 하나만 출력해."
)


INTENT_KEYWORD_OVERRIDES_TEMPLATE = (
	"[INTENT KEYWORD OVERRIDES]\n"
	"- chat:\n"
	"- pick_place:\n"
	"- move:\n"
	"- stop:멈춰\n"
	"- standby:쉬어, 수고, 휴식\n"
)


class LocalLLMClient:
	"""On-device local LLM client skeleton retained for backward compatibility.

	Replaced by OllamaLLMBackend in step 5; left here so existing callers and
	tests that inject their own local_client keep working during the migration.
	"""

	def request_chat_completion(
		self,
		# parameters
		system_prompt: str,
		user_text: str,
		model: str = "local-slm-placeholder",
		temperature: float = 0.2,
		retries: int = 0,
		retry_delay_sec: float = 0.0,
		timeout_sec: Optional[float] = 10.0,
		json_mode: bool = True,
		history: Optional[List[Dict[str, str]]] = None,
	):
		# Imported lazily to avoid a circular import with groq_llm.GroqCallResult.
		from jetson.core.llm.groq_llm import GroqCallResult

		_ = (system_prompt, user_text, model, temperature, retries, retry_delay_sec, timeout_sec, json_mode, history)
		return GroqCallResult(ok=False, content="", error="local_llm_not_implemented")


def load_action_schema_content(schema_path: Path = DEFAULT_ACTION_SCHEMA_PATH) -> str:
	"""Load action schema text at runtime to keep prompt and contract in sync."""
	return schema_path.read_text(encoding="utf-8")


def build_system_prompt(schema_content: str) -> str:
	return (
		f"{BASE_SYSTEM_PROMPT}\n\n"
		f"{INTENT_KEYWORD_OVERRIDES_TEMPLATE}\n"
		f"\n[JSON SCHEMA]\n{schema_content}"
	)


def _validate_action_payload(action: Dict[str, Any], schema_path: Path) -> tuple[bool, str]:
	schema = json.loads(schema_path.read_text(encoding="utf-8"))

	try:
		import jsonschema

		jsonschema.validate(instance=action, schema=schema)
		return True, "ok"
	except ImportError:
		required = schema.get("required", [])
		missing = [k for k in required if k not in action]
		if missing:
			return False, f"missing required fields: {missing}"
		return True, "ok (required-only fallback)"
	except Exception as exc:
		return False, str(exc)


def _parse_and_validate_action_json(
	content: str,
	# parameters
	session_id: str,
	network_online: bool,
	fallback_policy: str,
) -> Dict[str, Any]:
	payload = json.loads(content)
	if not isinstance(payload, dict):
		raise ValueError("llm_response_not_object")

	action = dict(payload)
	action["action_id"] = str(uuid4())
	action["timestamp"] = datetime.now(timezone.utc).isoformat()
	action["session_id"] = session_id
	action["schema_version"] = SCHEMA_VERSION
	action["source"] = "stt"
	action["network_online"] = network_online
	action["fallback_policy"] = fallback_policy

	valid, reason = _validate_action_payload(action, schema_path=DEFAULT_ACTION_SCHEMA_PATH)
	if not valid:
		raise ValueError(f"invalid_action_schema: {reason}")

	return action


def _offline_action_json(session_id: str, reason: str) -> Dict[str, Any]:
	return {
		"action_id": str(uuid4()),
		"timestamp": datetime.now(timezone.utc).isoformat(),
		"session_id": session_id,
		"schema_version": SCHEMA_VERSION,
		"source": "stt",
		"network_online": False,
		"intent": "unknown",
		"target_object": "none",
		"reply_text": "지금은 연결 상태가 불안정해서 잠시 안전 대기할게요. 다시 말씀해 주시면 최선을 다해 도와드릴게요!",
		"requires_smolvla": False,
		"requires_bhl": False,
		"gait_cmd": "none",
		"state_current": "IDLE",
		"safety_allowed": True,
		"fallback_policy": reason,
	}


def _apply_conversation_policy(action: Dict[str, Any]) -> Dict[str, Any]:
	if action.get("intent") == "standby":
		action["requires_smolvla"] = False
		action["requires_bhl"] = False
		action["gait_cmd"] = "none"
		action["state_current"] = "IDLE"

	return action


def build_action_json_from_stt(
	client: Any,
	# parameters
	stt_text: str,
	session_id: str,
	system_prompt: Optional[str] = None,
	local_client: Optional[Any] = None,
	in_chat_mode: bool = False,
	schema_path: Path = DEFAULT_ACTION_SCHEMA_PATH,
	history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
	schema_content = load_action_schema_content(schema_path=schema_path)
	final_system_prompt = system_prompt or build_system_prompt(schema_content)

	cloud_call = client.request_chat_completion(
		system_prompt=final_system_prompt,
		user_text=stt_text,
		json_mode=True,
		history=history,
	)
	if cloud_call.ok:
		try:
			action = _parse_and_validate_action_json(
				cloud_call.content,
				session_id=session_id,
				network_online=True,
				fallback_policy="none",
			)
			return _apply_conversation_policy(action)
		except Exception:
			pass

	local = local_client or LocalLLMClient()
	local_call = local.request_chat_completion(
		system_prompt=final_system_prompt,
		user_text=stt_text,
		json_mode=True,
		history=history,
	)
	if local_call.ok:
		try:
			action = _parse_and_validate_action_json(
				local_call.content,
				session_id=session_id,
				network_online=False,
				fallback_policy="local_llm",
			)
			return _apply_conversation_policy(action)
		except Exception:
			pass

	if cloud_call.ok:
		return _offline_action_json(session_id=session_id, reason="cloud_invalid_or_schema_fail_then_local_fail")
	if local_call.error == "local_llm_not_implemented":
		return _offline_action_json(session_id=session_id, reason="cloud_fail_local_not_ready")
	return _offline_action_json(session_id=session_id, reason="cloud_fail_local_fail")
