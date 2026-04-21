"""Database helpers for the FastAPI application."""

from collections.abc import AsyncIterator
import os

import aiosqlite


DB_PATH = os.getenv("VIBERAILS_DB_PATH", "./vibrails.db")


async def get_db() -> AsyncIterator[aiosqlite.Connection]:
    """Yield a SQLite connection for request-scoped use."""
    async with aiosqlite.connect(DB_PATH) as connection:
        connection.row_factory = aiosqlite.Row
        yield connection
