"""Chat message endpoints with AI integration."""

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from server.ai_client import call_anthropic, call_openai
from server.crypto_utils import decrypt_value
from server.database import get_db
from server.models import ChatMessage, ChatSendRequest, ChatSendResponse


router = APIRouter(prefix="/chat", tags=["chat"])


async def _get_active_provider(
    db: aiosqlite.Connection, provider_id: int | None = None
) -> dict | None:
    if provider_id is not None:
        cursor = await db.execute(
            "SELECT * FROM ai_providers WHERE id = ? AND is_active = 1",
            (provider_id,),
        )
    else:
        cursor = await db.execute(
            "SELECT * FROM ai_providers WHERE is_active = 1 ORDER BY id LIMIT 1"
        )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def _get_chat_history(
    db: aiosqlite.Connection, feature_id: str, limit: int = 50
) -> list[dict]:
    cursor = await db.execute(
        """
        SELECT author_role, content FROM chat_messages
        WHERE feature_id = ?
        ORDER BY created_at ASC
        LIMIT ?
        """,
        (feature_id, limit),
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


@router.get("/{feature_id}", response_model=list[ChatMessage])
async def get_chat_messages(
    feature_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> list[ChatMessage]:
    cursor = await db.execute(
        """
        SELECT id, feature_id, author_name, author_role, content, created_at
        FROM chat_messages
        WHERE feature_id = ?
        ORDER BY created_at ASC
        """,
        (feature_id,),
    )
    rows = await cursor.fetchall()
    return [ChatMessage(**dict(row)) for row in rows]


@router.get("/{feature_id}/since/{message_id}", response_model=list[ChatMessage])
async def get_chat_messages_since(
    feature_id: str,
    message_id: int,
    db: aiosqlite.Connection = Depends(get_db),
) -> list[ChatMessage]:
    cursor = await db.execute(
        """
        SELECT id, feature_id, author_name, author_role, content, created_at
        FROM chat_messages
        WHERE feature_id = ? AND id > ?
        ORDER BY created_at ASC
        """,
        (feature_id, message_id),
    )
    rows = await cursor.fetchall()
    return [ChatMessage(**dict(row)) for row in rows]


@router.post("/send", response_model=ChatSendResponse)
async def send_chat_message(
    payload: ChatSendRequest,
    db: aiosqlite.Connection = Depends(get_db),
) -> ChatSendResponse:
    if not payload.content.strip():
        raise HTTPException(status_code=400, detail="message cannot be empty")

    # Insert user message
    user_cursor = await db.execute(
        """
        INSERT INTO chat_messages (feature_id, author_name, author_role, content)
        VALUES (?, ?, 'user', ?)
        """,
        (payload.feature_id, "User", payload.content),
    )
    await db.commit()

    # Fetch the inserted user message
    user_row_cursor = await db.execute(
        "SELECT id, feature_id, author_name, author_role, content, created_at FROM chat_messages WHERE id = ?",
        (user_cursor.lastrowid,),
    )
    user_row = await user_row_cursor.fetchone()
    if user_row is None:
        raise HTTPException(status_code=500, detail="failed to save message")
    user_message = ChatMessage(**dict(user_row))

    # Get active AI provider
    provider = await _get_active_provider(db, payload.provider_id)
    if provider is None:
        raise HTTPException(
            status_code=503,
            detail="No active AI provider configured. Please add one in AI Settings.",
        )

    # Get conversation history
    history = await _get_chat_history(db, payload.feature_id)

    # Call AI
    try:
        api_key = decrypt_value(provider["api_key_encrypted"])
        if provider["protocol"] == "anthropic":
            response_content = await call_anthropic(
                api_key, provider["api_base_url"], provider["model"], history
            )
        else:
            response_content = await call_openai(
                api_key, provider["api_base_url"], provider["model"], history
            )
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"AI provider error: {exc}"
        ) from exc

    # Insert assistant message
    ai_cursor = await db.execute(
        """
        INSERT INTO chat_messages (feature_id, author_name, author_role, content)
        VALUES (?, ?, 'assistant', ?)
        """,
        (payload.feature_id, "AI Assistant", response_content),
    )
    await db.commit()

    ai_row_cursor = await db.execute(
        "SELECT id, feature_id, author_name, author_role, content, created_at FROM chat_messages WHERE id = ?",
        (ai_cursor.lastrowid,),
    )
    ai_row = await ai_row_cursor.fetchone()
    if ai_row is None:
        raise HTTPException(status_code=500, detail="failed to save AI response")
    assistant_message = ChatMessage(**dict(ai_row))

    return ChatSendResponse(
        user_message=user_message,
        assistant_message=assistant_message,
    )
