"""
Evaluation script for Audio Steganography System.
Computes SNR, MSE, and extraction accuracy across different test scenarios.
Generates tables and charts for the report.
"""

import numpy as np
from scipy.io import wavfile
from steganography import FFTSteganography
import os
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt


# ── Metrics ──────────────────────────────────────────────────────────────────

def compute_snr(original, stego):
    """Signal-to-Noise Ratio in dB."""
    signal_power = np.sum(original.astype(np.float64) ** 2)
    noise = original.astype(np.float64) - stego.astype(np.float64)
    noise_power = np.sum(noise ** 2)
    if noise_power == 0:
        return float('inf')
    return 10 * np.log10(signal_power / noise_power)


def compute_mse(original, stego):
    """Mean Squared Error."""
    diff = original.astype(np.float64) - stego.astype(np.float64)
    return np.mean(diff ** 2)


# ── Audio Generators ─────────────────────────────────────────────────────────

def generate_sine(duration=5.0, sr=44100, freq=440):
    t = np.linspace(0, duration, int(sr * duration))
    data = 0.5 * np.sin(2 * np.pi * freq * t)
    return sr, (data * 32767).astype(np.int16)


def generate_multi_tone(duration=5.0, sr=44100):
    t = np.linspace(0, duration, int(sr * duration))
    data = (0.3 * np.sin(2 * np.pi * 220 * t) +
            0.3 * np.sin(2 * np.pi * 440 * t) +
            0.2 * np.sin(2 * np.pi * 880 * t))
    return sr, (data * 32767).astype(np.int16)


def generate_noise(duration=5.0, sr=44100):
    data = np.random.uniform(-0.5, 0.5, int(sr * duration))
    return sr, (data * 32767).astype(np.int16)


# ── Test Messages ────────────────────────────────────────────────────────────

MESSAGES = {
    "Short (10 chars)":   "Hello World",
    "Medium (50 chars)":  "The quick brown fox jumps over the lazy dog nearby",
    "Long (100 chars)":   "A" * 100,
    "Long (200 chars)":   "Steganography is the art of hiding information in plain sight! " * 3 + "End.",
}

AUDIO_TYPES = {
    "Sine 440Hz":   generate_sine,
    "Multi-tone":   generate_multi_tone,
    "White Noise":  generate_noise,
}


# ── Run Evaluation ───────────────────────────────────────────────────────────

def run_evaluation():
    engine = FFTSteganography()
    results = []

    temp_input = "_eval_input.wav"
    temp_stego = "_eval_stego.wav"

    print("=" * 80)
    print("AUDIO STEGANOGRAPHY — EVALUATION RESULTS")
    print("=" * 80)
    print()

    for audio_name, audio_gen in AUDIO_TYPES.items():
        for msg_name, message in MESSAGES.items():
            sr, original_data = audio_gen()
            wavfile.write(temp_input, sr, original_data)

            try:
                engine.embed(temp_input, message, temp_stego)
                _, stego_data = wavfile.read(temp_stego)

                # Ensure same length
                min_len = min(len(original_data), len(stego_data))
                orig_trimmed = original_data[:min_len]
                steg_trimmed = stego_data[:min_len]

                snr = compute_snr(orig_trimmed, steg_trimmed)
                mse = compute_mse(orig_trimmed, steg_trimmed)

                # Test extraction accuracy
                extracted = engine.extract(temp_stego)
                accurate = extracted == message
                accuracy = 100.0 if accurate else 0.0

                results.append({
                    "audio": audio_name,
                    "message": msg_name,
                    "msg_len": len(message),
                    "snr": snr,
                    "mse": mse,
                    "accuracy": accuracy,
                    "match": accurate,
                })

                print(f"[{audio_name}] [{msg_name}]")
                print(f"  SNR = {snr:.2f} dB | MSE = {mse:.4f} | Accuracy = {accuracy:.0f}%")
                print()

            except Exception as e:
                print(f"[{audio_name}] [{msg_name}] ERROR: {e}")
                results.append({
                    "audio": audio_name,
                    "message": msg_name,
                    "msg_len": len(message),
                    "snr": 0, "mse": 0, "accuracy": 0, "match": False,
                })

    # Cleanup temp files
    for f in [temp_input, temp_stego]:
        if os.path.exists(f):
            os.remove(f)

    return results


# ── Generate Charts ──────────────────────────────────────────────────────────

