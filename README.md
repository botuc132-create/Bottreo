# Free Fire Manager V2

This version adds:
- add up to five UIDs
- select up to four UIDs
- Run / Stop control state
- status and delete menus

Important: Run/Stop currently controls the bot's orchestration flag only. It does not launch Free Fire or automate ranked matches. A separate compatible game-running environment and supported control interface would be required.

## Railway
1. Upload these files to your private GitHub repo, replacing the previous files.
2. Railway redeploys from the connected repo.
3. Set Variables:
   - TELEGRAM_BOT_TOKEN = token from @BotFather
   - ADMIN_IDS = your numeric Telegram user ID
4. Check deploy logs, then send /start to your bot.

## Data persistence
The default JSON file under /tmp is ephemeral. For durable storage, migrate to PostgreSQL or a persistent volume.
Never put passwords or JWT/access tokens into chat or source code.
