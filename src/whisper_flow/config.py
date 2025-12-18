"""Configuration management for Whisper Flow."""

import json
import sys
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class HotkeyConfig(BaseModel):
    """Hotkey configuration."""

    # Default: Cmd+Shift+Space on Mac, Ctrl+Shift+Space on Windows
    modifier1: str = Field(default="cmd" if sys.platform == "darwin" else "ctrl")
    modifier2: str = Field(default="shift")
    key: str = Field(default="space")
    mode: Literal["hold", "toggle"] = Field(default="hold")  # hold-to-talk or push-to-toggle


class WhisperConfig(BaseModel):
    """Whisper model configuration."""

    model_size: Literal["tiny", "base", "small", "medium", "large-v3"] = Field(default="base")
    device: Literal["auto", "cpu", "cuda"] = Field(default="auto")
    compute_type: Literal["auto", "int8", "float16", "float32"] = Field(default="auto")
    language: str | None = Field(default=None)  # None = auto-detect


class AIEditorConfig(BaseModel):
    """AI editor configuration."""

    enabled: bool = Field(default=True)
    provider: Literal["none", "ollama", "openai", "anthropic"] = Field(default="none")

    # Ollama settings
    ollama_model: str = Field(default="llama3.2:3b")
    ollama_host: str = Field(default="http://localhost:11434")

    # Cloud API settings (keys loaded from env)
    openai_model: str = Field(default="gpt-4o-mini")
    anthropic_model: str = Field(default="claude-3-haiku-20240307")

    # Editing presets
    preset: Literal["default", "email", "commit", "notes", "code"] = Field(default="default")
    custom_prompt: str | None = Field(default=None)


class AudioConfig(BaseModel):
    """Audio recording configuration."""

    sample_rate: int = Field(default=16000)  # Whisper expects 16kHz
    channels: int = Field(default=1)  # Mono
    dtype: str = Field(default="int16")
    device: int | str | None = Field(default=None)  # None = system default, int = device index, str = device name


class UIConfig(BaseModel):
    """UI configuration."""

    show_overlay: bool = Field(default=True)
    overlay_position: Literal["top-left", "top-right", "bottom-left", "bottom-right", "center"] = (
        Field(default="top-right")
    )
    play_sounds: bool = Field(default=True)


class DictionaryConfig(BaseModel):
    """Personal dictionary configuration."""

    enabled: bool = Field(default=True)
    auto_learn: bool = Field(default=True)  # Learn from user corrections


class SnippetsConfig(BaseModel):
    """Snippets configuration."""

    enabled: bool = Field(default=True)


class VoiceCommandsConfig(BaseModel):
    """Voice commands configuration."""

    enabled: bool = Field(default=True)


class AppContextConfig(BaseModel):
    """App context awareness configuration."""

    enabled: bool = Field(default=True)
    # Per-app preset overrides (bundle ID -> preset name)
    app_presets: dict[str, str] = Field(default_factory=lambda: {
        "com.apple.mail": "email",
        "com.microsoft.Outlook": "email",
        "com.google.Chrome": "default",  # Could be anything in browser
        "com.slack.Slack": "default",
        "com.tinyspeck.slackmacgap": "default",
        "com.microsoft.VSCode": "code",
        "dev.zed.Zed": "code",
        "com.apple.Terminal": "code",
        "com.googlecode.iterm2": "code",
        "com.apple.Notes": "notes",
        "com.notion.Notion": "notes",
    })


class Settings(BaseSettings):
    """Main settings container."""

    hotkey: HotkeyConfig = Field(default_factory=HotkeyConfig)
    whisper: WhisperConfig = Field(default_factory=WhisperConfig)
    ai_editor: AIEditorConfig = Field(default_factory=AIEditorConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    dictionary: DictionaryConfig = Field(default_factory=DictionaryConfig)
    snippets: SnippetsConfig = Field(default_factory=SnippetsConfig)
    voice_commands: VoiceCommandsConfig = Field(default_factory=VoiceCommandsConfig)
    app_context: AppContextConfig = Field(default_factory=AppContextConfig)

    # API keys from environment
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


def get_config_dir() -> Path:
    """Get the configuration directory."""
    if sys.platform == "darwin":
        config_dir = Path.home() / "Library" / "Application Support" / "WhisperFlow"
    elif sys.platform == "win32":
        config_dir = Path.home() / "AppData" / "Local" / "WhisperFlow"
    else:
        config_dir = Path.home() / ".config" / "whisper-flow"

    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_path() -> Path:
    """Get the configuration file path."""
    return get_config_dir() / "config.json"


def load_settings() -> Settings:
    """Load settings from config file and environment."""
    config_path = get_config_path()

    if config_path.exists():
        with open(config_path) as f:
            data = json.load(f)
        return Settings(**data)

    return Settings()


def save_settings(settings: Settings) -> None:
    """Save settings to config file."""
    config_path = get_config_path()

    # Convert to dict, excluding env-based API keys
    data = settings.model_dump(exclude={"openai_api_key", "anthropic_api_key"})

    with open(config_path, "w") as f:
        json.dump(data, f, indent=2)
