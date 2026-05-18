from __future__ import annotations

import argparse
import json
import os
import re
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
MAX_HISTORY_TURNS = 4
# parameter: silence gate. A recorded turn whose loudest 30ms frame RMS stays
# below this is treated as "no speech" -> Whisper is skipped and the turn is
# handled as `unknown` (Whisper hallucinates fixed filler phrases on silence).
# Lower it if real speech keeps falling through to unknown; raise it if silence
# still leaks past the gate.
SPEECH_RMS_THRESHOLD = 400
# parameter: no-speech escalation in chat mode. The first SILENT_QUIET_TURNS
# silent turns just listen again in silence; the next one (turn
# SILENT_QUIET_TURNS + 1) speaks a single re-prompt; a silent turn after that
# ends chat mode and returns to wake-word standby.
SILENT_QUIET_TURNS = 0
# parameter: Whisper hallucination filter. A noise-only clip can clear the RMS
# gate yet carry no real speech; Whisper then fills it with one of a small set
# of fixed filler phrases ("감사합니다." 등) instead of an empty string. Those
# phrases are not user input — a turn whose ENTIRE transcript normalizes to one
# of them is treated exactly like a silent turn (-> unknown, never sent to the
# LLM). Matching is exact on the normalized transcript, never substring, so real
# speech that merely contains one of these words is left untouched. Add a phrase
# here (lowercase, no surrounding punctuation) if a new hallucination shows up.
WHISPER_HALLUCINATION_PHRASES = frozenset({
	"감사합니다",
	"고맙습니다",
	"시청해주셔서 감사합니다",
	"시청해 주셔서 감사합니다",
	"오늘도 시청해주셔서 감사합니다",
	"구독과 좋아요 부탁드립니다",
	"구독 부탁드립니다",
	"구독과 좋아요 알림설정 부탁드립니다",
	"다음 영상에서 만나요",
	"다음 시간에 만나요",
	"이 영상은 유료광고를 포함하고 있습니다",
})

from jetson.core.bhl_client import BhlClient
from jetson.core.gesture_client import start_gesture_daemon
from jetson.core.llm import build_llm_backend
from jetson.core.network import is_online
from jetson.core.stt import build_input_event, build_stt_backend
from jetson.core.stt.local_whisper import warm_up as warm_up_local_whisper
from jetson.expression.microphone import record_to_wav, wav_has_speech
from jetson.expression.mouth_servo import cleanup_gpio, MouthServoController
from jetson.expression.speaker import DEFAULT_CLOVA_SPEAKER, build_tts_backend
from jetson.expression.wake_word import build_wake_word_listener


# BHL 동작 완료 알림 timeout 여유분(초). duration_sec + 이 값까지 대기.
BHL_DONE_TIMEOUT_MARGIN_SEC = 2.0
# duration_sec 누락/0 일 때 사용할 기본 대기 (BhlClient.wait_for_done 의 timeout 계산용).
BHL_DEFAULT_DURATION_SEC = 3.0



def _print_block(title: str, payload: dict) -> None:
	print("\n" + "=" * 72)
	print(title)
	print("=" * 72)
	print(json.dumps(payload, ensure_ascii=False, indent=2))


_WHITESPACE_RE = re.compile(r"\s+")


def _normalize_transcript(text: str) -> str:
	"""Normalize a transcript for hallucination matching.

	Strips surrounding whitespace/quotes/punctuation, collapses internal runs of
	whitespace to a single space, and lowercases — so "시청해  주셔서 감사합니다."
	and "시청해 주셔서 감사합니다" compare equal against WHISPER_HALLUCINATION_PHRASES.
	"""
	cleaned = text.strip().strip(".!?…。\"'` ").strip()
	return _WHITESPACE_RE.sub(" ", cleaned).lower()


def _is_whisper_hallucination(text: str) -> bool:
	"""True iff the whole transcript is a known Whisper silence-hallucination.

	Exact match on the normalized transcript only — a real utterance that merely
	contains one of these phrases as a substring is NOT flagged.
	"""
	return _normalize_transcript(text) in WHISPER_HALLUCINATION_PHRASES


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
		"gesture_name": "none",
		"duration_sec": 0.0,
		"state_current": "IDLE",
		"safety_allowed": True,
		"fallback_policy": reason,
	}


