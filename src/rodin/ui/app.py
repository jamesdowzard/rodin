"""Native macOS app with settings window."""

import sys
import threading

if sys.platform != "darwin":
    raise ImportError("Mac app UI only available on macOS")

import objc
from AppKit import (
    NSApp,
    NSApplication,
    NSApplicationActivationPolicyAccessory,
    NSApplicationActivationPolicyRegular,
    NSBackingStoreBuffered,
    NSButton,
    NSColor,
    NSFont,
    NSImage,
    NSMakeRect,
    NSMenuItem,
    NSMenu,
    NSPopUpButton,
    NSScreen,
    NSSegmentedControl,
    NSSegmentStyleTexturedSquare,
    NSSlider,
    NSStackView,
    NSStatusBar,
    NSTextField,
    NSTextFieldCell,
    NSUserInterfaceLayoutOrientationVertical,
    NSView,
    NSWindow,
    NSWindowStyleMaskClosable,
    NSWindowStyleMaskMiniaturizable,
    NSWindowStyleMaskTitled,
    NSStackViewDistributionFill,
    NSStackViewDistributionFillEqually,
    NSLayoutConstraint,
    NSVariableStatusItemLength,
)
from Foundation import NSObject
from PyObjCTools import AppHelper

from ..config import (
    APP_NAME,
    APP_VERSION,
    Settings,
    load_settings,
    save_settings,
)
from .overlay import OverlayWindow


