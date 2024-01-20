# main.py
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from commands import start, set_value, get_value, help_command, button_handler
import logging

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def main():
    logger.info("Starting bot")
    app = (
        ApplicationBuilder()
        .token("6644951933:AAGtdD7f1pLUzXAziDgNRwZKGo9YXuYPAUI")
        .build()
    )

    # Rejestrowanie handlerów komend
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set", set_value))
    app.add_handler(CommandHandler("get", get_value))
    app.add_handler(CommandHandler("help", help_command))

    # Rejestrowanie handlera dla zapytań zwrotnych od przycisków klawiatury inline
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()


if __name__ == "__main__":
    main()
