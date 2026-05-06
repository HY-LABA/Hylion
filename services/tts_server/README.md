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

- `GET  /health`        → `{"status":"ok","model":"melotts-KR","device":"cuda","loaded":bool}`
- `POST /warmup`        → load model + run a 1-call warm-up. Idempotent.
                          Blocks until ready (~22s first ever, ~4s after unload).
- `POST /unload`        → drop model references; **does not free host RAM**
                          (PyTorch allocator caches it). To fully reclaim RAM,
                          restart the daemon (`systemctl restart hylion-tts`).
- `POST /synthesize`    → body `{"text": str, "speed": float}`,
                          response `audio/wav` (44.1 kHz mono PCM int16).
                          Auto-warms model if not loaded (first call pays
                          ~22s cold-load cost).

## Lifecycle (lazy-load)

The daemon process starts at **~40 MB** with no model loaded. Coordinator
controls when to actually load the heavy model:

```
[coordinator startup]
  is_online() probe
    │
    ├─ online  → daemon stays at 40 MB (never warmed)
    │           Online TTS uses Clova HTTP, this daemon idle
    │
    └─ offline → coordinator calls POST /warmup
                 daemon loads MeloTTS + Korean BERT (~22s first time, ~4s after)
                 RSS jumps to ~2.5 GB, GPU 0.76 GB
                 subsequent /synthesize calls: ~1s each
```

Online → offline transition (graceful degradation, step 6) calls /warmup
on demand; first offline turn pays the cold-load cost once.

Offline → online transition calls /unload to flush GPU cache (host RAM stays
held by PyTorch allocator — restart daemon for full reclaim).

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

Daemon process RSS:
- **Idle (no warmup yet)**: ~40 MB
- **After /warmup**: ~2.5 GB (model + framework + Korean BERT)
- **After /unload**: stays at ~2.5 GB (PyTorch allocator caches host pages)
- **After daemon restart**: back to ~40 MB

GPU memory: 0.76 GB while loaded.

Coexists with Ollama (EXAONE 2.4B, ~2.3 GB when active) —
- **Online mode**: this daemon idle at 40 MB, Ollama unloaded after 5 min
  → total Hylion footprint ~3 GB, leaves ~4 GB headroom for future smolvla.
- **Offline mode**: both loaded → ~5–6 GB combined, leaves ~1.5 GB headroom.

## Performance

- Model load (cached): ~5–10s
- Korean BERT first-call download: only on first ever synthesis (~140s, one-time)
- Steady-state synthesis: RTF ≈ 0.22–0.27x  (≈ 1s per ~4–5s of audio)

## Future: OpenVoice v2 voice cloning

Plan: add `services/tts_server/openvoice_extension.py` that piles tone color
conversion (CLOVA `nhajun` reference clip → child voice) on top of MeloTTS
output. Same `/synthesize` endpoint, returns the converted WAV. See
`docs/10_hybrid_online_offline_refactor_plan.md` §F6.
