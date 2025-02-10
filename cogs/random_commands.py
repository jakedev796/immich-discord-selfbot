import discord
from discord.ext import commands
import asyncio
import io
from typing import Optional, Dict, Any, Tuple, List
from utils.config import config
from utils.formatting import (
    parse_size_string, format_file_size, get_progress_message,
    format_file_details
)
from utils.discord_utils import (
    send_error_message, delete_command_message,
    update_progress_message, send_file_to_discord
)
from utils.asset_utils import asset_utils
from utils.state_utils import state_manager
import os
import mimetypes
import logging

logger = logging.getLogger(__name__)

class RandomCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.asset_cache = {}  # Simple cache for asset info
        self.cache_ttl = 300  # 5 minutes cache TTL
        self.file_type_icons = {
            'image': '🖼️',
            'video': '🎥',
            'unknown': '📄'
        }

    def parse_random_args(self, args: tuple) -> tuple[Optional[int], Optional[int], Optional[str], Optional[int]]:
        """Parse arguments for random command."""
        min_size = max_size = None
        media_type = None
        count = 1

        for arg in args:
            arg = str(arg).lower()
            if arg.startswith('min:'):
                min_size = parse_size_string(arg[4:])
            elif arg.startswith('max:'):
                max_size = parse_size_string(arg[4:])
            elif arg in ['image', 'video']:
                media_type = arg
            elif arg.startswith('count:'):
                try:
                    count = int(arg[6:])
                    if count < 1 or count > 10:  # Limit to 10 items at once
                        count = 1
                except ValueError:
                    count = 1

        return min_size, max_size, media_type, count

    def format_command_details(self, ctx: commands.Context, args: tuple) -> str:
        """Format command details for inclusion in message."""
        command_str = f"{ctx.prefix}{ctx.command}"
        if args:
            command_str += " " + " ".join(str(arg) for arg in args)
        return command_str.strip()

    def get_file_extension(self, original_filename: str, content_type: str) -> str:
        """Get appropriate file extension from original filename or content type."""
        # First try to get extension from original filename
        if original_filename and '.' in original_filename:
            return os.path.splitext(original_filename)[1]

        # Fallback to content type mapping
        extension = mimetypes.guess_extension(content_type) or ''
        if extension == '.jpe':
            extension = '.jpg'
        elif content_type == 'video/mp4':
            extension = '.mp4'
        return extension

    async def check_file_size(self, size_bytes: int, user_id: str) -> Tuple[bool, str]:
        """Check if file size is within Discord limits."""
        max_file_size = config.get_file_size_limit(user_id)
        if size_bytes > max_file_size:
            return False, f"⚠️ File too large for Discord upload (Size: {format_file_size(size_bytes)}, Limit: {format_file_size(max_file_size)})"
        return True, ""

    async def get_asset_info(self, asset_id: str) -> Optional[Dict]:
        """Get asset info with caching support."""
        cache_key = f"asset_info_{asset_id}"
        cached = self.asset_cache.get(cache_key)
        if cached:
            return cached

        asset_info = await asset_utils.fetch_asset_info(asset_id)
        if asset_info:
            self.asset_cache[cache_key] = asset_info
            # Schedule cache cleanup
            asyncio.create_task(self._cleanup_cache(cache_key))
        return asset_info

    async def _cleanup_cache(self, cache_key: str):
        """Clean up cached item after TTL."""
        await asyncio.sleep(self.cache_ttl)
        self.asset_cache.pop(cache_key, None)

    async def fetch_assets_batch(self, count: int) -> Tuple[list, Optional[str]]:
        """Fetch assets in optimized batches."""
        batch_size = min(10, count)  # Fetch in batches of 10 or less
        assets = []
        error = None

        while len(assets) < count:
            batch, err = await asset_utils.fetch_random_assets(batch_size)
            if err:
                error = err
                break
            if not batch:
                break
            assets.extend(batch)

        return assets[:count], error

    def get_file_type_icon(self, asset_type: str) -> str:
        """Get the appropriate icon for the file type."""
        return self.file_type_icons.get(asset_type.lower(), self.file_type_icons['unknown'])

    def format_progress_bar(self, current: int, total: int, width: int = 10) -> str:
        """Create a progress bar string."""
        filled = int(width * current / total)
        bar = '▰' * filled + '▱' * (width - filled)
        percentage = current / total * 100
        return f"{bar} {percentage:.1f}%"

    async def download_with_progress(self, ctx: commands.Context, asset_id: str, size_bytes: int) -> Optional[bytes]:
        """Download asset data with progress updates."""
        try:
            # Start with 0% progress message
            progress_msg = await ctx.send(f"📥 Downloading... {self.format_progress_bar(0, 100)}")
            
            # Download the file
            file_data = await asset_utils.fetch_asset_data(asset_id)
            if not file_data:
                await progress_msg.edit(content="❌ Failed to download asset")
                return None

            # Show 100% progress
            await progress_msg.edit(content=f"✅ Download complete! {self.format_progress_bar(100, 100)}")
            await asyncio.sleep(1)  # Show completion for a moment
            await progress_msg.delete()
            
            return file_data
        except Exception as e:
            logger.error(f"Error downloading asset {asset_id}: {str(e)}")
            await progress_msg.edit(content=f"❌ Download failed: {str(e)}")
            return None

    def format_error_message(self, error: str, command_str: str) -> str:
        """Format an error message with helpful information."""
        base_msg = f"❌ Error: {error}\n\n"
        
        if "rate limit" in error.lower():
            base_msg += "🕒 You're making too many requests. Please wait a moment and try again."
        elif "not found" in error.lower():
            base_msg += "🔍 The requested asset could not be found. It may have been deleted."
        elif "permission" in error.lower():
            base_msg += "🔒 You don't have permission to access this asset."
        elif "size" in error.lower():
            base_msg += "📏 The file size exceeds Discord's upload limit. Try using size filters."
        else:
            base_msg += "⚠️ An unexpected error occurred. Please try again or contact support."

        base_msg += f"\n\nCommand used: `{command_str}`"
        return base_msg

    async def send_asset(self,
                        ctx: commands.Context,
                        asset: Dict,
                        command_str: str) -> Optional[discord.Message]:
        """Send an asset with proper formatting and error handling."""
        try:
            # Get basic asset info
            asset_type = asset['info'].get('type', '').lower()
            file_size = asset['info']['exifInfo']['fileSizeInByte']
            icon = self.get_file_type_icon(asset_type)

            details = (
                f"{icon} **Asset Details**\n\n"
                f"**Command Used:** `{command_str}`\n"
                f"{format_file_details(asset['info'], file_size)}\n"
            )

            # Get file info
            content_type = asset['info'].get('contentType', '')
            original_filename = asset['info'].get('originalFileName', '')
            extension = self.get_file_extension(original_filename, content_type)

            # Download with progress bar for large files (>10MB)
            if file_size > 10 * 1024 * 1024:  # 10MB
                file_data = await self.download_with_progress(ctx, asset['id'], file_size)
                if not file_data:
                    return None
            else:
                file_data = asset['data']

            # Create and send file
            file = discord.File(
                io.BytesIO(file_data),
                f"asset_{asset['id']}{extension}"
            )
            
            return await ctx.send(content=details, file=file)

        except Exception as e:
            error_msg = self.format_error_message(str(e), command_str)
            await ctx.send(content=error_msg, delete_after=30)
            logger.error(f"Error sending asset: {str(e)}")
            return None

    async def process_random_assets(self,
                                    ctx: commands.Context,
                                    count: int,
                                    min_size: Optional[int] = None,
                                    max_size: Optional[int] = None,
                                    media_type: Optional[str] = None) -> None:
        """Process and send random assets with progress updates."""
        user_id = ctx.author.id
        user_prefs = config.get_user_preferences(str(user_id))
        account_max_size = config.get_file_size_limit(str(user_id))
        command_str = self.format_command_details(ctx, ctx.args[2:])

        # Check if min_size exceeds max allowed file size
        if min_size and min_size > account_max_size:
            await ctx.message.edit(
                content=self.format_error_message(
                    f"Minimum file size ({format_file_size(min_size)}) cannot exceed your account's maximum file size limit ({format_file_size(account_max_size)})",
                    command_str
                ),
                delete_after=15
            )
            return

        # If max_size is specified, ensure it doesn't exceed account limit
        if max_size and max_size > account_max_size:
            max_size = account_max_size

        # Start tracking this job
        state_manager.start_job(user_id, ctx.message)

        try:
            valid_assets = []
            attempts = 0
            max_attempts = user_prefs['max_attempts']

            # Initial progress message
            await ctx.message.edit(content="🔍 Starting search...")
            last_update_time = 0

            while attempts < max_attempts and len(valid_assets) < count:
                if state_manager.should_cancel(user_id):
                    await ctx.message.edit(content="✋ Search cancelled", delete_after=15)
                    return

                current_time = asyncio.get_event_loop().time()
                should_update = current_time - last_update_time >= 5

                # Fetch assets in optimized batches
                assets, error = await self.fetch_assets_batch(min(5, count - len(valid_assets)))
                if error or not assets:
                    attempts += max(1, len(assets))
                    if should_update:
                        await ctx.message.edit(
                            content=f"🔍 Searching for assets... (Attempt {attempts}/{max_attempts})"
                        )
                        last_update_time = current_time
                    continue

                # Process assets concurrently
                asset_infos = await asyncio.gather(
                    *[self.get_asset_info(asset['id']) for asset in assets],
                    return_exceptions=True
                )

                for asset, asset_info in zip(assets, asset_infos):
                    attempts += 1
                    
                    # Update progress message every 5 seconds
                    current_time = asyncio.get_event_loop().time()
                    if current_time - last_update_time >= 5:
                        progress_text = f"🔍 Searching for assets... (Attempt {attempts}/{max_attempts})"
                        # Add found assets to progress
                        for valid_asset in valid_assets:
                            asset_type = valid_asset['info'].get('type', '').lower()
                            icon = self.get_file_type_icon(asset_type)
                            progress_text += f"\n└─ Asset Found! {icon}"
                        await ctx.message.edit(content=progress_text)
                        last_update_time = current_time

                    if attempts > max_attempts:
                        break

                    if isinstance(asset_info, Exception) or not asset_info:
                        continue

                    file_size = asset_info['exifInfo']['fileSizeInByte']
                    asset_type = asset_info.get('type', '').lower()

                    # Apply filters
                    if media_type and asset_type != media_type:
                        continue
                    if min_size and file_size < min_size:
                        continue
                    if max_size and file_size > max_size:
                        continue

                    # Check file size
                    can_upload, size_message = await self.check_file_size(file_size, str(user_id))
                    if not can_upload:
                        continue

                    # Fetch file data
                    file_data = await asset_utils.fetch_asset_data(asset['id'])
                    if not file_data:
                        continue

                    valid_assets.append({
                        'info': asset_info,
                        'data': file_data,
                        'id': asset['id'],
                        'can_upload': True,
                        'size_message': size_message
                    })

                    # Show progress with new asset found
                    progress_text = f"🔍 Searching for assets... (Attempt {attempts}/{max_attempts})"
                    for valid_asset in valid_assets:
                        asset_type = valid_asset['info'].get('type', '').lower()
                        icon = self.get_file_type_icon(asset_type)
                        progress_text += f"\n└─ Asset Found! {icon}"
                    await ctx.message.edit(content=progress_text)

                    if len(valid_assets) >= count:
                        break

            # Handle no results found
            if not valid_assets:
                await ctx.message.edit(
                    content=f"❌ No matching assets found for command: `{command_str}` after {attempts} attempts.",
                    delete_after=15
                )
                return

            # Send all assets
            await ctx.message.delete()  # Delete the progress message
            for asset in valid_assets:
                message = await self.send_asset(ctx, asset, command_str)
                if message:
                    state_manager.set_last_asset(ctx.author.id, asset['id'], message.id)

        except Exception as e:
            error_msg = self.format_error_message(str(e), command_str)
            await ctx.message.edit(content=error_msg, delete_after=30)
            logger.error(f"Error processing random assets: {str(e)}")
        finally:
            state_manager.end_job(user_id)

    @commands.command()
    async def cancel(self, ctx):
        """
        Cancel any running search operations.
        Usage: .cancel
        """
        try:
            search_msg = state_manager.get_search_message(ctx.author.id)

            if state_manager.cancel_job(ctx.author.id):
                # First update to show cancellation in progress
                await ctx.message.edit(content="🛑 Cancelling search...")

                # Wait a moment for the search to actually cancel
                await asyncio.sleep(1)

                # Delete the original random command message
                if search_msg:
                    try:
                        await search_msg.delete()
                    except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
                        logger.error(f"Failed to delete search message: {e}")

                # Update the cancel command message and set it to delete
                await ctx.message.edit(
                    content="✋ Search cancelled",
                    delete_after=15
                )
            else:
                await ctx.message.edit(
                    content="❌ No active search to cancel",
                    delete_after=15
                )
        except Exception as e:
            logger.error(f"Error in cancel command: {str(e)}")
            await ctx.send("Error processing cancel command", delete_after=5)

    @commands.command()
    async def random(self, ctx, *args):
        """
        Fetch random assets with optional filters.
        Usage: .random [min:size] [max:size] [image|video] [count:n]
        Example: .random min:2mb max:5mb image count:3
        """
        min_size, max_size, media_type, count = self.parse_random_args(args)
        await self.process_random_assets(ctx, count, min_size, max_size, media_type)

async def setup(bot):
    await bot.add_cog(RandomCommands(bot))