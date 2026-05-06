from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4


class OfflineStubLLMBackend:
	"""Step 3 placeholder for the offline LLM path; replaced by Ollama in step 5.

	Mirrors the LocalLLM class previously embedded in coordinator.py so
	post-flatten behavior is byte-identical to the pre-refactor pipeline.
	"""

	name = "offline-stub"

	def warm_up(self) -> None:
		return None

	def build_action(
		self,
		stt_text: str,
		*,
		session_id: str,
		history: List[Dict[str, str]],
		in_chat_mode: bool,
	) -> Dict[str, Any]:
		print("[Offline Mode] LocalLLM 동작 예정 (현재 미구현)")
		reply_text = "오프라인 모드는 아직 준비 중이에요."
		intent = "standby" if stt_text.strip() else "unknown"
		return {
			"action_id": str(uuid4()),
			"timestamp": datetime.now(timezone.utc).isoformat(),
			"session_id": session_id,
			"schema_version": "1.0",
			"source": "local_llm_stub",
			"network_online": False,
			"intent": intent,
			"target_object": "none",
			"reply_text": reply_text,
			"requires_smolvla": False,
			"requires_bhl": False,
			"gait_cmd": "none",
			"state_current": "IDLE",
			"safety_allowed": True,
			"fallback_policy": "offline_stub",
		}
