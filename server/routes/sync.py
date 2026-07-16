"""Sync endpoints."""

import json

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from server.database import get_db
from server.models import (
    LockedModule,
    SyncContract,
    SyncLogEntry,
    SyncMember,
    SyncScope,
    SyncStandard,
    SyncStandards,
    SyncStatus,
)


router = APIRouter(prefix="/sync", tags=["sync"])


@router.get("/status", response_model=SyncStatus)
async def get_sync_status(
    db: aiosqlite.Connection = Depends(get_db),
) -> SyncStatus:
    cursor = await db.execute(
        """
        SELECT id, member_id, status, detail, synced_at
        FROM sync_log
        ORDER BY synced_at DESC
        LIMIT 5
        """
    )
    rows = await cursor.fetchall()

    recent_syncs = [SyncLogEntry(**dict(row)) for row in rows]
    overall = "healthy"
    if recent_syncs and recent_syncs[0].status != "success":
        overall = "error"

    return SyncStatus(
        state=overall,
        detail=f"{len(recent_syncs)} recent syncs" if recent_syncs else "No syncs yet",
        recent_syncs=recent_syncs,
    )


@router.get("/{member_id}", response_model=SyncContract)
async def get_member_contract(
    member_id: int,
    db: aiosqlite.Connection = Depends(get_db),
) -> SyncContract:
    member_cursor = await db.execute(
        """
        SELECT member_id, name, role
        FROM members
        WHERE member_id = ?
        """,
        (member_id,),
    )
    member_row = await member_cursor.fetchone()
    if member_row is None:
        raise HTTPException(status_code=404, detail="member not found")

    scope_cursor = await db.execute(
        """
        SELECT patterns
        FROM scopes
        WHERE member_id = ?
        """,
        (member_id,),
    )
    scope_row = await scope_cursor.fetchone()
    patterns = json.loads(scope_row["patterns"]) if scope_row is not None else []

    locked_cursor = await db.execute(
        """
        SELECT pattern, reason
        FROM locked_modules
        ORDER BY pattern
        """
    )
    locked_rows = await locked_cursor.fetchall()

    global_cursor = await db.execute(
        """
        SELECT category, content
        FROM standards
        WHERE scope = 'global'
        ORDER BY category
        """
    )
    global_rows = await global_cursor.fetchall()

    personal_cursor = await db.execute(
        """
        SELECT category, content
        FROM standards
        WHERE scope = ?
        ORDER BY category
        """,
        (str(member_id),),
    )
    personal_rows = await personal_cursor.fetchall()

    await db.execute(
        """
        INSERT INTO sync_log (member_id, status, detail)
        VALUES (?, 'success', 'Contract synced successfully')
        """,
        (member_id,),
    )
    await db.commit()

    return SyncContract(
        member=SyncMember(**dict(member_row)),
        scope=SyncScope(patterns=patterns),
        locked_modules=[LockedModule(**dict(row)) for row in locked_rows],
        standards=SyncStandards(
            global_=[SyncStandard(**dict(row)) for row in global_rows],
            personal=[SyncStandard(**dict(row)) for row in personal_rows],
        ),
    )
