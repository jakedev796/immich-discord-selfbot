import discord
from discord.ext import commands
import requests
import os
from dotenv import load_dotenv
import io
import random
import mimetypes
from datetime import datetime
import logging
import json

# Set up logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

load_dotenv()

class AssetCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.getenv('API_KEY')
        self.admin_api_key = os.getenv('ADMIN_API_KEY')
        self.base_url = os.getenv('BASE_URL')
        self.error_message = "An error occurred. Please try again later."
        self.message_delete_delay = 10  # Seconds before deleting messages

    async def handle_error(self, ctx, error_type, details):
        """
        Handles errors by logging them and sending a generic error message to the user.
        """
        logger.error(f"{error_type}: {details}")
        await ctx.send(self.error_message, delete_after=self.message_delete_delay)

    async def delete_command_message(self, ctx):
        """
        Attempts to delete the command message to keep the chat clean.
        """
        try:
            await ctx.message.delete()
        except discord.errors.Forbidden:
            logger.warning("Bot doesn't have permission to delete messages")
        except discord.errors.NotFound:
            logger.info("Message not found, it might have been deleted already")
        except Exception as e:
            logger.error(f"An error occurred while deleting the message: {e}")

    def format_file_size(self, size_in_bytes):
        """
        Formats file size from bytes to a human-readable format.
        """
        if size_in_bytes >= 1_000_000:
            return f"{size_in_bytes / 1_000_000:.2f} MB"
        else:
            return f"{size_in_bytes / 1_000:.2f} KB"

    def format_date(self, date_string):
        """
        Formats date string to a more readable format.
        """
        date = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return date.strftime('%m/%d/%y - %H:%M:%S UTC')

    async def fetch_asset_info(self, asset_id):
        """
        Fetches asset information from the API.
        """
        headers = {
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }
        asset_info_url = f"{self.base_url}/api/assets/{asset_id}"
        response = requests.get(asset_info_url, headers=headers)
        response.raise_for_status()
        return response.json()

    async def fetch_and_send_asset(self, ctx, asset_id):
        """
        Fetches an asset and sends it to the Discord channel.
        """
        headers = {
            'Accept': 'application/octet-stream',
            'x-api-key': self.api_key
        }

        try:
            asset_info = await self.fetch_asset_info(asset_id)
            asset_url = f"{self.base_url}/api/assets/{asset_id}/original"
            asset_response = requests.get(asset_url, headers=headers)
            asset_response.raise_for_status()

            content_type = asset_response.headers.get('content-type', '')
            extension = mimetypes.guess_extension(content_type) or ''
            if extension == '.jpe':
                extension = '.jpg'

            file_size = self.format_file_size(asset_info['exifInfo']['fileSizeInByte'])
            resolution = f"{asset_info['exifInfo']['exifImageWidth']}x{asset_info['exifInfo']['exifImageHeight']}"
            downloaded_at = self.format_date(asset_info['fileCreatedAt'])
            original_file_name = asset_info.get('originalFileName', 'Unknown')

            asset_data = io.BytesIO(asset_response.content)
            file_details = (
                f"**File Details:**\n"
                f"ID: {asset_id}\n"
                f"Original File Name: {original_file_name}\n"
                f"Size: {file_size}\n"
                f"Resolution: {resolution}\n"
                f"Downloaded: {downloaded_at}"
            )

            await ctx.send(file_details, file=discord.File(asset_data, filename=f"asset_{asset_id}{extension}"))

        except Exception as e:
            await self.handle_error(ctx, "Asset fetch error", f"Error fetching asset {asset_id}: {str(e)}")

    @commands.command()
    async def random(self, ctx):
        """
        Fetches and displays a random asset.
        """
        try:
            headers = {
                'Accept': 'application/json',
                'x-api-key': self.api_key
            }
            random_asset_url = f"{self.base_url}/api/assets/random"
            response = requests.get(random_asset_url, headers=headers)
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, list) or len(data) == 0:
                raise ValueError("No assets found in API response")

            asset = random.choice(data)
            asset_id = asset.get('id')

            if not asset_id:
                raise ValueError("No asset ID found in selected asset")

            await self.fetch_and_send_asset(ctx, asset_id)

        except Exception as e:
            await self.handle_error(ctx, "Random asset error", str(e))
        finally:
            await self.delete_command_message(ctx)

    @commands.command()
    async def get(self, ctx, asset_id: str):
        """
        Fetches and displays a specific asset by ID.
        """
        try:
            await self.fetch_and_send_asset(ctx, asset_id)
        except Exception as e:
            await self.handle_error(ctx, "Get asset error", f"Error getting asset {asset_id}: {str(e)}")
        finally:
            await self.delete_command_message(ctx)

    @commands.command()
    async def favorite(self, ctx, asset_id: str):
        """
        Marks an asset as a favorite.
        """
        try:
            url = f"{self.base_url}/api/assets/{asset_id}"
            payload = json.dumps({
                "isFavorite": True,
            })
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'x-api-key': self.api_key
            }
            response = requests.put(url, headers=headers, data=payload)
            response.raise_for_status()

            await ctx.send(f"Asset {asset_id} has been marked as favorite.", delete_after=self.message_delete_delay)
        except Exception as e:
            await self.handle_error(ctx, "Favorite asset error", f"Error favoriting asset {asset_id}: {str(e)}")
        finally:
            await self.delete_command_message(ctx)

    @commands.command()
    async def delete(self, ctx, asset_id: str):
        """
        Deletes a specific asset by ID.
        """
        try:
            url = f"{self.base_url}/api/assets"
            payload = json.dumps({
                "force": True,
                "ids": [asset_id]
            })
            headers = {
                'Content-Type': 'application/json',
                'x-api-key': self.api_key
            }
            response = requests.delete(url, headers=headers, data=payload)
            response.raise_for_status()

            await ctx.send(f"Asset {asset_id} has been deleted.", delete_after=self.message_delete_delay)
        except Exception as e:
            await self.handle_error(ctx, "Delete asset error", f"Error deleting asset {asset_id}: {str(e)}")
        finally:
            await self.delete_command_message(ctx)

    @commands.command()
    async def stats(self, ctx):
        """
        Displays server statistics.
        """
        try:
            url = f"{self.base_url}/api/server/statistics"
            headers = {
                'Accept': 'application/json',
                'x-api-key': self.admin_api_key  # Using admin API key for stats
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            photos_count = data['photos']
            videos_count = data['videos']
            total_assets = photos_count + videos_count

            stats_message = (
                "**Server Statistics**\n\n"
                f"**Total Assets:** {total_assets:,}\n"
                f"**Photos:** {photos_count:,}\n"
                f"**Videos:** {videos_count:,}\n"
            )

            await ctx.send(stats_message)

        except Exception as e:
            await self.handle_error(ctx, "Stats error", f"Error fetching stats: {str(e)}")
        finally:
            await self.delete_command_message(ctx)

    @commands.command()
    async def help(self, ctx):
        """
        Displays a help message with all available commands.
        """
        help_message = """
```
Asset Bot Help
==============

Available Commands:
-------------------
?random           : Fetches and displays a random asset
?get <asset_id>   : Fetches and displays a specific asset
?favorite <asset_id> : Marks an asset as a favorite
?delete <asset_id>: Deletes a specific asset
?stats            : Displays server statistics
?help             : Shows this help message

All commands use the '?' prefix.
```
"""
        await ctx.send(help_message)
        await self.delete_command_message(ctx)

async def setup(bot):
    await bot.add_cog(AssetCommands(bot))