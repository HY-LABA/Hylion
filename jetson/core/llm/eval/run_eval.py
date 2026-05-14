"""Prompt eval harness for the Hylion coordinator LLM.

Harness engineering needs measurement: you change a prompt, you run this, you
compare the number. Without it, prompt tuning is vibes.

Each line of cases.jsonl is one utterance with its expected intent (and, where
it matters, expected target_object / gait_cmd). This script runs every case
through a real LLM backend and reports per-intent accuracy plus a failure list.

Usage:
    python -m jetson.core.llm.eval.run_eval --backend offline
    python -m jetson.core.llm.eval.run_eval --backend online
    python -m jetson.core.llm.eval.run_eval --backend offline --cases path/to/cases.jsonl

`offline` needs the Ollama daemon up; `online` needs GROQ_API_KEY. The backend
is exercised exactly as the coordinator uses it (build_action), so this measures
the prompt + harness as actually shipped.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from jetson.core.llm import build_llm_backend  # noqa: E402

DEFAULT_CASES_PATH = Path(__file__).resolve().parent / "cases.jsonl"


def _load_cases(path: Path) -> list[dict]:
	cases: list[dict] = []
	for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
		raw = raw.strip()
		if not raw or raw.startswith("#"):
			continue
		try:
			cases.append(json.loads(raw))
		except json.JSONDecodeError as exc:
			print(f"[eval] skipping malformed line {line_no}: {exc}")
	return cases


def _check_case(case: dict, action: dict) -> tuple[bool, str]:
	"""Return (passed, reason). Only checks fields the case actually pins."""
	got_intent = action.get("intent")
	if got_intent != case["expect_intent"]:
		return False, f"intent {got_intent!r} != {case['expect_intent']!r}"

	if "expect_target" in case:
		got = str(action.get("target_object", "")).strip()
		want = case["expect_target"].strip()
		# Loose match: the expected object name should appear in the model's
		# target_object (the model may add color/qualifier words).
		if want not in got and got not in want:
			return False, f"target_object {got!r} !~ {want!r}"

	if "expect_gait" in case:
		got = action.get("gait_cmd")
		if got != case["expect_gait"]:
			return False, f"gait_cmd {got!r} != {case['expect_gait']!r}"

	if "expect_gesture" in case:
		# gesture_name is keyword-detected in code (not model output), so this
		# pins the detect_gesture path: a gesture keyword on a chat turn fills
		# it, anything else stays "none".
		got = action.get("gesture_name")
		if got != case["expect_gesture"]:
			return False, f"gesture_name {got!r} != {case['expect_gesture']!r}"

	return True, "ok"


def run(backend_name: str, cases_path: Path) -> int:
	online = backend_name == "online"
	backend = build_llm_backend(online=online)
	print(f"[eval] backend={backend.name}  cases={cases_path}")

	try:
		backend.warm_up()
	except Exception as exc:
		print(f"[eval] warm_up failed (continuing): {exc}")

	cases = _load_cases(cases_path)
	if not cases:
		print("[eval] no cases loaded")
		return 1

	passed = 0
	failures: list[str] = []
	per_intent: dict[str, list[int]] = {}  # intent -> [pass, total]
	t0 = time.time()

	for i, case in enumerate(cases, start=1):
		text = case["text"]
		expect = case["expect_intent"]
		per_intent.setdefault(expect, [0, 0])
		per_intent[expect][1] += 1
		try:
			action = backend.build_action(
				stt_text=text,
				session_id="eval",
				history=[],
				in_chat_mode=True,
			)
		except Exception as exc:
			failures.append(f"  [{i:02d}] {text!r} -> EXCEPTION: {exc}")
			continue

		ok, reason = _check_case(case, action)
		if ok:
			passed += 1
			per_intent[expect][0] += 1
		else:
			failures.append(
				f"  [{i:02d}] {text!r} -> {reason}  | reply={action.get('reply_text')!r}"
			)

	elapsed = time.time() - t0
	total = len(cases)
	print("\n" + "=" * 60)
	print(f"RESULT  {passed}/{total} passed  ({passed / total * 100:.1f}%)  in {elapsed:.1f}s")
	print("-" * 60)
	for intent in sorted(per_intent):
		p, t = per_intent[intent]
		print(f"  {intent:<12} {p}/{t}")
	if failures:
		print("-" * 60)
		print("FAILURES:")
		print("\n".join(failures))
	print("=" * 60)

	return 0 if passed == total else 1


def _parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Hylion coordinator LLM prompt eval.")
	parser.add_argument(
		"--backend",
		choices=["online", "offline"],
		default="offline",
		help="online = Groq, offline = Ollama (default: offline)",
	)
	parser.add_argument(
		"--cases",
		type=Path,
		default=DEFAULT_CASES_PATH,
		help="path to cases.jsonl",
	)
	return parser.parse_args()


if __name__ == "__main__":
	args = _parse_args()
	raise SystemExit(run(args.backend, args.cases))