def generate_charts(results):
    output_dir = "e:/audiosteg/evaluation_results"
    os.makedirs(output_dir, exist_ok=True)

    # ── Chart 1: SNR by Audio Type (grouped bar) ──
    fig, ax = plt.subplots(figsize=(10, 6))
    audio_types = list(AUDIO_TYPES.keys())
    msg_types = list(MESSAGES.keys())
    x = np.arange(len(audio_types))
    width = 0.18

    for i, msg in enumerate(msg_types):
        snr_vals = [r["snr"] for r in results if r["message"] == msg]
        bars = ax.bar(x + i * width, snr_vals, width, label=msg)

    ax.set_xlabel("Audio Type", fontsize=12)
    ax.set_ylabel("SNR (dB)", fontsize=12)
    ax.set_title("Signal-to-Noise Ratio by Audio Type and Message Length", fontsize=14)
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(audio_types)
    ax.legend(loc="upper right")
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "snr_comparison.png"), dpi=150)
    plt.close()
    print(f"Saved: {output_dir}/snr_comparison.png")

    # ── Chart 2: MSE by Audio Type (grouped bar) ──
    fig, ax = plt.subplots(figsize=(10, 6))

    for i, msg in enumerate(msg_types):
        mse_vals = [r["mse"] for r in results if r["message"] == msg]
        ax.bar(x + i * width, mse_vals, width, label=msg)

    ax.set_xlabel("Audio Type", fontsize=12)
    ax.set_ylabel("MSE", fontsize=12)
    ax.set_title("Mean Squared Error by Audio Type and Message Length", fontsize=14)
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(audio_types)
    ax.legend(loc="upper right")
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "mse_comparison.png"), dpi=150)
    plt.close()
    print(f"Saved: {output_dir}/mse_comparison.png")

    # ── Chart 3: SNR vs Message Length (line chart) ──
    fig, ax = plt.subplots(figsize=(10, 6))

    for audio_name in audio_types:
        audio_results = [r for r in results if r["audio"] == audio_name]
        msg_lens = [r["msg_len"] for r in audio_results]
        snrs = [r["snr"] for r in audio_results]
        ax.plot(msg_lens, snrs, marker='o', linewidth=2, label=audio_name)

    ax.set_xlabel("Message Length (characters)", fontsize=12)
    ax.set_ylabel("SNR (dB)", fontsize=12)
    ax.set_title("SNR vs Message Length for Different Audio Types", fontsize=14)
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "snr_vs_length.png"), dpi=150)
    plt.close()
    print(f"Saved: {output_dir}/snr_vs_length.png")

    # ── Chart 4: Accuracy Table (text-based visual) ──
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.axis('off')

    table_data = []
    for r in results:
        table_data.append([
            r["audio"],
            r["message"],
            f"{r['snr']:.2f}",
            f"{r['mse']:.4f}",
            f"{r['accuracy']:.0f}%"
        ])

    table = ax.table(
        cellText=table_data,
        colLabels=["Audio Type", "Message", "SNR (dB)", "MSE", "Accuracy"],
        cellLoc='center',
        loc='center'
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.2, 1.5)

    # Color header
    for j in range(5):
        table[0, j].set_facecolor('#4A6FA5')
        table[0, j].set_text_props(color='white', fontweight='bold')

    # Color accuracy cells
    for i, r in enumerate(results):
        color = '#c8e6c9' if r["match"] else '#ffcdd2'
        table[i + 1, 4].set_facecolor(color)

    plt.title("Evaluation Summary Table", fontsize=14, pad=20)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "summary_table.png"), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_dir}/summary_table.png")

    # ── Print LaTeX Table ──
    print("\n" + "=" * 80)
    print("LATEX TABLE (copy into your report)")
    print("=" * 80)
    print(r"""
\begin{table}[h]
\centering
\caption{Evaluation Results: SNR, MSE, and Extraction Accuracy}
\label{tab:evaluation-results}
\begin{tabular}{|l|l|c|c|c|}
\hline
\textbf{Audio Type} & \textbf{Message Length} & \textbf{SNR (dB)} & \textbf{MSE} & \textbf{Accuracy} \\
\hline""")

    for r in results:
        print(f"{r['audio']} & {r['message']} & {r['snr']:.2f} & {r['mse']:.4f} & {r['accuracy']:.0f}\\% \\\\")
        print(r"\hline")

    print(r"""\end{tabular}
\end{table}""")


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    results = run_evaluation()
    generate_charts(results)
    print("\n✅ Evaluation complete! Charts saved to e:/audiosteg/evaluation_results/")
