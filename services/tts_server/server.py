"""MeloTTS Korean offline TTS HTTP daemon.

Runs in a dedicated venv (.venv-melotts/ at jetson/expression/) with torch 2.8 +
torchaudio 2.8 from jetson-ai-lab. Hylion's coordinator stays on torch 2.5 and
talks to this daemon over loopback HTTP (mirrors the Ollama pattern).

Endpoints:
  GET  /health        - liveness + model identity
  POST /synthesize    - body: {"text": str, "speed": float}
                        returns: audio/wav bytes
"""

from __future__ import annotations

import gc
import logging
import os
import sys
import tempfile
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

# Resolve MeloTTS source location (vendored repo, not pip-installed)
MELO_REPO = Path(__file__).resolve().parents[2] / "third_party" / "MeloTTS"
if str(MELO_REPO) not in sys.path:
	sys.path.insert(0, str(MELO_REPO))

# python-mecab-ko bundles a workable mecabrc; ensure it's discoverable so
# any imports that touch system MeCab don't fail with "no /usr/local/etc/mecabrc".
_MECABRC_HINT = Path(__file__).resolve().parents[2] / "jetson" / "expression" / ".venv-melotts" / "lib" / "python3.10" / "site-packages" / "mecab" / "mecabrc"
os.environ.setdefault("MECABRC", str(_MECABRC_HINT))

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("tts_server")


# parameters
DEFAULT_LANGUAGE = "KR"
DEFAULT_DEVICE = "cuda"
DEFAULT_SPEAKER_ID = 0

# Daemon stays at ~300MB until first warmup/synthesis. Coordinator triggers
# /warmup explicitly when starting in offline mode, or implicitly on first
# /synthesize call if it hasn't been warmed yet. /unload frees memory when
# the system flips back to online (handed off to graceful-degradation logic).

_TTS_MODEL = None
_LOAD_LOCK = threading.Lock()


def _ensure_model_loaded() -> None:
	"""Idempotent: load MeloTTS + run a 1-call warm-up exactly once."""
	global _TTS_MODEL
	if _TTS_MODEL is not None:
		return
	with _LOAD_LOCK:
		if _TTS_MODEL is not None:
			return
		from melo.api import TTS
		t0 = time.time()
		model = TTS(language=DEFAULT_LANGUAGE, device=DEFAULT_DEVICE)
		logger.info("MeloTTS '%s' loaded on %s in %.2fs", DEFAULT_LANGUAGE, DEFAULT_DEVICE, time.time() - t0)
		# Trigger Korean BERT download + first inference path so subsequent
		# calls hit the warm path (without this, first turn is ~140s).
		with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as fh:
			t0 = time.time()
			model.tts_to_file("준비 완료", DEFAULT_SPEAKER_ID, fh.name, speed=1.0)
			logger.info("warm-up synthesis done in %.2fs", time.time() - t0)
		_TTS_MODEL = model


def _unload_model() -> None:
	global _TTS_MODEL
	with _LOAD_LOCK:
		if _TTS_MODEL is None:
			return
		_TTS_MODEL = None
		gc.collect()
		try:
			import torch
			if torch.cuda.is_available():
				torch.cuda.empty_cache()
		except Exception:
			pass
		logger.info("model unloaded; CUDA cache cleared")


@asynccontextmanager
async def lifespan(app: FastAPI):
	logger.info("daemon ready (lazy: model not loaded yet, ~300MB)")
	yield
	_unload_model()
	logger.info("shutting down")


app = FastAPI(title="Hylion MeloTTS daemon", lifespan=lifespan)


class SynthesizeRequest(BaseModel):
	text: str = Field(min_length=1, max_length=2000)
	speed: float = Field(default=1.0, ge=0.5, le=2.0)
	speaker_id: int = Field(default=DEFAULT_SPEAKER_ID, ge=0)


@app.get("/health")
def health():
	return {
		"status": "ok",
		"model": f"melotts-{DEFAULT_LANGUAGE}",
		"device": DEFAULT_DEVICE,
		"loaded": _TTS_MODEL is not None,
	}


@app.post("/warmup")
def warmup():
	"""Eagerly load model + run warm-up synthesis. Blocks until ready.

	Coordinator calls this in offline mode at startup so the first user-facing
	turn doesn't pay the ~10s cold-load cost. Idempotent.
	"""
	t0 = time.time()
	already_loaded = _TTS_MODEL is not None
	_ensure_model_loaded()
	return {
		"status": "ok",
		"already_loaded": already_loaded,
		"elapsed_sec": round(time.time() - t0, 2),
	}


@app.post("/unload")
def unload():
	"""Free model memory; daemon process stays alive at ~300MB.

	Coordinator calls this when graceful-degradation flips back to online so
	the offline TTS pipeline doesn't squat on ~2GB unnecessarily.
	"""
	was_loaded = _TTS_MODEL is not None
	_unload_model()
	return {"status": "ok", "was_loaded": was_loaded}


@app.post("/synthesize")
def synthesize(req: SynthesizeRequest) -> Response:
	# Auto-warmup if coordinator forgot to /warmup; first call pays cold cost.
	_ensure_model_loaded()

	t0 = time.time()
	with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fh:
		out_path = fh.name
	try:
		_TTS_MODEL.tts_to_file(req.text, req.speaker_id, out_path, speed=req.speed)
		audio_bytes = Path(out_path).read_bytes()
	finally:
		Path(out_path).unlink(missing_ok=True)

	elapsed = time.time() - t0
	logger.info("synthesized %d bytes in %.2fs (text=%r speed=%.2f)", len(audio_bytes), elapsed, req.text[:40], req.speed)
	return Response(
		content=audio_bytes,
		media_type="audio/wav",
		headers={"X-Synthesis-Time-Ms": f"{int(elapsed * 1000)}"},
	)


def main():
	import uvicorn
	host = os.environ.get("HYLION_TTS_HOST", "127.0.0.1")
	port = int(os.environ.get("HYLION_TTS_PORT", "8001"))
	logger.info("starting Hylion MeloTTS daemon on %s:%d", host, port)
	uvicorn.run(app, host=host, port=port, log_level="info", access_log=False)


if __name__ == "__main__":
	main()
