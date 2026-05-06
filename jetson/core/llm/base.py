from __future__ import annotations

from typing import Any, Dict, List, Protocol, runtime_checkable


@runtime_checkable
class LLMBackend(Protocol):
    name: str

    def build_action(
        self,
        stt_text: str,
        *,
        session_id: str,
        history: List[Dict[str, str]],
        in_chat_mode: bool,
    ) -> Dict[str, Any]: ...

    def warm_up(self) -> None: ...
