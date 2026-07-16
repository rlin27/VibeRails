"""AI provider configuration endpoints."""

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from server.ai_client import call_anthropic, call_openai
from server.crypto_utils import decrypt_value, encrypt_value
from server.database import get_db
from server.models import (
    AIProvider,
    AIProviderCreate,
    AIProviderTestResult,
    AIProviderUpdate,
)


router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/providers", response_model=list[AIProvider])
async def list_providers(
    db: aiosqlite.Connection = Depends(get_db),
) -> list[AIProvider]:
    cursor = await db.execute(
        "SELECT id, name, api_base_url, model, protocol, is_active, created_at, updated_at FROM ai_providers ORDER BY id"
    )
    rows = await cursor.fetchall()
    return [AIProvider(**dict(row)) for row in rows]


@router.post("/providers", response_model=AIProvider, status_code=201)
async def create_provider(
    payload: AIProviderCreate,
    db: aiosqlite.Connection = Depends(get_db),
) -> AIProvider:
    encrypted = encrypt_value(payload.api_key)
    cursor = await db.execute(
        """
        INSERT INTO ai_providers (name, api_base_url, api_key_encrypted, model, protocol, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            payload.name,
            payload.api_base_url,
            encrypted,
            payload.model,
            payload.protocol,
            int(payload.is_active),
        ),
    )
    await db.commit()

    result_cursor = await db.execute(
        "SELECT id, name, api_base_url, model, protocol, is_active, created_at, updated_at FROM ai_providers WHERE id = ?",
        (cursor.lastrowid,),
    )
    row = await result_cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=500, detail="failed to create provider")
    return AIProvider(**dict(row))


@router.patch("/providers/{provider_id}", response_model=AIProvider)
async def update_provider(
    provider_id: int,
    payload: AIProviderUpdate,
    db: aiosqlite.Connection = Depends(get_db),
) -> AIProvider:
    existing = await db.execute(
        "SELECT id FROM ai_providers WHERE id = ?", (provider_id,)
    )
    if await existing.fetchone() is None:
        raise HTTPException(status_code=404, detail="provider not found")

    updates: list[str] = []
    params: list[str | int] = []

    if payload.name is not None:
        updates.append("name = ?")
        params.append(payload.name)
    if payload.api_base_url is not None:
        updates.append("api_base_url = ?")
        params.append(payload.api_base_url)
    if payload.api_key is not None:
        updates.append("api_key_encrypted = ?")
        params.append(encrypt_value(payload.api_key))
    if payload.model is not None:
        updates.append("model = ?")
        params.append(payload.model)
    if payload.protocol is not None:
        updates.append("protocol = ?")
        params.append(payload.protocol)
    if payload.is_active is not None:
        updates.append("is_active = ?")
        params.append(int(payload.is_active))

    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(provider_id)
        await db.execute(
            f"UPDATE ai_providers SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        await db.commit()

    result_cursor = await db.execute(
        "SELECT id, name, api_base_url, model, protocol, is_active, created_at, updated_at FROM ai_providers WHERE id = ?",
        (provider_id,),
    )
    row = await result_cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="provider not found")
    return AIProvider(**dict(row))


@router.delete("/providers/{provider_id}")
async def delete_provider(
    provider_id: int,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict[str, str]:
    cursor = await db.execute(
        "DELETE FROM ai_providers WHERE id = ?", (provider_id,)
    )
    await db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="provider not found")
    return {"message": "provider deleted"}


@router.post("/providers/test", response_model=AIProviderTestResult)
async def test_provider(
    payload: AIProviderCreate,
    db: aiosqlite.Connection = Depends(get_db),
) -> AIProviderTestResult:
    try:
        test_messages = [{"author_role": "user", "content": "Reply with exactly: OK"}]
        if payload.protocol == "anthropic":
            await call_anthropic(
                payload.api_key, payload.api_base_url, payload.model, test_messages
            )
        else:
            await call_openai(
                payload.api_key, payload.api_base_url, payload.model, test_messages
            )
        return AIProviderTestResult(success=True, message="Connection successful")
    except Exception as exc:
        return AIProviderTestResult(
            success=False, message=f"Connection failed: {exc}"
        )
