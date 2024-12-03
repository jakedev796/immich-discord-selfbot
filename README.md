Immich Discord Selfbot
================
Immich Discord Selfbot is Discord bot designed to manage and interact with assets stored on your immich server. It provides functionality to fetch random assets, get specific assets, mark assets as favorites, delete assets, and view server statistics.

## Features

- Fetch and display random assets with filtering options:
   - Filter by media type (image/video)
   - Filter by file size (min/max)
   - Fetch multiple assets at once
- Get specific assets by ID
- Mark assets as favorites
- Delete assets
- View server statistics
- User-specific preferences
- Help commands for easy reference

## Prerequisites

- Python 3.7 or higher
- [Immich](https://github.com/immich-app/immich)
- Docker (optional)

## Installation

### Using Python

1. Clone the repository:
   ```
   git clone https://github.com/jakedev796/immich-discord-selfbot.git
   cd immich-discord-selfbot
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Copy the `.env.sample` file to `.env`:
   ```
   cp .env.sample .env
   ```

4. Copy the preferences template:
   ```
   mkdir -p data
   cp data/preferences.json.example data/preferences.json
   ```

5. Edit the `.env` file and fill in your actual API keys, Discord bot token, and base URL:
   ```
   BASE_URL=https://photos.example.com
   API_KEY=your_regular_api_key
   ADMIN_API_KEY=your_admin_api_key
   DISCORD_TOKEN=your_discord_user_token
   MAX_FILE_SIZE_MB=499
   BOT_PREFIX=.
   ```

6. Run the bot:
   ```
   python main.py
   ```

### Using Docker

1. Clone the repository:
   ```
   git clone https://github.com/jakedev796/immich-discord-selfbot.git
   cd immich-discord-selfbot
   ```

2. Copy and edit the configuration files:
   ```
   cp .env.sample .env
   mkdir -p data
   cp data/preferences.json.example data/preferences.json
   ```

3. Edit the `.env` file as described in step 5 of the Python installation.

4. Build and run the Docker container:
   ```
   docker-compose up --build
   ```

## Usage

The bot responds to the following commands:

### Core Commands
- `.random [options]`: Fetches and displays random assets
   - Options:
      - `min:size`: Minimum file size (e.g., min:2mb, min:500kb)
      - `max:size`: Maximum file size (e.g., max:5mb, max:900kb)
      - `image/video`: Asset type filter
      - `count:n`: Number of assets to fetch (max 10)
   - Example: `.random min:2mb max:5mb image count:3`
- `.get <asset_id>`: Fetches and displays a specific asset
- `.favorite <asset_id|last>`: Marks an asset as a favorite
- `.unfavorite <asset_id|last>`: Removes an asset from favorites
- `.delete <asset_id|last>`: Deletes a specific asset
- `.stats`: Displays server statistics

### Preference Commands
- `.prefs`: Show current preferences
- `.prefs set <setting> <value>`: Update a preference
   - Available settings:
      - `media_type` (aliases: mt, type): Default media type (image, video, all)
      - `min_size` (aliases: mins, min): Default minimum file size
      - `max_size` (aliases: maxs, max): Default maximum file size
      - `max_attempts` (aliases: attempts, retry): Maximum API retry attempts
      - `update_interval` (aliases: interval, update): Progress update interval
- `.prefs reset`: Reset preferences to defaults
- `.helppref`: Show detailed preference help

### Help Commands
- `.help`: Shows general help message
- `.helppref`: Shows detailed preference settings help

## Environment Variables

The bot uses the following environment variables, which should be set in the `.env` file:

- `BASE_URL`: The base URL of the asset server
- `API_KEY`: The regular API key for accessing the asset server
- `ADMIN_API_KEY`: The admin API key for accessing server statistics
- `DISCORD_TOKEN`: Your Discord user token
- `MAX_FILE_SIZE_MB`: Maximum file size for uploads (based on your Discord account type)
- `BOT_PREFIX`: Command prefix for the bot (default is '.')

## User Preferences

User preferences are stored in `data/preferences.json`. The following preferences can be configured:

- Default media type (image/video/all)
- Minimum file size
- Maximum file size
- Maximum API retry attempts
- Progress update interval

## Disclaimer: Use of Discord Selfbots

This repository contains code that may be used for Discord selfbots, which are against Discord's [Terms of Service](https://discord.com/terms). Using a selfbot can result in your account being banned or suspended. The creator and contributors are not responsible for any consequences, including account bans or data loss. Use this code at your own risk and for educational purposes only.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues or have questions, please open an issue on the GitHub repository.