"""Main entry point for Whisper Flow."""

import argparse
import sys

from .config import load_settings, save_settings


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Whisper Flow - Local voice dictation with AI editing"
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run in CLI mode (no menu bar)",
    )
    parser.add_argument(
        "--overlay",
        action="store_true",
        help="Run with floating overlay button (recommended)",
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List available audio input devices",
    )
    parser.add_argument(
        "--model",
        choices=["tiny", "base", "small", "medium", "large-v3"],
        help="Whisper model size",
    )
    parser.add_argument(
        "--mode",
        choices=["hold", "toggle"],
        help="Recording mode (hold-to-talk or push-to-toggle)",
    )
    parser.add_argument(
        "--editor",
        choices=["none", "ollama", "openai", "anthropic"],
        help="AI editor provider",
    )
    parser.add_argument(
        "--preset",
        choices=["default", "email", "commit", "notes", "code"],
        help="AI editor preset",
    )
    parser.add_argument(
        "--test",
        metavar="TEXT",
        help="Test the AI editor with given text (no recording)",
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run performance benchmark",
    )
    parser.add_argument(
        "--record-test",
        type=int,
        metavar="SECONDS",
        help="Record for N seconds and transcribe (test mode)",
    )

    # Dictionary management
    parser.add_argument(
        "--add-word",
        nargs=2,
        metavar=("SPOKEN", "CORRECTED"),
        help="Add a word to personal dictionary (e.g., --add-word 'john doe' 'John Doe')",
    )
    parser.add_argument(
        "--remove-word",
        metavar="SPOKEN",
        help="Remove a word from personal dictionary",
    )
    parser.add_argument(
        "--list-dictionary",
        action="store_true",
        help="List all words in personal dictionary",
    )

    # Snippet management
    parser.add_argument(
        "--add-snippet",
        nargs=2,
        metavar=("TRIGGER", "EXPANSION"),
        help="Add a snippet (e.g., --add-snippet 'sig' 'Best regards, James')",
    )
    parser.add_argument(
        "--remove-snippet",
        metavar="TRIGGER",
        help="Remove a snippet",
    )
    parser.add_argument(
        "--list-snippets",
        action="store_true",
        help="List all snippets",
    )

    args = parser.parse_args()

    # List devices and exit
    if args.list_devices:
        from .recorder import AudioRecorder

        devices = AudioRecorder.list_devices()
        print("Available audio input devices:")
        for device in devices:
            print(f"  [{device['index']}] {device['name']}")
            print(f"      Channels: {device['channels']}, Sample Rate: {device['sample_rate']}")
        return

    # Dictionary management commands
    if args.add_word:
        from .dictionary import PersonalDictionary
        dictionary = PersonalDictionary()
        spoken, corrected = args.add_word
        dictionary.add_word(spoken, corrected)
        print(f"Added: '{spoken}' → '{corrected}'")
        return

    if args.remove_word:
        from .dictionary import PersonalDictionary
        dictionary = PersonalDictionary()
        if dictionary.remove_word(args.remove_word):
            print(f"Removed: '{args.remove_word}'")
        else:
            print(f"Word not found: '{args.remove_word}'")
        return

    if args.list_dictionary:
        from .dictionary import PersonalDictionary
        dictionary = PersonalDictionary()
        corrections = dictionary.get_corrections()
        if corrections:
            print("Personal Dictionary:")
            for spoken, corrected in sorted(corrections.items()):
                print(f"  '{spoken}' → '{corrected}'")
        else:
            print("Dictionary is empty. Add words with: --add-word 'spoken' 'Corrected'")
        return

    # Snippet management commands
    if args.add_snippet:
        from .snippets import SnippetExpander
        snippets = SnippetExpander()
        trigger, expansion = args.add_snippet
        snippets.add_snippet(trigger, expansion)
        print(f"Added snippet: '{trigger}' → '{expansion[:50]}{'...' if len(expansion) > 50 else ''}'")
        return

    if args.remove_snippet:
        from .snippets import SnippetExpander
        snippets = SnippetExpander()
        if snippets.remove_snippet(args.remove_snippet):
            print(f"Removed snippet: '{args.remove_snippet}'")
        else:
            print(f"Snippet not found: '{args.remove_snippet}'")
        return

    if args.list_snippets:
        from .snippets import SnippetExpander
        snippets = SnippetExpander()
        all_snippets = snippets.list_snippets()
        if all_snippets:
            print("Snippets:")
            for trigger, expansion in sorted(all_snippets):
                preview = expansion[:50] + ('...' if len(expansion) > 50 else '')
                preview = preview.replace('\n', '\\n')
                print(f"  '{trigger}' → '{preview}'")
        else:
            print("No snippets. Add with: --add-snippet 'trigger' 'expansion text'")
        return

    # Load and potentially update settings
    settings = load_settings()

    if args.model:
        settings.whisper.model_size = args.model
        save_settings(settings)

    if args.mode:
        settings.hotkey.mode = args.mode
        save_settings(settings)

    if args.editor:
        settings.ai_editor.provider = args.editor
        settings.ai_editor.enabled = args.editor != "none"
        save_settings(settings)

    if args.preset:
        settings.ai_editor.preset = args.preset
        save_settings(settings)

    # Test mode - just test AI editor with text
    if args.test:
        run_test(settings, args.test)
        return

    # Benchmark mode
    if args.benchmark:
        run_benchmark(settings)
        return

    # Record test mode
    if args.record_test:
        run_record_test(settings, args.record_test)
        return

    # Run appropriate mode
    if args.overlay:
        run_overlay_mode(settings)
    elif args.cli:
        run_cli(settings)
    else:
        run_overlay_mode(settings)  # Default to overlay mode


