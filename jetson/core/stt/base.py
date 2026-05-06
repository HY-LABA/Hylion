from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Protocol, runtime_checkable
from uuid import uuid4


@dataclass(frozen=True)
class STTResult:
    text: str
    language: str


@runtime_checkable
class STTBackend(Protocol):
    name: str

    def transcribe(self, wav_path: str, *, language: Optional[str] = None) -> STTResult: ...

    def warm_up(self) -> None: ...


def build_input_event(
    stt_result: STTResult,
    session_id: str,
    source: str = "stt",
    schema_version: str = "1.0",
    confidence: Optional[float] = None,
) -> Dict[str, Any]:
    event: Dict[str, Any] = {
        "event_id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "source": source,
        "schema_version": schema_version,
        "input_text": stt_result.text,
        "language": stt_result.language,
    }

    if confidence is not None:
        event["confidence"] = confidence

    return event
