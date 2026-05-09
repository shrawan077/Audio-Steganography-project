import io
import numpy as np
from scipy.io import wavfile


# ── Manual FFT / IFFT (Cooley-Tukey radix-2) ────────────────────────────────

def _fft_recursive(x):
    """Cooley-Tukey radix-2 Decimation-In-Time FFT (recursive).
    Input length MUST be a power of 2.
    """
    N = len(x)
    if N <= 1:
        return x

    # Split into even / odd indices
    even = _fft_recursive(x[0::2])
    odd  = _fft_recursive(x[1::2])

    # Twiddle factors  W_N^k = e^{-2πjk/N}
    T = np.exp(-2j * np.pi * np.arange(N // 2) / N) * odd

    return np.concatenate([even + T, even - T])


def manual_fft(x):
    """Compute the DFT of x using the Cooley-Tukey FFT algorithm.
    Automatically zero-pads to the next power of 2.
    """
    N = len(x)
    # Pad to next power of 2
    n_padded = 1
    while n_padded < N:
        n_padded <<= 1

    x_padded = np.zeros(n_padded, dtype=complex)
    x_padded[:N] = x
    return _fft_recursive(x_padded)


def manual_ifft(X):
    """Compute the inverse DFT using the FFT via the conjugate method:
       ifft(X) = conj( fft( conj(X) ) ) / N
    """
    N = len(X)
    # Pad to next power of 2 (should already be, but just in case)
    n_padded = 1
    while n_padded < N:
        n_padded <<= 1

    X_padded = np.zeros(n_padded, dtype=complex)
    X_padded[:N] = X
    return np.conjugate(_fft_recursive(np.conjugate(X_padded))) / n_padded

class FFTSteganography:
    def __init__(self, frame_size=1024, freq_range=(100, 300), step=0.1):
        """
        Initialize the steganography engine.
        :param frame_size: Size of FFT frames.
        :param freq_range: Range of frequency bins (mid-frequencies) to use for embedding.
        :param step: Magnitude quantization step for embedding.
        """
        self.frame_size = frame_size
        self.freq_range = freq_range
        self.step = step
        self.terminator = "###END###"

    def _text_to_bits(self, text):
        bits = []
        for char in text:
            bin_val = bin(ord(char))[2:].zfill(8)
            bits.extend([int(b) for b in bin_val])
        return bits

    def _bits_to_text(self, bits):
        chars = []
        for i in range(0, len(bits), 8):
            byte = bits[i:i+8]
            if len(byte) < 8:
                break
            char_code = int("".join(map(str, byte)), 2)
            chars.append(chr(char_code))
        return "".join(chars)

    def embed(self, input_path, message, output_path):
        """
        Embed message into audio file.
        """
        sample_rate, data = wavfile.read(input_path)
        
        # Convert to mono float64
        if len(data.shape) > 1:
            audio = data.mean(axis=1).astype(np.float64)
        else:
            audio = data.astype(np.float64)

        # Normalize to [-1, 1] if it was 16-bit PCM
        if data.dtype == np.int16:
            audio /= 32768.0

        message_with_term = message + self.terminator
        bits = self._text_to_bits(message_with_term)
        bit_idx = 0
        total_bits = len(bits)

        num_frames = len(audio) // self.frame_size
        stego_audio = np.zeros_like(audio)

        for i in range(num_frames):
            frame = audio[i * self.frame_size : (i + 1) * self.frame_size]
            
            # FFT
            f_transform = manual_fft(frame)
            magnitudes = np.abs(f_transform)
            phases = np.angle(f_transform)

            # Embed bits into magnitude
            # Use only freq_range to avoid audible distortion in lows/highs
            for freq in range(self.freq_range[0], self.freq_range[1]):
                if bit_idx < total_bits:
                    bit = bits[bit_idx]
                    
                    # QIM (Quantization Index Modulation) on magnitude
                    # magnitude' = round(magnitude / step) * step
                    # If bit is 1, shift by step/2
                    m = magnitudes[freq]
                    q = np.floor(m / self.step)
                    
                    if bit == 1:
                        if q % 2 == 0:
                            magnitudes[freq] = (q + 1) * self.step
                        else:
                            magnitudes[freq] = q * self.step
                    else:
                        if q % 2 == 1:
                            magnitudes[freq] = (q + 1) * self.step
                        else:
                            magnitudes[freq] = q * self.step
                    
                    # Also update the symmetric component for real FFT result
                    magnitudes[self.frame_size - freq] = magnitudes[freq]
                    
                    bit_idx += 1

            # Reconstruct frame
            new_f_transform = magnitudes * np.exp(1j * phases)
            stego_frame = np.real(manual_ifft(new_f_transform))
            stego_audio[i * self.frame_size : (i + 1) * self.frame_size] = stego_frame

        if bit_idx < total_bits:
            raise ValueError(f"Message too long for the given audio. Embedded {bit_idx}/{total_bits} bits.")

        # Convert back to 16-bit PCM
        # Clip to avoid overflow
        stego_audio = np.clip(stego_audio, -1, 1)
        stego_audio_int = (stego_audio * 32767).astype(np.int16)
        
        wavfile.write(output_path, sample_rate, stego_audio_int)
        return True

    def embed_array(self, audio_array: np.ndarray, sample_rate: int, message: str) -> tuple[np.ndarray, int]:
        """
        Embed *message* into *audio_array* (int16 or float64, mono).
        Returns (stego_int16_array, sample_rate).
        Works entirely in-memory — no file I/O.
        """
        # Normalise to float64 in [-1, 1]
        if audio_array.dtype == np.int16:
            audio = audio_array.astype(np.float64) / 32768.0
        else:
            audio = audio_array.astype(np.float64)

        message_with_term = message + self.terminator
        bits = self._text_to_bits(message_with_term)
        bit_idx = 0
        total_bits = len(bits)

        num_frames = len(audio) // self.frame_size
        stego_audio = np.zeros_like(audio)

        for i in range(num_frames):
            frame = audio[i * self.frame_size : (i + 1) * self.frame_size]
            f_transform = manual_fft(frame)
            magnitudes = np.abs(f_transform)
            phases = np.angle(f_transform)

            for freq in range(self.freq_range[0], self.freq_range[1]):
                if bit_idx < total_bits:
                    bit = bits[bit_idx]
                    m = magnitudes[freq]
                    q = np.floor(m / self.step)
                    if bit == 1:
                        if q % 2 == 0:
                            magnitudes[freq] = (q + 1) * self.step
                        else:
                            magnitudes[freq] = q * self.step
                    else:
                        if q % 2 == 1:
                            magnitudes[freq] = (q + 1) * self.step
                        else:
                            magnitudes[freq] = q * self.step
                    magnitudes[self.frame_size - freq] = magnitudes[freq]
                    bit_idx += 1

            new_f = magnitudes * np.exp(1j * phases)
            stego_frame = np.real(manual_ifft(new_f))
            stego_audio[i * self.frame_size : (i + 1) * self.frame_size] = stego_frame

        if bit_idx < total_bits:
            raise ValueError(f"Message too long. Embedded {bit_idx}/{total_bits} bits.")

        stego_int16 = (np.clip(stego_audio, -1, 1) * 32767).astype(np.int16)
        return stego_int16, sample_rate

    def extract_array(self, audio_array: np.ndarray) -> str:
        """
        Extract the hidden message from *audio_array* (int16 or float64, mono).
        Returns the extracted text string.
        """
        if audio_array.dtype == np.int16:
            audio = audio_array.astype(np.float64) / 32768.0
        else:
            audio = audio_array.astype(np.float64)

        bits = []
        num_frames = len(audio) // self.frame_size

        for i in range(num_frames):
            frame = audio[i * self.frame_size : (i + 1) * self.frame_size]
            f_transform = manual_fft(frame)
            magnitudes = np.abs(f_transform)
            for freq in range(self.freq_range[0], self.freq_range[1]):
                m = magnitudes[freq]
                q = np.round(m / self.step)
                bits.append(int(q % 2))

            current_text = self._bits_to_text(bits)
            if self.terminator in current_text:
                return current_text.split(self.terminator)[0]

        return "[Terminator not found — extraction may be incomplete]"

    # ── WAV ↔ bytes helpers (for TCP transfer) ─────────────────────────────

    @staticmethod
    def array_to_wav_bytes(audio_array: np.ndarray, sample_rate: int) -> bytes:
        """Serialise a numpy int16 audio array into raw WAV bytes (in-memory)."""
        buf = io.BytesIO()
        wavfile.write(buf, sample_rate, audio_array.astype(np.int16))
        return buf.getvalue()

    @staticmethod
    def wav_bytes_to_array(wav_bytes: bytes) -> tuple[np.ndarray, int]:
        """Deserialise raw WAV bytes back into (int16 array, sample_rate)."""
        buf = io.BytesIO(wav_bytes)
        sample_rate, data = wavfile.read(buf)
        if len(data.shape) > 1:
            data = data.mean(axis=1).astype(np.int16)
        return data, sample_rate

    def extract(self, stego_path):
        """
        Extract message from audio file.
        """
        sample_rate, data = wavfile.read(stego_path)
        
        # Audio is likely already mono from our process, but handle just in case
        if len(data.shape) > 1:
            audio = data.mean(axis=1).astype(np.float64)
        else:
            audio = data.astype(np.float64)

        if data.dtype == np.int16:
            audio /= 32768.0

        bits = []
        num_frames = len(audio) // self.frame_size

        for i in range(num_frames):
            frame = audio[i * self.frame_size : (i + 1) * self.frame_size]
            f_transform = manual_fft(frame)
            magnitudes = np.abs(f_transform)

            for freq in range(self.freq_range[0], self.freq_range[1]):
                m = magnitudes[freq]
                q = np.round(m / self.step)
                bits.append(int(q % 2))

            # Partial extraction check for terminator
            # Check every frame for efficiency
            current_text = self._bits_to_text(bits)
            if self.terminator in current_text:
                return current_text.split(self.terminator)[0]

        return "Terminator not found. Extraction may be incomplete."

