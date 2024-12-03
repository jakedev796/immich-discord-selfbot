import os
import requests
from typing import Tuple, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class AssetUtils:
    def __init__(self):
        self.api_key = os.getenv('API_KEY')
        self.admin_api_key = os.getenv('ADMIN_API_KEY')
        self.base_url = os.getenv('BASE_URL')

    def get_headers(self, admin: bool = False) -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            'Accept': 'application/json',
            'x-api-key': self.admin_api_key if admin else self.api_key
        }

    async def fetch_asset_info(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Fetch asset information from the API."""
        try:
            headers = self.get_headers()
            asset_info_url = f"{self.base_url}/api/assets/{asset_id}"
            response = requests.get(asset_info_url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching asset info: {str(e)}")
            return None

    async def fetch_random_assets(self, count: int = 1) -> Tuple[Optional[list], Optional[str]]:
        """Fetch random assets from the API."""
        try:
            headers = self.get_headers()
            url = f"{self.base_url}/api/assets/random?count={count}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, list):
                return None, "Invalid response from API"

            return data, None
        except Exception as e:
            logger.error(f"Error fetching random assets: {str(e)}")
            return None, str(e)

    async def delete_asset(self, asset_id: str) -> Tuple[bool, Optional[str]]:
        """Delete an asset."""
        try:
            headers = {
                'Content-Type': 'application/json',
                'x-api-key': self.api_key
            }
            url = f"{self.base_url}/api/assets"
            payload = {"force": True, "ids": [asset_id]}
            response = requests.delete(url, headers=headers, json=payload)
            response.raise_for_status()
            return True, None
        except Exception as e:
            logger.error(f"Error deleting asset: {str(e)}")
            return False, str(e)

    async def fetch_asset_data(self, asset_id: str) -> Optional[bytes]:
        """Fetch the actual asset data."""
        try:
            headers = {
                'Accept': 'application/octet-stream',
                'x-api-key': self.api_key
            }
            url = f"{self.base_url}/api/assets/{asset_id}/original"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Error fetching asset data: {str(e)}")
            return None

    async def set_favorite(self, asset_id: str, is_favorite: bool) -> bool:
        """Set or unset an asset as favorite."""
        try:
            url = f"{self.base_url}/api/assets/{asset_id}"
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'x-api-key': self.api_key
            }
            response = requests.put(url, headers=headers, json={"isFavorite": is_favorite})
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error setting favorite status: {str(e)}")
            return False

    async def fetch_server_stats(self) -> Optional[Dict[str, Any]]:
        """Fetch server statistics."""
        try:
            headers = self.get_headers(admin=True)
            url = f"{self.base_url}/api/server/statistics"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching server stats: {str(e)}")
            return None

# Global instance
asset_utils = AssetUtils()