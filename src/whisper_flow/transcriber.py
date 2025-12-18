"""Speech-to-text transcription using Whisper."""

import io
import tempfile
from pathlib import Path

from faster_whisper import WhisperModel

from .config import WhisperConfig, get_config_dir


class Transcriber:
    """Transcribes audio using faster-whisper."""

    def __init__(self, config: WhisperConfig | None = None):
        self.config = config or WhisperConfig()
        self._model: WhisperModel | None = None

    def _get_model_dir(self) -> Path:
        """Get directory for storing Whisper models."""
        model_dir = get_config_dir() / "models"
        model_dir.mkdir(parents=True, exist_ok=True)
        return model_dir

    def _get_local_model_path(self) -> Path | None:
        """Get path to locally cached model if it exists."""
        model_dir = self._get_model_dir()
        # Map model size to HuggingFace repo name
        model_repos = {
            "tiny": "Systran/faster-whisper-tiny",
            "base": "Systran/faster-whisper-base",
            "small": "Systran/faster-whisper-small",
            "medium": "Systran/faster-whisper-medium",
            "large-v3": "Systran/faster-whisper-large-v3",
        }
        repo = model_repos.get(self.config.model_size, f"Systran/faster-whisper-{self.config.model_size}")
        repo_dir_name = f"models--{repo.replace('/', '--')}"
        repo_dir = model_dir / repo_dir_name / "snapshots"

        if repo_dir.exists():
            # Find the snapshot directory (there should be one)
            snapshots = list(repo_dir.iterdir())
            if snapshots:
                snapshot_dir = snapshots[0]
                # Check if model.bin exists
                if (snapshot_dir / "model.bin").exists():
                    return snapshot_dir
        return None

    def _get_device_and_compute(self) -> tuple[str, str]:
        """Determine device and compute type."""
        device = self.config.device
        compute_type = self.config.compute_type

        if device == "auto":
            # Try CUDA first, fall back to CPU
            try:
                import torch

                device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                device = "cpu"

        if compute_type == "auto":
            compute_type = "int8" if device == "cpu" else "float16"

        return device, compute_type

    def load_model(self) -> None:
        """Load the Whisper model."""
        if self._model is not None:
            return

        device, compute_type = self._get_device_and_compute()

        # Try to use local model first (no network access)
        local_path = self._get_local_model_path()

        if local_path:
            print(f"Loading Whisper model '{self.config.model_size}' from local cache on {device}...")
            self._model = WhisperModel(
                str(local_path),
                device=device,
                compute_type=compute_type,
                local_files_only=True,
            )
        else:
            # Fall back to downloading (will fail if network blocked)
            model_dir = self._get_model_dir()
            print(f"Loading Whisper model '{self.config.model_size}' on {device}...")
            self._model = WhisperModel(
                self.config.model_size,
                device=device,
                compute_type=compute_type,
                download_root=str(model_dir),
            )

        print("Model loaded successfully")

    def transcribe(self, audio_data: bytes) -> str:
        """Transcribe audio data to text.

        Args:
            audio_data: WAV audio data as bytes

        Returns:
            Transcribed text
        """
        if self._model is None:
            self.load_model()

        # Write audio to temporary file (faster-whisper needs a file path)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_file.write(audio_data)
            tmp_path = tmp_file.name

        try:
            segments, info = self._model.transcribe(
                tmp_path,
                language=self.config.language,
                beam_size=5,
                vad_filter=True,  # Filter out silence
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    speech_pad_ms=400,
                ),
            )

            # Combine all segments
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text.strip())

            return " ".join(text_parts)

        finally:
            # Clean up temp file
            Path(tmp_path).unlink(missing_ok=True)

    def unload_model(self) -> None:
        """Unload the model to free memory."""
        self._model = None

    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._model is not None
