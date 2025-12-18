# Rodin

Local voice dictation with AI editing - an open source alternative to [Wispr Flow](https://wisprflow.ai).

**100% offline transcription** using [faster-whisper](https://github.com/SYSTRAN/faster-whisper). Your voice never leaves your device.

## Features

- **Local Transcription** - Whisper model runs locally via faster-whisper
- **AI Text Editing** - Cleanup with Ollama (local) or cloud APIs (OpenAI/Anthropic)
- **Personal Dictionary** - Auto-learn names, technical terms, custom vocabulary
- **Snippets** - Text expansion shortcuts (say "sig" → full signature)
- **Voice Commands** - "Delete that", "new line", "undo" and more
- **App Context Awareness** - Auto-adjusts tone based on active app (macOS)
- **Cross-Platform** - macOS and Windows with floating overlay UI
- **System-wide Hotkey** - Works in any application

## Quick Start

```bash
# Install
git clone https://github.com/jamesdowzard/rodin.git
cd rodin
pip install -e .

# Run
rodin
```

**Default hotkey**: `Cmd+Shift+Space` (Mac) or `Ctrl+Shift+Space` (Windows) - hold to talk

## Documentation

- [Installation Guide](docs/installation.md)
- [Quick Start](docs/quickstart.md)
- [Features](docs/features.md)
- [Configuration](docs/configuration.md)
- [CLI Reference](docs/cli.md)
- [Development](docs/development.md)

## Usage Examples

```bash
# Run with floating overlay (default)
rodin

# CLI mode
rodin --cli

# Enable Ollama AI editing
rodin --editor ollama

# Add custom words
rodin --add-word "acme corp" "ACME Corporation"

# Add snippets
rodin --add-snippet "sig" "Best regards, James"

# Test recording
rodin --record-test 5
```

## AI Editing Providers

| Provider | Type | Setup |
|----------|------|-------|
| None | Rule-based | No setup needed |
| Ollama | Local LLM | Install [Ollama](https://ollama.ai), run `ollama pull llama3.2:3b` |
| OpenAI | Cloud API | Set `OPENAI_API_KEY` environment variable |
| Anthropic | Cloud API | Set `ANTHROPIC_API_KEY` environment variable |

## Voice Commands

| Command | Action |
|---------|--------|
| "Delete that" | Remove last typed text |
| "Scratch that" | Same as delete |
| "New line" | Press Enter |
| "New paragraph" | Press Enter twice |
| "Undo" | Cmd+Z / Ctrl+Z |
| "Delete last word" | Delete previous word |

## Comparison with Wispr Flow

| Feature | Rodin | Wispr Flow |
|---------|--------------|------------|
| Transcription | Local (Whisper) | Cloud |
| Privacy | 100% offline option | Cloud servers |
| AI Editing | Local or Cloud | Cloud only |
| Personal Dictionary | Yes | Yes |
| Snippets | Yes | Yes |
| Voice Commands | Yes | Yes |
| App Context | Yes (macOS) | Yes |
| Price | Free & Open Source | $12/month |
| Platforms | macOS, Windows | macOS, Windows, iOS |

## Troubleshooting

### Microphone not working

1. Grant microphone permission in System Settings → Privacy & Security → Microphone
2. Check available devices: `rodin --list-devices`

### Hotkey not working

Grant accessibility permission in System Settings → Privacy & Security → Accessibility

### Overlay not visible

The floating button appears on the right side of your screen. Try `Cmd+Shift+Space` even if you can't see it.

## License

MIT License - see [LICENSE](LICENSE)

## Credits

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) - Fast Whisper implementation
- [OpenAI Whisper](https://github.com/openai/whisper) - Original Whisper model
