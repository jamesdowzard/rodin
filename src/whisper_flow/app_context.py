"""App context awareness for macOS."""

import sys
from typing import Literal

if sys.platform == "darwin":
    from AppKit import NSWorkspace


def get_frontmost_app() -> str | None:
    """Get the bundle identifier of the frontmost application.

    Returns:
        Bundle identifier string (e.g., 'com.apple.mail') or None if not available.
    """
    if sys.platform != "darwin":
        return None

    try:
        workspace = NSWorkspace.sharedWorkspace()
        active_app = workspace.frontmostApplication()
        if active_app:
            return active_app.bundleIdentifier()
    except Exception:
        pass

    return None


def get_frontmost_app_name() -> str | None:
    """Get the name of the frontmost application.

    Returns:
        Application name (e.g., 'Mail') or None if not available.
    """
    if sys.platform != "darwin":
        return None

    try:
        workspace = NSWorkspace.sharedWorkspace()
        active_app = workspace.frontmostApplication()
        if active_app:
            return active_app.localizedName()
    except Exception:
        pass

    return None


class AppContextManager:
    """Manages app-specific settings based on the frontmost application."""

    def __init__(self, app_presets: dict[str, str] | None = None):
        """Initialize with app preset mappings.

        Args:
            app_presets: Dict mapping bundle IDs to preset names
        """
        self._app_presets = app_presets or {}

    def get_preset_for_app(
        self,
        bundle_id: str | None,
        default: Literal["default", "email", "commit", "notes", "code"] = "default"
    ) -> str:
        """Get the AI editor preset for an app.

        Args:
            bundle_id: The app's bundle identifier
            default: Default preset if app not in mappings

        Returns:
            Preset name to use for AI editing
        """
        if bundle_id and bundle_id in self._app_presets:
            return self._app_presets[bundle_id]
        return default

    def get_context(self) -> dict:
        """Get current app context information.

        Returns:
            Dict with app context info including bundle_id, name, and suggested preset
        """
        bundle_id = get_frontmost_app()
        name = get_frontmost_app_name()
        preset = self.get_preset_for_app(bundle_id)

        return {
            "bundle_id": bundle_id,
            "name": name,
            "preset": preset,
        }

    def is_code_editor(self, bundle_id: str | None) -> bool:
        """Check if the app is a code editor."""
        if not bundle_id:
            return False

        code_editors = {
            "com.microsoft.VSCode",
            "com.microsoft.VSCodeInsiders",
            "dev.zed.Zed",
            "com.sublimetext.4",
            "com.apple.dt.Xcode",
            "com.jetbrains.intellij",
            "com.jetbrains.pycharm",
            "com.cursor.Cursor",
            "io.windsurf.Windsurf",
        }
        return bundle_id in code_editors

    def is_terminal(self, bundle_id: str | None) -> bool:
        """Check if the app is a terminal."""
        if not bundle_id:
            return False

        terminals = {
            "com.apple.Terminal",
            "com.googlecode.iterm2",
            "io.warp.Warp",
            "co.zeit.hyper",
            "com.github.wez.wezterm",
        }
        return bundle_id in terminals

    def is_email_client(self, bundle_id: str | None) -> bool:
        """Check if the app is an email client."""
        if not bundle_id:
            return False

        email_clients = {
            "com.apple.mail",
            "com.microsoft.Outlook",
            "com.readdle.smartemail-Mac",
            "com.google.Gmail",
        }
        return bundle_id in email_clients
