"""Floating overlay window for Whisper Flow."""

import sys
import threading
import time

if sys.platform != "darwin":
    raise ImportError("Overlay UI only available on macOS")

import objc
from AppKit import (
    NSApplication,
    NSApplicationActivationPolicyAccessory,
    NSBackingStoreBuffered,
    NSBezierPath,
    NSColor,
    NSFont,
    NSFontAttributeName,
    NSForegroundColorAttributeName,
    NSMakeRect,
    NSScreen,
    NSView,
    NSWindow,
    NSWindowStyleMaskBorderless,
    NSStatusWindowLevel,
    NSTrackingArea,
    NSTrackingMouseEnteredAndExited,
    NSTrackingActiveAlways,
    NSTrackingInVisibleRect,
)
from PyObjCTools import AppHelper

from ..app_context import AppContextManager, get_frontmost_app
from ..config import Settings, load_settings, get_config_dir
from ..dictionary import PersonalDictionary
from ..editor import create_editor
from ..hotkey import HotkeyHandler
from ..recorder import AudioRecorder
from ..snippets import SnippetExpander
from ..transcriber import Transcriber
from ..typer import TextTyper
from ..voice_commands import VoiceCommandProcessor


class MicButtonView(NSView):
    """Custom view for the microphone button."""

    def initWithFrame_(self, frame):
        self = objc.super(MicButtonView, self).initWithFrame_(frame)
        if self is None:
            return None

        self._is_recording = False
        self._is_processing = False
        self._is_hovering = False
        self._audio_level = 0.0
        self._on_click = None

        # Set up tracking area for hover
        tracking_area = NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
            self.bounds(),
            NSTrackingMouseEnteredAndExited | NSTrackingActiveAlways | NSTrackingInVisibleRect,
            self,
            None
        )
        self.addTrackingArea_(tracking_area)

        return self

    def drawRect_(self, rect):
        """Draw the button."""
        # Background circle
        bounds = self.bounds()
        circle_rect = NSMakeRect(2, 2, bounds.size.width - 4, bounds.size.height - 4)
        path = NSBezierPath.bezierPathWithOvalInRect_(circle_rect)

        # Colors based on state
        if self._is_recording:
            # Pulsing red when recording
            pulse = 0.7 + 0.3 * abs(time.time() % 1 - 0.5) * 2
            NSColor.colorWithRed_green_blue_alpha_(0.9 * pulse, 0.2, 0.2, 0.95).setFill()
        elif self._is_processing:
            # Orange when processing
            NSColor.colorWithRed_green_blue_alpha_(0.9, 0.6, 0.2, 0.95).setFill()
        elif self._is_hovering:
            # Lighter when hovering
            NSColor.colorWithRed_green_blue_alpha_(0.3, 0.3, 0.35, 0.95).setFill()
        else:
            # Dark gray default
            NSColor.colorWithRed_green_blue_alpha_(0.2, 0.2, 0.25, 0.9).setFill()

        path.fill()

        # Border
        NSColor.colorWithRed_green_blue_alpha_(0.4, 0.4, 0.45, 1.0).setStroke()
        path.setLineWidth_(1.5)
        path.stroke()

        # Mic icon (simple text emoji for now)
        icon = "🎤" if not self._is_recording else "🔴"
        if self._is_processing:
            icon = "⏳"

        attrs = {
            NSFontAttributeName: NSFont.systemFontOfSize_(24),
            NSForegroundColorAttributeName: NSColor.whiteColor(),
        }
        icon_size = icon.sizeWithAttributes_(attrs) if hasattr(icon, 'sizeWithAttributes_') else (24, 24)

        # Center the icon
        from Foundation import NSString, NSMakePoint
        ns_icon = NSString.stringWithString_(icon)
        icon_size = ns_icon.sizeWithAttributes_(attrs)
        x = (bounds.size.width - icon_size.width) / 2
        y = (bounds.size.height - icon_size.height) / 2
        ns_icon.drawAtPoint_withAttributes_(NSMakePoint(x, y), attrs)

    def mouseDown_(self, event):
        """Handle mouse click."""
        if self._on_click:
            self._on_click()

    def mouseEntered_(self, event):
        """Handle mouse enter."""
        self._is_hovering = True
        self.setNeedsDisplay_(True)

    def mouseExited_(self, event):
        """Handle mouse exit."""
        self._is_hovering = False
        self.setNeedsDisplay_(True)

    def setRecording_(self, recording):
        self._is_recording = recording
        self.setNeedsDisplay_(True)

    def setProcessing_(self, processing):
        self._is_processing = processing
        self.setNeedsDisplay_(True)

    def setOnClick_(self, callback):
        self._on_click = callback


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
    """Floating overlay window with mic button."""

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
        self.app_context = AppContextManager(self.settings.app_context.app_presets)

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
        # Window size
        button_size = 50

        # Position on right side, middle of screen (use visibleFrame to avoid menu bar)
        screen = NSScreen.mainScreen()
        visible_frame = screen.visibleFrame()
        x = visible_frame.origin.x + visible_frame.size.width - button_size - 20  # 20px from right edge
        y = visible_frame.origin.y + visible_frame.size.height / 2 - button_size / 2  # Centered vertically

        # Create window
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, y, button_size, button_size),
            NSWindowStyleMaskBorderless,
            NSBackingStoreBuffered,
            False,
        )

        # Configure window
        self.window.setLevel_(NSStatusWindowLevel)  # Higher than floating, below screen saver
        self.window.setOpaque_(False)
        self.window.setBackgroundColor_(NSColor.clearColor())
        self.window.setHasShadow_(True)
        self.window.setMovableByWindowBackground_(True)
        self.window.setCollectionBehavior_(1 << 0)  # Can join all spaces
        self.window.setIgnoresMouseEvents_(False)

        # Create button view
        self.button_view = MicButtonView.alloc().initWithFrame_(
            NSMakeRect(0, 0, button_size, button_size)
        )
        self.button_view.setOnClick_(self._on_click)

        self.window.setContentView_(self.button_view)

    def _on_click(self):
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
        self.button_view.setRecording_(True)
        self.recorder.start()

        # Schedule UI refresh for animation
        self._schedule_refresh()

    def _on_deactivate(self):
        """Stop recording and process."""
        if not self._is_recording:
            return

        self._is_recording = False
        self._is_processing = True
        self.button_view.setRecording_(False)
        self.button_view.setProcessing_(True)

        # Process in background
        threading.Thread(target=self._process_recording, daemon=True).start()

    def _process_recording(self):
        """Process the recorded audio.

        Pipeline:
        1. Transcribe audio → raw text
        2. Apply personal dictionary corrections
        3. Check for voice commands (may exit early)
        4. AI editing (with app context awareness)
        5. Snippet expansion
        6. Type the text at cursor
        """
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
                        # Pure command, no text to process
                        duration = _time.time() - start_time
                        _log_transcription(raw_text, f"[Command: {command[0]}]", duration)
                        return
                    text = remaining_text

            # 4. Get app context for AI editing preset
            preset = self.settings.ai_editor.preset
            if self.settings.app_context.enabled:
                context = self.app_context.get_context()
                if context["preset"] != "default":
                    preset = context["preset"]
                    print(f"App context: {context['name']} → {preset}")

            # 5. AI editing
            if self.settings.ai_editor.enabled:
                text = self.editor.edit(text, preset=preset)
                print(f"Edited: {text}")

            # 6. Snippet expansion
            if self.settings.snippets.enabled:
                expanded = self.snippets.expand(text)
                if expanded != text:
                    text = expanded
                    print(f"Snippet: {text[:50]}...")

            # 7. Type the text
            self.typer.type_text(text)

            # Track for "delete that" command
            self.voice_commands.set_last_typed_length(len(text))

            # Auto-learn from corrections if enabled
            if self.settings.dictionary.auto_learn and text != raw_text:
                self.dictionary.learn_from_correction(raw_text, text)

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
            AppHelper.callAfter(lambda: self.button_view.setProcessing_(False))

    def _schedule_refresh(self):
        """Schedule UI refresh for recording animation."""
        if self._is_recording:
            self.button_view.setNeedsDisplay_(True)
            # Refresh every 100ms for animation
            AppHelper.callLater(0.1, self._schedule_refresh)

    def run(self):
        """Run the overlay."""
        # Set up app
        app = NSApplication.sharedApplication()
        app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)

        # Show window and force to front
        self.window.orderFrontRegardless()
        self.window.makeKeyAndOrderFront_(None)

        # Debug: print window position
        frame = self.window.frame()
        print(f"Window position: x={frame.origin.x}, y={frame.origin.y}, size={frame.size.width}x{frame.size.height}")

        # Load model in background
        print("Loading Whisper model...")
        threading.Thread(target=self.transcriber.load_model, daemon=True).start()

        # Start hotkey listener in a separate thread to avoid event loop conflict
        def start_hotkey():
            import time
            time.sleep(1)  # Wait for event loop to start
            self.hotkey_handler.start()
        threading.Thread(target=start_hotkey, daemon=True).start()

        print(f"Whisper Flow ready!")
        print(f"Hotkey: Cmd+Shift+Space (hold to talk)")
        print(f"Or click the mic button on the right side of your screen")

        # Run the app
        AppHelper.runEventLoop()

    def stop(self):
        """Stop the overlay."""
        self.hotkey_handler.stop()
        AppHelper.stopEventLoop()


def run_overlay(settings: Settings | None = None):
    """Run the overlay window."""
    overlay = OverlayWindow(settings)
    overlay.run()
