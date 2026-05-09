#  CryptoWave — Covert Audio Steganography Communication System

A real-time **covert communication platform** that hides secret text messages inside audio files and transmits them between devices over a local Wi-Fi network. The audio sounds completely normal to anyone listening — the hidden message is invisible and inaudible.

Built with a custom **Cooley-Tukey FFT** implementation and **QIM (Quantization Index Modulation)** for frequency-domain steganography.

---

##  Features

-  **Live Microphone Recording** — capture audio directly from your laptop mic
-  **FFT + QIM Steganography** — hide text inside frequency-domain magnitudes (inaudible)
-  **Real-time LAN Transfer** — send stego audio to another device over TCP/IP (Wi-Fi)
-  **Auto-receive & Extract** — receiver automatically detects and decodes the hidden message
-  **Bidirectional Chat** — both devices can send and reply (covert walkie-talkie)
-  **Premium Dark UI** — 4-screen PyQt5 interface with activity logs and playback

---

## 🖥 How It Works

```
[Sender]                                  [Receiver]
  Speak into mic                            Listening on TCP port 9999
       ↓
  Record 5 seconds of audio
       ↓
  FFT → embed secret text                ──── WAV over Wi-Fi ────→   Receive WAV
  in frequency magnitudes                                              FFT → extract text
       ↓                                 ←─── reply WAV ─────────   Record reply → embed → send
  Receive reply & extract
```

Both sides look like they are exchanging audio clips — but each clip carries a hidden message that only this app can extract.

---

##  Project Structure

```
audiosteg/
├── main.py             # Entry point + premium dark stylesheet
├── gui.py              # 4-screen PyQt5 GUI (Home, Send, Receive, Settings)
├── steganography.py    # Core FFT + QIM embed/extract engine (manual FFT)
├── network.py          # TCP send/receive over LAN (length-prefixed protocol)
├── recorder.py         # Microphone capture (sounddevice, async-ready)
├── generate_samples.py # Helper: generate test WAV files
├── verify.py           # Helper: verify embedding integrity
├── evaluate.py         # Evaluation metrics (SNR, capacity, BER)
└── requirements.txt
```

---

##  Installation

**Requirements**: Python 3.10+

```bash
# 1. Clone the repo
git clone https://github.com/shrawan077/Audio-Steganography.git
cd Audio-Steganography

# 2. Create a virtual environment
python -m venv .venv

# 3. Activate it
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux / macOS

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the app
python main.py
```

---

##  Usage — Two Laptops on the Same Wi-Fi

### Device B (Receiver) — do this first
1. Run `python main.py`
2. Click **" Receive Message"**
3. Note the IP address shown (e.g. `192.168.1.10`) — share it with the sender
4. Click **" Start Listening"** — the app is now waiting for incoming audio

### Device A (Sender)
1. Run `python main.py`
2. Click **"Send Message"**
3. Click **"Record Mic"** — speak for 5 seconds
4. Type your secret message in the text box
5. Enter Device B's IP address
6. Click **"Embed & Send"**

Device B will automatically receive the audio, play it (sounds normal), and display the extracted hidden message. Click **"↩ Reply"** to send a message back.

>  **Tip**: Use your phone as a mobile hotspot and connect both laptops to it — no college/office network restrictions.

---

##  Algorithm

### Embedding
1. **Text → Bits**: Each character → 8-bit ASCII. Append `###END###` terminator.
2. **Frame FFT**: Split audio into 1024-sample frames. Apply Cooley-Tukey radix-2 FFT.
3. **QIM on magnitudes**: For each bit, quantize the magnitude of frequency bins 100–300:
   - Odd quantization index → bit `1`
   - Even quantization index → bit `0`
   - Max perturbation: `step = 0.1` (imperceptible)
4. **IFFT**: Reconstruct audio from modified magnitudes + original phases.

### Extraction
1. Apply FFT to each frame, read magnitudes of bins 100–300.
2. `bit = round(magnitude / step) % 2`
3. Collect bits until terminator is found → decode to text.

**Capacity**: ~5,000 characters per 5-second recording at 44100 Hz.

### Why QIM over LSB?
| | LSB (time domain) | QIM (frequency domain) |
|---|---|---|
| Robustness to noise | ❌ Very fragile | ✅ Robust |
| Audio quality impact | Low | Very low |
| Survives re-encoding | ❌ No | ✅ Partial |

---

## 🌐 Network Protocol

Simple length-prefixed TCP protocol over LAN:

```
┌─────────────────────────────────────────┐
│  4 bytes (uint32, big-endian) = length  │  ← tells receiver how many bytes to expect
│  N bytes = raw WAV file content         │  ← the stego audio
└─────────────────────────────────────────┘
```

The receiver runs a daemon thread (`ReceiverServer`) that listens on port `9999` and fires a Qt signal when a complete transfer arrives — keeping the GUI fully responsive.

---

## 🛠 Firewall (Windows)

If the receiver can't receive connections, run this in **Command Prompt (Admin)**:

```powershell
netsh advfirewall firewall add rule name="CryptoWave" protocol=TCP dir=in localport=9999 action=allow
```

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `numpy` | Array operations |
| `scipy` | WAV file I/O |
| `PyQt5` | GUI framework |
| `sounddevice` | Microphone capture |

---
