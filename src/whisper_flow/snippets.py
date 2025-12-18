"""Snippet expansion for text shortcuts."""

import json
import re
from pathlib import Path

from .config import get_config_dir


class SnippetExpander:
    """Manages text snippets that expand trigger words into full text."""

    def __init__(self, snippets_path: Path | None = None):
        self.snippets_path = snippets_path or get_config_dir() / "snippets.json"
        self._snippets: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        """Load snippets from file."""
        if self.snippets_path.exists():
            with open(self.snippets_path) as f:
                data = json.load(f)
            self._snippets = data.get("snippets", {})
        else:
            self._snippets = {}

    def _save(self) -> None:
        """Save snippets to file."""
        data = {"snippets": self._snippets}
        with open(self.snippets_path, "w") as f:
            json.dump(data, f, indent=2)

    def add_snippet(self, trigger: str, expansion: str) -> None:
        """Add a snippet.

        Args:
            trigger: The word/phrase that triggers expansion
            expansion: The full text to expand to
        """
        self._snippets[trigger.lower()] = expansion
        self._save()

    def remove_snippet(self, trigger: str) -> bool:
        """Remove a snippet.

        Returns:
            True if snippet was removed, False if not found
        """
        key = trigger.lower()
        if key in self._snippets:
            del self._snippets[key]
            self._save()
            return True
        return False

    def get_snippets(self) -> dict[str, str]:
        """Get all snippets."""
        return self._snippets.copy()

    def expand(self, text: str) -> str:
        """Expand any snippets found in the text.

        If the entire text (trimmed) matches a snippet trigger,
        replaces it completely. Otherwise, expands triggers as
        word boundaries.
        """
        if not self._snippets:
            return text

        # Check if entire text is a snippet trigger
        text_lower = text.strip().lower()
        if text_lower in self._snippets:
            return self._snippets[text_lower]

        # Otherwise, expand triggers found within text
        result = text
        for trigger, expansion in self._snippets.items():
            # Case-insensitive word boundary match
            pattern = re.compile(rf'\b{re.escape(trigger)}\b', re.IGNORECASE)
            result = pattern.sub(expansion, result)

        return result

    def list_snippets(self) -> list[tuple[str, str]]:
        """List all snippets as (trigger, expansion) tuples."""
        return list(self._snippets.items())
