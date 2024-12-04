import os
from typing import Dict, Any
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Ensure data directory exists
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

# Discord upload limits by account type (in bytes)
DISCORD_UPLOAD_LIMITS = {
    'basic': 25 * 1_000_000,      # 25MB
    'nitro_basic': 50 * 1_000_000, # 50MB
    'nitro': 500 * 1_000_000       # 500MB
}

# Default preferences
DEFAULT_PREFERENCES = {
    "max_attempts": 50,
    "default_media_type": None,  # None means both image and video
    "min_size_bytes": None,
    "max_size_bytes": DISCORD_UPLOAD_LIMITS['basic'],  # Default to basic Discord limit
    "progress_update_interval": 5,  # seconds
    "message_delete_delay": 10,  # seconds
    "account_type": "basic"  # can be 'basic', 'nitro_basic', or 'nitro'
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
                    loaded_prefs = json.load(f)

                    # Only update missing keys, don't overwrite existing ones
                    for user_id, prefs in loaded_prefs.items():
                        if user_id not in self.user_preferences:
                            self.user_preferences[user_id] = {}

                        # First, copy all existing preferences
                        for key, value in prefs.items():
                            self.user_preferences[user_id][key] = value

                        # Then, only add missing default keys
                        for key, value in DEFAULT_PREFERENCES.items():
                            if key not in self.user_preferences[user_id]:
                                logger.info(f"Adding missing default preference '{key}' for user {user_id}")
                                self.user_preferences[user_id][key] = value

                    # Only save if we added missing defaults
                    if self.user_preferences != loaded_prefs:
                        self.save_preferences()

            except json.JSONDecodeError as e:
                logger.error(f"Error loading preferences: {e}")
                self.user_preferences = {}
        else:
            self.user_preferences = {}

    def save_preferences(self) -> None:
        """Save preferences to JSON file."""
        try:
            with open(self.preferences_file, 'w') as f:
                json.dump(self.user_preferences, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving preferences: {e}")

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

        # Special handling for account type updates
        if key == "account_type" and value in DISCORD_UPLOAD_LIMITS:
            self.user_preferences[user_id]["max_size_bytes"] = DISCORD_UPLOAD_LIMITS[value]
            self.user_preferences[user_id][key] = value
        else:
            self.user_preferences[user_id][key] = value

        self.save_preferences()

    def reset_user_preferences(self, user_id: str) -> None:
        """Reset a user's preferences to default."""
        self.user_preferences[user_id] = DEFAULT_PREFERENCES.copy()
        self.save_preferences()

    def get_file_size_limit(self, user_id: str) -> int:
        """Get the file size limit for a user based on their account type."""
        prefs = self.get_user_preferences(user_id)
        account_type = prefs.get('account_type', 'basic')
        return DISCORD_UPLOAD_LIMITS[account_type]

# Global config instance
config = Config()