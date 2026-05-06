#!/usr/bin/env bash
# Reproducible setup for Hylion MeloTTS daemon.
# Run from project root: bash services/tts_server/setup.sh
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VENV="${PROJECT_ROOT}/jetson/expression/.venv-melotts"
THIRD_PARTY="${PROJECT_ROOT}/third_party"
MELO_DIR="${THIRD_PARTY}/MeloTTS"
PATCH="${PROJECT_ROOT}/services/tts_server/patches/melotts_korean_only.patch"

echo "[1/5] create venv at ${VENV}"
mkdir -p "${THIRD_PARTY}"
if [[ ! -d "${VENV}" ]]; then
    virtualenv -p python3.10 "${VENV}"
fi

# shellcheck disable=SC1091
source "${VENV}/bin/activate"
PIP="${VENV}/bin/python3 -m pip"

echo "[2/5] install Jetson torch + torchaudio (jetson-ai-lab.io)"
TORCH_URL="https://pypi.jetson-ai-lab.io/jp6/cu126/+f/62a/1beee9f2f1470/torch-2.8.0-cp310-cp310-linux_aarch64.whl"
TORCHAUDIO_URL="https://pypi.jetson-ai-lab.io/jp6/cu126/+f/81a/775c8af36ac85/torchaudio-2.8.0-cp310-cp310-linux_aarch64.whl"
${PIP} install "${TORCH_URL}" "${TORCHAUDIO_URL}"

echo "[3/5] clone + patch MeloTTS"
if [[ ! -d "${MELO_DIR}" ]]; then
    git clone https://github.com/myshell-ai/MeloTTS.git "${MELO_DIR}"
fi
( cd "${MELO_DIR}" && git checkout -- melo/text/cleaner.py melo/text/__init__.py 2>/dev/null || true )
( cd "${MELO_DIR}" && git apply "${PATCH}" )

echo "[4/5] install MeloTTS + Korean-only deps"
${PIP} install --no-deps -e "${MELO_DIR}"
${PIP} install --no-deps \
    nltk g2pkk jamo num2words txtsplit pydub anyascii python-mecab-ko \
    g2p_en transformers cached_path soundfile librosa scipy tqdm \
    "numpy<2" "pydantic>=2"
${PIP} install fastapi uvicorn

echo "[5/5] download nltk data"
python3 -c "import nltk; [nltk.download(p, quiet=True) for p in ('cmudict','averaged_perceptron_tagger','averaged_perceptron_tagger_eng')]"

echo ""
echo "MeloTTS daemon venv ready at ${VENV}"
echo "  Manual launch:"
echo "    ${VENV}/bin/python3 -m uvicorn services.tts_server.server:app --host 127.0.0.1 --port 8001"
echo "  Or install systemd unit:"
echo "    sudo cp services/tts_server/hylion-tts.service /etc/systemd/system/"
echo "    sudo systemctl daemon-reload && sudo systemctl enable --now hylion-tts"
