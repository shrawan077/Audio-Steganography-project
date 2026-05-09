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


import sounddevice as sd

class AsyncRecorder:
    """
    Non-blocking continuous audio recorder for GUI use.

    Usage:
        rec = AsyncRecorder(on_done=callback, on_error=err_cb)
        rec.start()
        # later...
        rec.stop()  # triggers on_done(samples, sample_rate)
    """

    def __init__(self, on_done, on_error=None,
                 sample_rate: int = DEFAULT_SAMPLE_RATE,
                 channels: int = DEFAULT_CHANNELS):
        self.on_done      = on_done
        self.on_error     = on_error
        self.sample_rate  = sample_rate
        self.channels     = channels
        self.frames       = []
        self.stream       = None

    def start(self):
        self.frames = []
        def callback(indata, frames, time, status):
            if status:
                logger.warning(f"Recording status: {status}")
            self.frames.append(indata.copy())

        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32",
                callback=callback
            )
            self.stream.start()
            logger.info("Recording started.")
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            if self.on_error:
                self.on_error(str(e))

    def stop(self):
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            logger.info("Recording stopped.")
            
            if not self.frames:
                if self.on_error:
                    self.on_error("No audio recorded.")
                return

            samples_float = np.concatenate(self.frames).flatten()
            samples_int16 = (np.clip(samples_float, -1.0, 1.0) * 32767).astype(np.int16)
            self.on_done(samples_int16, self.sample_rate)
