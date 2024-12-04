import discord
from discord.ext import commands
import asyncio
import io
from typing import Optional, Dict, Any, Tuple
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
                content=f"❌ Minimum file size ({format_file_size(min_size)}) cannot exceed your account's maximum file size limit ({format_file_size(account_max_size)})",
                delete_after=15
            )
            return

        # If max_size is specified, ensure it doesn't exceed account limit
        if max_size and max_size > account_max_size:
            max_size = account_max_size

        progress_msg = ctx.message

        # Start tracking this job
        state_manager.start_job(user_id, progress_msg)

        try:
            valid_assets = []
            attempts = 0
            max_attempts = user_prefs['max_attempts']
            last_update = 0

            # Initial progress message
            await progress_msg.edit(content="🔍 Starting asset search...")

            while attempts < max_attempts and len(valid_assets) < count:
                # Check for cancellation
                if state_manager.should_cancel(user_id):
                    return

                current_time = asyncio.get_event_loop().time()
                if current_time - last_update >= user_prefs['progress_update_interval']:
                    await progress_msg.edit(
                        content=f"🔍 Found {len(valid_assets)}/{count} assets... (Attempt {attempts + 1}/{max_attempts})"
                    )
                    last_update = current_time

                assets, error = await asset_utils.fetch_random_assets(min(5, count - len(valid_assets)))
                if error or not assets:
                    attempts += 1
                    continue

                for asset in assets:
                    attempts += 1
                    if attempts > max_attempts:
                        break

                    asset_info = await asset_utils.fetch_asset_info(asset['id'])
                    if not asset_info:
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

                    # Check file size before fetching data
                    can_upload, size_message = await self.check_file_size(file_size, str(user_id))

                    # Only fetch file data if size check passes
                    file_data = await asset_utils.fetch_asset_data(asset['id']) if can_upload else None

                    valid_assets.append({
                        'info': asset_info,
                        'data': file_data,
                        'id': asset['id'],
                        'can_upload': can_upload,
                        'size_message': size_message
                    })

                    if len(valid_assets) >= count:
                        break

            # Handle no results found
            if not valid_assets:
                await progress_msg.edit(
                    content=f"❌ No matching assets found for command: `{command_str}` after {attempts} attempts.",
                    delete_after=15
                )
                return

            # Clean up progress message if we found assets
            await progress_msg.delete()

            # Send each valid asset
            for asset in valid_assets:
                details = (
                    f"**Command Used:** `{command_str}`\n\n"
                    f"{format_file_details(asset['info'], asset['info']['exifInfo']['fileSizeInByte'])}\n"
                )

                if asset['can_upload']:
                    # Get content type and extension
                    content_type = asset['info'].get('contentType', '')
                    original_filename = asset['info'].get('originalFileName', '')
                    extension = self.get_file_extension(original_filename, content_type)

                    file = discord.File(
                        io.BytesIO(asset['data']),
                        f"asset_{asset['id']}{extension}"
                    )
                    message = await ctx.send(details, file=file)
                else:
                    details += f"\n{asset['size_message']}"
                    message = await ctx.send(details)

                state_manager.set_last_asset(ctx.author.id, asset['id'], message.id)

        except Exception as e:
            logger.error(f"Error processing random assets: {str(e)}")
            await progress_msg.edit(
                content=f"❌ An error occurred while processing command: `{command_str}`",
                delete_after=15
            )
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