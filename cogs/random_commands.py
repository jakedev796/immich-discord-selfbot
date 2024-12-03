import discord
from discord.ext import commands
import asyncio
import io
from typing import Optional, List, Dict, Any
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

    async def process_random_assets(self,
                                    ctx: commands.Context,
                                    count: int,
                                    min_size: Optional[int] = None,
                                    max_size: Optional[int] = None,
                                    media_type: Optional[str] = None) -> None:
        """Process and send random assets with progress updates."""
        # Delete the original command message
        await delete_command_message(ctx)

        # Create progress message
        progress_msg = await ctx.send("Starting asset search...")
        user_prefs = config.get_user_preferences(str(ctx.author.id))

        try:
            valid_assets = []
            attempts = 0
            max_attempts = user_prefs['max_attempts']
            last_update = 0

            while attempts < max_attempts and len(valid_assets) < count:
                # Update progress message
                current_time = asyncio.get_event_loop().time()
                if current_time - last_update >= user_prefs['progress_update_interval']:
                    await update_progress_message(
                        progress_msg,
                        f"Found {len(valid_assets)}/{count} assets... (Attempt {attempts + 1}/{max_attempts})"
                    )
                    last_update = current_time

                # Fetch a batch of random assets
                assets, error = await asset_utils.fetch_random_assets(min(5, count - len(valid_assets)))
                if error or not assets:
                    attempts += 1
                    continue

                # Process each asset in the batch
                for asset in assets:
                    attempts += 1
                    if attempts > max_attempts:
                        break

                    # Get asset info and check filters
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

                    # Get the actual file data
                    file_data = await asset_utils.fetch_asset_data(asset['id'])
                    if not file_data:
                        continue

                    valid_assets.append({
                        'info': asset_info,
                        'data': file_data,
                        'id': asset['id']
                    })

                    if len(valid_assets) >= count:
                        break

            # Clean up progress message
            await progress_msg.delete()

            if not valid_assets:
                await send_error_message(ctx, f"No matching assets found after {attempts} attempts")
                return

            # Send each asset individually with its details
            for asset in valid_assets:
                file = discord.File(
                    io.BytesIO(asset['data']),
                    f"asset_{asset['id']}.{asset['info'].get('originalFileName', '').split('.')[-1]}"
                )
                message = await ctx.send(
                    format_file_details(asset['info'], asset['info']['exifInfo']['fileSizeInByte']),
                    file=file
                )
                # Store the last asset info in the state manager
                state_manager.set_last_asset(ctx.author.id, asset['id'], message.id)

        except Exception as e:
            logger.error(f"Error processing random assets: {str(e)}")
            await send_error_message(ctx, f"Error processing random assets: {str(e)}")

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