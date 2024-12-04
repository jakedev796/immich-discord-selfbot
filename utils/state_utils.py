from collections import defaultdict
from typing import Dict, Optional, Set
from dataclasses import dataclass
import discord
import logging

logger = logging.getLogger(__name__)

@dataclass
class AssetState:
    asset_id: str
    message_id: Optional[int] = None

@dataclass
class JobState:
    should_cancel: bool = False
    message: Optional[discord.Message] = None

class StateManager:
    def __init__(self):
        self._last_fetched_assets: Dict[int, AssetState] = defaultdict(lambda: None)
        self._active_jobs: Dict[int, JobState] = {}

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

    def start_job(self, user_id: int, message: discord.Message) -> None:
        """Start tracking a job for a user."""
        logger.info(f"Starting job for user {user_id}")
        self._active_jobs[user_id] = JobState(False, message)

    def cancel_job(self, user_id: int) -> bool:
        """Mark a user's job for cancellation. Returns whether a job was found to cancel."""
        if user_id in self._active_jobs:
            job = self._active_jobs[user_id]
            logger.info(f"Cancelling job for user {user_id}")
            job.should_cancel = True
            return True
        return False

    def should_cancel(self, user_id: int) -> bool:
        """Check if a user's job should be cancelled."""
        job = self._active_jobs.get(user_id)
        return job.should_cancel if job else False

    def get_search_message(self, user_id: int) -> Optional[discord.Message]:
        """Get the original search message for a user."""
        job = self._active_jobs.get(user_id)
        if job:
            logger.info(f"Retrieved search message for user {user_id}: {job.message and job.message.id}")
        return job.message if job else None

    def end_job(self, user_id: int) -> None:
        """Clean up job tracking for a user."""
        if user_id in self._active_jobs:
            del self._active_jobs[user_id]

# Global state manager instance
state_manager = StateManager()