"""macOS menu bar application using rumps."""

import sys
import threading

if sys.platform != "darwin":
    raise ImportError("Menu bar UI only available on macOS")

import rumps

from ..config import Settings, load_settings, save_settings
from ..editor import create_editor
from ..hotkey import HotkeyHandler
from ..recorder import AudioRecorder
from ..transcriber import Transcriber
from ..typer import TextTyper


class WhisperFlowApp(rumps.App):
    """Menu bar application for Rodin."""

    def __init__(self, settings: Settings | None = None):
        super().__init__("Rodin", icon=None, quit_button=None)

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

        # State
        self._is_recording = False
        self._is_processing = False

        # Hotkey handler
        self.hotkey_handler = HotkeyHandler(
            self.settings.hotkey,
            on_activate=self._on_hotkey_activate,
            on_deactivate=self._on_hotkey_deactivate,
        )

        # Build menu
        self._build_menu()

        # Status display
        self._update_title("idle")

    def _build_menu(self) -> None:
        """Build the menu bar menu."""
        self.menu.clear()

        # Status indicator
        self.status_item = rumps.MenuItem("Status: Idle")
        self.status_item.set_callback(None)
        self.menu.add(self.status_item)

        self.menu.add(rumps.separator)

        # Recording mode
        mode_menu = rumps.MenuItem("Recording Mode")
        hold_item = rumps.MenuItem(
            "Hold to Talk",
            callback=lambda _: self._set_mode("hold"),
        )
        toggle_item = rumps.MenuItem(
            "Push to Toggle",
            callback=lambda _: self._set_mode("toggle"),
        )

        if self.settings.hotkey.mode == "hold":
            hold_item.state = 1
        else:
            toggle_item.state = 1

        mode_menu.add(hold_item)
        mode_menu.add(toggle_item)
        self.menu.add(mode_menu)

        # Whisper model
        model_menu = rumps.MenuItem("Whisper Model")
        for size in ["tiny", "base", "small", "medium", "large-v3"]:
            item = rumps.MenuItem(
                size.title(),
                callback=lambda sender, s=size: self._set_model(s),
            )
            if self.settings.whisper.model_size == size:
                item.state = 1
            model_menu.add(item)
        self.menu.add(model_menu)

        # AI Editor
        editor_menu = rumps.MenuItem("AI Editor")
        for provider in ["none", "ollama", "openai", "anthropic"]:
            label = provider.title() if provider != "none" else "Disabled"
            item = rumps.MenuItem(
                label,
                callback=lambda sender, p=provider: self._set_editor(p),
            )
            if self.settings.ai_editor.provider == provider:
                item.state = 1
            editor_menu.add(item)

        editor_menu.add(rumps.separator)

        # Presets submenu
        preset_menu = rumps.MenuItem("Preset")
        for preset in ["default", "email", "commit", "notes", "code"]:
            item = rumps.MenuItem(
                preset.title(),
                callback=lambda sender, p=preset: self._set_preset(p),
            )
            if self.settings.ai_editor.preset == preset:
                item.state = 1
            preset_menu.add(item)
        editor_menu.add(preset_menu)

        self.menu.add(editor_menu)

        self.menu.add(rumps.separator)

        # Load model button
        self.menu.add(rumps.MenuItem("Load Whisper Model", callback=self._load_model))

        # Test recording
        self.menu.add(rumps.MenuItem("Test Recording", callback=self._test_recording))

        self.menu.add(rumps.separator)

        # Quit
        self.menu.add(rumps.MenuItem("Quit", callback=self._quit))

    def _update_title(self, state: str) -> None:
        """Update menu bar icon/title based on state."""
        icons = {
            "idle": "🎤",
            "recording": "🔴",
            "processing": "⏳",
            "error": "⚠️",
        }
        self.title = icons.get(state, "🎤")

        status_text = {
            "idle": "Status: Idle",
            "recording": "Status: Recording...",
            "processing": "Status: Processing...",
            "error": "Status: Error",
        }
        if hasattr(self, "status_item"):
            self.status_item.title = status_text.get(state, "Status: Unknown")

    def _on_hotkey_activate(self) -> None:
        """Called when hotkey is pressed/activated."""
        if self._is_processing:
            return

        self._is_recording = True
        self._update_title("recording")

        # Start recording
        self.recorder.start(on_audio_level=self._on_audio_level)

    def _on_hotkey_deactivate(self) -> None:
        """Called when hotkey is released/deactivated."""
        if not self._is_recording:
            return

        self._is_recording = False
        self._is_processing = True
        self._update_title("processing")

        # Stop recording and process in background
        threading.Thread(target=self._process_recording, daemon=True).start()

    def _process_recording(self) -> None:
        """Process the recorded audio."""
        try:
            # Get audio data
            audio_data = self.recorder.stop()

            if not audio_data:
                print("No audio recorded")
                return

            # Transcribe
            text = self.transcriber.transcribe(audio_data)

            if not text:
                print("No speech detected")
                return

            print(f"Transcribed: {text}")

            # Edit/cleanup
            if self.settings.ai_editor.enabled:
                text = self.editor.edit(
                    text,
                    preset=self.settings.ai_editor.preset,
                    custom_prompt=self.settings.ai_editor.custom_prompt,
                )
                print(f"Edited: {text}")

            # Type the text
            self.typer.type_text(text)

        except Exception as e:
            print(f"Error processing recording: {e}")
            self._update_title("error")
            rumps.notification(
                "Rodin Error",
                "Processing failed",
                str(e),
            )
        finally:
            self._is_processing = False
            self._update_title("idle")

    def _on_audio_level(self, level: float) -> None:
        """Called with audio level updates during recording."""
        # Could be used to update UI with audio level visualization
        pass

    def _set_mode(self, mode: str) -> None:
        """Set recording mode."""
        self.settings.hotkey.mode = mode
        save_settings(self.settings)
        self.hotkey_handler.update_config(self.settings.hotkey)
        self._build_menu()

    def _set_model(self, model: str) -> None:
        """Set Whisper model."""
        self.settings.whisper.model_size = model
        save_settings(self.settings)
        self.transcriber = Transcriber(self.settings.whisper)
        self._build_menu()

    def _set_editor(self, provider: str) -> None:
        """Set AI editor provider."""
        self.settings.ai_editor.provider = provider
        self.settings.ai_editor.enabled = provider != "none"
        save_settings(self.settings)
        self.editor = create_editor(
            self.settings.ai_editor,
            {
                "openai": self.settings.openai_api_key,
                "anthropic": self.settings.anthropic_api_key,
            },
        )
        self._build_menu()

    def _set_preset(self, preset: str) -> None:
        """Set AI editor preset."""
        self.settings.ai_editor.preset = preset
        save_settings(self.settings)
        self._build_menu()

    @rumps.clicked("Load Whisper Model")
    def _load_model(self, _) -> None:
        """Pre-load the Whisper model."""
        if self.transcriber.is_loaded():
            rumps.notification("Rodin", "Model Status", "Model already loaded")
            return

        self._update_title("processing")

        def load():
            try:
                self.transcriber.load_model()
                rumps.notification(
                    "Rodin",
                    "Model Loaded",
                    f"Loaded {self.settings.whisper.model_size} model",
                )
            except Exception as e:
                rumps.notification("Rodin", "Error", f"Failed to load model: {e}")
            finally:
                self._update_title("idle")

        threading.Thread(target=load, daemon=True).start()

    @rumps.clicked("Test Recording")
    def _test_recording(self, _) -> None:
        """Test recording for 3 seconds."""
        import time

        def test():
            self._update_title("recording")
            self.recorder.start()
            time.sleep(3)
            audio_data = self.recorder.stop()

            if audio_data:
                duration = len(audio_data) / (16000 * 2)  # 16kHz, 16-bit
                rumps.notification(
                    "Rodin",
                    "Test Complete",
                    f"Recorded {duration:.1f}s of audio",
                )
            else:
                rumps.notification("Rodin", "Test Failed", "No audio captured")

            self._update_title("idle")

        threading.Thread(target=test, daemon=True).start()

    def _quit(self, _) -> None:
        """Quit the application."""
        self.hotkey_handler.stop()
        rumps.quit_application()

    def run(self) -> None:
        """Start the application."""
        # Start hotkey listener
        self.hotkey_handler.start()

        # Pre-load model in background
        threading.Thread(target=self.transcriber.load_model, daemon=True).start()

        # Run the app
        super().run()


def run_menubar_app(settings: Settings | None = None) -> None:
    """Run the menu bar application."""
    app = WhisperFlowApp(settings)
    app.run()
