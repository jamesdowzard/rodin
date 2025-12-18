"""Sound effects for Rodin."""

import sys
from pathlib import Path


def play_start_sound() -> None:
    """Play sound when recording starts."""
    if sys.platform == "darwin":
        _play_macos_sound("Tink")
    elif sys.platform == "win32":
        _play_windows_sound("start")


def play_stop_sound() -> None:
    """Play sound when recording stops."""
    if sys.platform == "darwin":
        _play_macos_sound("Pop")
    elif sys.platform == "win32":
        _play_windows_sound("stop")


def play_success_sound() -> None:
    """Play sound on successful transcription."""
    if sys.platform == "darwin":
        _play_macos_sound("Glass")
    elif sys.platform == "win32":
        _play_windows_sound("success")


def play_error_sound() -> None:
    """Play sound on error."""
    if sys.platform == "darwin":
        _play_macos_sound("Basso")
    elif sys.platform == "win32":
        _play_windows_sound("error")


def _play_macos_sound(name: str) -> None:
    """Play a macOS system sound."""
    try:
        from AppKit import NSSound

        # Try system sounds first
        sound = NSSound.soundNamed_(name)
        if sound:
            sound.play()
            return

        # Try /System/Library/Sounds/
        sound_path = Path(f"/System/Library/Sounds/{name}.aiff")
        if sound_path.exists():
            sound = NSSound.alloc().initWithContentsOfFile_byReference_(
                str(sound_path), True
            )
            if sound:
                sound.play()

    except Exception as e:
        # Silently fail - sounds are optional
        pass


def _play_windows_sound(sound_type: str) -> None:
    """Play a Windows system sound."""
    try:
        import winsound

        sounds = {
            "start": winsound.MB_OK,
            "stop": winsound.MB_OK,
            "success": winsound.MB_OK,
            "error": winsound.MB_ICONHAND,
        }
        winsound.MessageBeep(sounds.get(sound_type, winsound.MB_OK))

    except Exception:
        # Silently fail - sounds are optional
        pass
