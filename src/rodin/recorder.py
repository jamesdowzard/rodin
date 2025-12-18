"""Audio recording functionality."""

import io
import queue
import threading
import wave
from typing import Callable

import numpy as np
import sounddevice as sd

from .config import AudioConfig


class AudioRecorder:
    """Records audio from the default microphone."""

    def __init__(self, config: AudioConfig | None = None):
        self.config = config or AudioConfig()
        self._audio_queue: queue.Queue[np.ndarray] = queue.Queue()
        self._is_recording = False
        self._stream: sd.InputStream | None = None
        self._recording_thread: threading.Thread | None = None
        self._on_audio_level: Callable[[float], None] | None = None

    def _audio_callback(
        self, indata: np.ndarray, frames: int, time_info: dict, status: sd.CallbackFlags
    ) -> None:
        """Callback for audio stream."""
        if status:
            print(f"Audio callback status: {status}")

        if self._is_recording:
            self._audio_queue.put(indata.copy())

            # Calculate audio level for UI feedback
            if self._on_audio_level:
                level = np.abs(indata).mean()
                self._on_audio_level(float(level))

    def start(self, on_audio_level: Callable[[float], None] | None = None) -> None:
        """Start recording audio."""
        if self._is_recording:
            return

        self._on_audio_level = on_audio_level
        self._is_recording = True
        self._audio_queue = queue.Queue()

        # Resolve device - can be index, name, or None (default)
        device = self.config.device
        if isinstance(device, str):
            # Find device by name
            for i, dev in enumerate(sd.query_devices()):
                if device.lower() in dev["name"].lower() and dev["max_input_channels"] > 0:
                    device = i
                    break
            else:
                print(f"Warning: Device '{self.config.device}' not found, using default")
                device = None

        self._stream = sd.InputStream(
            device=device,
            samplerate=self.config.sample_rate,
            channels=self.config.channels,
            dtype=self.config.dtype,
            callback=self._audio_callback,
        )
        self._stream.start()

    def stop(self) -> bytes:
        """Stop recording and return audio data as WAV bytes."""
        if not self._is_recording:
            return b""

        self._is_recording = False

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        # Collect all audio data
        audio_chunks = []
        while not self._audio_queue.empty():
            audio_chunks.append(self._audio_queue.get())

        if not audio_chunks:
            return b""

        # Concatenate all chunks
        audio_data = np.concatenate(audio_chunks)

        # Convert to WAV bytes
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(self.config.channels)
            wav_file.setsampwidth(2)  # 16-bit = 2 bytes
            wav_file.setframerate(self.config.sample_rate)
            wav_file.writeframes(audio_data.tobytes())

        return wav_buffer.getvalue()

    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._is_recording

    @staticmethod
    def list_devices() -> list[dict]:
        """List available audio input devices."""
        devices = sd.query_devices()
        input_devices = []

        for i, device in enumerate(devices):
            if device["max_input_channels"] > 0:
                input_devices.append(
                    {
                        "index": i,
                        "name": device["name"],
                        "channels": device["max_input_channels"],
                        "sample_rate": device["default_samplerate"],
                    }
                )

        return input_devices
