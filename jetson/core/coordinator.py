from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from time import sleep
from uuid import uuid4

# parameters
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LIVE_AUDIO_DIR = PROJECT_ROOT / "data" / "episodes"
SESSION_LOG_DIR = PROJECT_ROOT / "data" / "sessions"
AUTO_STANDBY_COOLDOWN_SEC = 1.5
CHAT_STANDBY_COOLDOWN_SEC = 1.2
# parameter: number of recent (user, assistant) turn pairs kept in the LLM context.
# Increase for longer memory at the cost of more tokens / latency per request.
MAX_HISTORY_TURNS = 10

from jetson.cloud.groq_client import GroqClient, build_action_json_from_stt
from jetson.core.brain.network_probe import is_online
from jetson.expression.mouth_servo import cleanup_gpio, MouthServoController
from jetson.expression.wake_word import build_wake_word_listener
from jetson.expression.speaker import DEFAULT_CLOVA_SPEAKER, build_tts_backend
from jetson.expression.microphone import record_to_wav
from jetson.expression.stt_whisper import build_input_event, transcribe_wav



def _print_block(title: str, payload: dict) -> None:
	print("\n" + "=" * 72)
	print(title)
	print("=" * 72)
	print(json.dumps(payload, ensure_ascii=False, indent=2))


def _append_session_log(session_id: str, entry: dict) -> None:
	SESSION_LOG_DIR.mkdir(parents=True, exist_ok=True)
	log_path = SESSION_LOG_DIR / f"{session_id}.jsonl"
	stamped = {"timestamp": datetime.now(timezone.utc).isoformat(), **entry}
	with log_path.open("a", encoding="utf-8") as fh:
		fh.write(json.dumps(stamped, ensure_ascii=False) + "\n")


def _truncate_history(history: list[dict], max_turns: int) -> list[dict]:
	max_messages = max_turns * 2
	if len(history) <= max_messages:
		return history
	return history[-max_messages:]


def _build_standby_action(session_id: str, reason: str = "task_completed") -> dict:
	return {
		"action_id": str(uuid4()),
		"timestamp": datetime.now(timezone.utc).isoformat(),
		"session_id": session_id,
		"schema_version": "1.0",
		"source": "stt",
		"network_online": True,
		"intent": "standby",
		"target_object": "none",
		"reply_text": "작업을 마쳤고, 다음 지시를 기다릴게요.",
		"requires_smolvla": False,
		"requires_bhl": False,
		"gait_cmd": "none",
		"state_current": "IDLE",
		"safety_allowed": True,
		"fallback_policy": reason,
	}


def _probe_real_groq_connection(client: GroqClient) -> None:
	probe = client.request_chat_completion(
		system_prompt='Return JSON only: {"ok": true}',
		user_text="연결 점검",
		retries=0,
		retry_delay_sec=0.0,
		timeout_sec=10.0,
		json_mode=True,
	)
	if not probe.ok:
		raise RuntimeError(f"Groq API connection failed: {probe.error}")


class LocalLLM:
	def build_action_json_from_stt(self, stt_text: str, session_id: str, in_chat_mode: bool) -> dict:
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


def _build_turn_services(online: bool):
	if online:
		try:
			client = GroqClient()
			_probe_real_groq_connection(client)
			tts_backend = build_tts_backend(
				is_online=True,
				speaker=DEFAULT_CLOVA_SPEAKER,
				tts_provider="clova",
			)
			return True, client, tts_backend
		except Exception as exc:
			print(f"[Hybrid] online route unavailable -> fallback to offline stub: {exc}")

	local_llm = LocalLLM()
	tts_backend = build_tts_backend(is_online=False)
	return False, local_llm, tts_backend


def _route_action(action_json: dict) -> None:
	intent = action_json.get("intent")
	if intent == "pick_place":
		print("[Executor] pick_place -> SMOLVLA executor route")
	elif intent in {"move", "stop"}:
		print("[Executor] move/stop -> BHL executor route")
	elif intent == "chat":
		print("[Executor] chat -> reply/TTS route")
	else:
		print("[Executor] no-op route")

	# Phase 4 mock executor delay.
	sleep(0.2)


