"""Resilient audio queue - never lose a recording."""

import json
import shutil
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from .config import get_config_dir


@dataclass
class PendingRecording:
    """A recording waiting to be transcribed."""

    id: str
    audio_path: Path
    metadata_path: Path
    timestamp: datetime
    app_bundle_id: str | None
    app_name: str | None
    preset: str | None

    @classmethod
    def from_metadata_file(cls, metadata_path: Path) -> "PendingRecording":
        """Load a pending recording from its metadata file."""
        with open(metadata_path) as f:
            data = json.load(f)

        audio_path = metadata_path.with_suffix(".wav")
        return cls(
            id=metadata_path.stem,
            audio_path=audio_path,
            metadata_path=metadata_path,
            timestamp=datetime.fromisoformat(data["timestamp"]),
            app_bundle_id=data.get("app_bundle_id"),
            app_name=data.get("app_name"),
            preset=data.get("preset"),
        )


class AudioQueue:
    """Manages pending audio recordings for resilient transcription.

    Audio is saved immediately after recording. If transcription fails
    (network down, model not loaded, error), the audio is kept and
    retried later. Only deleted after successful transcription.
    """

    def __init__(self, queue_dir: Path | None = None):
        if queue_dir is None:
            queue_dir = get_config_dir() / "pending"
        self.queue_dir = queue_dir
        self.queue_dir.mkdir(parents=True, exist_ok=True)

        # Processing state
        self._processing_lock = threading.Lock()
        self._is_processing = False
        self._stop_event = threading.Event()

    def save_recording(
        self,
        audio_data: bytes,
        app_bundle_id: str | None = None,
        app_name: str | None = None,
        preset: str | None = None,
    ) -> PendingRecording:
        """Save a recording to the pending queue.

        Returns the PendingRecording object.
        """
        # Generate unique ID from timestamp
        now = datetime.now()
        recording_id = now.strftime("%Y%m%d_%H%M%S_%f")

        audio_path = self.queue_dir / f"{recording_id}.wav"
        metadata_path = self.queue_dir / f"{recording_id}.json"

        # Write audio file first (most important)
        audio_path.write_bytes(audio_data)

        # Write metadata
        metadata = {
            "timestamp": now.isoformat(),
            "app_bundle_id": app_bundle_id,
            "app_name": app_name,
            "preset": preset,
        }
        with open(metadata_path, "w") as f:
            json.dump(metadata, f)

        return PendingRecording(
            id=recording_id,
            audio_path=audio_path,
            metadata_path=metadata_path,
            timestamp=now,
            app_bundle_id=app_bundle_id,
            app_name=app_name,
            preset=preset,
        )

    def mark_completed(self, recording: PendingRecording) -> None:
        """Mark a recording as successfully processed - delete it."""
        try:
            recording.audio_path.unlink(missing_ok=True)
            recording.metadata_path.unlink(missing_ok=True)
        except Exception as e:
            print(f"Warning: Failed to delete completed recording: {e}")

    def get_pending(self) -> list[PendingRecording]:
        """Get all pending recordings, oldest first."""
        recordings = []

        for metadata_path in sorted(self.queue_dir.glob("*.json")):
            try:
                recording = PendingRecording.from_metadata_file(metadata_path)
                # Only include if audio file exists
                if recording.audio_path.exists():
                    recordings.append(recording)
                else:
                    # Orphaned metadata, clean up
                    metadata_path.unlink(missing_ok=True)
            except Exception as e:
                print(f"Warning: Failed to load pending recording {metadata_path}: {e}")

        return recordings

    def get_pending_count(self) -> int:
        """Get count of pending recordings."""
        return len(list(self.queue_dir.glob("*.json")))

    def process_pending(
        self,
        process_fn: Callable[[PendingRecording, bytes], bool],
        on_progress: Callable[[int, int], None] | None = None,
    ) -> int:
        """Process all pending recordings.

        Args:
            process_fn: Function that takes (recording, audio_bytes) and returns
                       True if successful (recording will be deleted).
            on_progress: Optional callback (processed, total) for progress updates.

        Returns:
            Number of successfully processed recordings.
        """
        with self._processing_lock:
            if self._is_processing:
                return 0
            self._is_processing = True

        try:
            pending = self.get_pending()
            total = len(pending)
            processed = 0

            for i, recording in enumerate(pending):
                if self._stop_event.is_set():
                    break

                try:
                    audio_data = recording.audio_path.read_bytes()
                    success = process_fn(recording, audio_data)

                    if success:
                        self.mark_completed(recording)
                        processed += 1

                except Exception as e:
                    print(f"Error processing recording {recording.id}: {e}")

                if on_progress:
                    on_progress(i + 1, total)

            return processed

        finally:
            with self._processing_lock:
                self._is_processing = False

    def start_background_processor(
        self,
        process_fn: Callable[[PendingRecording, bytes], bool],
        interval_seconds: float = 30.0,
    ) -> threading.Thread:
        """Start a background thread that periodically processes pending recordings.

        Args:
            process_fn: Function that takes (recording, audio_bytes) and returns True if successful.
            interval_seconds: How often to check for pending recordings.

        Returns:
            The background thread (already started).
        """
        self._stop_event.clear()

        def processor_loop():
            while not self._stop_event.wait(interval_seconds):
                count = self.get_pending_count()
                if count > 0:
                    print(f"Processing {count} pending recording(s)...")
                    processed = self.process_pending(process_fn)
                    if processed > 0:
                        print(f"Processed {processed} recording(s)")

        thread = threading.Thread(target=processor_loop, daemon=True)
        thread.start()
        return thread

    def stop_background_processor(self) -> None:
        """Stop the background processor."""
        self._stop_event.set()

    def get_queue_size_bytes(self) -> int:
        """Get total size of pending audio files in bytes."""
        return sum(f.stat().st_size for f in self.queue_dir.glob("*.wav") if f.exists())

    def cleanup_old(self, max_age_days: int = 7) -> int:
        """Remove recordings older than max_age_days.

        Returns number of recordings removed.
        """
        cutoff = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)
        removed = 0

        for metadata_path in self.queue_dir.glob("*.json"):
            try:
                if metadata_path.stat().st_mtime < cutoff:
                    audio_path = metadata_path.with_suffix(".wav")
                    metadata_path.unlink(missing_ok=True)
                    audio_path.unlink(missing_ok=True)
                    removed += 1
            except Exception:
                pass

        return removed


# Singleton instance
_queue: AudioQueue | None = None


def get_queue() -> AudioQueue:
    """Get the audio queue singleton."""
    global _queue
    if _queue is None:
        _queue = AudioQueue()
    return _queue
