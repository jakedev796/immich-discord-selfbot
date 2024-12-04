import discord
from discord.ext import commands
from utils.config import config
from utils.formatting import format_file_details, format_file_size
from utils.discord_utils import (
    send_error_message, delete_command_message,
    send_file_to_discord
)
from utils.asset_utils import asset_utils
from typing import Optional, Dict, Tuple
from utils.state_utils import state_manager
from collections import defaultdict
import mimetypes
import os
import logging

logger = logging.getLogger(__name__)

class AssetCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_fetched_asset = defaultdict(lambda: None)
        self.last_message_id = defaultdict(lambda: None)

    def format_command_details(self, ctx: commands.Context) -> str:
        """Format command details for inclusion in message."""
        command_str = f"{ctx.prefix}{ctx.command}"
        if len(ctx.args) > 2:  # Skip ctx and self args
            command_str += " " + " ".join(str(arg) for arg in ctx.args[2:])
        return command_str

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

    async def fetch_and_send_asset(self, ctx: commands.Context, asset_id: str) -> Tuple[bool, Optional[str]]:
        """Fetch and send an asset to the Discord channel."""
        progress_msg = ctx.message
        command_str = self.format_command_details(ctx)

        try:
            # Update original message to show progress
            await progress_msg.edit(content=f"📥 Fetching asset {asset_id}...")

            asset_info = await asset_utils.fetch_asset_info(asset_id)
            if not asset_info:
                await progress_msg.edit(content=f"❌ Failed to fetch asset information for command: `{command_str}`")
                return False, None

            file_size_bytes = asset_info['exifInfo']['fileSizeInByte']
            user_id = str(ctx.author.id)

            # Check file size before fetching data
            can_upload, size_message = await self.check_file_size(file_size_bytes, user_id)

            # Prepare the message content
            details = (
                f"**Command Used:** `{command_str}`\n\n"
                f"{format_file_details(asset_info, file_size_bytes)}"
            )

            if not can_upload:
                details += f"\n\n{size_message}"
                await progress_msg.edit(content=details)
                state_manager.set_last_asset(ctx.author.id, asset_id, progress_msg.id)
                return True, None

            # Update progress before fetching file data
            await progress_msg.edit(content=f"📥 Downloading asset {asset_id}...")

            # Get file data only if size check passes
            file_data = await asset_utils.fetch_asset_data(asset_id)
            if not file_data:
                await progress_msg.edit(content=f"❌ Failed to fetch asset data for command: `{command_str}`")
                return False, None

            # Get content type and extension
            content_type = asset_info.get('contentType', '')
            original_filename = asset_info.get('originalFileName', '')
            extension = self.get_file_extension(original_filename, content_type)

            # Clean up progress message
            await progress_msg.delete()

            # Send the file in a new message
            message = await send_file_to_discord(
                ctx,
                file_data,
                f"asset_{asset_id}{extension}",
                details
            )

            if message:
                state_manager.set_last_asset(ctx.author.id, asset_id, message.id)
                return True, None
            else:
                await progress_msg.edit(content=f"❌ Failed to send file to Discord for command: `{command_str}`")
                return False, None

        except Exception as e:
            logger.error(f"Error fetching asset {asset_id}: {str(e)}")
            await progress_msg.edit(content=f"❌ An error occurred while processing command: `{command_str}`")
            return False, None

    @commands.command()
    async def get(self, ctx, asset_id: str):
        """
        Fetch and display a specific asset by ID.
        Usage: .get <asset_id>
        """
        try:
            success, message = await self.fetch_and_send_asset(ctx, asset_id)
            if not success and message:  # Only send error message if we haven't already handled it
                await send_error_message(ctx, message)
        except Exception as e:
            logger.error(f"Error in get asset command: {str(e)}")
            await send_error_message(ctx, "An error occurred while processing the asset. Please try again.")
            await delete_command_message(ctx)  # Only delete if we haven't successfully processed the asset

    @commands.command()
    async def delete(self, ctx, asset_id: str):
        """
        Delete an asset by ID. Use 'last' to delete the last fetched asset.
        Usage: .delete <asset_id|last>
        """
        try:
            if asset_id.lower() == 'last':
                asset_state = state_manager.get_last_asset(ctx.author.id)
                if asset_state is None:
                    await send_error_message(ctx, "No asset has been fetched yet.")
                    return
                asset_id = asset_state.asset_id

                # Try to delete the Discord message if we have its ID
                if asset_state.message_id is not None:
                    try:
                        message = await ctx.channel.fetch_message(asset_state.message_id)
                        await message.delete()
                    except Exception as e:
                        logger.error(f"Failed to delete Discord message: {str(e)}")

            # Delete the asset from Immich
            success, error = await asset_utils.delete_asset(asset_id)
            if not success:
                await send_error_message(ctx, f"Error deleting asset: {error}")
                return

            await ctx.send(f"Asset {asset_id} has been deleted.", delete_after=5)

            # Clear the stored asset if we just deleted it
            last_asset = state_manager.get_last_asset(ctx.author.id)
            if last_asset and last_asset.asset_id == asset_id:
                state_manager.clear_last_asset(ctx.author.id)

        except Exception as e:
            logger.error(f"Error in delete asset command: {str(e)}")
            await send_error_message(ctx, f"Error deleting asset {asset_id}: {str(e)}")
        finally:
            await delete_command_message(ctx)

    @commands.command()
    async def stats(self, ctx):
        """
        Display server statistics.
        Usage: .stats
        """
        try:
            stats_data = await asset_utils.fetch_server_stats()
            if not stats_data:
                await send_error_message(ctx, "Failed to fetch server statistics.")
                return

            photos_count = stats_data.get('photos', 0)
            videos_count = stats_data.get('videos', 0)
            total_assets = photos_count + videos_count

            stats_message = (
                "**Server Statistics**\n\n"
                f"**Total Assets:** {total_assets:,}\n"
                f"**Photos:** {photos_count:,}\n"
                f"**Videos:** {videos_count:,}\n"
            )

            await ctx.send(stats_message)
        except Exception as e:
            logger.error(f"Error in stats command: {str(e)}")
            await send_error_message(ctx, f"Error fetching stats: {str(e)}")
        finally:
            await delete_command_message(ctx)

async def setup(bot):
    await bot.add_cog(AssetCommands(bot))