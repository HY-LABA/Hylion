"""Gesture registry — single source of truth for valid gesture names.

The gesture trajectories themselves live OUTSIDE this repo: they are recorded
on the DGX and rsync'd to the Jetson at `~/smolvla/orin/gestures/<name>/`, the
same root `play_gesture.sh` replays from. This module is the one place that
knows which gestures actually exist, so the LLM prompt enum (prompt.py) and the
executor route (coordinator.py) can never drift apart — both ask here.

Discovery is a directory scan: a subdirectory is a valid gesture iff it has a
`meta/info.json` (the LeRobotDataset marker). Result is cached for the process;
call `refresh()` after a new gesture is synced mid-run.

Env override:
  ORIN_GESTURES_ROOT   gesture data root (default: ~/smolvla/orin/gestures)
                       — must match play_gesture.sh's ORIN_GESTURES_ROOT.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import List, Optional

# play_gesture.sh enforces this same snake_case shape on its <gesture_name> arg.
_GESTURE_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def gestures_root() -> Path:
	"""Resolve the gesture data root, honoring ORIN_GESTURES_ROOT."""
	env = os.getenv("ORIN_GESTURES_ROOT")
	if env:
		return Path(env).expanduser()
	return Path.home() / "smolvla" / "orin" / "gestures"


_cache: Optional[List[str]] = None


def list_gestures() -> List[str]:
	"""Return sorted valid gesture names found under the gestures root.

	A directory counts as a gesture only if it has `meta/info.json`. Missing
	root (e.g. dev machine without synced data) yields an empty list rather
	than raising — callers degrade gracefully.
	"""
	global _cache
	if _cache is not None:
		return _cache

	root = gestures_root()
	found: List[str] = []
	if root.is_dir():
		for child in root.iterdir():
			if not child.is_dir():
				continue
			if not _GESTURE_NAME_RE.match(child.name):
				continue
			if (child / "meta" / "info.json").is_file():
				found.append(child.name)
	_cache = sorted(found)
	return _cache


def refresh() -> List[str]:
	"""Drop the cache and re-scan. Use after syncing a new gesture mid-run."""
	global _cache
	_cache = None
	return list_gestures()


def is_valid_gesture(name: str) -> bool:
	"""True iff `name` is a currently-available gesture."""
	return bool(name) and name in list_gestures()


def gesture_frames(name: str) -> Optional[int]:
	"""total_frames from the gesture's meta/info.json, or None if unavailable."""
	if not is_valid_gesture(name):
		return None
	info_path = gestures_root() / name / "meta" / "info.json"
	try:
		return int(json.loads(info_path.read_text(encoding="utf-8"))["total_frames"])
	except Exception:
		return None
