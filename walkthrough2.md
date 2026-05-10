# Audio Steganography: Core Processes

This document provides a visual representation of how the FFT-based audio steganography system embeds and extracts messages using a **manual recursive FFT** algorithm.

## 1. Embedding Process

The embedding process uses **Quantization Index Modulation (QIM)** in the frequency domain with a custom Cooley-Tukey FFT implementation.

```mermaid
graph TD
    A["Audio Source (Mic Stream or WAV)"] --> B["Capture/Read & Convert to Mono"]
    B --> C["Normalize Audio Samples"]
    D["Secret Message"] --> E["Convert to UTF-8 Bits & Add Terminator"]
    C --> F["Divide Audio into 1024-sample Frames"]
    E --> G["Process Each Frame"]
    F --> G
    
    subgraph "Per Frame Processing (Manual FFT)"
        G --> H["Manual Recursive FFT"]
        H --> I["Get Magnitudes & Phases"]
        I --> J["Modify Magnitudes using QIM"]
        J --> K["Symmetric Update for Real FFT"]
        K --> L["Manual Inverse FFT (IFFT)"]
    end
    
    L --> M["Reconstruct Stego Audio"]
    M --> N["Convert to 16-bit PCM (WAV bytes)"]
    N --> O["Transmit via TCP over LAN"]
```

---

## 2. Extraction Process

The extraction process reverses the quantization to retrieve the bitstream from incoming network packets.

```mermaid
graph TD
    A["Incoming TCP Packets (WAV bytes)"] --> B["Reconstruct Signal & Normalize"]
    B --> C["Divide Audio into 1024-sample Frames"]
    C --> D["Process Each Frame"]
    
    subgraph "Per Frame Extraction (Manual FFT)"
        D --> E["Manual Recursive FFT"]
        E --> F["Get Magnitudes"]
        F --> G["Check Bin Magnitudes (100-300Hz)"]
        G --> H["Quantize Magnitude / Step (0.1)"]
        H --> I["Extract Bit: Q % 2"]
    end
    
    I --> J["Append Bits to Buffer"]
    J --> K["Convert Bits to UTF-8 Text"]
    K --> L{"###END### Found?"}
    L -- "Yes" --> M["Stop & Show Message"]
    L -- "No" --> D
    
    M --> N["Final Decoded Message"]
```

## Presentation Slides (Concise Versions)

These simplified diagrams highlight the core high-level logic for presentations.

### Embedding (Simplified)
```mermaid
graph LR
    Msg["Secret Message"] --> Bits["UTF-8 Bitstream"]
    Audio["Mic Recording"] --> FFT["Manual FFT"]
    Bits --> QIM["QIM Embedding"]
    FFT --> QIM
    QIM --> IFFT["Manual IFFT"]
    IFFT --> TCP["TCP Transmission"]
```

### Extraction (Simplified)
```mermaid
graph LR
    TCP["TCP Signal"] --> FFT["Manual FFT"]
    FFT --> QIM["QIM Detection"]
    QIM --> Bits["UTF-8 Bits"]
    Bits --> Msg["Secret Message"]
```

## Key Technologies
- **Manual FFT:** A Cooley-Tukey radix-2 implementation built from scratch in Python.
- **Start/Stop Recording:** Continuous audio streaming for flexible message embedding.
- **QIM (Quantization Index Modulation):** Encodes bits by forcing frequency magnitudes to even or odd multiples of a quantization step.
- **UTF-8 Encoding:** Robust character support including emojis and special symbols.
- **Responsive UI:** Dynamic font scaling that adjusts automatically to full-screen mode.
- **P2P Networking:** Direct TCP/IP communication between devices on the same Wi-Fi.
