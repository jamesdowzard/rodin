# CLI Reference

## Basic Commands

```bash
rodin [OPTIONS]
```

## Mode Options

| Option | Description |
|--------|-------------|
| `--overlay` | Run with floating overlay button (default) |
| `--cli` | Run in CLI mode (terminal output) |
| `--menubar` | Run with menu bar app (macOS only) |

## Configuration Options

| Option | Values | Description |
|--------|--------|-------------|
| `--model` | tiny, base, small, medium, large-v3 | Whisper model size |
| `--mode` | hold, toggle, wispr | Recording mode (see below) |
| `--editor` | none, ollama, openai, anthropic | AI editor provider |
| `--preset` | default, email, commit, notes, code | AI editing preset |

### Recording Modes

| Mode | Behavior |
|------|----------|
| `hold` | Hold hotkey to record, release to stop (default) |
| `toggle` | Press once to start, press again to stop |
| `wispr` | Hold to talk OR double-tap for continuous mode (tap to stop) |

## Testing & Debugging

| Option | Description |
|--------|-------------|
| `--list-devices` | List available audio input devices |
| `--test TEXT` | Test AI editor with given text |
| `--benchmark` | Run performance benchmark |
| `--record-test N` | Record for N seconds and transcribe |

## Dictionary Management

| Option | Description |
|--------|-------------|
| `--add-word SPOKEN CORRECTED` | Add word to dictionary |
| `--remove-word SPOKEN` | Remove word from dictionary |
| `--list-dictionary` | List all dictionary entries |

## Snippet Management

| Option | Description |
|--------|-------------|
| `--add-snippet TRIGGER EXPANSION` | Add a snippet |
| `--remove-snippet TRIGGER` | Remove a snippet |
| `--list-snippets` | List all snippets |

## Examples

### Basic Usage

```bash
# Start with overlay
rodin

# Start in CLI mode
rodin --cli

# Use a larger model
rodin --model small

# Enable Ollama editing
rodin --editor ollama --preset email
```

### Dictionary Operations

```bash
# Add your name
rodin --add-word "james dowzard" "James Dowzard"

# Add company name
rodin --add-word "jhg" "John Holland Group"

# View dictionary
rodin --list-dictionary

# Remove entry
rodin --remove-word "jhg"
```

### Snippet Operations

```bash
# Add email signature
rodin --add-snippet "sig" "Best regards,
James Dowzard
Senior Developer"

# Add meeting template
rodin --add-snippet "standup" "Yesterday:
-

Today:
-

Blockers:
- None"

# View snippets
rodin --list-snippets

# Remove snippet
rodin --remove-snippet "sig"
```

### Testing

```bash
# List audio devices to find microphone
rodin --list-devices

# Test 5-second recording
rodin --record-test 5

# Test AI editor
rodin --test "um like I was thinking we should uh update the code"

# Run benchmark
rodin --benchmark
```

### Configuration via CLI

```bash
# Change model (persisted to config)
rodin --model medium

# Change mode (persisted)
rodin --mode toggle

# Change editor (persisted)
rodin --editor ollama

# Change preset (persisted)
rodin --preset email
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (see stderr for details) |
