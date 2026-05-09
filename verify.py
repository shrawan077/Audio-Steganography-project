import numpy as np
from scipy.io import wavfile
from steganography import FFTSteganography
import os

def create_sample_audio(filename, duration=5.0, sr=44100):
    # Noise/Signal for testing
    t = np.linspace(0, duration, int(sr * duration))
    # Mix of some frequencies to make it non-silent
    data = 0.5 * np.sin(2 * np.pi * 440 * t) + 0.3 * np.sin(2 * np.pi * 880 * t)
    # Convert to 16-bit PCM
    data_int = (data * 32767).astype(np.int16)
    wavfile.write(filename, sr, data_int)
    print(f"Created sample audio: {filename}")

def run_test():
    engine = FFTSteganography()
    input_wav = "sample_input.wav"
    stego_wav = "sample_stego.wav"
    secret_msg = "Top Secret Message: FFT Steganography is cool!"
    
    try:
        if not os.path.exists(input_wav):
            create_sample_audio(input_wav)
            
        print(f"Embedding message: '{secret_msg}'")
        engine.embed(input_wav, secret_msg, stego_wav)
        
        print("Extracting message...")
        extracted = engine.extract(stego_wav)
        
        print(f"Extracted: '{extracted}'")
        
        if extracted == secret_msg:
            print("SUCCESS: Message matches!")
        else:
            print("FAILURE: Message mismatch.")
            
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        # Cleanup
        for f in [input_wav, stego_wav]:
            if os.path.exists(f):
                os.remove(f)

if __name__ == "__main__":
    run_test()
