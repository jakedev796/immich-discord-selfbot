import discord
from discord.ext import commands
from utils.config import config
from utils.formatting import format_file_size

class HelpCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def format_help_menu(self, ctx, user_prefs: dict) -> str:
        """Create a formatted help menu."""
        # Header with current preferences
        header = (
            "📋 IMMICH DISCORD BOT HELP\n"
            "═══════════════════════\n\n"
            "⚙️ Current Settings\n"
            f"  • Max File Size: {format_file_size(config.get_file_size_limit(str(ctx.author.id)))}\n"
            f"  • Max Attempts: {user_prefs['max_attempts']}\n"
            f"  • Update Interval: {user_prefs['progress_update_interval']}s\n"
        )

        # Commands section with tree structure
        commands = (
            "\n🎲 Random Assets\n"
            "  └─ .random [options]\n"
            "     ├─ min:size    Minimum file size (e.g., min:2mb)\n"
            "     ├─ max:size    Maximum file size (e.g., max:5mb)\n"
            "     ├─ image/video Filter by type\n"
            "     ├─ count:n     Number of assets (max 10)\n"
            "     └─ Example: .random min:2mb max:5mb image count:3\n"
            "\n"
            "⚙️ Preferences\n"
            "  └─ .prefs [setting] [value]\n"
            "     └─ Example: .prefs max_attempts 50\n"
            "     💡 Use .prefs with no arguments to see all available settings\n"
            "\n"
            "🛑 Control\n"
            "  └─ .cancel    Stop ongoing search\n"
            "\n"
            "💡 Tips\n"
            "  • Use count:n to get multiple assets at once\n"
            "  • Large files show download progress\n"
            "  • Cancel search anytime with .cancel\n"
            "  • Run .prefs to see and configure all available settings"
        )

        return f"```\n{header}{commands}```"

    @commands.command()
    async def help(self, ctx):
        """Show help information with current preferences."""
        try:
            user_prefs = config.get_user_preferences(str(ctx.author.id))
            help_text = self.format_help_menu(ctx, user_prefs)
            await ctx.send(help_text)
        except Exception as e:
            await ctx.send(f"❌ Error showing help: {str(e)}")

async def setup(bot):
    await bot.add_cog(HelpCommands(bot))