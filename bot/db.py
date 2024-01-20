import aiosqlite
import os
import logging

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def get_connection():
    logger.info("Establishing database connection")
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(parent_dir, "group_data.db")
    connection = await aiosqlite.connect(db_path)
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS group_info (
            group_id INTEGER,
            key TEXT,
            value TEXT,
            PRIMARY KEY (group_id, key)
        )
        """
    )
    await connection.commit()
    return connection


async def set_value_in_db(connection, group_id, key, value):
    logger.info(f"Setting value in DB for group_id: {group_id}, key: {key}")
    await connection.execute(
        "REPLACE INTO group_info (group_id, key, value) VALUES (?, ?, ?)",
        (group_id, key, value),
    )


async def get_value_from_db(connection, group_id, key):
    cursor = await connection.execute(
        "SELECT value FROM group_info WHERE group_id = ? AND key = ?",
        (group_id, key),
    )
    return await cursor.fetchone()
