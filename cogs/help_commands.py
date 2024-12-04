import discord
from discord.ext import commands
from utils.discord_utils import delete_command_message

class HelpCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx):
        """Display help for all commands."""
        help_message = f"""```
    Asset Bot Help
    ==============
    
    Core Commands:
    -------------
    {ctx.prefix}random [options]  : Fetch random assets
        Options:
        - min:size     : Minimum file size (e.g., min:2mb, min:500kb)
        - max:size     : Maximum file size (e.g., max:5mb, max:900kb)
        - image/video  : Asset type filter
        - count:n      : Number of assets to fetch (max 10)
        Example: {ctx.prefix}random min:2mb max:5mb image count:3
    
    {ctx.prefix}get <asset_id>   : Fetch a specific asset
    {ctx.prefix}delete <asset_id|last> : Delete an asset
    {ctx.prefix}favorite <asset_id|last> : Mark as favorite
    {ctx.prefix}unfavorite <asset_id|last> : Remove from favorites
    {ctx.prefix}stats : Show server statistics
    {ctx.prefix}cancel : Cancel an ongoing random search
    
    Preference Commands:
    ------------------
    {ctx.prefix}prefs : Show current preferences
    {ctx.prefix}prefs set <setting> <value> : Update a preference
    {ctx.prefix}prefs reset : Reset preferences
    {ctx.prefix}helppref : Show detailed preference help
    
    Tips:
    -----
    - Use 'last' with favorite/unfavorite/delete to act on the last fetched asset
    - Use 'cancel' to stop a random search in progress
    ```
    """
        await ctx.send(help_message, delete_after=60)
        await delete_command_message(ctx)

async def setup(bot):
    await bot.add_cog(HelpCommands(bot))