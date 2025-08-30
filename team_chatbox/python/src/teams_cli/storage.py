"""Local storage utilities for Teams CLI."""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any


def get_app_data_dir() -> Path:
    """Get the application data directory for storing files."""
    if os.name == 'nt':  # Windows
        # Use %LOCALAPPDATA%\teams-cli
        local_app_data = os.getenv('LOCALAPPDATA')
        if local_app_data:
            return Path(local_app_data) / "teams-cli"
    
    # Fallback for other platforms
    home = Path.home()
    return home / ".teams-cli"


def get_delta_file_path(chat_id: str) -> Path:
    """Get the path to the delta link file for a specific chat."""
    app_dir = get_app_data_dir()
    app_dir.mkdir(parents=True, exist_ok=True)
    
    # Sanitize chat_id for filename
    safe_chat_id = "".join(c for c in chat_id if c.isalnum() or c in ('-', '_', '.'))
    return app_dir / f"delta-{safe_chat_id}.txt"


def save_delta_link(chat_id: str, delta_link: str) -> None:
    """Save a delta link for a specific chat."""
    try:
        delta_file = get_delta_file_path(chat_id)
        with open(delta_file, 'w', encoding='utf-8') as f:
            f.write(delta_link.strip())
    except Exception as e:
        # Don't fail the operation if we can't save delta link
        print(f"Warning: Could not save delta link: {e}")


def load_delta_link(chat_id: str) -> Optional[str]:
    """Load the delta link for a specific chat."""
    try:
        delta_file = get_delta_file_path(chat_id)
        if delta_file.exists():
            with open(delta_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
    except Exception:
        # Ignore errors when loading delta link
        pass
    return None


def save_app_settings(settings: Dict[str, Any]) -> None:
    """Save application settings to local storage."""
    try:
        app_dir = get_app_data_dir()
        app_dir.mkdir(parents=True, exist_ok=True)
        
        settings_file = app_dir / "settings.json"
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save settings: {e}")


def load_app_settings() -> Dict[str, Any]:
    """Load application settings from local storage."""
    try:
        app_dir = get_app_data_dir()
        settings_file = app_dir / "settings.json"
        
        if settings_file.exists():
            with open(settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        # Return empty dict if settings can't be loaded
        pass
    
    return {}


def clear_app_data() -> None:
    """Clear all application data (for testing or reset purposes)."""
    import shutil
    
    try:
        app_dir = get_app_data_dir()
        if app_dir.exists():
            shutil.rmtree(app_dir)
    except Exception as e:
        print(f"Warning: Could not clear app data: {e}")