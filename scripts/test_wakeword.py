"""Standalone wake-word model tester.

Opens the same P5HD mic / resample path that the coordinator's WakeWordListener
uses, runs ONE model continuously for N seconds, and prints every prediction
above a tiny floor so you can read the score distribution directly. Useful for
A/B-ing freshly trained wake-word checkpoints without spinning up the whole
coordinator + BHL stack.

Usage (from PROJECT_ROOT):
    bash scripts/test_wakeword.sh checkpoints/wakeword/hailion_stop.tflite
    bash scripts/test_wakeword.sh checkpoints/wakeword/hailion_stop.onnx 20 0.005
        # args: <model_path> [duration_sec=30] [print_floor=0.001]
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from jetson.expression.wake_word import (  # noqa: E402
    DEFAULT_DEVICE_KEYWORD,
    DEFAULT_SAMPLE_RATE,
    WakeWordConfig,
    WakeWordListener,
)


def _framework_for(model_path: str) -> str:
    return "onnx" if model_path.lower().endswith(".onnx") else "tflite"


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    model_path = sys.argv[1]
    duration_sec = float(sys.argv[2]) if len(sys.argv) >= 3 else 30.0
    print_floor = float(sys.argv[3]) if len(sys.argv) >= 4 else 0.001

    resolved = Path(model_path).expanduser()
    if not resolved.is_absolute():
        resolved = (PROJECT_ROOT / resolved).resolve()
    if not resolved.exists():
        print(f"[test_wakeword] model not found: {resolved}")
        sys.exit(2)

    config = WakeWordConfig(
        model_name=str(resolved),
        threshold=1.0,  # 절대 트리거되지 않게 — 본 스크립트는 score 만 본다
        device_keyword=DEFAULT_DEVICE_KEYWORD or "P5HD",
        sample_rate=DEFAULT_SAMPLE_RATE,
        baton_touch_delay_sec=0.0,
        inference_framework=_framework_for(str(resolved)),
    )

    listener = WakeWordListener(config=config)
    # WakeWordListener 의 wait_for_wake_word 는 첫 트리거에서 return 하므로
    # 여기서는 stream / model 만 빌려 직접 loop 를 돈다. close() 가 stream 도
    # 정리해주니 cleanup 은 그대로 위임.
    listener._reset_model_state()  # noqa: SLF001
    listener._open_stream()  # noqa: SLF001

    print(f"[test_wakeword] model={resolved.name} framework={config.inference_framework}")
    print(f"[test_wakeword] duration={duration_sec:.1f}s print_floor={print_floor:.3f}")
    print("[test_wakeword] speak now ↓ ↓ ↓")

    peak = 0.0
    peak_label = ""
    started = time.time()
    try:
        stream = listener._stream  # noqa: SLF001
        while time.time() - started < duration_sec:
            raw_chunk, _ = stream.read(stream.blocksize)
            audio_frame = listener._frame_to_model_input(raw_chunk)  # noqa: SLF001
            if audio_frame.size == 0:
                continue
            predictions = listener._model.predict(audio_frame)  # noqa: SLF001
            if not predictions:
                continue
            best_label = ""
            best_score = 0.0
            for label, score in predictions.items():
                s = float(score)
                if s > best_score:
                    best_label = str(label)
                    best_score = s
            if best_score > peak:
                peak = best_score
                peak_label = best_label
            if best_score >= print_floor:
                t = time.time() - started
                print(f"[{t:6.2f}s] best={best_label!r} score={best_score:.3f}")
    finally:
        listener.close()

    print(f"[test_wakeword] DONE — peak={peak:.3f} label={peak_label!r}")


if __name__ == "__main__":
    main()
