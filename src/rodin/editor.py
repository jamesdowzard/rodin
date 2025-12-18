"""AI-powered text editing and cleanup."""

import re
from abc import ABC, abstractmethod

import httpx

from .config import AIEditorConfig


# Filler words to remove in basic cleanup
FILLER_WORDS = [
    r"\bum+\b",
    r"\buh+\b",
    r"\blike\b(?=,|\s+,)",  # "like," but not "I like"
    r"\byou know\b",
    r"\bi mean\b",
    r"\bkind of\b",
    r"\bsort of\b",
    r"\bbasically\b",
    r"\bactually\b",  # Often filler
    r"\bliterally\b",  # Often filler
    r"\bhonestly\b",  # Often filler
]

# Preset prompts for different contexts
PRESET_PROMPTS = {
    "default": """Clean up this transcribed speech. Fix grammar, remove filler words,
add proper punctuation and capitalization. Keep the meaning and tone intact.
Return ONLY the cleaned text, nothing else.

Text: {text}""",
    "email": """Convert this transcribed speech into a professional email.
Fix grammar, structure it properly with greeting/body/closing if appropriate.
Be concise but complete. Return ONLY the email text, nothing else.

Text: {text}""",
    "commit": """Convert this transcribed speech into a concise git commit message.
Follow conventional commit format if possible (feat:, fix:, docs:, etc.).
Keep it under 72 characters for the first line. Return ONLY the commit message.

Text: {text}""",
    "notes": """Clean up this transcribed speech into well-formatted notes.
Use bullet points where appropriate. Fix grammar and organize logically.
Return ONLY the formatted notes, nothing else.

Text: {text}""",
    "code": """Convert this transcribed speech into code or a code comment.
If it's describing code, write the code. If it's explaining something,
make it a clear comment. Return ONLY the code/comment, nothing else.

Text: {text}""",
}


class TextEditor(ABC):
    """Abstract base class for text editors."""

    @abstractmethod
    def edit(self, text: str, preset: str = "default", custom_prompt: str | None = None) -> str:
        """Edit/clean up transcribed text."""
        pass


class BasicEditor(TextEditor):
    """Basic rule-based text cleanup (no AI)."""

    def edit(self, text: str, preset: str = "default", custom_prompt: str | None = None) -> str:
        """Apply basic cleanup rules."""
        result = text

        # Remove filler words
        for pattern in FILLER_WORDS:
            result = re.sub(pattern, "", result, flags=re.IGNORECASE)

        # Fix multiple spaces
        result = re.sub(r"\s+", " ", result)

        # Fix punctuation spacing
        result = re.sub(r"\s+([.,!?;:])", r"\1", result)
        result = re.sub(r"([.,!?;:])(?=[^\s])", r"\1 ", result)

        # Capitalize first letter
        result = result.strip()
        if result:
            result = result[0].upper() + result[1:]

        # Ensure ending punctuation
        if result and result[-1] not in ".!?":
            result += "."

        return result


class OllamaEditor(TextEditor):
    """Text editor using Ollama for local LLM processing."""

    def __init__(self, model: str = "llama3.2:3b", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host.rstrip("/")

    def edit(self, text: str, preset: str = "default", custom_prompt: str | None = None) -> str:
        """Edit text using Ollama."""
        prompt_template = custom_prompt or PRESET_PROMPTS.get(preset, PRESET_PROMPTS["default"])
        prompt = prompt_template.format(text=text)

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.host}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,  # Lower temperature for more consistent output
                            "num_predict": 500,
                        },
                    },
                )
                response.raise_for_status()
                return response.json()["response"].strip()

        except Exception as e:
            print(f"Ollama error: {e}, falling back to basic cleanup")
            return BasicEditor().edit(text, preset)


class OpenAIEditor(TextEditor):
    """Text editor using OpenAI API."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model

    def edit(self, text: str, preset: str = "default", custom_prompt: str | None = None) -> str:
        """Edit text using OpenAI."""
        prompt_template = custom_prompt or PRESET_PROMPTS.get(preset, PRESET_PROMPTS["default"])
        prompt = prompt_template.format(text=text)

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3,
                        "max_tokens": 500,
                    },
                )
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"].strip()

        except Exception as e:
            print(f"OpenAI error: {e}, falling back to basic cleanup")
            return BasicEditor().edit(text, preset)


class AnthropicEditor(TextEditor):
    """Text editor using Anthropic API."""

    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        self.api_key = api_key
        self.model = model

    def edit(self, text: str, preset: str = "default", custom_prompt: str | None = None) -> str:
        """Edit text using Anthropic."""
        prompt_template = custom_prompt or PRESET_PROMPTS.get(preset, PRESET_PROMPTS["default"])
        prompt = prompt_template.format(text=text)

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "max_tokens": 500,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                response.raise_for_status()
                return response.json()["content"][0]["text"].strip()

        except Exception as e:
            print(f"Anthropic error: {e}, falling back to basic cleanup")
            return BasicEditor().edit(text, preset)


def create_editor(config: AIEditorConfig, api_keys: dict | None = None) -> TextEditor:
    """Factory function to create the appropriate editor."""
    api_keys = api_keys or {}

    if not config.enabled or config.provider == "none":
        return BasicEditor()

    if config.provider == "ollama":
        return OllamaEditor(model=config.ollama_model, host=config.ollama_host)

    if config.provider == "openai":
        api_key = api_keys.get("openai")
        if not api_key:
            print("OpenAI API key not found, falling back to basic cleanup")
            return BasicEditor()
        return OpenAIEditor(api_key=api_key, model=config.openai_model)

    if config.provider == "anthropic":
        api_key = api_keys.get("anthropic")
        if not api_key:
            print("Anthropic API key not found, falling back to basic cleanup")
            return BasicEditor()
        return AnthropicEditor(api_key=api_key, model=config.anthropic_model)

    return BasicEditor()