def _build_unknown_action(session_id: str, reason: str = "no_speech", reply_text: str = "") -> dict:
	"""Action for a turn that carried no usable speech.

	A silent recording must never reach the LLM — Whisper hallucinates fixed
	filler phrases ("감사합니다." 등) on silence, which would otherwise become a
	bogus chat turn. We synthesize an `unknown` action directly: intent=unknown
	keeps the chat loop alive (run_live_pipeline treats chat/unknown alike).

	reply_text is empty by default so the robot stays quiet on a silent turn;
	the caller passes a non-empty re-prompt only on the escalation turn (see
	SILENT_QUIET_TURNS), so the robot asks the user to repeat exactly once
	instead of nagging every silent turn.
	"""
	return {
		"action_id": str(uuid4()),
		"timestamp": datetime.now(timezone.utc).isoformat(),
		"session_id": session_id,
		"schema_version": "1.0",
		"source": "stt",
		"network_online": True,
		"intent": "unknown",
		"target_object": "none",
		"reply_text": reply_text,
		"requires_smolvla": False,
		"requires_bhl": False,
		"gait_cmd": "none",
		"gesture_name": "none",
		"duration_sec": 0.0,
		"state_current": "IDLE",
		"safety_allowed": True,
		"fallback_policy": reason,
	}


def _build_turn_services(
	online: bool,
	*,
	whisper_model_size: str,
	whisper_language: str,
):
	"""Pick STT/LLM/TTS backends for this turn.

	If the online path fails its warm-up probe (e.g. Groq unreachable despite
	is_online=True), fall back to offline backends so the user still gets a
	response this turn.
	"""
	if online:
		try:
			llm_backend = build_llm_backend(online=True)
			llm_backend.warm_up()
			stt_backend = build_stt_backend(
				online=True,
				model_size=whisper_model_size,
				language=whisper_language,
			)
			tts_backend = build_tts_backend(
				is_online=True,
				speaker=DEFAULT_CLOVA_SPEAKER,
				tts_provider="clova",
			)
			return True, stt_backend, llm_backend, tts_backend
		except Exception as exc:
			print(f"[Hybrid] online route unavailable -> fallback to offline stub: {exc}")

	stt_backend = build_stt_backend(
		online=False,
		model_size=whisper_model_size,
		language=whisper_language,
	)
	llm_backend = build_llm_backend(online=False)
	tts_backend = build_tts_backend(is_online=False)
	return False, stt_backend, llm_backend, tts_backend


def _route_action(action_json: dict, bhl_client: BhlClient | None = None) -> None:
	"""intent 별 executor 분기.

	BHL 라우트는 bhl_client 가 주어지면 실제로 NUC bridge 로 송신하고 DONE 까지 대기.
	bhl_client 가 None 이면 옛 동작(stdout 로그만) — 테스트/오프라인 디버깅용.
	"""
	intent = action_json.get("intent")
	if intent == "pick_place":
		print("[Executor] pick_place -> SMOLVLA executor route")
		sleep(0.2)
		return

	if intent in {"move", "stop"}:
		if bhl_client is None:
			print("[Executor] move/stop -> BHL executor route (bhl_client=None, stub)")
			sleep(0.2)
			return
		_dispatch_to_bhl(action_json, bhl_client)
		return

	if intent == "chat":
		print("[Executor] chat -> reply/TTS route")
	else:
		print("[Executor] no-op route")
	sleep(0.2)


