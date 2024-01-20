from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import CallbackContext, ContextTypes, CommandHandler
from cachetools import TTLCache, cached
from db import get_connection, set_value_in_db, get_value_from_db, remove_value_from_db
import logging

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)
# Ustawienie pamięci podręcznej z limitem 100 elementów i czasem życia 10 minut
cache = TTLCache(maxsize=100, ttl=600)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_message = (
        "*Welcome to GroupDataKeeper!* 🤖\n\n"
        "Here's how to use the bot: 👇\n\n"
        "`/set <key> <value>` - Set a new value or update an existing one\n"
        "_Example:_ `/set website https://example.com`\n\n"
        "`/get <key>` - Retrieve the value of a key\n"
        "_Example:_ `/get website`\n\n"
        "`/help` - See all keys that have been set and their retrieval commands\n\n"
        "Use the commands below to manage your group data:"
    )
    commands = [
        "`/start` - Show all commands and usage examples",
        "`/set <key> <value>` - Set a value for a key",
        "`/get <key>` - Get the value of a key",
        "`/help` - Show all keys that have been set"
        # You can add more commands here
    ]

    # Usunięto powtarzające się wywołanie odpowiedzi, pozostawiając tylko jedno
    await update.message.reply_text(
        welcome_message + "\n\n" + "\n".join(commands), parse_mode="Markdown"
    )


async def set_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"Executing /set command with args: {context.args}")
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /set <key> <value>")
        return

    # Sprawdź czy komenda została wywołana w grupie
    if not update.effective_chat.type in ["group", "supergroup"]:
        await update.message.reply_text("This command can only be used in groups.")
        return

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Sprawdź, czy użytkownik jest administratorem
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status not in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
            await update.message.reply_text(
                "You must be an administrator or the owner to use this command."
            )
            return
    except Exception as e:
        await update.message.reply_text(f"Error checking admin status: {e}")
        return

    key, value = context.args
    value = sanitize_value(value)

    try:
        conn = await get_connection()
        await set_value_in_db(conn, chat_id, key, value)
        await conn.commit()
        await update.message.reply_text(f"Value set for {key}")

        # Po zmianie wartości, czyścimy pamięć podręczną
        cache.clear()
    except Exception as e:
        await update.message.reply_text(f"Error occurred: {e}")
    finally:
        await conn.close()


def sanitize_value(value):
    sanitized_value = value.replace(";", "").replace("--", "")
    return sanitized_value[:100]


async def remove_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /remove <key>")
        return

    key = context.args[0]

    try:
        conn = await get_connection()
        await remove_value_from_db(conn, update.effective_chat.id, key)
        await conn.commit()
        await update.message.reply_text(f"Value removed for {key}")

        # Po usunięciu wartości, czyścimy pamięć podręczną
        cache.clear()
    except Exception as e:
        await update.message.reply_text(f"Error occurred: {e}")
    finally:
        await conn.close()


# Używamy dekoratora cached z zadeklarowanym cache
@cached(cache)
async def cached_get_value_from_db(connection, group_id, key):
    return await get_value_from_db(connection, group_id, key)


async def get_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /get <key>")
        return

    key = context.args[0]

    try:
        conn = await get_connection()
        value = await cached_get_value_from_db(conn, update.effective_chat.id, key)
        if value:
            await update.message.reply_text(f"{key}: {value[0]}")
        else:
            await update.message.reply_text(f"No value set for {key}")
    except Exception as e:
        await update.message.reply_text(f"Error occurred: {e}")
    finally:
        await conn.close()


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    key = query.data[len("get_") :]  # Odcina "get_" od callback_data, aby uzyskać klucz
    conn = await get_connection()
    value = await cached_get_value_from_db(conn, query.message.chat_id, key)
    await conn.close()

    text = f"{key}: {value[0]}" if value else f"No value set for {key}"
    await query.edit_message_text(text=text)


# Możesz zdefiniować tę funkcję w pliku commands.py
def get_dynamic_keyboard(keys):
    keyboard = [
        [InlineKeyboardButton(f"Get value for {key}", callback_data=f"get_{key}")]
        for key in keys
    ]
    return InlineKeyboardMarkup(keyboard)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        conn = await get_connection()
        cursor = await conn.execute(
            "SELECT key FROM group_info WHERE group_id = ?", (update.effective_chat.id,)
        )
        rows = await cursor.fetchall()

        if not rows:
            await update.message.reply_text("No keys have been set.")
            return

        # Tworzenie klawiatury dynamicznej na podstawie dostępnych kluczy
        keyboard = get_dynamic_keyboard([row[0] for row in rows])
        await update.message.reply_text(
            "Click on a button to get the value for a key:", reply_markup=keyboard
        )

    except Exception as e:
        await update.message.reply_text(f"Error occurred: {e}")
    finally:
        await conn.close()
