import os
import sys

APP_NAME = "MailSorter"

_active_profile: str | None = None


def get_app_root_dir() -> str:
    """Return the top-level app directory (%APPDATA%/MailSorter)."""
    base = os.environ.get("APPDATA")
    if not base:
        base = os.path.expanduser("~")
    root = os.path.join(base, APP_NAME)
    os.makedirs(root, exist_ok=True)
    return root


def set_active_profile(profile_name: str) -> None:
    """Set the active user profile. Must be called before get_data_file()."""
    global _active_profile
    _active_profile = profile_name
    os.makedirs(get_app_data_dir(), exist_ok=True)


def get_active_profile() -> str | None:
    return _active_profile


def list_profiles() -> list[str]:
    """Return sorted list of existing profile folder names."""
    root = get_app_root_dir()
    profiles = []
    for entry in os.scandir(root):
        if entry.is_dir():
            profiles.append(entry.name)
    profiles.sort(key=str.lower)
    return profiles


def get_app_data_dir() -> str:
    """Return the active profile's data directory."""
    root = get_app_root_dir()
    if _active_profile:
        app_dir = os.path.join(root, _active_profile)
    else:
        app_dir = root
    os.makedirs(app_dir, exist_ok=True)
    return app_dir


def get_data_file(filename: str) -> str:
    return os.path.join(get_app_data_dir(), filename)


def get_resource_file(filename: str) -> str:
    if getattr(sys, "frozen", False):
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, filename)
