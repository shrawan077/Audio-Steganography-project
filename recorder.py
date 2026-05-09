"""
recorder.py — Microphone Audio Capture
----------------------------------------
Captures live audio from the default system microphone and returns
a numpy int16 array ready for FFT steganography embedding.

Dependencies:
    pip install sounddevice

Usage:
    from recorder import record_audio
    samples, sample_rate = record_audio(duration_sec=5)
"""

import numpy as np
import threading
import logging

logger = logging.getLogger(__name__)

DEFAULT_SAMPLE_RATE = 44100   # Hz  (CD quality)
DEFAULT_CHANNELS    = 1       # Mono (steganography engine expects mono)


def record_audio(duration_sec: float,
                 sample_rate: int = DEFAULT_SAMPLE_RATE,
                 channels: int   = DEFAULT_CHANNELS) -> tuple[np.ndarray, int]:
    """
    Record audio from the default microphone for `duration_sec` seconds.

    Returns
    -------
    samples : np.ndarray, dtype=int16
        Recorded audio samples (mono).
    sample_rate : int
        The sample rate used for recording.

    Raises
    ------
    RuntimeError
        If sounddevice is not installed or no microphone is found.
    """
    try:
        import sounddevice as sd
    except ImportError:
        raise RuntimeError(
            "sounddevice is not installed. Run: pip install sounddevice"
        )

    logger.info(f"Recording {duration_sec}s at {sample_rate}Hz ...")

    # sd.rec returns float32 in [-1.0, 1.0]
    recording = sd.rec(
        int(duration_sec * sample_rate),
        samplerate=sample_rate,
        channels=channels,
        dtype="float32",
    )
    sd.wait()   # block until done

    # Flatten to 1-D mono
    samples_float = recording.flatten()

    # Convert float32 → int16
    samples_int16 = (np.clip(samples_float, -1.0, 1.0) * 32767).astype(np.int16)

    logger.info(f"Recording complete: {len(samples_int16)} samples")
    return samples_int16, sample_rate


class AsyncRecorder:
    """
    Non-blocking wrapper around record_audio for GUI use.

    Usage:
        rec = AsyncRecorder(duration_sec=5, on_done=callback, on_error=err_cb)
        rec.start()
        # callback(samples: np.ndarray, sample_rate: int) fires when done
    """

    def __init__(self, duration_sec: float, on_done, on_error=None,
                 sample_rate: int = DEFAULT_SAMPLE_RATE):
        self.duration_sec = duration_sec
        self.on_done      = on_done
        self.on_error     = on_error
        self.sample_rate  = sample_rate
        self._thread: threading.Thread | None = None

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        try:
            samples, sr = record_audio(self.duration_sec, self.sample_rate)
            self.on_done(samples, sr)
        except Exception as e:
            logger.error(f"Recording error: {e}")
            if self.on_error:
                self.on_error(str(e))
