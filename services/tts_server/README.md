# Hylion MeloTTS daemon

Offline Korean TTS HTTP service. Hylion's coordinator (main venv, torch 2.5)
talks to this daemon over loopback HTTP so the heavy ML stack (torch 2.8 +
torchaudio 2.8 + MeloTTS) stays isolated in its own venv. Mirrors the Ollama
pattern.

## Components

```
services/tts_server/
├─ server.py              FastAPI app + MeloTTS lifecycle
├─ hylion-tts.service     systemd unit (enable on boot)
└─ README.md              this file
```

Runtime dependencies:
- **Service venv**: `jetson/expression/.venv-melotts/` (torch 2.8 + torchaudio
  2.8 from jetson-ai-lab.io, coqui-tts deps, MeloTTS source vendored at
  `third_party/MeloTTS/`). Owns its torch — does not affect Hylion main venv.
- **Patched MeloTTS source**: `third_party/MeloTTS/melo/text/{__init__,cleaner}.py`
  edited to import only the Korean code path (skips Japanese MeCab / Chinese jieba
  imports we don't install). Re-pulling MeloTTS upstream needs to reapply these
  edits.
- **HF cache**: models pre-downloaded at `~/.cache/huggingface/hub/`:
  - `myshell-ai/MeloTTS-Korean` (~199 MB)
  - `kykim/bert-kor-base` (~908 MB)
  Once cached, the daemon needs no internet at runtime.

## Endpoints

- `GET  /health`        → `{"status":"ok","model":"melotts-KR","device":"cuda"}`
- `POST /synthesize`    → body `{"text": str, "speed": float}`,
                          response `audio/wav` (44.1 kHz mono PCM int16)

## Manual launch (development / troubleshooting)

```bash
cd /home/laba/Hylion
jetson/expression/.venv-melotts/bin/python3 -m uvicorn \
    services.tts_server.server:app \
    --host 127.0.0.1 --port 8001
```

First boot loads model + warm-up: ~60–140s. Subsequent boots: ~5–10s.

## Install as systemd service (auto-start on boot)

```bash
sudo cp services/tts_server/hylion-tts.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now hylion-tts.service

# logs
journalctl -u hylion-tts -f

# restart after editing source
sudo systemctl restart hylion-tts
```

## Health probe

```bash
curl -sS http://127.0.0.1:8001/health
curl -sS -X POST http://127.0.0.1:8001/synthesize \
    -H 'Content-Type: application/json' \
    -d '{"text":"하이리온 오프라인 합성 테스트","speed":1.0}' \
    -o /tmp/out.wav
aplay /tmp/out.wav
```

## Offline verification

After service is up and HF cache is populated, the daemon should run with no
internet:

```bash
# Disable network briefly (or unplug WiFi)
sudo nmcli networking off

curl -sS http://127.0.0.1:8001/health     # still ok
curl -sS -X POST http://127.0.0.1:8001/synthesize \
    -H 'Content-Type: application/json' \
    -d '{"text":"오프라인 모드 동작 확인","speed":1.0}' \
    -o /tmp/offline.wav
aplay /tmp/offline.wav

sudo nmcli networking on
```

## Memory footprint

Steady state on Jetson Orin Nano 8 GB:
- Daemon process RSS: ~2.0–2.5 GB (model + framework + Korean BERT)
- GPU memory: ~0.76 GB

Coexists with Ollama (EXAONE 2.4B, ~2.3 GB) — combined ~5 GB, leaves ~2 GB headroom.

## Performance

- Model load (cached): ~5–10s
- Korean BERT first-call download: only on first ever synthesis (~140s, one-time)
- Steady-state synthesis: RTF ≈ 0.22–0.27x  (≈ 1s per ~4–5s of audio)

## Future: OpenVoice v2 voice cloning

Plan: add `services/tts_server/openvoice_extension.py` that piles tone color
conversion (CLOVA `nhajun` reference clip → child voice) on top of MeloTTS
output. Same `/synthesize` endpoint, returns the converted WAV. See
`docs/10_hybrid_online_offline_refactor_plan.md` §F6.
