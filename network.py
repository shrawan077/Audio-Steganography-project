"""
network.py — TCP Audio Transfer Engine
---------------------------------------
Handles sending and receiving WAV audio files over a TCP socket on the LAN.

Protocol:
  - Sender connects, sends a 4-byte big-endian integer = length of WAV bytes
  - Sender then streams the WAV bytes
  - Receiver reads the length, reads exactly that many bytes, fires callback

Usage:
    # Sender side
    send_audio("192.168.1.10", 9999, wav_bytes)

    # Receiver side
    server = ReceiverServer(port=9999, on_received=my_callback)
    server.start()
    ...
    server.stop()
"""

import socket
import struct
import threading
import logging

logger = logging.getLogger(__name__)

DEFAULT_PORT = 9999
CHUNK_SIZE   = 65536  # 64 KB read chunks


# ── Sender ────────────────────────────────────────────────────────────────────

def send_audio(ip: str, port: int, wav_bytes: bytes, timeout: float = 10.0) -> None:
    """
    Connect to the peer at (ip, port) and transmit raw WAV bytes.

    Raises:
        ConnectionRefusedError  – peer not listening
        socket.timeout          – could not connect within `timeout` seconds
        OSError                 – other network error
    """
    with socket.create_connection((ip, port), timeout=timeout) as sock:
        # Send 4-byte length header
        header = struct.pack(">I", len(wav_bytes))
        sock.sendall(header)
        # Send WAV data
        sock.sendall(wav_bytes)
        logger.info(f"Sent {len(wav_bytes)} bytes to {ip}:{port}")


# ── Receiver ──────────────────────────────────────────────────────────────────

class ReceiverServer(threading.Thread):
    """
    Background TCP server that listens for incoming audio files.

    Parameters
    ----------
    port : int
        TCP port to bind.
    on_received : callable(bytes)
        Called on the server thread each time a complete WAV is received.
    on_error : callable(str), optional
        Called when an error occurs.
    """

    def __init__(self, port: int, on_received, on_error=None):
        super().__init__(daemon=True)
        self.port        = port
        self.on_received = on_received
        self.on_error    = on_error
        self._stop_event = threading.Event()
        self._server_sock: socket.socket | None = None

    # ------------------------------------------------------------------
    def run(self):
        try:
            self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_sock.bind(("", self.port))
            self._server_sock.listen(5)
            self._server_sock.settimeout(1.0)   # so we can check _stop_event
            logger.info(f"ReceiverServer listening on port {self.port}")
        except OSError as e:
            logger.error(f"Failed to bind port {self.port}: {e}")
            if self.on_error:
                self.on_error(f"Could not start server: {e}")
            return

        while not self._stop_event.is_set():
            try:
                conn, addr = self._server_sock.accept()
            except socket.timeout:
                continue          # check stop_event and retry
            except OSError:
                break             # socket was closed externally

            logger.info(f"Connection from {addr}")
            try:
                wav_bytes = self._recv_all(conn)
                if wav_bytes:
                    self.on_received(wav_bytes, addr[0])
            except Exception as e:
                logger.error(f"Receive error from {addr}: {e}")
                if self.on_error:
                    self.on_error(f"Receive error: {e}")
            finally:
                conn.close()

        if self._server_sock:
            try:
                self._server_sock.close()
            except Exception:
                pass
        logger.info("ReceiverServer stopped.")

    # ------------------------------------------------------------------
    def stop(self):
        """Signal the server thread to stop."""
        self._stop_event.set()
        if self._server_sock:
            try:
                self._server_sock.close()
            except Exception:
                pass

    # ------------------------------------------------------------------
    @staticmethod
    def _recv_all(conn: socket.socket) -> bytes:
        """Read the length-prefixed WAV bytes from an open connection."""
        # Read 4-byte header
        header = b""
        while len(header) < 4:
            chunk = conn.recv(4 - len(header))
            if not chunk:
                raise ConnectionError("Connection closed before header was received.")
            header += chunk

        total_length = struct.unpack(">I", header)[0]
        if total_length == 0:
            return b""

        # Read exactly total_length bytes
        data = bytearray()
        while len(data) < total_length:
            remaining = total_length - len(data)
            chunk = conn.recv(min(CHUNK_SIZE, remaining))
            if not chunk:
                raise ConnectionError(
                    f"Connection closed after {len(data)}/{total_length} bytes."
                )
            data.extend(chunk)

        return bytes(data)


# ── Utility ───────────────────────────────────────────────────────────────────

def get_local_ip() -> str:
    """Return the machine's LAN IP address (best guess)."""
    try:
        # Connect to an external host (doesn't actually send data)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
