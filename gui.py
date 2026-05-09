"""
gui.py — Audio Steganography
----------------------------------------------------------
4-screen PyQt5 application:
  1. Home       – title + navigation
  2. Send       – record mic / load WAV → embed message → send over TCP
  3. Receive    – listen for incoming audio → play it → extract hidden message
  4. Settings   – peer IP, port, recording duration
"""

import sys
import os
import io
import tempfile
import threading
import time

import numpy as np
from scipy.io import wavfile

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QFileDialog, QMessageBox,
    QFrame, QStackedWidget, QLineEdit, QSpinBox, QProgressBar,
    QSizePolicy, QScrollArea
)
from PyQt5.QtCore import Qt, QUrl, QTimer, pyqtSignal, QObject
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtGui import QFont, QColor

from steganography import FFTSteganography
from network import ReceiverServer, send_audio, get_local_ip
from recorder import AsyncRecorder


def get_style(width, height):
    # Calculate scale factor based on a reference resolution (e.g., 900x700)
    # Use the smaller of width/height scale to prevent massive fonts on ultrawide
    scale = min(width / 900.0, height / 700.0)
    scale = max(0.8, min(scale, 2.0))  # Clamp between 0.8x and 2.0x

    base_fs = int(13 * scale)
    card_title_fs = int(11 * scale)
    app_title_fs = int(42 * scale)
    app_subtitle_fs = int(15 * scale)
    screen_title_fs = int(20 * scale)
    nav_card_fs = int(15 * scale)
    big_btn_fs = int(16 * scale)
    extract_box_fs = int(14 * scale)
    log_box_fs = int(12 * scale)

    return f"""
/* ─── Global ─────────────────────────────────────────────────────────────── */
QMainWindow, QWidget {{
    background-color: #0d1117;
    color: #e6edf3;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: {base_fs}px;
}}

/* ─── Cards ──────────────────────────────────────────────────────────────── */
QFrame#Card {{
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 4px;
}}

QLabel#CardTitle {{
    font-size: {card_title_fs}px;
    font-weight: bold;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 6px;
}}

/* ─── App Title (Home) ───────────────────────────────────────────────────── */
QLabel#AppTitle {{
    font-size: {app_title_fs}px;
    font-weight: 800;
    color: #58a6ff;
    margin-top: 20px;
    margin-bottom: 4px;
}}

QLabel#AppSubtitle {{
    font-size: {app_subtitle_fs}px;
    color: #8b949e;
    margin-bottom: 10px;
}}

QLabel#HintLabel {{
    font-size: {base_fs}px;
    color: #6e7681;
    line-height: 1.6;
}}

QLabel#IpBadge {{
    font-size: {base_fs}px;
    color: #4ecca3;
    background-color: #0d2b20;
    border: 1px solid #4ecca3;
    border-radius: 8px;
    padding: 6px 18px;
    margin: 6px;
}}

/* ─── Screen title ───────────────────────────────────────────────────────── */
QLabel#ScreenTitle {{
    font-size: {screen_title_fs}px;
    font-weight: 700;
    color: #e6edf3;
}}

QLabel#InfoLabel {{
    color: #8b949e;
    font-size: {base_fs}px;
}}

/* ─── Navigation cards ───────────────────────────────────────────────────── */
QPushButton#NavCard {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #1c2333, stop:1 #161b22);
    border: 1px solid #30363d;
    border-radius: 16px;
    color: #e6edf3;
    font-size: {nav_card_fs}px;
    font-weight: 600;
    padding: 20px;
}}
QPushButton#NavCard:hover {{
    border-color: #58a6ff;
    color: #58a6ff;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #1c2a42, stop:1 #1c2333);
}}

/* ─── Buttons ────────────────────────────────────────────────────────────── */
QPushButton {{
    background-color: #21262d;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 8px 16px;
    font-size: {base_fs}px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: #30363d;
    border-color: #58a6ff;
}}
QPushButton:disabled {{
    color: #484f58;
    border-color: #21262d;
    background-color: #161b22;
}}

QPushButton#ActionBtn {{
    background-color: #1a7f64;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 9px 20px;
    font-weight: 600;
}}
QPushButton#ActionBtn:hover {{ background-color: #238a6f; }}

QPushButton#SecondaryBtn {{
    background-color: #21262d;
    color: #58a6ff;
    border: 1px solid #30363d;
}}
QPushButton#SecondaryBtn:hover {{ border-color: #58a6ff; }}

QPushButton#BigActionBtn {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0d4a8a, stop:1 #1a7f64);
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 14px;
    font-size: {big_btn_fs}px;
    font-weight: 700;
    min-height: 44px;
}}
QPushButton#BigActionBtn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1158a8, stop:1 #238a6f);
}}
QPushButton#BigActionBtn:disabled {{
    background: #21262d;
    color: #484f58;
}}

QPushButton#ListenBtn {{
    background-color: #0d4a8a;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 9px 20px;
    font-weight: 600;
}}
QPushButton#ListenBtn:hover {{ background-color: #1158a8; }}
QPushButton#ListenBtn:checked {{
    background-color: #6e1f1f;
}}
QPushButton#ListenBtn:checked:hover {{ background-color: #8a2323; }}

QPushButton#PlayBtn {{
    background-color: #1a7f64;
    color: #ffffff;
    border: none;
    border-radius: 20px;
    min-width: 40px;
    min-height: 40px;
    max-width: 40px;
    max-height: 40px;
    font-size: {big_btn_fs}px;
    padding: 0;
}}
QPushButton#PlayBtn:hover {{ background-color: #238a6f; }}

QPushButton#PlayBtnLg {{
    background-color: #1a7f64;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 8px 24px;
    font-weight: 600;
    font-size: {extract_box_fs}px;
}}
QPushButton#PlayBtnLg:hover {{ background-color: #238a6f; }}
QPushButton#PlayBtnLg:disabled {{ background-color: #161b22; color: #484f58; }}

QPushButton#BackBtn {{
    background-color: transparent;
    color: #8b949e;
    border: 1px solid #30363d;
    border-radius: 6px;
    font-size: {card_title_fs}px;
    padding: 5px 10px;
}}
QPushButton#BackBtn:hover {{
    color: #e6edf3;
    border-color: #8b949e;
}}

/* ─── Inputs ─────────────────────────────────────────────────────────────── */
QLineEdit#InputField, QSpinBox {{
    background-color: #0d1117;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 7px 10px;
    font-size: {base_fs}px;
}}
QLineEdit#InputField:focus, QSpinBox:focus {{
    border-color: #58a6ff;
}}

QTextEdit {{
    background-color: #0d1117;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 10px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: {base_fs}px;
}}

QTextEdit#LogBox {{
    color: #8b949e;
    font-size: {log_box_fs}px;
    border: 1px solid #21262d;
}}

QTextEdit#ExtractBox {{
    border: 1px solid #4ecca3;
    color: #4ecca3;
    font-size: {extract_box_fs}px;
    font-weight: 500;
}}

/* ─── Progress bar ───────────────────────────────────────────────────────── */
QProgressBar#RecBar {{
    background-color: #21262d;
    border: none;
    border-radius: 4px;
    height: 6px;
}}
QProgressBar#RecBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #58a6ff, stop:1 #4ecca3);
    border-radius: 4px;
}}

/* ─── Scrollbars ─────────────────────────────────────────────────────────── */
QScrollBar:vertical {{
    background: #0d1117;
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: #30363d;
    border-radius: 4px;
}}
QScrollBar::handle:vertical:hover {{ background: #58a6ff; }}

QLabel {{
    color: #8b949e;
}}
"""


