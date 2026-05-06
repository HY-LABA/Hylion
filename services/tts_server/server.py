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

import logging
import os
import sys
import tempfile
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


_TTS_MODEL = None  # populated on startup


def _load_model() -> None:
	global _TTS_MODEL
	from melo.api import TTS
	t0 = time.time()
	_TTS_MODEL = TTS(language=DEFAULT_LANGUAGE, device=DEFAULT_DEVICE)
	logger.info("MeloTTS '%s' loaded on %s in %.2fs", DEFAULT_LANGUAGE, DEFAULT_DEVICE, time.time() - t0)


def _warm_up_synth() -> None:
	"""Trigger Korean BERT download + first inference path so subsequent calls
	hit the warm path. Without this the first user-facing turn is ~140s."""
	with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as fh:
		t0 = time.time()
		_TTS_MODEL.tts_to_file("준비 완료", DEFAULT_SPEAKER_ID, fh.name, speed=1.0)
		logger.info("warm-up synthesis done in %.2fs", time.time() - t0)


@asynccontextmanager
async def lifespan(app: FastAPI):
	_load_model()
	_warm_up_synth()
	yield
	logger.info("shutting down")


app = FastAPI(title="Hylion MeloTTS daemon", lifespan=lifespan)


class SynthesizeRequest(BaseModel):
	text: str = Field(min_length=1, max_length=2000)
	speed: float = Field(default=1.0, ge=0.5, le=2.0)
	speaker_id: int = Field(default=DEFAULT_SPEAKER_ID, ge=0)


@app.get("/health")
def health():
	if _TTS_MODEL is None:
		return {"status": "loading", "model": f"melotts-{DEFAULT_LANGUAGE}"}
	return {
		"status": "ok",
		"model": f"melotts-{DEFAULT_LANGUAGE}",
		"device": DEFAULT_DEVICE,
	}


@app.post("/synthesize")
def synthesize(req: SynthesizeRequest) -> Response:
	if _TTS_MODEL is None:
		raise HTTPException(status_code=503, detail="model not loaded yet")

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
