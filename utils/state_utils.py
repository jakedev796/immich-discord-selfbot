from collections import defaultdict
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class AssetState:
    asset_id: str
    message_id: Optional[int] = None

class StateManager:
    def __init__(self):
        self._last_fetched_assets: Dict[int, AssetState] = defaultdict(lambda: None)

    def set_last_asset(self, user_id: int, asset_id: str, message_id: Optional[int] = None) -> None:
        """Store the last fetched asset for a user."""
        self._last_fetched_assets[user_id] = AssetState(asset_id, message_id)

    def get_last_asset(self, user_id: int) -> Optional[AssetState]:
        """Get the last fetched asset for a user."""
        return self._last_fetched_assets.get(user_id)

    def clear_last_asset(self, user_id: int) -> None:
        """Clear the last fetched asset for a user."""
        if user_id in self._last_fetched_assets:
            del self._last_fetched_assets[user_id]

# Global state manager instance
state_manager = StateManager()