def run_cli(settings) -> None:
    """Run in CLI mode without GUI."""
    from .editor import create_editor
    from .hotkey import HotkeyHandler
    from .recorder import AudioRecorder
    from .transcriber import Transcriber
    from .typer import TextTyper

    print("Whisper Flow - CLI Mode")
    print("=" * 40)

    # Initialize components
    recorder = AudioRecorder(settings.audio)
    transcriber = Transcriber(settings.whisper)
    editor = create_editor(
        settings.ai_editor,
        {
            "openai": settings.openai_api_key,
            "anthropic": settings.anthropic_api_key,
        },
    )
    typer = TextTyper()

    # Load model
    print("Loading Whisper model...")
    transcriber.load_model()

    is_recording = False
    is_processing = False

    def on_activate():
        nonlocal is_recording
        if is_processing:
            return
        is_recording = True
        print("\n🔴 Recording...")
        recorder.start()

    def on_deactivate():
        nonlocal is_recording, is_processing
        if not is_recording:
            return

        is_recording = False
        is_processing = True
        print("⏳ Processing...")

        try:
            audio_data = recorder.stop()

            if not audio_data:
                print("No audio recorded")
                return

            text = transcriber.transcribe(audio_data)

            if not text:
                print("No speech detected")
                return

            print(f"📝 Transcribed: {text}")

            if settings.ai_editor.enabled:
                text = editor.edit(
                    text,
                    preset=settings.ai_editor.preset,
                    custom_prompt=settings.ai_editor.custom_prompt,
                )
                print(f"✨ Edited: {text}")

            typer.type_text(text)
            print("✅ Text inserted")

        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            is_processing = False

    # Set up hotkey handler
    hotkey = HotkeyHandler(
        settings.hotkey,
        on_activate=on_activate,
        on_deactivate=on_deactivate,
    )
    hotkey.start()

    mod1 = "Cmd" if settings.hotkey.modifier1 == "cmd" else settings.hotkey.modifier1.title()
    mod2 = settings.hotkey.modifier2.title()
    key = settings.hotkey.key.title()

    print(f"\nReady! Press {mod1}+{mod2}+{key} to record")
    print("Press Ctrl+C to quit\n")

    try:
        import time

        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        hotkey.stop()


def run_overlay_mode(settings) -> None:
    """Run with floating overlay button."""
    if sys.platform == "darwin":
        from .ui.overlay import run_overlay

        run_overlay(settings)
    else:
        print("Overlay mode only available on macOS, running in CLI mode")
        run_cli(settings)


def run_gui(settings) -> None:
    """Run with GUI (menu bar on macOS)."""
    if sys.platform == "darwin":
        from .ui.menubar import run_menubar_app

        run_menubar_app(settings)
    else:
        # Fall back to CLI mode on non-macOS
        print("GUI mode not available on this platform, running in CLI mode")
        run_cli(settings)


