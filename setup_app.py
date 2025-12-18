"""py2app setup script for Rodin.app"""

from setuptools import setup

APP = ['src/rodin/main.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'plist': {
        'CFBundleName': 'Rodin',
        'CFBundleDisplayName': 'Rodin',
        'CFBundleIdentifier': 'com.jamesdowzard.rodin',
        'CFBundleVersion': '0.1.0',
        'CFBundleShortVersionString': '0.1.0',
        'LSMinimumSystemVersion': '12.0',
        'LSUIElement': True,  # Menu bar app (no dock icon)
        'NSMicrophoneUsageDescription': 'Rodin needs microphone access to transcribe your voice.',
        'NSAppleEventsUsageDescription': 'Rodin needs accessibility access to type transcribed text.',
    },
    'packages': [
        'rodin',
        'faster_whisper',
        'ctranslate2',
        'sounddevice',
        'pynput',
        'httpx',
        'pydantic',
        'pydantic_settings',
    ],
}

setup(
    app=APP,
    name='Rodin',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
