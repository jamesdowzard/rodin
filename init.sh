#!/bin/bash
# Whisper Flow development environment setup

set -e

echo "Setting up Whisper Flow development environment..."

# Install in editable mode
pip install -e . --quiet

# Ensure MacBook Pro Microphone is the default input
if command -v SwitchAudioSource &> /dev/null; then
    SwitchAudioSource -t input -s "MacBook Pro Microphone" 2>/dev/null || true
    echo "Audio input: $(SwitchAudioSource -c -t input)"
fi

# Set input volume
osascript -e 'set volume input volume 80' 2>/dev/null || true

# Check Ollama is running (for AI editing)
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "Ollama: Running"
else
    echo "Ollama: Not running (start with 'ollama serve' for AI editing)"
fi

# Show available commands
echo ""
echo "Ready! Available commands:"
echo "  whisper-flow              # Run with floating overlay"
echo "  whisper-flow --cli        # Run in terminal mode"
echo "  whisper-flow --benchmark  # Run performance benchmark"
echo "  whisper-flow --test TEXT  # Test AI editor"
echo ""
echo "Hotkey: Cmd+Shift+Space (hold to talk)"
