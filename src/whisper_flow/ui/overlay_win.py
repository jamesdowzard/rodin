"""Floating overlay window for Windows using tkinter."""

import sys
import threading
import tkinter as tk
from tkinter import font as tkfont

if sys.platform == "darwin":
    raise ImportError("Use overlay.py on macOS")

from ..config import Settings, load_settings, get_config_dir
from ..dictionary import PersonalDictionary
from ..editor import create_editor
from ..hotkey import HotkeyHandler
from ..recorder import AudioRecorder
from ..snippets import SnippetExpander
from ..transcriber import Transcriber
from ..typer import TextTyper
from ..voice_commands import VoiceCommandProcessor


def _log_transcription(raw_text: str, edited_text: str | None, duration: float) -> None:
    """Log transcription to file."""
    from datetime import datetime
    log_dir = get_config_dir()
    log_file = log_dir / "transcriptions.log"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"\n=== {timestamp} ({duration:.1f}s) ===\n")
        f.write(f"Raw: {raw_text}\n")
        if edited_text and edited_text != raw_text:
            f.write(f"Edited: {edited_text}\n")


class OverlayWindow:
    """Floating overlay window with mic button for Windows."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or load_settings()

        # Core components
        self.recorder = AudioRecorder(self.settings.audio)
        self.transcriber = Transcriber(self.settings.whisper)
        self.editor = create_editor(
            self.settings.ai_editor,
            {
                "openai": self.settings.openai_api_key,
                "anthropic": self.settings.anthropic_api_key,
            },
        )
        self.typer = TextTyper()

        # New feature components
        self.dictionary = PersonalDictionary()
        self.snippets = SnippetExpander()
        self.voice_commands = VoiceCommandProcessor()

        # State
        self._is_recording = False
        self._is_processing = False

        # Create window
        self._create_window()

        # Hotkey handler
        self.hotkey_handler = HotkeyHandler(
            self.settings.hotkey,
            on_activate=self._on_activate,
            on_deactivate=self._on_deactivate,
        )

    def _create_window(self):
        """Create the floating overlay window."""
        self.root = tk.Tk()
        self.root.title("Whisper Flow")

        # Window size
        button_size = 60

        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Position on right side, middle of screen
        x = screen_width - button_size - 30
        y = (screen_height // 2) - (button_size // 2)

        # Configure window
        self.root.geometry(f"{button_size}x{button_size}+{x}+{y}")
        self.root.overrideredirect(True)  # Remove window decorations
        self.root.attributes("-topmost", True)  # Always on top
        self.root.attributes("-alpha", 0.9)  # Slight transparency

        # Make window draggable
        self.root.bind("<Button-1>", self._start_drag)
        self.root.bind("<B1-Motion>", self._drag)

        # Create circular canvas for button
        self.canvas = tk.Canvas(
            self.root,
            width=button_size,
            height=button_size,
            highlightthickness=0,
            bg="gray20"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Draw button
        padding = 4
        self.button_circle = self.canvas.create_oval(
            padding, padding,
            button_size - padding, button_size - padding,
            fill="#333340",
            outline="#666670",
            width=2
        )

        # Icon text
        self.icon_text = self.canvas.create_text(
            button_size // 2,
            button_size // 2,
            text="🎤",
            font=("Segoe UI Emoji", 20),
            fill="white"
        )

        # Bind click
        self.canvas.bind("<Button-1>", self._on_click)

        # Store for dragging
        self._drag_start_x = 0
        self._drag_start_y = 0

    def _start_drag(self, event):
        """Start dragging the window."""
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _drag(self, event):
        """Drag the window."""
        x = self.root.winfo_x() + (event.x - self._drag_start_x)
        y = self.root.winfo_y() + (event.y - self._drag_start_y)
        self.root.geometry(f"+{x}+{y}")

    def _on_click(self, event=None):
        """Handle button click - toggle recording."""
        if self._is_processing:
            return

        if self._is_recording:
            self._on_deactivate()
        else:
            self._on_activate()

    def _on_activate(self):
        """Start recording."""
        if self._is_processing or self._is_recording:
            return

        self._is_recording = True
        # Schedule UI update on main thread
        self.root.after(0, self._update_button_state)
        self.recorder.start()
        print("Recording started...")

    def _on_deactivate(self):
        """Stop recording and process."""
        if not self._is_recording:
            return

        self._is_recording = False
        self._is_processing = True
        # Schedule UI update on main thread
        self.root.after(0, self._update_button_state)
        print("Recording stopped, processing...")

        # Process in background
        threading.Thread(target=self._process_recording, daemon=True).start()

    def _update_button_state(self):
        """Update button appearance based on state."""
        if self._is_recording:
            self.canvas.itemconfig(self.button_circle, fill="#cc3333")
            self.canvas.itemconfig(self.icon_text, text="🔴")
        elif self._is_processing:
            self.canvas.itemconfig(self.button_circle, fill="#cc8833")
            self.canvas.itemconfig(self.icon_text, text="⏳")
        else:
            self.canvas.itemconfig(self.button_circle, fill="#333340")
            self.canvas.itemconfig(self.icon_text, text="🎤")

    def _process_recording(self):
        """Process the recorded audio."""
        import time as _time
        start_time = _time.time()

        try:
            audio_data = self.recorder.stop()

            if not audio_data:
                print("No audio recorded")
                return

            # 1. Transcribe
            text = self.transcriber.transcribe(audio_data)

            if not text:
                print("No speech detected")
                return

            raw_text = text
            print(f"Transcribed: {text}")

            # 2. Apply personal dictionary corrections
            if self.settings.dictionary.enabled:
                text = self.dictionary.apply(text)
                if text != raw_text:
                    print(f"Dictionary: {text}")

            # 3. Check for voice commands
            if self.settings.voice_commands.enabled:
                command, remaining_text = self.voice_commands.detect_command(text)
                if command:
                    print(f"Voice command: {command[0]}")
                    self.voice_commands.execute_command(command, self.typer)
                    if not remaining_text:
                        duration = _time.time() - start_time
                        _log_transcription(raw_text, f"[Command: {command[0]}]", duration)
                        return
                    text = remaining_text

            # 4. AI editing
            preset = self.settings.ai_editor.preset
            if self.settings.ai_editor.enabled:
                text = self.editor.edit(text, preset=preset)
                print(f"Edited: {text}")

            # 5. Snippet expansion
            if self.settings.snippets.enabled:
                expanded = self.snippets.expand(text)
                if expanded != text:
                    text = expanded
                    print(f"Snippet: {text[:50]}...")

            # 6. Type the text
            self.typer.type_text(text)

            # Track for "delete that" command
            self.voice_commands.set_last_typed_length(len(text))

            # Log transcription
            duration = _time.time() - start_time
            _log_transcription(raw_text, text if text != raw_text else None, duration)

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._is_processing = False
            # Update UI on main thread
            self.root.after(0, self._update_button_state)

    def run(self):
        """Run the overlay."""
        # Load model in background
        print("Loading Whisper model...")
        threading.Thread(target=self.transcriber.load_model, daemon=True).start()

        # Start hotkey listener
        self.hotkey_handler.start()

        print("Whisper Flow ready!")
        print("Hotkey: Ctrl+Shift+Space (hold to talk)")
        print("Or click the mic button on the right side of your screen")

        # Run the tkinter event loop
        self.root.mainloop()

    def stop(self):
        """Stop the overlay."""
        self.hotkey_handler.stop()
        self.root.quit()


def run_overlay(settings: Settings | None = None):
    """Run the overlay window."""
    overlay = OverlayWindow(settings)
    overlay.run()
