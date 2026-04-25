from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict
from uuid import uuid4


SCHEMA_VERSION = "1.0"


class MessageType(str, Enum):
	INPUT_EVENT = "input_event"
	ACTION_JSON = "action_json"
	EXECUTOR_COMMAND = "executor_command"
	EMERGENCY_EVENT = "emergency_event"
	ACK = "ack"


@dataclass(frozen=True)
class MessageHeader:
	msg_type: MessageType
	session_id: str
	source: str
	seq: int
	timestamp: str
	event_id: str
	schema_version: str = SCHEMA_VERSION

	def to_dict(self) -> Dict[str, Any]:
		return {
			"msg_type": self.msg_type.value,
			"session_id": self.session_id,
			"source": self.source,
			"seq": self.seq,
			"timestamp": self.timestamp,
			"event_id": self.event_id,
			"schema_version": self.schema_version,
		}


def utc_now_iso() -> str:
	return datetime.now(timezone.utc).isoformat()


def make_header(msg_type: MessageType, session_id: str, source: str, seq: int) -> MessageHeader:
	return MessageHeader(
		msg_type=msg_type,
		session_id=session_id,
		source=source,
		seq=seq,
		timestamp=utc_now_iso(),
		event_id=str(uuid4()),
	)


def wrap_message(header: MessageHeader, payload: Dict[str, Any]) -> Dict[str, Any]:
	return {
		**header.to_dict(),
		"payload": payload,
	}


def make_ack(session_id: str, source: str, seq: int, ack_seq: int) -> Dict[str, Any]:
	header = make_header(MessageType.ACK, session_id=session_id, source=source, seq=seq)
	return wrap_message(header, payload={"ack_seq": ack_seq})
