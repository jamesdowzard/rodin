"""Personal dictionary for custom word corrections."""

import json
import re
from pathlib import Path

from .config import get_config_dir


class PersonalDictionary:
    """Manages personal dictionary for word corrections and custom vocabulary."""

    def __init__(self, dictionary_path: Path | None = None):
        self.dictionary_path = dictionary_path or get_config_dir() / "dictionary.json"
        self._corrections: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        """Load dictionary from file."""
        if self.dictionary_path.exists():
            with open(self.dictionary_path) as f:
                data = json.load(f)
            self._corrections = data.get("corrections", {})
        else:
            self._corrections = {}

    def _save(self) -> None:
        """Save dictionary to file."""
        data = {"corrections": self._corrections}
        with open(self.dictionary_path, "w") as f:
            json.dump(data, f, indent=2)

    def add_word(self, spoken: str, corrected: str) -> None:
        """Add a word correction to the dictionary.

        Args:
            spoken: How the word sounds when spoken (lowercase)
            corrected: The correct spelling/capitalization
        """
        self._corrections[spoken.lower()] = corrected
        self._save()

    def remove_word(self, spoken: str) -> bool:
        """Remove a word from the dictionary.

        Returns:
            True if word was removed, False if not found
        """
        key = spoken.lower()
        if key in self._corrections:
            del self._corrections[key]
            self._save()
            return True
        return False

    def get_corrections(self) -> dict[str, str]:
        """Get all corrections."""
        return self._corrections.copy()

    def apply(self, text: str) -> str:
        """Apply dictionary corrections to text.

        Performs case-insensitive matching but preserves the
        correction's capitalization.
        """
        if not self._corrections:
            return text

        result = text
        for spoken, corrected in self._corrections.items():
            # Case-insensitive word boundary match
            pattern = re.compile(rf'\b{re.escape(spoken)}\b', re.IGNORECASE)
            result = pattern.sub(corrected, result)

        return result

    def learn_from_correction(self, original: str, corrected: str) -> None:
        """Learn new words by comparing original and corrected text.

        Identifies words that were changed and adds them to the dictionary.
        """
        original_words = original.lower().split()
        corrected_words = corrected.split()

        # Simple heuristic: if a word was changed but sounds similar,
        # it's likely a spelling/capitalization correction
        if len(original_words) == len(corrected_words):
            for orig, corr in zip(original_words, corrected_words):
                if orig != corr.lower() and self._sounds_similar(orig, corr.lower()):
                    self.add_word(orig, corr)

    def _sounds_similar(self, word1: str, word2: str) -> bool:
        """Check if two words sound similar (basic heuristic)."""
        # Simple check: same first letter and similar length
        if not word1 or not word2:
            return False
        return (
            word1[0] == word2[0] and
            abs(len(word1) - len(word2)) <= 2
        )
