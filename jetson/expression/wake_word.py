from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence, Tuple

import numpy as np

try:
    import audioop  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - audioop is optional and may disappear in newer Python versions
    audioop = None

try:
    import sounddevice as sd  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - Jetson target dependency
    sd = None

try:
    import openwakeword  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - Jetson target dependency
    openwakeword = None


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WAKEWORD_MODEL_PATH = str(PROJECT_ROOT / "checkpoints" / "wakeword" / "Hey_Hyleon.tflite")
DEFAULT_WAKEWORD_MODEL = os.getenv("HYLION_WAKEWORD_MODEL", DEFAULT_WAKEWORD_MODEL_PATH)
DEFAULT_WAKEWORD_THRESHOLD = float(os.getenv("HYLION_WAKEWORD_THRESHOLD", "0.5"))
DEFAULT_DEVICE_KEYWORD = os.getenv("HYLION_WAKEWORD_DEVICE_KEYWORD", "")
DEFAULT_SAMPLE_RATE = int(os.getenv("HYLION_WAKEWORD_SAMPLE_RATE", "44100"))
DEFAULT_WAKEWORD_BLOCK_MS = int(os.getenv("HYLION_WAKEWORD_BLOCK_MS", "80"))
DEFAULT_BATON_TOUCH_DELAY_SEC = float(os.getenv("HYLION_WAKEWORD_BATON_TOUCH_DELAY_SEC", "0.5"))

# openWakeWord requires 16 kHz mono int16 input, so the captured audio must be
# resampled to this rate before feeding the model.
WAKEWORD_MODEL_RATE = 16000


@dataclass(frozen=True)
class WakeWordActivation:
    label: str
    score: float
    sample_rate: int
    device_name: str


@dataclass(frozen=True)
class WakeWordConfig:
    # parameters
    model_name: str = DEFAULT_WAKEWORD_MODEL
    threshold: float = DEFAULT_WAKEWORD_THRESHOLD
    device_keyword: str = DEFAULT_DEVICE_KEYWORD
    sample_rate: int = DEFAULT_SAMPLE_RATE
    block_ms: int = DEFAULT_WAKEWORD_BLOCK_MS
    baton_touch_delay_sec: float = DEFAULT_BATON_TOUCH_DELAY_SEC
    inference_framework: str = "tflite"
    vad_threshold: float = 0.0


