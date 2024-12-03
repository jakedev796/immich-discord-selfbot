import os
from typing import Dict, Any
import json
from pathlib import Path

# Ensure data directory exists
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

# Default preferences
DEFAULT_PREFERENCES = {
    "max_attempts": 50,
    "default_media_type": None,  # None means both image and video
    "min_size_bytes": None,
    "max_size_bytes": None,
    "progress_update_interval": 5,  # seconds
    "message_delete_delay": 10,  # seconds
}

class Config:
    def __init__(self):
        self.preferences_file = data_dir / "preferences.json"
        self.user_preferences: Dict[str, Dict[str, Any]] = {}
        self.load_preferences()

    def load_preferences(self) -> None:
        """Load preferences from JSON file."""
        if self.preferences_file.exists():
            try:
                with open(self.preferences_file, 'r') as f:
                    self.user_preferences = json.load(f)
            except json.JSONDecodeError:
                self.user_preferences = {}
        else:
            self.user_preferences = {}

    def save_preferences(self) -> None:
        """Save preferences to JSON file."""
        with open(self.preferences_file, 'w') as f:
            json.dump(self.user_preferences, f, indent=4)

    def get_user_preferences(self, user_id: str) -> dict:
        """Get preferences for a specific user, creating default if none exist."""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = DEFAULT_PREFERENCES.copy()
            self.save_preferences()
        return self.user_preferences[user_id]

    def update_user_preference(self, user_id: str, key: str, value: Any) -> None:
        """Update a specific preference for a user."""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = DEFAULT_PREFERENCES.copy()
        self.user_preferences[user_id][key] = value
        self.save_preferences()

    def reset_user_preferences(self, user_id: str) -> None:
        """Reset a user's preferences to default."""
        self.user_preferences[user_id] = DEFAULT_PREFERENCES.copy()
        self.save_preferences()

# Global config instance
config = Config()