class AppDelegate(NSObject):
    """macOS application delegate."""

    def init(self):
        self = objc.super(AppDelegate, self).init()
        if self is None:
            return None

        self.settings = load_settings()
        self.overlay: OverlayWindow | None = None
        self.preferences_window: NSWindow | None = None
        self.status_item = None

        return self

    def applicationDidFinishLaunching_(self, notification):
        """Called when the application has finished launching."""
        # Create status bar item
        self._create_status_bar()

        # Create and show overlay
        self.overlay = OverlayWindow(self.settings)

        # Show overlay window
        self.overlay.window.orderFrontRegardless()

        # Load model and start hotkey in background
        def startup():
            import time
            time.sleep(0.5)
            self.overlay.transcriber.load_model()
            self.overlay.hotkey_handler.start()

        threading.Thread(target=startup, daemon=True).start()

        # Show stats on startup
        stats = self.overlay.stats_db.get_stats()
        if stats.total_transcriptions > 0:
            print(f"{APP_NAME}: {stats.total_words:,} words in {stats.total_transcriptions:,} transcriptions")

        print(f"{APP_NAME} ready! Cmd+Shift+Space to dictate.")

    def _create_status_bar(self):
        """Create the menu bar status item."""
        status_bar = NSStatusBar.systemStatusBar()
        self.status_item = status_bar.statusItemWithLength_(NSVariableStatusItemLength)

        # Use microphone emoji as icon
        self.status_item.button().setTitle_("🎤")

        # Create menu
        menu = NSMenu.alloc().init()

        # Stats item
        stats = self.overlay.stats_db.get_stats() if self.overlay else None
        if stats and stats.total_words > 0:
            stats_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                f"{stats.total_words:,} words dictated", None, ""
            )
            stats_item.setEnabled_(False)
            menu.addItem_(stats_item)
            menu.addItem_(NSMenuItem.separatorItem())

        # Preferences
        prefs_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Preferences...", "showPreferences:", ","
        )
        prefs_item.setTarget_(self)
        menu.addItem_(prefs_item)

        menu.addItem_(NSMenuItem.separatorItem())

        # Quit
        quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            f"Quit {APP_NAME}", "terminate:", "q"
        )
        menu.addItem_(quit_item)

        self.status_item.setMenu_(menu)

    def showPreferences_(self, sender):
        """Show the preferences window."""
        if self.preferences_window is None:
            self._create_preferences_window()

        self.preferences_window.makeKeyAndOrderFront_(None)
        NSApp.activateIgnoringOtherApps_(True)

    def _create_preferences_window(self):
        """Create the preferences window."""
        # Window size
        width = 500
        height = 400

        # Center on screen
        screen = NSScreen.mainScreen()
        screen_frame = screen.frame()
        x = (screen_frame.size.width - width) / 2
        y = (screen_frame.size.height - height) / 2

        # Create window
        self.preferences_window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, y, width, height),
            NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskMiniaturizable,
            NSBackingStoreBuffered,
            False,
        )
        self.preferences_window.setTitle_(f"{APP_NAME} Preferences")
        self.preferences_window.setReleasedWhenClosed_(False)

        # Create content view with padding
        content_view = self.preferences_window.contentView()

        # Main vertical stack
        vstack = NSStackView.alloc().initWithFrame_(NSMakeRect(20, 20, width - 40, height - 40))
        vstack.setOrientation_(NSUserInterfaceLayoutOrientationVertical)
        vstack.setSpacing_(16)
        vstack.setAlignment_(1)  # NSLayoutAttributeLeading

        # Model section
        model_section = self._create_model_section()
        vstack.addArrangedSubview_(model_section)

        # Hotkey section
        hotkey_section = self._create_hotkey_section()
        vstack.addArrangedSubview_(hotkey_section)

        # AI Editor section
        editor_section = self._create_editor_section()
        vstack.addArrangedSubview_(editor_section)

        content_view.addSubview_(vstack)

        # Add constraints
        vstack.setTranslatesAutoresizingMaskIntoConstraints_(False)
        NSLayoutConstraint.activateConstraints_([
            vstack.topAnchor().constraintEqualToAnchor_constant_(content_view.topAnchor(), 20),
            vstack.leadingAnchor().constraintEqualToAnchor_constant_(content_view.leadingAnchor(), 20),
            vstack.trailingAnchor().constraintEqualToAnchor_constant_(content_view.trailingAnchor(), -20),
        ])

    def _create_section_label(self, text: str) -> NSTextField:
        """Create a section header label."""
        label = NSTextField.labelWithString_(text)
        label.setFont_(NSFont.boldSystemFontOfSize_(13))
        return label

    def _create_model_section(self) -> NSView:
        """Create the model selection section."""
        container = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 460, 60))

        # Label
        label = self._create_section_label("Whisper Model")
        label.setFrame_(NSMakeRect(0, 35, 200, 20))
        container.addSubview_(label)

        # Popup button for model selection
        popup = NSPopUpButton.alloc().initWithFrame_pullsDown_(
            NSMakeRect(0, 5, 200, 25), False
        )
        models = ["tiny", "base", "small", "medium", "large-v3"]
        for model in models:
            popup.addItemWithTitle_(model)

        # Select current model
        current = self.settings.whisper.model_size
        popup.selectItemWithTitle_(current)

        # Set action
        popup.setTarget_(self)
        popup.setAction_(objc.selector(self.modelChanged_, signature=b"v@:@"))

        container.addSubview_(popup)

        return container

    def modelChanged_(self, sender):
        """Handle model selection change."""
        model = sender.titleOfSelectedItem()
        self.settings.whisper.model_size = model
        save_settings(self.settings)
        print(f"Model changed to: {model}")

    def _create_hotkey_section(self) -> NSView:
        """Create the hotkey mode section."""
        container = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 460, 60))

        # Label
        label = self._create_section_label("Recording Mode")
        label.setFrame_(NSMakeRect(0, 35, 200, 20))
        container.addSubview_(label)

        # Segmented control for mode
        segment = NSSegmentedControl.alloc().initWithFrame_(NSMakeRect(0, 5, 300, 25))
        segment.setSegmentCount_(3)
        segment.setLabel_forSegment_("Hold", 0)
        segment.setLabel_forSegment_("Toggle", 1)
        segment.setLabel_forSegment_("Double-tap", 2)

        # Select current mode
        modes = {"hold": 0, "toggle": 1, "wispr": 2}
        current = modes.get(self.settings.hotkey.mode, 0)
        segment.setSelectedSegment_(current)

        segment.setTarget_(self)
        segment.setAction_(objc.selector(self.modeChanged_, signature=b"v@:@"))

        container.addSubview_(segment)

        return container

    def modeChanged_(self, sender):
        """Handle mode selection change."""
        modes = {0: "hold", 1: "toggle", 2: "wispr"}
        mode = modes.get(sender.selectedSegment(), "hold")
        self.settings.hotkey.mode = mode
        save_settings(self.settings)
        print(f"Mode changed to: {mode}")

        # Update hotkey handler
        if self.overlay and self.overlay.hotkey_handler:
            self.overlay.hotkey_handler.config.mode = mode

    def _create_editor_section(self) -> NSView:
        """Create the AI editor section."""
        container = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 460, 60))

        # Label
        label = self._create_section_label("AI Editor")
        label.setFrame_(NSMakeRect(0, 35, 200, 20))
        container.addSubview_(label)

        # Popup button for editor selection
        popup = NSPopUpButton.alloc().initWithFrame_pullsDown_(
            NSMakeRect(0, 5, 200, 25), False
        )
        editors = ["none", "ollama", "openai", "anthropic"]
        for editor in editors:
            popup.addItemWithTitle_(editor)

        # Select current
        current = self.settings.ai_editor.provider
        popup.selectItemWithTitle_(current)

        popup.setTarget_(self)
        popup.setAction_(objc.selector(self.editorChanged_, signature=b"v@:@"))

        container.addSubview_(popup)

        return container

    def editorChanged_(self, sender):
        """Handle editor selection change."""
        editor = sender.titleOfSelectedItem()
        self.settings.ai_editor.provider = editor
        self.settings.ai_editor.enabled = editor != "none"
        save_settings(self.settings)
        print(f"Editor changed to: {editor}")

    def applicationWillTerminate_(self, notification):
        """Called when the application is about to terminate."""
        if self.overlay:
            self.overlay.stop()


def run_app():
    """Run the native Mac app."""
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)

    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)

    # Run event loop
    AppHelper.runEventLoop()
