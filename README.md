# Based Count Bot (Discord)

https://discord.com/oauth2/authorize?client_id=1465591527446155264
A Discord bot that tracks "based" and "cringe" counts for users and collects "pills" (text associated with being based).

This project is inspired by the Reddit bot [basedcount_bot](https://github.com/basedcount/basedcount_bot).

## Features

- **Track Counts**: Tracks how many times a user has been called "based" or "cringe".
- **Pills**: Captures text following the word "based" as a "pill" (e.g., "based and redpilled").
- **Leaderboard**: Displays the top 5 most based users in the server.
- **Profiles**: View your own or another user's stats and pill history.
- **Persistence**: Uses a local SQLite database (`based_count.db`) to store data.

## Commands

- `!mybased`: Shows your current based count, cringe count, and recent pills.
- `!checkbased @user`: Checks the profile of a specific user.
- `!leaderboard`: Shows the top 5 users by based count.

## Usage

To give someone a count:
1. **Reply** to their message with "based" or "cringe".
2. **Mention** them in a message starting with "based" or "cringe" (e.g., `@User based`).

To add a pill:
- Reply with "based and [text]" (e.g., "based and logic pilled").

## Setup

1. **Clone the repository** (or download the files).

2. **Install dependencies**:
   It is recommended to use a virtual environment.
   ```bash
   pip install discord.py aiosqlite python-dotenv
   ```

3. **Configuration**:
   Create a `.env` file in the root directory and add your Discord bot token:
   ```env
   bot_token=YOUR_DISCORD_BOT_TOKEN
   ```

4. **Run the bot**:
   ```bash
   python main.py
   ```

## License

MIT