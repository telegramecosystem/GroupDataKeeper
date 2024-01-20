# main.py
import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from commands import (
    start,
    set_value,
    get_value,
    help_command,
    button_handler,
    remove_value,
)
import logging

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Load .env file which is one directory above the current directory
dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path)


def main():
    logger.info("Starting bot")
    # Use the token from the .env file
    bot_token = os.getenv("TELEGRAM_TOKEN")
    app = ApplicationBuilder().token(bot_token).build()

    # Rejestrowanie handlerów komend
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set", set_value))
    app.add_handler(CommandHandler("get", get_value))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("remove", remove_value))

    # Rejestrowanie handlera dla zapytań zwrotnych od przycisków klawiatury inline
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()


if __name__ == "__main__":
    main()