def run_test(settings, text: str) -> None:
    """Test the AI editor with given text."""
    import time

    from .editor import BasicEditor, create_editor

    print("Whisper Flow - Editor Test")
    print("=" * 40)
    print(f"Input: {text}")
    print()

    # Test basic editor
    print("Basic Editor (rule-based):")
    start = time.time()
    basic = BasicEditor()
    result = basic.edit(text)
    elapsed = time.time() - start
    print(f"  Result: {result}")
    print(f"  Time: {elapsed:.3f}s")
    print()

    # Test configured editor
    if settings.ai_editor.enabled and settings.ai_editor.provider != "none":
        print(f"AI Editor ({settings.ai_editor.provider}):")
        editor = create_editor(
            settings.ai_editor,
            {
                "openai": settings.openai_api_key,
                "anthropic": settings.anthropic_api_key,
            },
        )
        start = time.time()
        result = editor.edit(text, preset=settings.ai_editor.preset)
        elapsed = time.time() - start
        print(f"  Preset: {settings.ai_editor.preset}")
        print(f"  Result: {result}")
        print(f"  Time: {elapsed:.2f}s")
    else:
        print("AI Editor: Disabled")
        print("  Enable with: whisper-flow --editor ollama")


def run_benchmark(settings) -> None:
    """Run performance benchmark."""
    import io
    import time
    import wave

    import numpy as np

    from .editor import BasicEditor, create_editor
    from .transcriber import Transcriber

    print("Whisper Flow - Performance Benchmark")
    print("=" * 40)

    # Generate test audio (3 seconds)
    sample_rate = 16000
    duration = 3
    audio = np.zeros(int(sample_rate * duration), dtype=np.int16)
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(audio.tobytes())
    test_audio = wav_buffer.getvalue()

    # Test Whisper
    print(f"\n1. Whisper Model ({settings.whisper.model_size})")
    transcriber = Transcriber(settings.whisper)

    start = time.time()
    transcriber.load_model()
    load_time = time.time() - start
    print(f"   Load time: {load_time:.2f}s")

    start = time.time()
    transcriber.transcribe(test_audio)
    transcribe_time = time.time() - start
    print(f"   Transcribe (3s silence): {transcribe_time:.2f}s")

    # Test Basic Editor
    test_text = "Um so like I was thinking that we should uh probably update the database schema you know to handle the new user fields"
    print("\n2. Basic Editor (rule-based)")
    start = time.time()
    BasicEditor().edit(test_text)
    basic_time = time.time() - start
    print(f"   Time: {basic_time:.4f}s")

    # Test AI Editor
    if settings.ai_editor.enabled and settings.ai_editor.provider != "none":
        print(f"\n3. AI Editor ({settings.ai_editor.provider})")
        editor = create_editor(
            settings.ai_editor,
            {
                "openai": settings.openai_api_key,
                "anthropic": settings.anthropic_api_key,
            },
        )
        start = time.time()
        editor.edit(test_text)
        ai_time = time.time() - start
        print(f"   Time: {ai_time:.2f}s")
    else:
        ai_time = 0
        print("\n3. AI Editor: Disabled")

    # Summary
    print("\n" + "=" * 40)
    print("Summary (estimated for 3s speech):")
    total = transcribe_time + (ai_time if settings.ai_editor.enabled else basic_time)
    print(f"   Total pipeline: ~{total:.2f}s")
    if ai_time > 2:
        print("   ⚠️  AI editing is slow. Consider:")
        print("      - Using --editor none for basic cleanup")
        print("      - Using a faster Ollama model")
        print("      - Using cloud APIs (OpenAI/Anthropic)")


def run_record_test(settings, seconds: int) -> None:
    """Record for N seconds and transcribe."""
    import time

    from .editor import create_editor
    from .recorder import AudioRecorder
    from .transcriber import Transcriber

    print(f"Whisper Flow - Record Test ({seconds}s)")
    print("=" * 40)

    recorder = AudioRecorder(settings.audio)
    transcriber = Transcriber(settings.whisper)
    editor = create_editor(
        settings.ai_editor,
        {
            "openai": settings.openai_api_key,
            "anthropic": settings.anthropic_api_key,
        },
    )

    print("Loading model...")
    transcriber.load_model()

    print(f"\n🎤 Recording for {seconds} seconds... SPEAK NOW!")
    recorder.start()
    time.sleep(seconds)
    audio_data = recorder.stop()
    print("Recording complete.")

    print("\n⏳ Transcribing...")
    start = time.time()
    text = transcriber.transcribe(audio_data)
    transcribe_time = time.time() - start

    print(f"\n📝 Raw transcription ({transcribe_time:.2f}s):")
    print(f"   {text or '(no speech detected)'}")

    if text and settings.ai_editor.enabled:
        print(f"\n✨ AI edited ({settings.ai_editor.provider}):")
        start = time.time()
        edited = editor.edit(text, preset=settings.ai_editor.preset)
        edit_time = time.time() - start
        print(f"   {edited}")
        print(f"   (took {edit_time:.2f}s)")


if __name__ == "__main__":
    main()
