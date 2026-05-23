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
from jetson.core.online_gate import OnlineGate
from jetson.core.stt import build_input_event, build_stt_backend
from jetson.core.stt.local_whisper import warm_up as warm_up_local_whisper
from jetson.expression.microphone import record_to_wav, wav_has_speech
from jetson.expression.mouth_servo import cleanup_gpio, MouthServoController
from jetson.expression.speaker import DEFAULT_CLOVA_SPEAKER, build_tts_backend
from jetson.expression.wake_word import build_emergency_stop_listener, build_wake_word_listener


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


def _build_emergency_action(session_id: str, after_intent: str = "") -> dict:
	"""Post-emergency announce action — what the robot SAYS after an e-stop.

	두 가지 진입로에서 같은 메시지를 재사용한다:
	  1) e-stop wake-word 트리거 후 BHL DONE reason=="safety_or_emergency" 가
	     돌아온 경우 (현재 _dispatch_to_bhl 경로).
	  2) (예정) LLM 이 직접 intent="emergency" 를 내보내는 경우. 그 시점에
	     action.schema.json 의 intent enum 에 "emergency" 를 추가하고 이 builder
	     의 intent 필드를 "emergency" 로 갈아끼우면 됨. 그 외 필드는 그대로.

	state_current/requires_bhl 은 _build_emergency_stop_action() (bridge 로 보내는
	STOP 명령) 과 의도가 다르다. 그쪽은 EMERGENCY UDP packet 을 트리거하기 위한
	control message 이고, 이쪽은 사용자에게 "비상정지 됐어요" TTS 만 하면 끝.
	그래서 requires_bhl=False, state_current=IDLE.
	"""
	return {
		"action_id": str(uuid4()),
		"timestamp": datetime.now(timezone.utc).isoformat(),
		"session_id": session_id,
		"schema_version": "1.0",
		"source": "wake_word",
		"network_online": True,
		"intent": "standby",  # schema 에 "emergency" 추가되면 그 때 변경
		"target_object": "none",
		"reply_text": "비상정지 했어요!",
		"requires_smolvla": False,
		"requires_bhl": False,
		"gait_cmd": "none",
		"gesture_name": "none",
		"duration_sec": 0.0,
		"state_current": "IDLE",
		"safety_allowed": True,
		"fallback_policy": f"emergency_after_{after_intent}" if after_intent else "emergency",
	}


