# Installation

## Requirements

- Python 3.11 or later
- macOS 12+ or Windows 10/11
- Microphone access

## macOS Installation

```bash
# Clone the repository
git clone https://github.com/jamesdowzard/rodin.git
cd rodin

# Install in editable mode
pip install -e .

# Run the overlay
rodin
```

### macOS Permissions

You'll need to grant microphone and accessibility permissions:

1. **Microphone**: System Settings → Privacy & Security → Microphone → Enable for Terminal/iTerm
2. **Accessibility**: System Settings → Privacy & Security → Accessibility → Enable for Terminal/iTerm (required for text insertion)

## Windows Installation

```powershell
# Clone the repository
git clone https://github.com/jamesdowzard/rodin.git
cd rodin

# Install with Python 3.11 (recommended)
& "C:\Program Files\Python311\python.exe" -m pip install -e .

# Run the overlay
& "C:\Program Files\Python311\python.exe" -m rodin.main --overlay
```

### Windows Notes

- Python 3.14 may have compatibility issues with some dependencies
- Python 3.11 or 3.12 recommended for best compatibility
- No admin rights required

## Optional: Ollama for AI Editing

For local AI-powered text cleanup:

```bash
# Install Ollama (macOS)
brew install ollama

# Or download from https://ollama.ai

# Start Ollama server
ollama serve

# Pull a model (in another terminal)
ollama pull llama3.2:3b
```

Then enable in Rodin:
```bash
rodin --editor ollama
```

## Verifying Installation

```bash
# List audio devices
rodin --list-devices

# Run a quick test
rodin --record-test 3

# Test AI editor
rodin --test "um like hello world you know"
```
