"""Voice command processing for hands-free editing."""

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .typer import TextTyper


# Command patterns and their actions
# Format: (regex pattern, action_name, action_arg)
VOICE_COMMANDS = [
    # Deletion commands
    (r"^(?:delete|scratch|cancel)\s+that\.?$", "delete_last", None),
    (r"^(?:delete|remove)\s+(?:the\s+)?last\s+word\.?$", "delete_words", 1),
    (r"^(?:delete|remove)\s+(?:the\s+)?last\s+(\d+)\s+words?\.?$", "delete_words", "match"),
    (r"^(?:backspace|back\s+space)\.?$", "backspace", 1),
    (r"^undo(?:\s+that)?\.?$", "undo", None),

    # Navigation/formatting commands
    (r"^new\s+line\.?$", "newline", 1),
    (r"^new\s+paragraph\.?$", "newline", 2),
    (r"^(?:press\s+)?enter\.?$", "newline", 1),
    (r"^(?:press\s+)?tab\.?$", "tab", 1),

    # Selection commands (for future use)
    (r"^select\s+all\.?$", "select_all", None),
    (r"^copy(?:\s+that)?\.?$", "copy", None),
    (r"^paste\.?$", "paste", None),
    (r"^cut(?:\s+that)?\.?$", "cut", None),
]


class VoiceCommandProcessor:
    """Processes voice commands for text editing operations."""

    def __init__(self):
        self._compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), action, arg)
            for pattern, action, arg in VOICE_COMMANDS
        ]
        self._last_typed_length = 0  # Track length of last typed text for "delete that"

    def set_last_typed_length(self, length: int) -> None:
        """Record the length of the last typed text for 'delete that' command."""
        self._last_typed_length = length

    def detect_command(self, text: str) -> tuple[tuple[str, any] | None, str]:
        """Detect if text contains a voice command.

        Args:
            text: The transcribed text to check

        Returns:
            Tuple of (command_tuple, remaining_text) where command_tuple is
            (action_name, action_arg) or None if no command detected.
            remaining_text is any text after the command, or the original
            text if no command was found.
        """
        text = text.strip()

        for pattern, action, arg in self._compiled_patterns:
            match = pattern.match(text)
            if match:
                # Handle dynamic argument from regex match
                actual_arg = arg
                if arg == "match" and match.groups():
                    actual_arg = int(match.group(1))

                # Get remaining text after command
                remaining = text[match.end():].strip()
                return (action, actual_arg), remaining

        return None, text

    def execute_command(self, command: tuple[str, any], typer: "TextTyper") -> bool:
        """Execute a voice command.

        Args:
            command: Tuple of (action_name, action_arg)
            typer: TextTyper instance for keyboard operations

        Returns:
            True if command was executed successfully
        """
        action, arg = command

        if action == "delete_last":
            # Delete the last typed text
            if self._last_typed_length > 0:
                typer.delete_chars(self._last_typed_length)
                self._last_typed_length = 0
            return True

        elif action == "delete_words":
            count = arg if arg else 1
            typer.delete_words(count)
            return True

        elif action == "backspace":
            count = arg if arg else 1
            typer.delete_chars(count)
            return True

        elif action == "undo":
            typer.undo()
            return True

        elif action == "newline":
            count = arg if arg else 1
            for _ in range(count):
                typer.press_enter()
            return True

        elif action == "tab":
            typer.press_tab()
            return True

        elif action == "select_all":
            typer.select_all()
            return True

        elif action == "copy":
            typer.copy()
            return True

        elif action == "paste":
            typer.paste()
            return True

        elif action == "cut":
            typer.cut()
            return True

        return False
