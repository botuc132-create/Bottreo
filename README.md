# Free Fire Account Manager (Telegram)

Starter bot for Railway. It stores up to five Free Fire UIDs and optional labels.
It does **not** log into Free Fire, store passwords/tokens, automate gameplay, or queue ranked matches.

## Setup
1. Create a Telegram bot with @BotFather and copy its token.
2. Get your Telegram numeric user ID using a trusted ID bot or Telegram tooling.
3. Push these files to a private GitHub repository.
4. In Railway, create a project -> Deploy from GitHub repo.
5. Add Variables:
   - `TELEGRAM_BOT_TOKEN` = token from BotFather
   - `ADMIN_IDS` = your numeric Telegram user ID
6. Deploy. Railway detects `Procfile` and runs `python bot.py`.

## Persistence
SQLite at `/tmp` is ephemeral on Railway and may be erased during redeploy. For durable storage, add Railway PostgreSQL and replace the SQLite functions with PostgreSQL, or use a persistent volume. Do not store game passwords or bearer tokens in this starter.

## Commands
- `/start`: show menu
- Add UID: stores a numeric UID and optional label
- List: show saved UIDs
- Delete: remove a saved UID

Keep the repository private and never commit `.env` or real tokens.
