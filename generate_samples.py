import numpy as np
from scipy.io import wavfile
import os

def generate_tone(filename, freq=440, duration=5.0, sr=44100):
    t = np.linspace(0, duration, int(sr * duration))
    # A simple sine wave tone
    data = 0.5 * np.sin(2 * np.pi * freq * t)
    # Convert to 16-bit PCM
    data_int = (data * 32767).astype(np.int16)
    wavfile.write(filename, sr, data_int)
    print(f"Generated: {filename} (Sine Tone {freq}Hz)")

def generate_noise(filename, duration=5.0, sr=44100):
    # White noise
    data = np.random.uniform(-0.5, 0.5, int(sr * duration))
    data_int = (data * 32767).astype(np.int16)
    wavfile.write(filename, sr, data_int)
    print(f"Generated: {filename} (White Noise)")

def generate_multi_tone(filename, duration=5.0, sr=44100):
    t = np.linspace(0, duration, int(sr * duration))
    # Combination of frequencies
    data = (0.3 * np.sin(2 * np.pi * 220 * t) + 
            0.3 * np.sin(2 * np.pi * 440 * t) + 
            0.2 * np.sin(2 * np.pi * 880 * t))
    data_int = (data * 32767).astype(np.int16)
    wavfile.write(filename, sr, data_int)
    print(f"Generated: {filename} (Multi-tone Complex)")

if __name__ == "__main__":
    output_dir = "e:/audiosteg/samples"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    generate_tone(os.path.join(output_dir, "sine_440hz.wav"), freq=440)
    generate_noise(os.path.join(output_dir, "white_noise.wav"))
    generate_multi_tone(os.path.join(output_dir, "complex_tone.wav"))
    
    print("\nSamples are ready in 'e:/audiosteg/samples'")
