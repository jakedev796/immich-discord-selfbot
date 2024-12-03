import discord
from discord.ext import commands
from utils.config import config
from utils.formatting import format_file_details
from utils.discord_utils import (
    send_error_message, delete_command_message,
    send_file_to_discord
)
from utils.asset_utils import asset_utils
from typing import Optional, Dict, Tuple  # Added complete typing imports
from utils.state_utils import state_manager
from collections import defaultdict
import mimetypes
import logging

logger = logging.getLogger(__name__)

class AssetCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_fetched_asset = defaultdict(lambda: None)  # user_id -> asset_id
        self.last_message_id = defaultdict(lambda: None)     # user_id -> message_id

    async def fetch_and_send_asset(self, ctx: commands.Context, asset_id: str) -> Tuple[bool, Optional[str]]:
        """Fetch and send an asset to the Discord channel."""
        try:
            # Get asset info
            asset_info = await asset_utils.fetch_asset_info(asset_id)
            if not asset_info:
                return False, "Failed to fetch asset information."

            file_size_bytes = asset_info['exifInfo']['fileSizeInByte']
            user_prefs = config.get_user_preferences(str(ctx.author.id))

            # Check file size against Discord limits
            max_file_size = float(user_prefs.get('max_file_size_mb', 25)) * 1_000_000
            if file_size_bytes > max_file_size:
                return False, f"Asset is too large to upload (Size: {format_file_size(file_size_bytes)}, Limit: {max_file_size} MB)"

            # Get content type and extension
            content_type = asset_info.get('contentType', '')
            extension = mimetypes.guess_extension(content_type) or ''
            if extension == '.jpe':
                extension = '.jpg'

            # Get file data from API
            file_data = await asset_utils.fetch_asset_data(asset_id)
            if not file_data:
                return False, "Failed to fetch asset data."

            # Send the file
            message = await send_file_to_discord(
                ctx,
                file_data,
                f"asset_{asset_id}{extension}",
                format_file_details(asset_info, file_size_bytes)
            )

            if message:
                # Store the asset and message IDs
                self.last_fetched_asset[ctx.author.id] = asset_id
                self.last_message_id[ctx.author.id] = message.id
                return True, None
            else:
                return False, "Failed to send file to Discord."

        except Exception as e:
            logger.error(f"Error fetching asset {asset_id}: {str(e)}")
            return False, f"Error fetching asset {asset_id}: {str(e)}"

    @commands.command()
    async def get(self, ctx, asset_id: str):
        """
        Fetch and display a specific asset by ID.
        Usage: .get <asset_id>
        """
        try:
            success, message = await self.fetch_and_send_asset(ctx, asset_id)
            if not success:
                await send_error_message(ctx, message)
        except Exception as e:
            logger.error(f"Error in get asset command: {str(e)}")
            await send_error_message(ctx, f"Error getting asset {asset_id}: {str(e)}")
        finally:
            await delete_command_message(ctx)

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