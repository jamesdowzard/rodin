# Features

## Core Features

### Local Speech-to-Text

Rodin uses [faster-whisper](https://github.com/SYSTRAN/faster-whisper), an optimised implementation of OpenAI's Whisper model.

- **100% offline** - No audio sent to the cloud
- **Multiple model sizes** - tiny, base, small, medium, large-v3
- **Fast transcription** - ~1 second for 3 seconds of audio (base model)
- **Automatic language detection** - Or specify a language

```bash
# Use a larger model for better accuracy
rodin --model small

# Use tiny for faster results
rodin --model tiny
```

### AI Text Editing

Clean up transcriptions with AI:

- Remove filler words (um, uh, like, you know)
- Fix punctuation and capitalisation
- Course correction ("meet at 2pm, actually make it 4pm" → "meet at 4pm")
- Tone adjustment based on context

**Providers:**
- **Ollama** - Local LLM (recommended for privacy)
- **OpenAI** - GPT-4o-mini
- **Anthropic** - Claude 3 Haiku
- **None** - Basic rule-based cleanup only

### Personal Dictionary

Automatically learn and correct:

- Names (people, companies, products)
- Technical terms
- Industry jargon
- Common misspellings

**How it works:**
1. Add words manually: `rodin --add-word "spoken" "Corrected"`
2. Auto-learn from corrections (when AI editing fixes a word)

**Storage:** `~/Library/Application Support/Rodin/dictionary.json` (macOS)

### Snippets

Text expansion for frequently used phrases:

```bash
# Add snippets
rodin --add-snippet "addr" "123 Main St, Sydney NSW 2000"
rodin --add-snippet "standup" "Yesterday:
-

Today:
-

Blockers:
- "
```

Say the trigger word and it expands to the full text.

### Voice Commands

Hands-free editing commands:

| Command | Action | Notes |
|---------|--------|-------|
| "Delete that" | Delete last typed text | Removes what you just dictated |
| "Scratch that" | Same as delete that | |
| "New line" | Insert line break | Press Enter once |
| "New paragraph" | Insert paragraph break | Press Enter twice |
| "Undo" | Undo last action | Cmd+Z / Ctrl+Z |
| "Backspace" | Delete one character | |
| "Delete last word" | Delete previous word | Option+Backspace / Ctrl+Backspace |
| "Delete last N words" | Delete N words | e.g., "delete last 3 words" |

### App Context Awareness (macOS)

Automatically adjusts AI editing based on the active application:

| Application | Preset | Tone |
|-------------|--------|------|
| Mail, Outlook | email | Professional, formal |
| VS Code, Xcode | code | Technical, precise |
| Notes, Notion | notes | Bullet points, concise |
| Slack, Messages | default | Casual |
| Terminal, iTerm | code | Command-focused |

**Customise per-app presets** in config.json:
```json
{
  "app_context": {
    "app_presets": {
      "com.apple.mail": "email",
      "com.slack.Slack": "default"
    }
  }
}
```

## UI Modes

### Floating Overlay (Default)

A small floating mic button on the right side of your screen.

- **Click** to toggle recording
- **Drag** to reposition
- **Visual feedback:**
  - 🎤 Ready
  - 🔴 Recording
  - ⏳ Processing

### CLI Mode

Terminal-based interface with text output.

```bash
rodin --cli
```

### Menu Bar Mode (macOS)

System tray app with dropdown menu.

```bash
rodin --menubar
```

## Transcription Logging

All transcriptions are logged to:
- **macOS:** `~/Library/Application Support/Rodin/transcriptions.log`
- **Windows:** `%LOCALAPPDATA%\Rodin\transcriptions.log`

Log format:
```
=== 2024-12-18 12:18:35 (4.9s) ===
Raw: Hello world, I'm just testing this
Edited: Hello world, I'm just testing this.
```