def _build_emergency_stop_action(session_id: str) -> dict:
	"""Action JSON sent to BHL bridge when the e-stop wake word fires.

	The bridge's map_json_to_packet() checks state_current=="EMERGENCY" as a
	top-priority STOP trigger (priority 2, right after safety_allowed=False),
	and finish_active_action("safety_or_emergency") is invoked, which sends a
	DONE for the currently-active move action. That DONE unblocks the
	coordinator's wait_for_done() so this trigger does not need any direct
	signal back to the main thread.
	"""
	return {
		"action_id": str(uuid4()),
		"timestamp": datetime.now(timezone.utc).isoformat(),
		"session_id": session_id,
		"schema_version": "1.0",
		"source": "wake_word",
		"network_online": True,
		"intent": "stop",
		"target_object": "none",
		"reply_text": "비상정지했어요.",
		"requires_smolvla": False,
		"requires_bhl": True,
		"gait_cmd": "stop",
		"gesture_name": "none",
		"duration_sec": 0.0,
		"state_current": "EMERGENCY",
		"safety_allowed": True,
		"fallback_policy": "emergency_stop_wake_word",
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
	gate: OnlineGate | None = None,
):
	"""Pick STT/LLM/TTS backends for this turn.

	If the online path fails its warm-up probe (e.g. Groq unreachable despite
	is_online=True), fall back to offline backends so the user still gets a
	response this turn — and report the failure to ``gate`` so subsequent
	activations spend one cooldown window in offline before retrying.
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
			if gate is not None:
				gate.report_online_failure()

	stt_backend = build_stt_backend(
		online=False,
		model_size=whisper_model_size,
		language=whisper_language,
	)
	llm_backend = build_llm_backend(online=False)
	tts_backend = build_tts_backend(is_online=False)
	return False, stt_backend, llm_backend, tts_backend


def _route_action(
	action_json: dict,
	bhl_client: BhlClient | None = None,
	estop_listener=None,
	session_id: str = "",
) -> str | None:
	"""intent 별 executor 분기.

	BHL 라우트는 bhl_client 가 주어지면 실제로 NUC bridge 로 송신하고 DONE 까지 대기.
	bhl_client 가 None 이면 옛 동작(stdout 로그만) — 테스트/오프라인 디버깅용.

	Returns the BHL DONE reason if the action was dispatched to BHL and got a
	response ("duration_elapsed" / "stop_command" / "safety_or_emergency" /
	"timeout"), else None. Used by the caller to pick the standby reply
	(emergency vs. normal completion).
	"""
	intent = action_json.get("intent")
	if intent == "pick_place":
		print("[Executor] pick_place -> SMOLVLA executor route")
		sleep(0.2)
		return None

	if intent in {"move", "stop"}:
		if bhl_client is None:
			print("[Executor] move/stop -> BHL executor route (bhl_client=None, stub)")
			sleep(0.2)
			return None
		return _dispatch_to_bhl(action_json, bhl_client, estop_listener=estop_listener, session_id=session_id)

	if intent == "chat":
		print("[Executor] chat -> reply/TTS route")
	else:
		print("[Executor] no-op route")
	sleep(0.2)
	return None


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


def _dispatch_to_bhl(
	action_json: dict,
	bhl_client: BhlClient,
	estop_listener=None,
	session_id: str = "",
) -> str | None:
	"""BHL 라우트 본체. 송신 → DONE 대기 → idle 복귀.

	안전 원칙:
	  - 모든 통신 예외를 흡수해서 coordinator main 흐름이 죽지 않게 함
	  - DONE 못 받으면 timeout 으로 끝내고 음성 안내 (이 함수 호출자가 처리)
	  - 마지막에 반드시 bhl_client.clear() 호출 (다음 명령이 자동 송신되지 않도록)

	estop_listener (옵션): "멈춰" 키워드를 background 에서 청취. 트리거되면
	EMERGENCY action 을 bridge 로 보내 active move 를 즉시 finish 시킴.
	bridge.finish_active_action("safety_or_emergency") 가 원래 action_id 의
	DONE 을 회신하므로 wait_for_done() 이 자연스럽게 풀린다. listener 는 본
	dispatch 함수가 mic 을 점유하지 않는 동안에만 도는 배타적 라이프사이클로
	관리되어 메인 wake listener 와 mic 충돌이 없다.

	Returns: BHL DONE reason ("duration_elapsed" / "stop_command" /
	"safety_or_emergency"), TIMEOUT 시 "timeout", 통신 예외 시 "error".
	"""
	action_id = action_json.get("action_id") or "unknown"
	intent = action_json.get("intent")
	duration = float(action_json.get("duration_sec") or BHL_DEFAULT_DURATION_SEC)
	timeout = duration + BHL_DONE_TIMEOUT_MARGIN_SEC
	# stop intent 는 bridge 가 즉시 DONE 회신하므로 짧은 timeout
	if intent == "stop":
		timeout = BHL_DONE_TIMEOUT_MARGIN_SEC

	# move 중에만 e-stop wake 청취. stop intent 는 본질적으로 즉시 끝나므로
	# 굳이 e-stop listener 를 띄울 필요 없음 (mic 점유만 낭비).
	use_estop = estop_listener is not None and intent == "move" and getattr(estop_listener, "available", False)
	# E-stop wake-word 가 잡혔는지 client-side 에서도 기억. bridge 가 죽어
	# DONE 회신을 못 보내거나 늦어서 timeout 으로 빠지더라도, "사용자가 멈춰
	# 라고 했다" 는 사실은 client 가 이미 알고 있으니 emergency UX (TTS,
	# standby 메시지 분기) 는 그 사실 하나로 충분히 살릴 수 있다. 즉 bridge
	# 의 done reason 과 별개로 client 가 reason 을 emergency 로 승격할 수 있게
	# 한 플래그.
	estop_fired = False
	if use_estop:
		def _on_estop() -> None:
			# 콜백은 e-stop listener 스레드에서 실행됨. set_command 만 호출하면
			# BhlClient 의 sender 스레드가 다음 keepalive 사이클에서 EMERGENCY 를
			# 송신하고, bridge 가 finish_active_action 으로 원래 action_id 의
			# DONE 을 보내 main thread 의 wait_for_done 이 풀린다. bridge 가
			# 응답 안 해도 nonlocal estop_fired 플래그를 켜두어 아래쪽에서
			# reason 을 emergency 로 승격한다.
			nonlocal estop_fired
			estop_fired = True
			estop_action = _build_emergency_stop_action(session_id=session_id)
			print(f"[E-Stop] sending EMERGENCY action_id={estop_action['action_id']} to bridge")
			try:
				bhl_client.set_command(estop_action)
			except Exception as exc:
				print(f"[E-Stop] set_command failed: {exc}")

		try:
			estop_listener.start(_on_estop)
		except Exception as exc:
			print(f"[E-Stop] listener start failed: {exc}")
			use_estop = False

	reason: str | None = None
	try:
		bhl_client.set_command(action_json)
		print(f"[BHL] TX action_id={action_id} intent={intent} gait={action_json.get('gait_cmd')} "
		      f"duration={duration:.1f}s timeout={timeout:.1f}s estop={'on' if use_estop else 'off'}")

		got_done, done_reason = bhl_client.wait_for_done(action_id, timeout=timeout)
		if got_done:
			reason = done_reason or "duration_elapsed"
			print(f"[BHL] DONE action_id={action_id} reason={reason}")
		else:
			reason = "timeout"
			print(f"[BHL] TIMEOUT action_id={action_id} (no DONE within {timeout:.1f}s)")
	except Exception as exc:
		reason = "error"
		print(f"[BHL] dispatch failed: {exc}")
	finally:
		# e-stop listener 정리 먼저 — mic 을 즉시 해제해서 다음 wake_word 사이클이
		# ALSA "Device busy" 없이 stream 을 열 수 있게 한다.
		if estop_listener is not None:
			try:
				estop_listener.stop()
			except Exception as exc:
				print(f"[E-Stop] listener stop failed: {exc}")
		try:
			bhl_client.clear()
		except Exception as exc:
			print(f"[BHL] clear failed: {exc}")

	# Client-side e-stop 승격: 사용자가 "멈춰" 외친 사실은 bridge 응답과
	# 무관하게 emergency 로 분류해야 한다. bridge 가 정상이라면 이미 reason ==
	# "safety_or_emergency" 일 것이고 이 승격은 no-op. bridge 가 죽어
	# timeout/error 로 떨어졌더라도 사용자 UX 측면에선 emergency 메시지가
	# 들려야 함.
	if estop_fired and reason != "safety_or_emergency":
		print(f"[E-Stop] promoting client-side reason -> safety_or_emergency (bridge reason was {reason!r})")
		reason = "safety_or_emergency"

	return reason


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
	gate: OnlineGate,
	bhl_client: BhlClient | None = None,
	estop_listener=None,
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

		online_probe = gate.is_active()
		print(f"[Network] online_active={online_probe} (sticky w/ cooldown)")
		online, stt_backend, llm_backend, tts_backend = _build_turn_services(
			online_probe,
			whisper_model_size=whisper_model_size,
			whisper_language=whisper_language,
			gate=gate,
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
			bhl_reason = _route_action(
				action_json,
				bhl_client=bhl_client,
				estop_listener=estop_listener,
				session_id=session_id,
			)

			# Emergency stop overrides the standby reply so the user hears that the
			# move was halted, not the generic "작업을 마쳤고..." completion line.
			# 같은 EMERGENCY 메시지/액션 형태를 향후 LLM 출력 intent=="emergency"
			# 분기에서도 재사용할 수 있도록 별도 _build_emergency_action() 으로 분리.
			if bhl_reason == "safety_or_emergency":
				standby_action = _build_emergency_action(session_id=session_id, after_intent=intent)
				_print_block("ACTION_JSON (EMERGENCY)", standby_action)
			else:
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


def _startup_warm_up(args: argparse.Namespace, gate: OnlineGate) -> None:
	"""§F5 warm-up policy: warm only the side likely to be hot.

	online → Groq probe (no model load). offline → local whisper + Ollama
	model + MeloTTS daemon model. The other side stays cold and lazy-loads on
	first runtime fallback. Failures here are logged but never abort startup;
	the pipeline degrades gracefully. Reads online state from ``gate`` (which
	already performed its own probe at construction) so the coordinator pays
	at most one ``is_online()`` cost before the first wake activation.
	"""
	initial_online = gate.is_active()
	print(f"[Startup] online_active={initial_online}")

	if initial_online:
		try:
			llm = build_llm_backend(online=True)
			llm.warm_up()
			print(f"[Warm-up] LLM  {llm.name} ... OK")
		except Exception as exc:
			print(f"[Warm-up] LLM  online Groq ... FAIL (lazy-load): {exc}")
			gate.report_online_failure()
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
	estop_listener = None
	bhl_client: BhlClient | None = None
	# Spawn the gesture daemon first so its ~8-10s warm-up (torch import + arm
	# connect, in the .hylion_arm venv) overlaps with model warm-up below.
	# Failure is non-fatal — start_gesture_daemon() returns a disabled handle.
	gesture_daemon = start_gesture_daemon()
	# Single sticky online/offline gate; one is_online() probe is paid at
	# construction and then reused across wake activations (with cooldown-based
	# retry on failures) instead of probing inside every turn.
	gate = OnlineGate()
	try:
		wakeword_listener = build_wake_word_listener()
		# E-stop listener is built once and started/stopped per BHL move.
		# Build is cheap (model is loaded lazily on the first start()), so a
		# missing model file or audio stack only surfaces a one-line warning
		# and the move executes without wake-word stop.
		estop_listener = build_emergency_stop_listener()
		_startup_warm_up(args, gate)
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
			gate=gate,
			bhl_client=bhl_client,
			estop_listener=estop_listener,
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
		if estop_listener is not None:
			try:
				estop_listener.stop()
			except Exception as exc:
				print(f"[Cleanup] estop listener stop failed: {exc}")
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