def _speak_reply_if_any(action_json: dict, stage: str, tts_backend, mouth_servo=None) -> None:
	reply_text = str(action_json.get("reply_text", "")).strip()
	if not reply_text:
		print(f"[Speaker] {stage} -> no reply_text; skip")
		return

	try:
		tts_params = action_json.get("tts", {}) if isinstance(action_json.get("tts"), dict) else {}
		elapsed = tts_backend.speak_with_lipsync(
			reply_text,
			mouth_servo=mouth_servo,
			speaker=str(tts_params.get("speaker", DEFAULT_CLOVA_SPEAKER)),
			voice=tts_params.get("voice"),
			pitch=tts_params.get("pitch"),
			rate=tts_params.get("rate"),
			speed=tts_params.get("speed"),
			volume=tts_params.get("volume"),
			audio_format=tts_params.get("format"),
			emotion=tts_params.get("emotion"),
			emotion_strength=tts_params.get("emotion_strength"),
		)
		print(f"[Speaker] {stage} -> done ({elapsed:.2f}s)")
	except Exception as exc:
		print(f"[Speaker] {stage} -> failed: {exc}")


def _build_greeting_action(session_id: str) -> dict:
	"""Build a greeting action that triggers chat mode with lip-sync response."""
	return {
		"action_id": str(uuid4()),
		"timestamp": datetime.now(timezone.utc).isoformat(),
		"session_id": session_id,
		"schema_version": "1.0",
		"source": "wake_word",
		"network_online": True,
		"intent": "chat",
		"target_object": "none",
		"reply_text": "네, 말씀하세요!",
		"requires_smolvla": False,
		"requires_bhl": False,
		"gait_cmd": "none",
		"state_current": "IDLE",
		"safety_allowed": True,
		"fallback_policy": "greeting",
	}


