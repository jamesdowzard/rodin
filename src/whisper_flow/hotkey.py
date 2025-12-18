"""Global hotkey handling."""

import sys
import threading
import time
from typing import Callable

from pynput import keyboard

from .config import HotkeyConfig


class HotkeyHandler:
    """Handles global hotkey detection.

    Supports three modes:
    - hold: Hold hotkey to record, release to stop
    - toggle: Press once to start, press again to stop
    - wispr: Hold to record OR double-tap to enter continuous mode (tap to stop)
    """

    def __init__(
        self,
        config: HotkeyConfig,
        on_activate: Callable[[], None],
        on_deactivate: Callable[[], None] | None = None,
    ):
        self.config = config
        self.on_activate = on_activate
        self.on_deactivate = on_deactivate

        self._listener: keyboard.Listener | None = None
        self._pressed_keys: set[str] = set()
        self._hotkey_active = False
        self._is_toggled = False  # For toggle mode

        # Double-tap detection for wispr mode
        self._last_tap_time = 0.0
        self._double_tap_threshold = 0.4  # seconds
        self._in_continuous_mode = False

    def _normalize_key(self, key) -> str | None:
        """Normalize a key to a string representation."""
        try:
            # Regular character key
            if hasattr(key, "char") and key.char:
                return key.char.lower()

            # Special keys
            if hasattr(key, "name"):
                return key.name.lower()

            # Handle Key enum
            key_str = str(key).replace("Key.", "").lower()

            # Normalize modifier names
            if key_str in ("cmd", "cmd_l", "cmd_r"):
                return "cmd"
            if key_str in ("ctrl", "ctrl_l", "ctrl_r"):
                return "ctrl"
            if key_str in ("shift", "shift_l", "shift_r"):
                return "shift"
            if key_str in ("alt", "alt_l", "alt_r", "option"):
                return "alt"

            return key_str

        except Exception:
            return None

    def _is_single_key_mode(self) -> bool:
        """Check if we're using single-key mode (just a modifier, no additional key)."""
        return not self.config.key or self.config.key.lower() == self.config.modifier1.lower()

    def _is_hotkey_pressed(self) -> bool:
        """Check if the configured hotkey combination is pressed."""
        if self._is_single_key_mode():
            # Single key mode: just the modifier alone
            required = {self.config.modifier1.lower()}
        else:
            required = {self.config.modifier1.lower(), self.config.key.lower()}
            # Only require modifier2 if it's set
            if self.config.modifier2:
                required.add(self.config.modifier2.lower())
        return required.issubset(self._pressed_keys)

    def _on_press(self, key) -> None:
        """Handle key press events."""
        key_str = self._normalize_key(key)
        if key_str:
            self._pressed_keys.add(key_str)

        if self._is_hotkey_pressed() and not self._hotkey_active:
            self._hotkey_active = True
            current_time = time.time()

            if self.config.mode == "toggle":
                # Toggle mode: press once to start, press again to stop
                self._is_toggled = not self._is_toggled
                if self._is_toggled:
                    threading.Thread(target=self.on_activate, daemon=True).start()
                elif self.on_deactivate:
                    threading.Thread(target=self.on_deactivate, daemon=True).start()

            elif self.config.mode == "wispr":
                # Wispr mode: hold to talk OR double-tap for continuous
                if self._in_continuous_mode:
                    # Already in continuous mode - tap to stop
                    self._in_continuous_mode = False
                    if self.on_deactivate:
                        threading.Thread(target=self.on_deactivate, daemon=True).start()
                elif current_time - self._last_tap_time < self._double_tap_threshold:
                    # Double-tap detected - enter continuous mode
                    self._in_continuous_mode = True
                    threading.Thread(target=self.on_activate, daemon=True).start()
                else:
                    # Single press - start recording (will stop on release)
                    threading.Thread(target=self.on_activate, daemon=True).start()

                self._last_tap_time = current_time

            else:
                # Hold mode: activate on press
                threading.Thread(target=self.on_activate, daemon=True).start()

    def _on_release(self, key) -> None:
        """Handle key release events."""
        key_str = self._normalize_key(key)
        if key_str:
            self._pressed_keys.discard(key_str)

        # In hold mode, deactivate when hotkey is released
        if self.config.mode == "hold" and self._hotkey_active:
            if not self._is_hotkey_pressed():
                self._hotkey_active = False
                if self.on_deactivate:
                    threading.Thread(target=self.on_deactivate, daemon=True).start()

        # In wispr mode, deactivate on release UNLESS in continuous mode
        if self.config.mode == "wispr" and self._hotkey_active and not self._in_continuous_mode:
            if not self._is_hotkey_pressed():
                self._hotkey_active = False
                if self.on_deactivate:
                    threading.Thread(target=self.on_deactivate, daemon=True).start()

        # Reset hotkey active flag when all keys released
        if not self._pressed_keys:
            self._hotkey_active = False

    def start(self) -> None:
        """Start listening for hotkeys."""
        if self._listener is not None:
            return

        self._listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        self._listener.start()

        mod1 = "Cmd" if self.config.modifier1 == "cmd" else self.config.modifier1.title()

        if self._is_single_key_mode():
            # Single key mode - just show the modifier
            hotkey_str = mod1
        elif self.config.modifier2:
            mod2 = self.config.modifier2.title()
            key = self.config.key.title()
            hotkey_str = f"{mod1}+{mod2}+{key}"
        else:
            key = self.config.key.title()
            hotkey_str = f"{mod1}+{key}"

        mode_desc = {
            "hold": "hold to talk",
            "toggle": "tap to toggle",
            "wispr": "hold to talk, double-tap for continuous",
        }.get(self.config.mode, self.config.mode)

        print(f"Hotkey active: {hotkey_str} ({mode_desc})")

    def stop(self) -> None:
        """Stop listening for hotkeys."""
        if self._listener:
            self._listener.stop()
            self._listener = None
        self._pressed_keys.clear()
        self._hotkey_active = False
        self._is_toggled = False

    def is_running(self) -> bool:
        """Check if the listener is running."""
        return self._listener is not None and self._listener.is_alive()

    def update_config(self, config: HotkeyConfig) -> None:
        """Update hotkey configuration."""
        was_running = self.is_running()
        if was_running:
            self.stop()

        self.config = config

        if was_running:
            self.start()
