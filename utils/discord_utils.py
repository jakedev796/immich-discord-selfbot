import discord
from typing import Optional
import logging
import io

logger = logging.getLogger(__name__)

async def send_error_message(ctx: discord.ext.commands.Context, message: str, delete_after: int = 10) -> None:
    """Send an error message that deletes itself after a delay."""
    try:
        await ctx.send(message, delete_after=delete_after)
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")

async def delete_command_message(ctx: discord.ext.commands.Context) -> None:
    """Delete the command message."""
    try:
        await ctx.message.delete()
    except Exception as e:
        logger.error(f"Failed to delete command message: {str(e)}")

async def update_progress_message(message: Optional[discord.Message],
                                  content: str) -> Optional[discord.Message]:
    """Update a progress message, return the message object."""
    if message is None:
        return None

    try:
        return await message.edit(content=content)
    except Exception as e:
        logger.error(f"Error updating progress message: {str(e)}")
        return message

async def send_file_to_discord(ctx: discord.ext.commands.Context,
                               file_data: bytes,
                               filename: str,
                               content: Optional[str] = None) -> Optional[discord.Message]:
    """Send a file to Discord channel."""
    try:
        file = discord.File(io.BytesIO(file_data), filename=filename)
        return await ctx.send(content=content, file=file)
    except Exception as e:
        logger.error(f"Error sending file: {str(e)}")
        return None