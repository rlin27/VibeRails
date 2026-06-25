"""Database helpers for the FastAPI application."""

from collections.abc import AsyncIterator
import os
from pathlib import Path

import aiosqlite


DB_PATH = os.getenv("DB_PATH", "./data/vibrails.db")


def _resolve_db_path() -> Path:
    """Resolve the configured database path and create its parent directory."""
    db_path = Path(DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


async def init_db() -> None:
    """Create all database tables required by the application."""
    db_path = _resolve_db_path()

    async with aiosqlite.connect(db_path) as connection:
        await connection.execute("PRAGMA foreign_keys = ON")

        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS members (
                member_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('owner', 'member')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS scopes (
                member_id INTEGER PRIMARY KEY REFERENCES members(member_id),
                patterns TEXT NOT NULL DEFAULT '[]'
            )
            """
        )

        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS locked_modules (
                pattern TEXT PRIMARY KEY,
                reason TEXT
            )
            """
        )

        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS standards (
                scope TEXT NOT NULL,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (scope, category)
            )
            """
        )

        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS interfaces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                signature TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'stable'
                    CHECK(status IN ('stable', 'in_progress', 'planned', 'deprecated')),
                owner_id INTEGER REFERENCES members(member_id),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(file_path, signature)
            )
            """
        )

        await connection.commit()


async def get_db() -> AsyncIterator[aiosqlite.Connection]:
    """Yield a SQLite connection for request-scoped use."""
    db_path = _resolve_db_path()

    async with aiosqlite.connect(db_path) as connection:
        await connection.execute("PRAGMA foreign_keys = ON")
        connection.row_factory = aiosqlite.Row
        yield connection
