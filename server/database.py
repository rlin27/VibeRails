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

        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS sync_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER REFERENCES members(member_id),
                status TEXT NOT NULL DEFAULT 'success',
                detail TEXT,
                synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # --- Features ---
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS features (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'planned'
                    CHECK(status IN ('planned', 'in_progress', 'stable', 'deprecated')),
                owner_id INTEGER REFERENCES members(member_id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS feature_interfaces (
                feature_id TEXT NOT NULL REFERENCES features(id) ON DELETE CASCADE,
                interface_id INTEGER NOT NULL REFERENCES interfaces(id) ON DELETE CASCADE,
                PRIMARY KEY (feature_id, interface_id)
            )
            """
        )

        # --- AI Providers ---
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_providers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                api_base_url TEXT NOT NULL,
                api_key_encrypted TEXT NOT NULL,
                model TEXT NOT NULL DEFAULT 'claude-sonnet-4-20250514',
                protocol TEXT NOT NULL DEFAULT 'anthropic'
                    CHECK(protocol IN ('anthropic', 'openai')),
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # --- Chat Messages ---
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature_id TEXT NOT NULL,
                author_name TEXT NOT NULL,
                author_role TEXT NOT NULL DEFAULT 'user'
                    CHECK(author_role IN ('user', 'assistant', 'system')),
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        await connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_chat_feature
            ON chat_messages(feature_id, created_at)
            """
        )

        # --- Issues ---
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'open'
                    CHECK(status IN ('open', 'in_progress', 'resolved', 'closed')),
                assignee_id INTEGER REFERENCES members(member_id),
                feature_id TEXT,
                interface_id INTEGER REFERENCES interfaces(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # --- Issue Comments ---
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS issue_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_id INTEGER NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
                author_name TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        await connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_issue_comments
            ON issue_comments(issue_id, created_at)
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
