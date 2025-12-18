"""Text insertion at cursor position."""

import sys
import time

import pyperclip
from pynput.keyboard import Controller, Key


class TextTyper:
    """Inserts text at the current cursor position."""

    def __init__(self, typing_delay: float = 0.01):
        self.keyboard = Controller()
        self.typing_delay = typing_delay

    def type_text(self, text: str, method: str = "auto") -> None:
        """Type text at the current cursor position.

        Args:
            text: Text to type
            method: Insertion method - "type", "paste", or "auto"
        """
        if not text:
            return

        if method == "auto":
            # Use paste for longer text (faster), type for short text
            method = "paste" if len(text) > 50 else "type"

        if method == "paste":
            self._paste_text(text)
        else:
            self._type_text(text)

    def _type_text(self, text: str) -> None:
        """Type text character by character."""
        for char in text:
            self.keyboard.type(char)
            if self.typing_delay > 0:
                time.sleep(self.typing_delay)

    def _paste_text(self, text: str) -> None:
        """Paste text using clipboard."""
        # Save current clipboard content
        try:
            original_clipboard = pyperclip.paste()
        except Exception:
            original_clipboard = None

        try:
            # Copy text to clipboard
            pyperclip.copy(text)

            # Small delay to ensure clipboard is ready
            time.sleep(0.05)

            # Paste using keyboard shortcut
            modifier = Key.cmd if sys.platform == "darwin" else Key.ctrl
            with self.keyboard.pressed(modifier):
                self.keyboard.tap("v")

            # Small delay before restoring clipboard
            time.sleep(0.1)

        finally:
            # Restore original clipboard content
            if original_clipboard is not None:
                try:
                    pyperclip.copy(original_clipboard)
                except Exception:
                    pass

    def press_key(self, key: Key | str) -> None:
        """Press a single key."""
        if isinstance(key, str):
            self.keyboard.tap(key)
        else:
            self.keyboard.tap(key)

    def press_enter(self) -> None:
        """Press Enter key."""
        self.keyboard.tap(Key.enter)

    def press_tab(self) -> None:
        """Press Tab key."""
        self.keyboard.tap(Key.tab)

    def delete_chars(self, count: int = 1) -> None:
        """Delete characters using backspace.

        Args:
            count: Number of characters to delete
        """
        for _ in range(count):
            self.keyboard.tap(Key.backspace)
            time.sleep(0.01)

    def delete_words(self, count: int = 1) -> None:
        """Delete words using Option+Backspace (Mac) or Ctrl+Backspace (Windows).

        Args:
            count: Number of words to delete
        """
        modifier = Key.alt if sys.platform == "darwin" else Key.ctrl
        for _ in range(count):
            with self.keyboard.pressed(modifier):
                self.keyboard.tap(Key.backspace)
            time.sleep(0.02)

    def undo(self) -> None:
        """Perform undo (Cmd+Z / Ctrl+Z)."""
        modifier = Key.cmd if sys.platform == "darwin" else Key.ctrl
        with self.keyboard.pressed(modifier):
            self.keyboard.tap("z")

    def redo(self) -> None:
        """Perform redo (Cmd+Shift+Z / Ctrl+Y)."""
        if sys.platform == "darwin":
            with self.keyboard.pressed(Key.cmd):
                with self.keyboard.pressed(Key.shift):
                    self.keyboard.tap("z")
        else:
            with self.keyboard.pressed(Key.ctrl):
                self.keyboard.tap("y")

    def select_all(self) -> None:
        """Select all text (Cmd+A / Ctrl+A)."""
        modifier = Key.cmd if sys.platform == "darwin" else Key.ctrl
        with self.keyboard.pressed(modifier):
            self.keyboard.tap("a")

    def copy(self) -> None:
        """Copy selection (Cmd+C / Ctrl+C)."""
        modifier = Key.cmd if sys.platform == "darwin" else Key.ctrl
        with self.keyboard.pressed(modifier):
            self.keyboard.tap("c")

    def cut(self) -> None:
        """Cut selection (Cmd+X / Ctrl+X)."""
        modifier = Key.cmd if sys.platform == "darwin" else Key.ctrl
        with self.keyboard.pressed(modifier):
            self.keyboard.tap("x")

    def paste(self) -> None:
        """Paste from clipboard (Cmd+V / Ctrl+V)."""
        modifier = Key.cmd if sys.platform == "darwin" else Key.ctrl
        with self.keyboard.pressed(modifier):
            self.keyboard.tap("v")
