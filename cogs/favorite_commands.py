import discord
from discord.ext import commands
from utils.discord_utils import send_error_message, delete_command_message
from utils.asset_utils import asset_utils
from utils.state_utils import state_manager
import logging

logger = logging.getLogger(__name__)

class FavoriteCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def favorite(self, ctx, asset_id: str):
        """
        Mark an asset as favorite. Use 'last' to favorite the last fetched asset.
        Usage: .favorite <asset_id|last>
        """
        try:
            if asset_id.lower() == 'last':
                asset_state = state_manager.get_last_asset(ctx.author.id)
                if asset_state is None:
                    await send_error_message(ctx, "No asset has been fetched yet.")
                    return
                asset_id = asset_state.asset_id

            success = await asset_utils.set_favorite(asset_id, True)
            if success:
                await ctx.send(f"Asset {asset_id} has been marked as favorite.", delete_after=5)
            else:
                await send_error_message(ctx, f"Failed to favorite asset {asset_id}")

        except Exception as e:
            logger.error(f"Error in favorite command: {str(e)}")
            await send_error_message(ctx, f"Error favoriting asset {asset_id}: {str(e)}")
        finally:
            await delete_command_message(ctx)

    @commands.command()
    async def unfavorite(self, ctx, asset_id: str):
        """
        Remove an asset from favorites. Use 'last' to unfavorite the last fetched asset.
        Usage: .unfavorite <asset_id|last>
        """
        try:
            if asset_id.lower() == 'last':
                asset_state = state_manager.get_last_asset(ctx.author.id)
                if asset_state is None:
                    await send_error_message(ctx, "No asset has been fetched yet.")
                    return
                asset_id = asset_state.asset_id

            success = await asset_utils.set_favorite(asset_id, False)
            if success:
                await ctx.send(f"Asset {asset_id} has been removed from favorites.", delete_after=5)
            else:
                await send_error_message(ctx, f"Failed to unfavorite asset {asset_id}")

        except Exception as e:
            logger.error(f"Error in unfavorite command: {str(e)}")
            await send_error_message(ctx, f"Error unfavoriting asset {asset_id}: {str(e)}")
        finally:
            await delete_command_message(ctx)

async def setup(bot):
    await bot.add_cog(FavoriteCommands(bot))