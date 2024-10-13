Immich Discord Selfbot
================
Immich Discord Selfbot is Discord bot designed to manage and interact with assets stored on your immich server. It provides functionality to fetch random assets, get specific assets, mark assets as favorites, delete assets, and view server statistics.

## Features

- Fetch and display random assets
- Get specific assets by ID
- Mark assets as favorites
- Delete assets
- View server statistics
- Help command for easy reference

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

4. Edit the `.env` file and fill in your actual API keys, Discord bot token, and base URL:
   ```
   BASE_URL=https://photos.boker.xyz
   API_KEY=your_regular_api_key
   ADMIN_API_KEY=your_admin_api_key
   DISCORD_TOKEN=your_discord_user_token
   ```

5. Run the bot:
   ```
   python main.py
   ```

### Using Docker

1. Clone the repository:
   ```
   git clone https://github.com/jakedev796/immich-discord-selfbot.git
   cd immich-discord-selfbot
   ```

2. Copy the `.env.sample` file to `.env` and edit it as described in step 4 of the Python installation.

3. Build and run the Docker container:
   ```
   docker-compose up --build
   ```
## Immich API

You will need an API key from Immich for this bot to work.

1. Go to your Immich server and log in.
2. Click on your profile picture in the top right corner and select "Account Settings".
3. Scroll down to the "API Keys" section and click "New API Key".
4. Enter a name for the API key and click "Create".
5. Copy the API key and use it in the `.env` file.
6. If you want to access server statistics, you will need to create an admin API key. This can be done from the original creator of the Immich server.

## Discord Token

You can find guides online on how to get your Discord user token. This token is used to log in to Discord and send messages on your behalf. Be careful with your token and do not share it with anyone.

## Usage

The bot responds to the following commands:

- `?random`: Fetches and displays a random asset
- `?get <asset_id>`: Fetches and displays a specific asset
- `?favorite <asset_id OR last>`: Marks an asset as a favorite
- `?delete <asset_id OR last>`: Deletes a specific asset
- `?stats`: Displays server statistics
- `?help`: Shows a help message with available commands

## Environment Variables

The bot uses the following environment variables, which should be set in the `.env` file:

- `BASE_URL`: The base URL of the asset server
- `API_KEY`: The regular API key for accessing the asset server
- `ADMIN_API_KEY`: The admin API key for accessing server statistics
- `DISCORD_TOKEN`: Your Discord user token

## Disclaimer: Use of Discord Selfbots

This repository contains code that may be used for Discord selfbots, which are against Discord's [Terms of Service](https://discord.com/terms). Using a selfbot can result in your account being banned or suspended. The creator and contributors are not responsible for any consequences, including account bans or data loss. Use this code at your own risk and for educational purposes only.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues or have questions, please open an issue on the GitHub repository.