def run_live_pipeline(
	record_sec: float,
	preferred_keyword: str,
	whisper_model_size: str,
	whisper_language: str,
    wakeword_listener,
) -> None:
	session_id = f"sess-live-{uuid4().hex[:8]}"
	# Conversation memory persists across wake-word re-activations within a single
	# program run; restarting the process starts a fresh session_id and empty history.
	history: list[dict] = []
	_append_session_log(session_id, {"event": "session_start", "session_id": session_id})

	# Initialize mouth servo for lip-sync
	mouth_servo = MouthServoController(pin=33)
	# MouthServoController initializes on first use, no explicit init() needed
	print(f"[MouthServo] created (available: {mouth_servo.is_available})")

	print("HYlion coordinator wake-word mode")
	print("- Real microphone capture")
	print("- Wake word trigger")
	print("- Whisper STT")
	print("- Real Groq action generation")
	print("- Auto standby after each completed turn")
	print("Waiting for wake word...")

	while True:
		activation = wakeword_listener.wait_for_wake_word()
		print(
			f"[Wake Word] label={activation.label}, score={activation.score:.3f}, "
			f"source={activation.source}, device={activation.device_name}"
		)

		online = is_online()
		print(f"[Network] is_online={online}")
		online, llm_backend, tts_backend = _build_turn_services(online)

		# Issue greeting action to enter chat mode (greeting is a meta-event and is
		# intentionally NOT added to LLM history so it doesn't pollute the dialogue).
		greeting_action = _build_greeting_action(session_id=session_id)
		_print_block("ACTION_JSON (GREETING)", greeting_action)
		_speak_reply_if_any(greeting_action, stage="greeting", tts_backend=tts_backend, mouth_servo=mouth_servo)
		_append_session_log(session_id, {"event": "wake_activation", "label": activation.label, "score": activation.score})

		in_chat_mode = True

		# Chat mode loop: keep listening without waiting for wake word again
		while in_chat_mode:
			wav_path = LIVE_AUDIO_DIR / f"live_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
			print("[Mic] Ready. Speak after the START line.")
			print(f"[Mic] START recording for {record_sec:.1f}s -> {wav_path}")
			recorded_path = record_to_wav(
				output_path=str(wav_path),
				duration_sec=record_sec,
				preferred_keyword=preferred_keyword,
			)
			print("[Mic] STOP recording")

			stt_result = transcribe_wav(
				recorded_path,
				model_size=whisper_model_size,
				language=whisper_language,
			)

			if not stt_result.text.strip():
				print("[STT] Empty transcription. Keeping current mode.")
				continue

			input_event = build_input_event(stt_result=stt_result, session_id=session_id, source="stt")
			_print_block("INPUT_JSON", input_event)

			if online:
				action_json = build_action_json_from_stt(
					client=llm_backend,
					stt_text=stt_result.text,
					session_id=session_id,
					in_chat_mode=in_chat_mode,
					history=history,
				)
			else:
				action_json = llm_backend.build_action_json_from_stt(
					stt_text=stt_result.text,
					session_id=session_id,
					in_chat_mode=in_chat_mode,
				)
			_print_block("ACTION_JSON", action_json)

			intent = action_json.get("intent", "unknown")
			reply_text = str(action_json.get("reply_text", "")).strip()
			# Update conversation memory with this turn (user utterance + assistant reply).
			history.append({"role": "user", "content": stt_result.text})
			if reply_text:
				history.append({"role": "assistant", "content": reply_text})
			history = _truncate_history(history, MAX_HISTORY_TURNS)
			_append_session_log(session_id, {
				"event": "turn",
				"intent": intent,
				"user_text": stt_result.text,
				"assistant_text": reply_text,
			})

			_speak_reply_if_any(action_json, stage=f"before_{intent}", tts_backend=tts_backend, mouth_servo=mouth_servo)

			if intent in {"chat", "unknown"}:
				# Chat (or unknown — re-prompt the user) continues; listen for next utterance
				print(f"[Mode] {intent} -> chat loop continues. Listening for next utterance.")
				continue

			if intent == "standby":
				# User ended conversation; exit chat mode immediately
				if CHAT_STANDBY_COOLDOWN_SEC > 0:
					print(f"[Mode] chat-standby cooldown for {CHAT_STANDBY_COOLDOWN_SEC:.1f}s before re-arming wake word.")
					sleep(CHAT_STANDBY_COOLDOWN_SEC)
				in_chat_mode = False
				print("[Mode] returned to wake-word standby.")
				continue

			# Non-chat, non-standby intent: execute action, then generate auto-standby
			_route_action(action_json)

			standby_action = _build_standby_action(session_id=session_id, reason=f"auto_after_{intent}")
			_print_block("ACTION_JSON (AUTO-STANDBY)", standby_action)
			_speak_reply_if_any(standby_action, stage=f"after_{intent}", tts_backend=tts_backend, mouth_servo=mouth_servo)
			if AUTO_STANDBY_COOLDOWN_SEC > 0:
				print(f"[Mode] standby cooldown for {AUTO_STANDBY_COOLDOWN_SEC:.1f}s before re-arming wake word.")
				sleep(AUTO_STANDBY_COOLDOWN_SEC)
			in_chat_mode = False
			print("[Mode] returned to wake-word standby.")


def _parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Run live mic->Whisper->Groq coordinator loop.")
	parser.add_argument("--record-sec", type=float, default=4.0, help="Microphone record duration per turn")
	parser.add_argument("--preferred-keyword", default="USB", help="Preferred mic device name keyword")
	parser.add_argument("--whisper-model-size", default="base", help="faster-whisper model size")
	parser.add_argument("--whisper-language", default="ko", help="Whisper language hint")
	return parser.parse_args()


def main() -> None:
	args = _parse_args()
	wakeword_listener = None
	try:
		wakeword_listener = build_wake_word_listener()
		run_live_pipeline(
			record_sec=args.record_sec,
			preferred_keyword=args.preferred_keyword,
			whisper_model_size=args.whisper_model_size,
			whisper_language=args.whisper_language,
			wakeword_listener=wakeword_listener,
		)
	except KeyboardInterrupt:
		print("Coordinator stopped by user.")
	finally:
		if wakeword_listener is not None:
			try:
				wakeword_listener.close()
			except Exception as exc:
				print(f"[Cleanup] wakeword listener close failed: {exc}")
		try:
			cleanup_gpio()
		except Exception as exc:
			print(f"[Cleanup] GPIO cleanup failed: {exc}")


if __name__ == "__main__":
	main()
