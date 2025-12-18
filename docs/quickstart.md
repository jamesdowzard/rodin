# Quick Start

## Starting Rodin

```bash
# Default: floating overlay mode
rodin

# CLI mode (terminal output)
rodin --cli

# Menu bar mode (macOS only)
rodin --menubar
```

## Basic Usage

1. **Start the app** - Run `rodin`
2. **Look for the mic button** - Floating on the right side of your screen
3. **Hold the hotkey** - Cmd+Shift+Space (Mac) or Ctrl+Shift+Space (Windows)
4. **Speak** - Talk naturally
5. **Release** - Text appears at your cursor

## Hotkey Modes

### Hold-to-Talk (Default)
- Hold the hotkey while speaking
- Release to transcribe and insert

### Toggle Mode
- Press once to start recording
- Press again to stop and transcribe

```bash
# Switch to toggle mode
rodin --mode toggle
```

## Adding Custom Words

Teach Rodin your vocabulary:

```bash
# Add a name
rodin --add-word "john smith" "John Smith"

# Add a company name
rodin --add-word "acme corp" "ACME Corporation"

# Add a technical term
rodin --add-word "kubernetes" "Kubernetes"

# View all words
rodin --list-dictionary
```

## Adding Snippets

Create text shortcuts:

```bash
# Email signature
rodin --add-snippet "sig" "Best regards,
James"

# Meeting link
rodin --add-snippet "zoom" "https://zoom.us/j/123456789"

# Code template
rodin --add-snippet "pydef" "def function_name():
    pass"

# View all snippets
rodin --list-snippets
```

## Voice Commands

Say these commands instead of typing:

| Command | Action |
|---------|--------|
| "Delete that" | Remove last transcribed text |
| "Scratch that" | Same as delete that |
| "New line" | Press Enter |
| "New paragraph" | Press Enter twice |
| "Undo" | Cmd+Z / Ctrl+Z |
| "Delete last word" | Delete previous word |
| "Delete last 3 words" | Delete previous 3 words |

## Enabling AI Editing

```bash
# Use local Ollama
rodin --editor ollama

# Use OpenAI (requires API key)
export OPENAI_API_KEY="sk-..."
rodin --editor openai

# Use Anthropic (requires API key)
export ANTHROPIC_API_KEY="sk-ant-..."
rodin --editor anthropic

# Disable AI editing
rodin --editor none
```

## AI Presets

```bash
# Default - general cleanup
rodin --preset default

# Email - professional formatting
rodin --preset email

# Code - code/comments formatting
rodin --preset code

# Notes - bullet point style
rodin --preset notes

# Commit - git commit message style
rodin --preset commit
```