def _play_gesture_if_any(action_json: dict, gesture_daemon) -> None:
	"""Replay a gesture on the right arm if this turn's action carries one.

	gesture_name is a harness-derived field (keyword detection in prompt.py)
	that is only ever non-"none" on a `chat` turn — gestures are a side-effect
	of conversation, not a standalone intent.

	The call is non-blocking: gesture_daemon.play() hands the gesture name to
	the persistent daemon (which holds lerobot + the arm connection warm) and
	returns on the daemon's immediate ACK. The arm then replays on the daemon's
	worker thread, concurrently with this turn's TTS reply + mouth servo. A
	failed or unavailable gesture is only logged — it must never break the chat
	loop.
	"""
	gesture_name = str(action_json.get("gesture_name", "none")).strip()
	if not gesture_name or gesture_name == "none":
		return

	ok, msg = gesture_daemon.play(gesture_name)
	if ok:
		print(f"[Gesture] {gesture_name} -> 데몬 수락 ({msg})")
	else:
		# 데몬 미가동/미준비/큐가득/데이터오류 — 전부 로그만, 대화 루프는 유지.
		print(f"[Gesture] {gesture_name} -> 재생 불가: {msg}")


def _dispatch_to_bhl(action_json: dict, bhl_client: BhlClient) -> None:
	"""BHL 라우트 본체. 송신 → DONE 대기 → idle 복귀.

	안전 원칙:
	  - 모든 통신 예외를 흡수해서 coordinator main 흐름이 죽지 않게 함
	  - DONE 못 받으면 timeout 으로 끝내고 음성 안내 (이 함수 호출자가 처리)
	  - 마지막에 반드시 bhl_client.clear() 호출 (다음 명령이 자동 송신되지 않도록)
	"""
	action_id = action_json.get("action_id") or "unknown"
	intent = action_json.get("intent")
	duration = float(action_json.get("duration_sec") or BHL_DEFAULT_DURATION_SEC)
	timeout = duration + BHL_DONE_TIMEOUT_MARGIN_SEC
	# stop intent 는 bridge 가 즉시 DONE 회신하므로 짧은 timeout
	if intent == "stop":
		timeout = BHL_DONE_TIMEOUT_MARGIN_SEC

	try:
		bhl_client.set_command(action_json)
		print(f"[BHL] TX action_id={action_id} intent={intent} gait={action_json.get('gait_cmd')} "
		      f"duration={duration:.1f}s timeout={timeout:.1f}s")

		got_done, reason = bhl_client.wait_for_done(action_id, timeout=timeout)
		if got_done:
			print(f"[BHL] DONE action_id={action_id} reason={reason}")
		else:
			print(f"[BHL] TIMEOUT action_id={action_id} (no DONE within {timeout:.1f}s)")
	except Exception as exc:
		print(f"[BHL] dispatch failed: {exc}")
	finally:
		try:
			bhl_client.clear()
		except Exception as exc:
			print(f"[BHL] clear failed: {exc}")


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
		"gesture_name": "none",
		"duration_sec": 0.0,
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
	gesture_daemon,
	bhl_client: BhlClient | None = None,
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

	print("Waiting for wake word...")

	while True:
		activation = wakeword_listener.wait_for_wake_word()
		print(
			f"[Wake Word] label={activation.label}, score={activation.score:.3f}, "
			f"device={activation.device_name}"
		)

		online_probe = is_online()
		print(f"[Network] is_online={online_probe}")
		online, stt_backend, llm_backend, tts_backend = _build_turn_services(
			online_probe,
			whisper_model_size=whisper_model_size,
			whisper_language=whisper_language,
		)
		print(f"[Backends] stt={stt_backend.name} llm={llm_backend.name}")

		# Issue greeting action to enter chat mode (greeting is a meta-event and is
		# intentionally NOT added to LLM history so it doesn't pollute the dialogue).
		greeting_action = _build_greeting_action(session_id=session_id)
		_print_block("ACTION_JSON (GREETING)", greeting_action)
		_speak_reply_if_any(greeting_action, stage="greeting", tts_backend=tts_backend, mouth_servo=mouth_servo)
		_append_session_log(session_id, {"event": "wake_activation", "label": activation.label, "score": activation.score})

		in_chat_mode = True
		# Consecutive no-speech turns in this chat session. Reset on every turn
		# that carries real speech; drives the SILENT_QUIET_TURNS escalation
		# (quiet -> single re-prompt -> wake-word standby).
		silent_turns = 0

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

			# 무음 게이트: 발화가 없는 녹음은 STT/LLM 으로 보내지 않는다. Whisper 는
			# 무음 클립에 "감사합니다." 같은 고정 환각 문구를 만들어내고, 그게
			# 그대로 LLM 입력이 되어 가짜 턴이 된다. 발화가 있을 때만 전사하고,
			# 빈 전사도 같은 무음 턴으로 취급한다.
			has_speech, peak_rms = wav_has_speech(recorded_path, rms_threshold=SPEECH_RMS_THRESHOLD)
			stt_result = stt_backend.transcribe(recorded_path) if has_speech else None

			transcript = stt_result.text.strip() if stt_result is not None else ""
			# 무음 클립이 RMS 게이트를 통과해 STT 까지 가면 Whisper 는 빈 문자열
			# 대신 고정 환각 문구를 채워 넣는다. 전사 전체가 그 문구면 사용자
			# 입력이 아니므로 무음 턴과 똑같이 처리한다 (LLM 입력으로 보내지 않음).
			is_hallucination = bool(transcript) and _is_whisper_hallucination(transcript)

			if not transcript or is_hallucination:
				# 무음 턴 escalation: 처음 SILENT_QUIET_TURNS 회는 조용히 다시
				# 듣고, 그 다음 1회는 한 번 되묻고, 그래도 무음이면 채팅 모드를
				# 끝내고 wake-word 대기로 복귀한다.
				silent_turns += 1
				if not has_speech:
					reason = "no_speech"
					print(f"[STT] 발화 없음 (peak_rms={peak_rms} < {SPEECH_RMS_THRESHOLD}) -> 무음 턴 {silent_turns}")
				elif is_hallucination:
					reason = "whisper_hallucination"
					print(f"[STT] Whisper 환각 문구 무시: {transcript!r} -> 무음 턴 {silent_turns}")
				else:
					reason = "empty_transcription"
					print(f"[STT] 빈 전사 -> 무음 턴 {silent_turns}")

				if silent_turns > SILENT_QUIET_TURNS + 1:
					print("[Mode] 무음이 계속됨 -> wake-word 대기로 복귀.")
					_append_session_log(session_id, {"event": "silent_standby", "silent_turns": silent_turns})
					if CHAT_STANDBY_COOLDOWN_SEC > 0:
						print(f"[Mode] chat-standby cooldown for {CHAT_STANDBY_COOLDOWN_SEC:.1f}s before re-arming wake word.")
						sleep(CHAT_STANDBY_COOLDOWN_SEC)
					in_chat_mode = False
					continue

				if silent_turns == SILENT_QUIET_TURNS + 1:
					# 마지막 1회: 사용자에게 한 번 되묻는다.
					unknown_action = _build_unknown_action(
						session_id,
						reason=f"{reason}_reprompt",
						reply_text="무슨 말인지 잘 모르겠어요. 다시 말씀해 주시겠어요?",
					)
				else:
					# 조용히 다시 듣는다 (reply_text 비어 있음 -> TTS skip).
					unknown_action = _build_unknown_action(session_id, reason=reason)

				_print_block("ACTION_JSON (UNKNOWN)", unknown_action)
				_speak_reply_if_any(unknown_action, stage="unknown", tts_backend=tts_backend, mouth_servo=mouth_servo)
				_append_session_log(session_id, {
					"event": "turn",
					"intent": "unknown",
					"user_text": "",
					"assistant_text": unknown_action["reply_text"],
				})
				continue

			# 발화가 있는 정상 턴 -> 무음 카운터 리셋.
			silent_turns = 0

			input_event = build_input_event(stt_result=stt_result, session_id=session_id, source="stt")
			_print_block("INPUT_JSON", input_event)

			action_json = llm_backend.build_action(
				stt_text=stt_result.text,
				session_id=session_id,
				history=history,
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

			# A chat turn may carry a keyword-detected gesture. Fire it BEFORE
			# speaking so the arm moves concurrently with the TTS reply + mouth
			# servo — gesture_daemon.play() is non-blocking (the daemon ACKs and
			# replays on its own worker thread). gesture_name is forced "none"
			# for non-chat turns upstream, so this safely no-ops outside chat.
			_play_gesture_if_any(action_json, gesture_daemon)

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
			_route_action(action_json, bhl_client=bhl_client)

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
	parser.add_argument("--whisper-model-size", default="small", help="openai-whisper model size (tiny/base/small/medium/large)")
	parser.add_argument("--whisper-language", default="ko", help="Whisper language hint")
	return parser.parse_args()


def _startup_warm_up(args: argparse.Namespace) -> None:
	"""§F5 warm-up policy: warm only the side likely to be hot.

	online → Groq probe (no model load). offline → local whisper + Ollama
	model + MeloTTS daemon model. The other side stays cold and lazy-loads on
	first runtime fallback. Failures here are logged but never abort startup;
	the pipeline degrades gracefully.
	"""
	initial_online = is_online()
	print(f"[Startup] is_online={initial_online}")

	if initial_online:
		try:
			llm = build_llm_backend(online=True)
			llm.warm_up()
			print(f"[Warm-up] LLM  {llm.name} ... OK")
		except Exception as exc:
			print(f"[Warm-up] LLM  online Groq ... FAIL (lazy-load): {exc}")
		return

	try:
		warm_up_local_whisper(model_size=args.whisper_model_size)
		print(f"[Warm-up] STT  whisper-{args.whisper_model_size} ... OK")
	except Exception as exc:
		print(f"[Warm-up] STT  whisper-{args.whisper_model_size} ... FAIL: {exc}")
	llm_label = "ollama"
	try:
		llm = build_llm_backend(online=False)
		llm_label = llm.name
		llm.warm_up()
		print(f"[Warm-up] LLM  {llm_label} ... OK")
	except Exception as exc:
		print(f"[Warm-up] LLM  {llm_label} ... FAIL (lazy-load): {exc}")
	try:
		from jetson.core.tts.melotts_client import MeloTTSSpeaker
		MeloTTSSpeaker(enable_lipsync=False).warm_up()
		print("[Warm-up] TTS  MeloTTS daemon ... OK")
	except Exception as exc:
		print(f"[Warm-up] TTS  MeloTTS daemon ... FAIL (lazy-load): {exc}")


def main() -> None:
	args = _parse_args()
	wakeword_listener = None
	bhl_client: BhlClient | None = None
	# Spawn the gesture daemon first so its ~8-10s warm-up (torch import + arm
	# connect, in the .hylion_arm venv) overlaps with model warm-up below.
	# Failure is non-fatal — start_gesture_daemon() returns a disabled handle.
	gesture_daemon = start_gesture_daemon()
	try:
		wakeword_listener = build_wake_word_listener()
		_startup_warm_up(args)
		if gesture_daemon.wait_ready(timeout=15.0):
			print("[Warm-up] Gesture daemon ... OK")
		else:
			print("[Warm-up] Gesture daemon ... 미준비 (gesture 비활성 상태로 계속)")

		# NUC bridge 연결 클라이언트. NUC 가 꺼져 있어도 백그라운드에서 재연결 시도하므로
		# coordinator 본체는 영향 없음. 명시적으로 비활성화하려면 HYLION_BHL_DISABLE=1.
		if os.environ.get("HYLION_BHL_DISABLE") == "1":
			print("[BHL] HYLION_BHL_DISABLE=1 -> BhlClient skipped (stub mode)")
		else:
			bhl_client = BhlClient()
			bhl_client.start()

		run_live_pipeline(
			record_sec=args.record_sec,
			preferred_keyword=args.preferred_keyword,
			whisper_model_size=args.whisper_model_size,
			whisper_language=args.whisper_language,
			wakeword_listener=wakeword_listener,
			gesture_daemon=gesture_daemon,
			bhl_client=bhl_client,
		)
	except KeyboardInterrupt:
		print("Coordinator stopped by user.")
	finally:
		if bhl_client is not None:
			try:
				bhl_client.stop()
			except Exception as exc:
				print(f"[Cleanup] bhl_client stop failed: {exc}")
		try:
			gesture_daemon.stop()
		except Exception as exc:
			print(f"[Cleanup] gesture daemon stop failed: {exc}")
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
