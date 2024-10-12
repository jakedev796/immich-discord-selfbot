import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

# Print Python path and version for debugging
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")

# Create the bot with chunk_guilds_at_startup set to False and help_command set to None
bot = commands.Bot(
    command_prefix='?',
    self_bot=True,
    chunk_guilds_at_startup=False,
    request_guilds=False,
    help_command=None  # This allows us to use our custom help command
)

@bot.event
async def on_ready():
    """
    Event that triggers when the bot is ready and connected to Discord.
    """
    print(f'Logged in as {bot.user.name}')
    await bot.load_extension('cogs.asset_commands')

# Print the token (first 10 characters) for debugging
token = os.getenv('DISCORD_TOKEN')
print(f"Token (first 10 characters): {token[:10]}...")

# Run the bot
try:
    bot.run(token)
except discord.errors.LoginFailure as e:
    print(f"Login failed. Error: {e}")
    print("Please check your token and make sure it's correct.")