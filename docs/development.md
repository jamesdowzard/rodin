# Development Guide

## Project Structure

```
rodin/
├── src/rodin/
│   ├── __init__.py          # Package init
│   ├── main.py              # CLI entry point
│   ├── config.py            # Configuration (Pydantic)
│   ├── recorder.py          # Audio recording (sounddevice)
│   ├── transcriber.py       # Whisper transcription
│   ├── editor.py            # AI text editing
│   ├── typer.py             # Text insertion (pynput)
│   ├── hotkey.py            # Global hotkeys (pynput)
│   ├── dictionary.py        # Personal dictionary
│   ├── snippets.py          # Text snippets
│   ├── voice_commands.py    # Voice command processing
│   ├── app_context.py       # App context awareness (macOS)
│   └── ui/
│       ├── __init__.py
│       ├── overlay.py       # macOS overlay (PyObjC)
│       ├── overlay_win.py   # Windows overlay (tkinter)
│       └── menubar.py       # macOS menu bar (rumps)
├── docs/                    # Documentation
├── pyproject.toml           # Package configuration
└── README.md
```

## Setting Up Development Environment

```bash
# Clone repo
git clone https://github.com/jamesdowzard/rodin.git
cd rodin

# Create virtual environment (optional)
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install in editable mode
pip install -e .

# Run development init script (macOS)
./init.sh
```

## Key Dependencies

| Package | Purpose |
|---------|---------|
| faster-whisper | Local Whisper transcription |
| sounddevice | Audio recording |
| pynput | Keyboard hotkeys and typing |
| pydantic | Configuration management |
| httpx | HTTP client for APIs |
| pyobjc (macOS) | Native macOS UI |
| rumps (macOS) | Menu bar app |

## Architecture

### Pipeline Flow

```
Audio Input
    ↓
AudioRecorder.start() / .stop()
    ↓
Transcriber.transcribe(audio_data)
    ↓
PersonalDictionary.apply(text)
    ↓
VoiceCommandProcessor.detect_command(text)
    ↓ (if not a command)
AppContextManager.get_preset_for_app()
    ↓
TextEditor.edit(text, preset)
    ↓
SnippetExpander.expand(text)
    ↓
TextTyper.type_text(text)
```

### Adding a New Feature

1. **Create module** in `src/rodin/`
2. **Add config class** in `config.py` (Pydantic model)
3. **Add to Settings** class in `config.py`
4. **Integrate into pipeline** in `overlay.py` and `main.py`
5. **Add CLI args** in `main.py` if needed
6. **Update documentation**

### Adding a New AI Editor

1. Create class inheriting from `TextEditor` in `editor.py`
2. Implement `edit(text, preset, custom_prompt)` method
3. Add to `create_editor()` factory function
4. Add provider option to `AIEditorConfig`

### Adding a New Voice Command

1. Add pattern to `VOICE_COMMANDS` in `voice_commands.py`
2. Add handler in `execute_command()` method
3. Add any needed methods to `typer.py`

## Testing

```bash
# Test transcription
rodin --record-test 3

# Test AI editor
rodin --test "test text here"

# Test specific components
python -c "from rodin.dictionary import PersonalDictionary; ..."
```

## Debugging

### Enable verbose output

The overlay prints to stdout/stderr. Run from terminal to see output:

```bash
python -m rodin.main --overlay
```

### Check transcription log

```bash
# macOS
cat ~/Library/Application\ Support/Rodin/transcriptions.log

# Windows
type %LOCALAPPDATA%\Rodin\transcriptions.log
```

### Audio issues

```bash
# List available devices
rodin --list-devices

# Test specific device
# Edit config.json: "audio": {"device": 0}
```

## Platform-Specific Notes

### macOS

- Overlay uses PyObjC for native window
- App context uses NSWorkspace to detect frontmost app
- Requires Accessibility permissions for text insertion

### Windows

- Overlay uses tkinter (built into Python)
- No app context awareness (not implemented)
- May need to run as administrator for some apps

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Test on your platform
5. Submit a pull request

## Release Checklist

1. Update version in `pyproject.toml`
2. Update CHANGELOG
3. Test on macOS and Windows
4. Create git tag
5. Push to GitHub