class WakeWordListener:
    """OpenWakeWord microphone listener.

    Opens the microphone at its hardware-native rate (default 44.1 kHz) and
    downsamples each chunk to 16 kHz in Python before feeding openWakeWord.
    """

    def __init__(self, config: Optional[WakeWordConfig] = None) -> None:
        if sd is None:
            raise RuntimeError("sounddevice is not available")
        if openwakeword is None:
            raise RuntimeError("openwakeword is not available")

        self.config = config or WakeWordConfig()
        self._model = self._build_model()
        self._stream: Optional[object] = None
        self._stream_sample_rate: int = self.config.sample_rate
        self._device_name: str = ""
        self._resample_state = None
        self._closed = False

    def _build_model(self):
        model_value = str(self.config.model_name).strip()
        if not model_value:
            raise RuntimeError("Wake word model is empty")

        # If the value looks like a file path, resolve it relative to the project
        # root and verify it exists. Otherwise treat it as an openWakeWord built-in
        # alias (e.g. "hey_jarvis") and pass it through untouched.
        looks_like_path = any(sep in model_value for sep in ("/", "\\")) or model_value.endswith((".tflite", ".onnx"))
        if looks_like_path:
            model_path = Path(model_value).expanduser()
            if not model_path.is_absolute():
                model_path = (PROJECT_ROOT / model_path).resolve()
            if not model_path.exists():
                raise RuntimeError(
                    f"Wake word model file not found: {model_path}. "
                    "Set HYLION_WAKEWORD_MODEL to a valid model path or built-in alias."
                )
            wakeword_models = [str(model_path)]
        else:
            wakeword_models = [model_value]

        return openwakeword.Model(
            wakeword_models=wakeword_models,
            inference_framework=self.config.inference_framework,
            vad_threshold=self.config.vad_threshold,
        )

    def _list_input_devices(self) -> Sequence[Tuple[int, str, float]]:
        devices = []
        for index, device in enumerate(sd.query_devices()):
            channels = int(device.get("max_input_channels", 0))
            if channels <= 0:
                continue
            devices.append((index, str(device.get("name", f"device-{index}")), float(device.get("default_samplerate", 0.0))))
        return devices

    def _pick_device(self, keyword: str) -> Tuple[int, str, float]:
        devices = self._list_input_devices()
        if not devices:
            raise RuntimeError("No input audio device available for wake word detection")

        if keyword:
            lowered = keyword.lower()
            for device in devices:
                if lowered in device[1].lower():
                    return device

        return devices[0]

    def _open_stream(self) -> None:
        device_index, device_name, _ = self._pick_device(self.config.device_keyword)
        block_size = int(self.config.sample_rate * self.config.block_ms / 1000)
        if block_size <= 0:
            block_size = 1280

        self._stream = sd.RawInputStream(
            samplerate=self.config.sample_rate,
            device=device_index,
            channels=1,
            dtype="int16",
            blocksize=block_size,
        )
        self._stream.start()
        self._stream_sample_rate = self.config.sample_rate
        self._device_name = device_name
        self._resample_state = None
        print(f"[WakeWord] stream opened on '{device_name}' @ {self.config.sample_rate} Hz")

    def _close_stream(self) -> None:
        stream = self._stream
        self._stream = None
        if stream is None:
            return

        try:
            stream.stop()
        except Exception:
            pass
        try:
            stream.close()
        except Exception:
            pass

    def close(self) -> None:
        self._closed = True
        self._close_stream()

    def __enter__(self) -> "WakeWordListener":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _reset_model_state(self) -> None:
        # openWakeWord keeps an internal melspectrogram + prediction buffer. Without an
        # explicit reset, the next wait_for_wake_word() call can re-trigger off the
        # leftover state from the last detection even if the new audio is silence.
        reset_fn = getattr(self._model, "reset", None)
        if callable(reset_fn):
            try:
                reset_fn()
            except Exception as exc:
                print(f"[WakeWord] model.reset() failed: {exc}")
            return

        prediction_buffer = getattr(self._model, "prediction_buffer", None)
        if isinstance(prediction_buffer, dict):
            for key, value in prediction_buffer.items():
                try:
                    value.clear()
                except Exception:
                    prediction_buffer[key] = type(value)()

    def _to_int16_array(self, raw_chunk) -> np.ndarray:
        if isinstance(raw_chunk, tuple):
            raw_chunk = raw_chunk[0]

        if isinstance(raw_chunk, np.ndarray):
            data = raw_chunk
            if data.dtype != np.int16:
                data = np.asarray(data, dtype=np.int16)
            return np.asarray(data).reshape(-1)

        return np.frombuffer(raw_chunk, dtype=np.int16)

    def _resample_to_model_rate(self, audio_native: np.ndarray) -> np.ndarray:
        if audio_native.size == 0:
            return audio_native.astype(np.int16)

        if audioop is not None:
            raw_bytes = audio_native.astype(np.int16, copy=False).tobytes()
            converted, self._resample_state = audioop.ratecv(
                raw_bytes,
                2,
                1,
                self._stream_sample_rate,
                WAKEWORD_MODEL_RATE,
                self._resample_state,
            )
            return np.frombuffer(converted, dtype=np.int16)

        # Lightweight numpy fallback. This is a linear interpolation downsampler,
        # which is enough for wake word triggering when audioop is unavailable.
        in_rate = float(self._stream_sample_rate)
        out_rate = float(WAKEWORD_MODEL_RATE)
        out_len = max(1, int(round(audio_native.size * out_rate / in_rate)))
        x_old = np.linspace(0.0, 1.0, num=audio_native.size, endpoint=False)
        x_new = np.linspace(0.0, 1.0, num=out_len, endpoint=False)
        downsampled = np.interp(x_new, x_old, audio_native.astype(np.float32))
        return np.clip(np.rint(downsampled), -32768, 32767).astype(np.int16)

    def _frame_to_model_input(self, raw_chunk) -> np.ndarray:
        frame = self._to_int16_array(raw_chunk)
        if self._stream_sample_rate == WAKEWORD_MODEL_RATE:
            return frame
        return self._resample_to_model_rate(frame)

    def _activation_from_predictions(self, predictions: dict) -> Optional[WakeWordActivation]:
        if not predictions:
            return None

        best_label = ""
        best_score = 0.0
        for label, score in predictions.items():
            if score > best_score:
                best_label = str(label)
                best_score = float(score)

        if best_score < self.config.threshold:
            return None

        return WakeWordActivation(
            label=best_label,
            score=best_score,
            sample_rate=self._stream_sample_rate,
            device_name=self._device_name,
        )

    def wait_for_wake_word(self) -> WakeWordActivation:
        """Block until the configured wake word is detected.

        Opens the device at the hardware-native sample rate and down-samples each chunk
        to 16 kHz before passing it to openWakeWord. Once a wake word is detected, the
        stream is closed immediately, then we sleep for a short baton-touch delay so
        ALSA can fully release the device before the recording pipeline tries to claim
        it.
        """
        if self._closed:
            raise RuntimeError("WakeWordListener is already closed")

        if self._stream is None:
            # Fresh stream means a fresh detection session; clear any state left over
            # from the previous activation so we don't immediately re-fire on stale
            # internal buffers.
            self._reset_model_state()
            self._open_stream()

        try:
            while True:
                if self._closed:
                    raise RuntimeError("WakeWordListener is closed")

                raw_chunk, _overflowed = self._stream.read(self._stream.blocksize)
                audio_frame = self._frame_to_model_input(raw_chunk)
                if audio_frame.size == 0:
                    continue

                predictions = self._model.predict(audio_frame)
                activation = self._activation_from_predictions(predictions)
                if activation is None:
                    continue

                # Baton touch: close the ALSA stream first, then give the OS a short
                # grace period so the next recording call can open the microphone without
                # a "Device busy" race.
                self._close_stream()
                time.sleep(self.config.baton_touch_delay_sec)
                print(
                    f"[WakeWord] detected '{activation.label}' score={activation.score:.3f} "
                    f"on {activation.device_name}"
                )
                return activation
        finally:
            # Ensure the device never stays open if an exception or Ctrl+C interrupts the loop.
            self._close_stream()


def build_wake_word_listener(
    model_name: Optional[str] = None,
    threshold: Optional[float] = None,
    device_keyword: Optional[str] = None,
    sample_rate: Optional[int] = None,
    baton_touch_delay_sec: Optional[float] = None,
) -> WakeWordListener:
    config = WakeWordConfig(
        model_name=model_name or DEFAULT_WAKEWORD_MODEL,
        threshold=DEFAULT_WAKEWORD_THRESHOLD if threshold is None else threshold,
        device_keyword=DEFAULT_DEVICE_KEYWORD if device_keyword is None else device_keyword,
        sample_rate=DEFAULT_SAMPLE_RATE if sample_rate is None else sample_rate,
        baton_touch_delay_sec=DEFAULT_BATON_TOUCH_DELAY_SEC if baton_touch_delay_sec is None else baton_touch_delay_sec,
    )
    return WakeWordListener(config=config)
