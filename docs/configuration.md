# Configuration

## Config File Location

- **macOS:** `~/Library/Application Support/Rodin/config.json`
- **Windows:** `%LOCALAPPDATA%\Rodin\config.json`

## Full Configuration Reference

```json
{
  "hotkey": {
    "modifier1": "cmd",
    "modifier2": "shift",
    "key": "space",
    "mode": "hold"
  },
  "whisper": {
    "model_size": "base",
    "device": "auto",
    "compute_type": "auto",
    "language": null
  },
  "ai_editor": {
    "enabled": true,
    "provider": "ollama",
    "ollama_model": "llama3.2:3b",
    "ollama_host": "http://localhost:11434",
    "openai_model": "gpt-4o-mini",
    "anthropic_model": "claude-3-haiku-20240307",
    "preset": "default",
    "custom_prompt": null
  },
  "audio": {
    "sample_rate": 16000,
    "channels": 1,
    "dtype": "int16",
    "device": null
  },
  "ui": {
    "show_overlay": true,
    "overlay_position": "top-right",
    "play_sounds": true
  },
  "dictionary": {
    "enabled": true,
    "auto_learn": true
  },
  "snippets": {
    "enabled": true
  },
  "voice_commands": {
    "enabled": true
  },
  "app_context": {
    "enabled": true,
    "app_presets": {
      "com.apple.mail": "email",
      "com.microsoft.Outlook": "email",
      "com.microsoft.VSCode": "code",
      "com.apple.Terminal": "code",
      "com.apple.Notes": "notes"
    }
  }
}
```

## Configuration Sections

### Hotkey

| Setting | Description | Default |
|---------|-------------|---------|
| `modifier1` | First modifier key | `cmd` (Mac) / `ctrl` (Windows) |
| `modifier2` | Second modifier key | `shift` |
| `key` | Main key | `space` |
| `mode` | `hold` or `toggle` | `hold` |

### Whisper

| Setting | Description | Default |
|---------|-------------|---------|
| `model_size` | tiny, base, small, medium, large-v3 | `base` |
| `device` | auto, cpu, cuda | `auto` |
| `compute_type` | auto, int8, float16, float32 | `auto` |
| `language` | ISO code or null for auto | `null` |

### AI Editor

| Setting | Description | Default |
|---------|-------------|---------|
| `enabled` | Enable AI editing | `true` |
| `provider` | none, ollama, openai, anthropic | `none` |
| `ollama_model` | Ollama model name | `llama3.2:3b` |
| `ollama_host` | Ollama server URL | `http://localhost:11434` |
| `preset` | default, email, commit, notes, code | `default` |
| `custom_prompt` | Custom editing prompt | `null` |

### Audio

| Setting | Description | Default |
|---------|-------------|---------|
| `sample_rate` | Sample rate in Hz | `16000` |
| `channels` | Number of channels | `1` |
| `device` | Device index, name, or null | `null` |

### Dictionary

| Setting | Description | Default |
|---------|-------------|---------|
| `enabled` | Enable dictionary corrections | `true` |
| `auto_learn` | Learn from AI corrections | `true` |

### App Context (macOS only)

| Setting | Description | Default |
|---------|-------------|---------|
| `enabled` | Enable app-aware presets | `true` |
| `app_presets` | Bundle ID → preset mapping | (see above) |

## Environment Variables

For API keys, use environment variables or a `.env` file:

```bash
# .env file in project root or home directory
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

## Data Files

| File | Description |
|------|-------------|
| `config.json` | Main configuration |
| `dictionary.json` | Personal dictionary words |
| `snippets.json` | Text snippets |
| `transcriptions.log` | Transcription history |
| `models/` | Downloaded Whisper models |
