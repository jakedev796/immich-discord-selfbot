import discord
from discord.ext import commands
from typing import Optional
from utils.config import config
from utils.formatting import parse_size_string, format_file_size
from utils.discord_utils import send_error_message, delete_command_message
import logging

logger = logging.getLogger(__name__)

class PreferenceCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.VALID_SETTINGS = {
            'media_type': ['mt', 'type'],  # Aliases for media_type
            'min_size': ['mins', 'min'],   # Aliases for min_size
            'max_size': ['maxs', 'max'],   # Aliases for max_size
            'max_attempts': ['attempts', 'retry'],  # Aliases for max_attempts
            'update_interval': ['interval', 'update']  # Aliases for update_interval
        }

    def get_setting_name(self, alias: str) -> Optional[str]:
        """Convert potential alias to main setting name."""
        alias = alias.lower()
        for main_setting, aliases in self.VALID_SETTINGS.items():
            if alias == main_setting or alias in aliases:
                return main_setting
        return None

    @commands.group(invoke_without_command=True)
    async def prefs(self, ctx):
        """Show current preferences."""
        if ctx.invoked_subcommand is None:
            prefs = config.get_user_preferences(str(ctx.author.id))

            # Format the preferences for display
            min_size = format_file_size(prefs['min_size_bytes']) if prefs['min_size_bytes'] else 'Not set'
            max_size = format_file_size(prefs['max_size_bytes']) if prefs['max_size_bytes'] else 'Not set'
            media_type = prefs['default_media_type'] if prefs['default_media_type'] else 'All types'

            prefs_message = (
                "**Your Current Preferences**\n"
                f"Default Media Type (mt): {media_type}\n"
                f"Minimum File Size (min): {min_size}\n"
                f"Maximum File Size (max): {max_size}\n"
                f"API Retry Attempts (attempts): {prefs['max_attempts']}\n"
                f"Progress Update Interval (interval): {prefs['progress_update_interval']}s\n\n"
                f"Use `{ctx.prefix}prefs set <setting> <value>` to change a setting\n"
                f"Use `{ctx.prefix}helppref` for detailed setting information\n"
                f"Use `{ctx.prefix}prefs reset` to reset to defaults"
            )

            await ctx.send(prefs_message, delete_after=60)
            await delete_command_message(ctx)

    @prefs.command(name="set")
    async def prefs_set(self, ctx, setting: str, *, value: str):
        """Set a preference value."""
        setting = self.get_setting_name(setting)
        if not setting:
            await send_error_message(
                ctx,
                "Invalid setting. Use `.helppref` to see available settings and their aliases."
            )
            return

        user_id = str(ctx.author.id)

        try:
            if setting == "media_type":
                if value.lower() not in ["image", "video", "all"]:
                    await send_error_message(ctx, "Media type must be 'image', 'video', or 'all'")
                    return
                value = None if value.lower() == "all" else value.lower()
                config.update_user_preference(user_id, "default_media_type", value)

            elif setting in ["min_size", "max_size"]:
                size_bytes = parse_size_string(value)
                if size_bytes is None:
                    await send_error_message(ctx, "Invalid size format. Use a number followed by 'mb' or 'kb' (e.g., 2mb, 500kb)")
                    return
                config.update_user_preference(user_id, f"{setting}_bytes", size_bytes)

            elif setting == "max_attempts":
                try:
                    attempts = int(value)
                    if attempts < 1:
                        raise ValueError
                    config.update_user_preference(user_id, "max_attempts", attempts)
                except ValueError:
                    await send_error_message(ctx, "Max attempts must be a positive number")
                    return

            elif setting == "update_interval":
                try:
                    interval = int(value)
                    if interval < 1:
                        raise ValueError
                    config.update_user_preference(user_id, "progress_update_interval", interval)
                except ValueError:
                    await send_error_message(ctx, "Update interval must be a positive number of seconds")
                    return

            await ctx.send(f"Updated {setting} preference.", delete_after=5)

        except Exception as e:
            await send_error_message(ctx, f"Error updating preference: {str(e)}")
        finally:
            await delete_command_message(ctx)

    @prefs.command(name="reset")
    async def prefs_reset(self, ctx):
        """Reset preferences to defaults."""
        try:
            config.reset_user_preferences(str(ctx.author.id))
            await ctx.send("Preferences reset to defaults.", delete_after=5)
        except Exception as e:
            await send_error_message(ctx, f"Error resetting preferences: {str(e)}")
        finally:
            await delete_command_message(ctx)

    @commands.command()
    async def helppref(self, ctx):
        """Display detailed help for preference settings."""
        help_message = f"""
    ```
    Preference Settings Help
    =======================
    
    Available Settings:
    ------------------
    media_type (mt, type)     : Default media type
        Values: image, video, all
        Example: {ctx.prefix}prefs set mt image
    
    min_size (mins, min)      : Default minimum file size
        Format: number + mb/kb
        Example: {ctx.prefix}prefs set min 2mb
    
    max_size (maxs, max)      : Default maximum file size
        Format: number + mb/kb
        Example: {ctx.prefix}prefs set max 5mb
    
    max_attempts (attempts)    : Maximum API retry attempts
        Format: positive number
        Example: {ctx.prefix}prefs set attempts 50
    
    update_interval (interval) : Progress update interval
        Format: seconds (positive number)
        Example: {ctx.prefix}prefs set interval 5
    
    Commands:
    ---------
    {ctx.prefix}prefs              : Show current preferences
    {ctx.prefix}prefs set <setting> <value> : Update a preference
    {ctx.prefix}prefs reset       : Reset to defaults
    ```
    """
        await ctx.send(help_message, delete_after=60)
        await delete_command_message(ctx)

async def setup(bot):
    await bot.add_cog(PreferenceCommands(bot))