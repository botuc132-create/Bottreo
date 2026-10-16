# Free Fire Account Manager for Railway

## Deploy
1. Upload these files to a private GitHub repository.
2. In Railway, create a project from that repository.
3. In the service Variables, set:
   - `TELEGRAM_BOT_TOKEN`: token from @BotFather
   - `ADMIN_IDS`: your numeric Telegram user ID
4. Deploy and open the bot; send `/start`.

This is an account-list manager for up to five UIDs. It does not log into Free Fire or automate ranked gameplay.

## Note on storage
The default SQLite path `/tmp/accounts.db` is ephemeral on Railway. For durable storage, configure PostgreSQL or a persistent volume before relying on it.