# ─────────────────────────────────────────────────────────────────────────────
# Signal bridge: lets background threads post safely to the Qt GUI thread
# ─────────────────────────────────────────────────────────────────────────────
class Bridge(QObject):
    log_signal      = pyqtSignal(str, str)   # (message, level)
    recv_signal     = pyqtSignal(bytes, str) # (wav_bytes, sender_ip)
    record_done     = pyqtSignal(object, int)# (np.ndarray, sample_rate)
    error_signal    = pyqtSignal(str)
    extract_done    = pyqtSignal(str)        # (extracted_message)


# ─────────────────────────────────────────────────────────────────────────────
# Main Window
# ─────────────────────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.stego     = FFTSteganography()
        self.bridge    = Bridge()
        self.player    = QMediaPlayer()
        self.receiver  = None          # ReceiverServer instance
        self.active_play_btn = None

        # Transient state
        self.recorded_samples   = None   # int16 ndarray from mic
        self.recorded_sr        = 44100
        self.loaded_audio_path  = None   # path for load-from-file
        self.received_wav_bytes = None   # latest received wav
        self.received_temp_path = None   # saved to temp for playback

        # Defaults (overridden by Settings screen)
        self.peer_ip    = ""
        self.peer_port  = 9999

        self._connect_bridge()
        self._init_ui()

    # ── Signal wiring ────────────────────────────────────────────────────────
    def _connect_bridge(self):
        self.bridge.log_signal.connect(self._append_log)
        self.bridge.recv_signal.connect(self._on_audio_received)
        self.bridge.record_done.connect(self._on_record_done)
        self.bridge.error_signal.connect(lambda msg: QMessageBox.critical(self, "Error", msg))
        self.bridge.extract_done.connect(self._show_extracted)

    # ── UI init ──────────────────────────────────────────────────────────────
    def _init_ui(self):
        self.setWindowTitle("Audio Steganography")
        self.setMinimumSize(820, 640)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.home_screen     = self._build_home()
        self.send_screen     = self._build_send()
        self.receive_screen  = self._build_receive()
        self.settings_screen = self._build_settings()

        for w in [self.home_screen, self.send_screen,
                  self.receive_screen, self.settings_screen]:
            self.stack.addWidget(w)

        self.player.stateChanged.connect(self._on_player_state)

    # ═════════════════════════════════════════════════════════════════════════
    # Screen builders
    # ═════════════════════════════════════════════════════════════════════════

    # ── HOME ─────────────────────────────────────────────────────────────────
    def _build_home(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(0)

        # Header
        title = QLabel("🔒 Audio Steganography")
        title.setObjectName("AppTitle")
        title.setAlignment(Qt.AlignCenter)
        lay.addWidget(title)

        subtitle = QLabel("Communication via Audio Steganography")
        subtitle.setObjectName("AppSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        lay.addWidget(subtitle)

        # Local IP badge
        ip_label = QLabel(f"Your IP:  {get_local_ip()}")
        ip_label.setObjectName("IpBadge")
        ip_label.setAlignment(Qt.AlignCenter)
        lay.addWidget(ip_label)

        lay.addSpacing(40)

        # Navigation cards
        cards = QHBoxLayout()
        cards.setSpacing(20)

        for label, icon, cb in [
            ("Send Message", "📤", self._goto_send),
            ("Receive Message", "📥", self._goto_receive),
            ("Settings", "⚙", self._goto_settings),
        ]:
            card = self._nav_card(icon, label, cb)
            cards.addWidget(card)

        lay.addLayout(cards)
        lay.addSpacing(40)

        # How-it-works blurb
        hint = QLabel(
            "Record your voice  →  embed a secret text  →  send the audio over Wi-Fi\n"
            "The recipient plays the audio (sounds normal)  →  extracts the hidden message"
        )
        hint.setObjectName("HintLabel")
        hint.setAlignment(Qt.AlignCenter)
        lay.addWidget(hint)

        return w

    def _nav_card(self, icon, label, callback):
        btn = QPushButton(f"{icon}\n{label}")
        btn.setObjectName("NavCard")
        btn.setMinimumSize(200, 140)
        btn.clicked.connect(callback)
        return btn

    # ── SEND ─────────────────────────────────────────────────────────────────
    def _build_send(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(12)

        # Top bar
        top = QHBoxLayout()
        back = self._back_btn(self._goto_home)
        top.addWidget(back)
        top.addStretch()
        heading = QLabel("📤 Send Message")
        heading.setObjectName("ScreenTitle")
        top.addWidget(heading)
        top.addStretch()
        lay.addLayout(top)

        # ── Step 1: Audio source ──────────────────────────────────────────
        src_frame = self._card("Step 1 — Audio Source")
        src_inner = src_frame.layout()

        row1 = QHBoxLayout()
        self.rec_status_label = QLabel("No audio recorded yet.")
        self.rec_status_label.setObjectName("InfoLabel")
        row1.addWidget(self.rec_status_label, stretch=1)

        self.rec_btn = QPushButton("🎙 Start Recording")
        self.rec_btn.setObjectName("ActionBtn")
        self.rec_btn.clicked.connect(self._toggle_recording)
        row1.addWidget(self.rec_btn)

        load_btn = QPushButton("📂 Load WAV")
        load_btn.setObjectName("SecondaryBtn")
        load_btn.clicked.connect(self._load_send_audio)
        row1.addWidget(load_btn)

        self.play_send_btn = QPushButton("▶")
        self.play_send_btn.setObjectName("PlayBtn")
        self.play_send_btn.setEnabled(False)
        self.play_send_btn.clicked.connect(lambda: self._toggle_play(self._send_temp_path(), self.play_send_btn))
        row1.addWidget(self.play_send_btn)

        src_inner.addLayout(row1)

        self.rec_progress = QProgressBar()
        self.rec_progress.setTextVisible(False)
        self.rec_progress.setMaximum(100)
        self.rec_progress.setValue(0)
        self.rec_progress.setObjectName("RecBar")
        self.rec_progress.setVisible(False)
        src_inner.addWidget(self.rec_progress)

        lay.addWidget(src_frame)

        # ── Step 2: Secret message ────────────────────────────────────────
        msg_frame = self._card("Step 2 — Secret Message")
        self.send_message_input = QTextEdit()
        self.send_message_input.setPlaceholderText("Type the secret message to hide inside the audio…")
        self.send_message_input.setMaximumHeight(100)
        msg_frame.layout().addWidget(self.send_message_input)
        lay.addWidget(msg_frame)

        # ── Step 3: Destination ────────────────────────────────────────────
        dest_frame = self._card("Step 3 — Destination")
        dest_inner = dest_frame.layout()

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Peer IP:"))
        self.send_ip_input = QLineEdit()
        self.send_ip_input.setPlaceholderText("e.g. 192.168.1.10")
        self.send_ip_input.setObjectName("InputField")
        row3.addWidget(self.send_ip_input, stretch=2)
        row3.addSpacing(20)
        row3.addWidget(QLabel("Port:"))
        self.send_port_input = QLineEdit("9999")
        self.send_port_input.setObjectName("InputField")
        self.send_port_input.setMaximumWidth(80)
        row3.addWidget(self.send_port_input)
        dest_inner.addLayout(row3)
        lay.addWidget(dest_frame)

        # ── Send button ─────────────────────────────────────────────────
        self.send_btn = QPushButton("🚀  Embed & Send")
        self.send_btn.setObjectName("BigActionBtn")
        self.send_btn.clicked.connect(self._do_embed_and_send)
        lay.addWidget(self.send_btn)

        # ── Send log ─────────────────────────────────────────────────────
        log_frame = self._card("Activity Log")
        self.send_log = QTextEdit()
        self.send_log.setReadOnly(True)
        self.send_log.setObjectName("LogBox")
        self.send_log.setMaximumHeight(120)
        log_frame.layout().addWidget(self.send_log)
        lay.addWidget(log_frame)

        return w

    # ── RECEIVE ──────────────────────────────────────────────────────────────
    def _build_receive(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(12)

        # Top bar
        top = QHBoxLayout()
        back = self._back_btn(self._goto_home)
        top.addWidget(back)
        top.addStretch()
        heading = QLabel("📥 Receive Message")
        heading.setObjectName("ScreenTitle")
        top.addWidget(heading)
        top.addStretch()
        lay.addLayout(top)

        # ── Listen panel ──────────────────────────────────────────────────
        listen_frame = self._card("Listener")
        listen_inner = listen_frame.layout()

        lrow = QHBoxLayout()
        self.local_ip_label = QLabel(f"This device's IP:  <b>{get_local_ip()}</b>  — share this with the sender")
        self.local_ip_label.setObjectName("IpBadge")
        lrow.addWidget(self.local_ip_label, stretch=1)
        self.listen_btn = QPushButton("▶  Start Listening")
        self.listen_btn.setObjectName("ListenBtn")
        self.listen_btn.setCheckable(True)
        self.listen_btn.clicked.connect(self._toggle_listener)
        lrow.addWidget(self.listen_btn)
        listen_inner.addLayout(lrow)

        self.listen_status = QLabel("Listener is stopped.")
        self.listen_status.setObjectName("InfoLabel")
        listen_inner.addWidget(self.listen_status)
        lay.addWidget(listen_frame)

        # ── Incoming audio ────────────────────────────────────────────────
        recv_frame = self._card("Received Audio")
        recv_inner = recv_frame.layout()

        self.recv_info_label = QLabel("Waiting for incoming audio…")
        self.recv_info_label.setObjectName("InfoLabel")
        recv_inner.addWidget(self.recv_info_label)

        recv_controls = QHBoxLayout()
        self.play_recv_btn = QPushButton("▶  Play")
        self.play_recv_btn.setObjectName("PlayBtnLg")
        self.play_recv_btn.setEnabled(False)
        self.play_recv_btn.clicked.connect(self._play_received)
        recv_controls.addWidget(self.play_recv_btn)

        self.save_recv_btn = QPushButton("💾  Save WAV")
        self.save_recv_btn.setObjectName("SecondaryBtn")
        self.save_recv_btn.setEnabled(False)
        self.save_recv_btn.clicked.connect(self._save_received)
        recv_controls.addWidget(self.save_recv_btn)

        recv_inner.addLayout(recv_controls)
        lay.addWidget(recv_frame)

        # ── Extracted message ─────────────────────────────────────────────
        ext_frame = self._card("Extracted Hidden Message")
        self.extracted_display = QTextEdit()
        self.extracted_display.setReadOnly(True)
        self.extracted_display.setPlaceholderText("The hidden message will appear here once audio is received…")
        self.extracted_display.setObjectName("ExtractBox")
        ext_frame.layout().addWidget(self.extracted_display)
        lay.addWidget(ext_frame)

        # ── Reply shortcut ────────────────────────────────────────────────
        self.reply_btn = QPushButton("↩  Reply (Switch to Send)")
        self.reply_btn.setObjectName("SecondaryBtn")
        self.reply_btn.setEnabled(False)
        self.reply_btn.clicked.connect(self._goto_send_for_reply)
        lay.addWidget(self.reply_btn)

        # ── Receive log ───────────────────────────────────────────────────
        rlog_frame = self._card("Activity Log")
        self.recv_log = QTextEdit()
        self.recv_log.setReadOnly(True)
        self.recv_log.setObjectName("LogBox")
        self.recv_log.setMaximumHeight(110)
        rlog_frame.layout().addWidget(self.recv_log)
        lay.addWidget(rlog_frame)

        return w

    # ── SETTINGS ─────────────────────────────────────────────────────────────
    def _build_settings(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setAlignment(Qt.AlignTop)
        lay.setSpacing(16)

        top = QHBoxLayout()
        top.addWidget(self._back_btn(self._goto_home))
        top.addStretch()
        heading = QLabel("⚙  Settings")
        heading.setObjectName("ScreenTitle")
        top.addWidget(heading)
        top.addStretch()
        lay.addLayout(top)

        frame = self._card("Network & Recording Defaults")
        inner = frame.layout()

        # Default peer IP
        r1 = QHBoxLayout()
        r1.addWidget(QLabel("Default Peer IP:"))
        self.def_ip_input = QLineEdit()
        self.def_ip_input.setPlaceholderText("192.168.x.x")
        self.def_ip_input.setObjectName("InputField")
        r1.addWidget(self.def_ip_input)
        inner.addLayout(r1)

        # Default port
        r2 = QHBoxLayout()
        r2.addWidget(QLabel("Default Port:"))
        self.def_port_spin = QSpinBox()
        self.def_port_spin.setRange(1024, 65535)
        self.def_port_spin.setValue(9999)
        r2.addWidget(self.def_port_spin)
        r2.addStretch()
        inner.addLayout(r2)

        lay.addWidget(frame)

        save_btn = QPushButton("✔  Save Settings")
        save_btn.setObjectName("ActionBtn")
        save_btn.clicked.connect(self._save_settings)
        lay.addWidget(save_btn)

        # Local info panel
        info_frame = self._card("Network Info")
        info_inner = info_frame.layout()
        info_inner.addWidget(QLabel(f"Local IP Address:  {get_local_ip()}"))
        info_inner.addWidget(QLabel("Share this IP with the other laptop so it can connect to you."))
        info_inner.addWidget(QLabel(
            "⚠  Make sure both laptops are on the same Wi-Fi network.\n"
            "⚠  If connection fails, temporarily disable Windows Firewall or allow the port."
        ))
        lay.addWidget(info_frame)

        return w

    # ═════════════════════════════════════════════════════════════════════════
    # Navigation
    # ═════════════════════════════════════════════════════════════════════════

    def _goto_home(self):
        self.player.stop()
        self.stack.setCurrentWidget(self.home_screen)

    def _goto_send(self):
        # Populate IP from settings if not already set
        if not self.send_ip_input.text() and self.peer_ip:
            self.send_ip_input.setText(self.peer_ip)
        self.stack.setCurrentWidget(self.send_screen)

    def _goto_receive(self):
        self.stack.setCurrentWidget(self.receive_screen)

    def _goto_settings(self):
        self.stack.setCurrentWidget(self.settings_screen)

    def _goto_send_for_reply(self):
        # Pre-fill sender's IP as the reply destination
        self.stack.setCurrentWidget(self.send_screen)
        self._log_send("Switched to Send — record and reply!")

    # ═════════════════════════════════════════════════════════════════════════
    # Settings
    # ═════════════════════════════════════════════════════════════════════════

    def _save_settings(self):
        self.peer_ip   = self.def_ip_input.text().strip()
        self.peer_port = self.def_port_spin.value()
        QMessageBox.information(self, "Settings Saved",
                                f"Default peer: {self.peer_ip}:{self.peer_port}")

    # ═════════════════════════════════════════════════════════════════════════
    # Recording
    # ═════════════════════════════════════════════════════════════════════════

    def _toggle_recording(self):
        if getattr(self, "is_recording", False):
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        self.is_recording = True
        self.rec_btn.setText("⏹ Stop Recording")
        self.rec_btn.setStyleSheet("background-color: #6e1f1f;")
        self.rec_progress.setVisible(True)
        self.rec_progress.setRange(0, 0)
        self.recorded_samples = None
        self.play_send_btn.setEnabled(False)
        self.rec_status_label.setText("Recording... (Click Stop when done)")

        self.recorder = AsyncRecorder(
            on_done=lambda s, sr: self.bridge.record_done.emit(s, sr),
            on_error=lambda e: self.bridge.error_signal.emit(f"Recording error: {e}"),
            sample_rate=44100
        )
        self.recorder.start()

    def _stop_recording(self):
        if hasattr(self, "recorder") and self.recorder:
            self.recorder.stop()
            self.recorder = None
        self.is_recording = False
        self.rec_btn.setText("🎙 Start Recording")
        self.rec_btn.setStyleSheet("")
        self.rec_progress.setRange(0, 100)
        self.rec_progress.setValue(100)

    def _on_record_done(self, samples, sr):
        self.rec_progress.setValue(100)
        self.recorded_samples = samples
        self.recorded_sr = sr
        self.loaded_audio_path = None

        duration = len(samples) / sr
        self.rec_status_label.setText(f"✔  Recorded {duration:.1f}s  ({sr} Hz, mono)")
        self.play_send_btn.setEnabled(True)
        self._log_send(f"Recording complete: {duration:.1f}s at {sr} Hz")

    # ═════════════════════════════════════════════════════════════════════════
    # Load audio file (send screen)
    # ═════════════════════════════════════════════════════════════════════════

    def _load_send_audio(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open WAV File", "", "WAV Files (*.wav)")
        if not path:
            return
        try:
            sr, data = wavfile.read(path)
            if len(data.shape) > 1:
                data = data.mean(axis=1).astype(np.int16)
            self.recorded_samples = data.astype(np.int16)
            self.recorded_sr = sr
            self.loaded_audio_path = path
            dur = len(data) / sr
            self.rec_status_label.setText(f"📂  {os.path.basename(path)}  |  {sr} Hz  |  {dur:.1f}s")
            self.play_send_btn.setEnabled(True)
            self._log_send(f"Loaded: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not read file:\n{e}")

    # ═════════════════════════════════════════════════════════════════════════
    # Embed & Send
    # ═════════════════════════════════════════════════════════════════════════

    def _do_embed_and_send(self):
        # Validate inputs
        if self.recorded_samples is None:
            QMessageBox.warning(self, "No Audio", "Please record or load an audio file first.")
            return

        message = self.send_message_input.toPlainText().strip()
        if not message:
            QMessageBox.warning(self, "No Message", "Please enter a secret message.")
            return

        ip   = self.send_ip_input.text().strip()
        port_str = self.send_port_input.text().strip()
        if not ip:
            QMessageBox.warning(self, "No IP", "Please enter the peer's IP address.")
            return
        try:
            port = int(port_str)
        except ValueError:
            port = 9999

        self.send_btn.setEnabled(False)
        self.send_btn.setText("Processing…")
        self._log_send(f"Embedding message into {len(self.recorded_samples)} samples…")

        # Run in background thread so GUI stays responsive
        threading.Thread(
            target=self._embed_and_send_worker,
            args=(self.recorded_samples.copy(), self.recorded_sr, message, ip, port),
            daemon=True
        ).start()

    def _embed_and_send_worker(self, samples, sr, message, ip, port):
        try:
            stego_arr, sr_out = self.stego.embed_array(samples, sr, message)
            self.bridge.log_signal.emit("Embedding complete. Serialising WAV…", "info")

            wav_bytes = FFTSteganography.array_to_wav_bytes(stego_arr, sr_out)
            self.bridge.log_signal.emit(
                f"WAV size: {len(wav_bytes)/1024:.1f} KB. Connecting to {ip}:{port}…", "info"
            )

            send_audio(ip, port, wav_bytes)
            self.bridge.log_signal.emit(f"✔  Sent successfully to {ip}:{port}", "success")

        except Exception as e:
            self.bridge.log_signal.emit(f"✘  {e}", "error")
        finally:
            # Re-enable button on GUI thread
            QTimer.singleShot(0, self._reset_send_btn)

    def _reset_send_btn(self):
        self.send_btn.setEnabled(True)
        self.send_btn.setText("🚀  Embed & Send")

    # ═════════════════════════════════════════════════════════════════════════
    # Listener
    # ═════════════════════════════════════════════════════════════════════════

    def _toggle_listener(self, checked):
        if checked:
            port_edit = getattr(self, "def_port_spin", None)
            port = self.peer_port if not port_edit else self.def_port_spin.value()
            self._start_listener(port)
        else:
            self._stop_listener()

    def _start_listener(self, port):
        if self.receiver and self.receiver.is_alive():
            return

        def on_recv(wav_bytes, sender_ip):
            self.bridge.recv_signal.emit(wav_bytes, sender_ip)

        def on_err(msg):
            self.bridge.log_signal.emit(f"Server error: {msg}", "error")

        self.receiver = ReceiverServer(port, on_received=on_recv, on_error=on_err)
        self.receiver.start()

        self.listen_btn.setText("⏹  Stop Listening")
        self.listen_status.setText(f"🟢  Listening on port {port}  —  tell sender to connect to  {get_local_ip()}")
        self._log_recv(f"Listener started on port {port}.")

    def _stop_listener(self):
        if self.receiver:
            self.receiver.stop()
            self.receiver = None
        self.listen_btn.setText("▶  Start Listening")
        self.listen_btn.setChecked(False)
        self.listen_status.setText("🔴  Listener stopped.")
        self._log_recv("Listener stopped.")

    # ═════════════════════════════════════════════════════════════════════════
    # Handle received audio
    # ═════════════════════════════════════════════════════════════════════════

    def _on_audio_received(self, wav_bytes: bytes, sender_ip: str):
        self._log_recv(f"📨  {len(wav_bytes)//1024} KB received from {sender_ip}. Extracting…")
        self.received_wav_bytes = wav_bytes

        # Save to temp file for playback
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.write(wav_bytes)
        tmp.close()
        self.received_temp_path = tmp.name

        # Update UI
        try:
            arr, sr = FFTSteganography.wav_bytes_to_array(wav_bytes)
            dur = len(arr) / sr
            self.recv_info_label.setText(
                f"📦  From {sender_ip}  |  {sr} Hz  |  {dur:.1f}s  |  {len(wav_bytes)//1024} KB"
            )
            self.play_recv_btn.setEnabled(True)
            self.save_recv_btn.setEnabled(True)

            # Extract in background
            threading.Thread(
                target=self._extract_worker, args=(arr,), daemon=True
            ).start()

        except Exception as e:
            self._log_recv(f"Error reading received audio: {e}")

    def _extract_worker(self, arr):
        try:
            msg = self.stego.extract_array(arr)
            self.bridge.extract_done.emit(msg)
        except Exception as e:
            self.bridge.log_signal.emit(f"Extraction error: {e}", "error")

    def _show_extracted(self, msg: str):
        self.extracted_display.setPlainText(msg)
        self._log_recv(f"✔  Message extracted:  «{msg[:60]}{'…' if len(msg)>60 else ''}»")
        self.reply_btn.setEnabled(True)

    # ═════════════════════════════════════════════════════════════════════════
    # Playback helpers
    # ═════════════════════════════════════════════════════════════════════════

    def _send_temp_path(self):
        """Return a temp WAV path for the send-screen preview."""
        if self.loaded_audio_path:
            return self.loaded_audio_path
        if self.recorded_samples is not None:
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            wavfile.write(tmp.name, self.recorded_sr, self.recorded_samples)
            tmp.close()
            return tmp.name
        return None

    def _toggle_play(self, path, btn):
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "No Audio", "No audio available to play.")
            return
        if self.active_play_btn == btn and self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
            return
        self.active_play_btn = btn
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(os.path.abspath(path))))
        self.player.play()

    def _play_received(self):
        if not self.received_temp_path:
            return
        self._toggle_play(self.received_temp_path, self.play_recv_btn)

    def _save_received(self):
        if not self.received_wav_bytes:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Received Audio", "received_stego.wav", "WAV Files (*.wav)"
        )
        if path:
            with open(path, "wb") as f:
                f.write(self.received_wav_bytes)
            QMessageBox.information(self, "Saved", f"Audio saved to:\n{path}")

    def _on_player_state(self, state):
        if self.active_play_btn:
            self.active_play_btn.setText(
                "⏸" if state == QMediaPlayer.PlayingState else "▶"
            )

    # ═════════════════════════════════════════════════════════════════════════
    # Logging
    # ═════════════════════════════════════════════════════════════════════════

    def _log_send(self, msg: str, level: str = "info"):
        self._append_log(msg, level, target="send")

    def _log_recv(self, msg: str, level: str = "info"):
        self._append_log(msg, level, target="recv")

    def _append_log(self, msg: str, level: str = "info", target: str = "send"):
        ts = time.strftime("%H:%M:%S")
        colors = {"info": "#aaa", "success": "#4ecca3", "error": "#ff6b6b"}
        color = colors.get(level, "#aaa")
        html = f'<span style="color:{color}">[{ts}] {msg}</span>'

        # Emit to both logs if from bridge signal
        if target == "send":
            self.send_log.append(html)
        else:
            self.recv_log.append(html)

    # ═════════════════════════════════════════════════════════════════════════
    # Helpers
    # ═════════════════════════════════════════════════════════════════════════

    def _card(self, title: str) -> QFrame:
        """Create a styled card widget with a vertical layout and title."""
        frame = QFrame()
        frame.setObjectName("Card")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(16, 12, 16, 12)
        if title:
            label = QLabel(title)
            label.setObjectName("CardTitle")
            lay.addWidget(label)
        return frame

    def _back_btn(self, callback) -> QPushButton:
        btn = QPushButton("← Back")
        btn.setObjectName("BackBtn")
        btn.setMaximumWidth(90)
        btn.clicked.connect(callback)
        return btn

    def closeEvent(self, event):
        self._stop_listener()
        self.player.stop()
        event.accept()

    def resizeEvent(self, event):
        # Update stylesheet on resize to scale fonts
        size = event.size()
        self.setStyleSheet(get_style(size.width(), size.height()))
        super().resizeEvent(event)
