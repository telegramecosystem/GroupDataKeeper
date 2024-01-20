# keyboards.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_help_keyboard(keys):
    # Create an inline keyboard with buttons for each command
    keyboard = [
        [InlineKeyboardButton(text=f"/get {key}", callback_data=f"get_{key}")]
        for key in keys
    ]
    return InlineKeyboardMarkup(keyboard)
