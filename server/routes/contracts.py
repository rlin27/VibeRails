"""Contract endpoints."""

import json

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from server.database import get_db
from server.models import (
    LockedModule,
    LockedModuleCreate,
    MessageResponse,
    ScopeResponse,
    ScopeUpdate,
    Standard,
    StandardCreate,
    StandardUpdate,
)


router = APIRouter(prefix="/contracts", tags=["contracts"])


async def _member_exists(db: aiosqlite.Connection, member_id: int) -> bool:
    cursor = await db.execute(
        "SELECT 1 FROM members WHERE member_id = ?",
        (member_id,),
    )
    return await cursor.fetchone() is not None


async def _get_standard(
    db: aiosqlite.Connection,
    scope: str,
    category: str,
) -> Standard | None:
    cursor = await db.execute(
        """
        SELECT scope, category, content, updated_at
        FROM standards
        WHERE scope = ? AND category = ?
        """,
        (scope, category),
    )
    row = await cursor.fetchone()
    return Standard(**dict(row)) if row is not None else None


def _validate_standard_scope(scope: str) -> str:
    if scope == "global":
        return scope
    if scope.isdigit():
        return scope
    raise HTTPException(status_code=400, detail="scope must be 'global' or a member_id string")


@router.put("/scopes/{member_id}", response_model=ScopeResponse)
async def upsert_scope(
    member_id: int,
    payload: ScopeUpdate,
    db: aiosqlite.Connection = Depends(get_db),
) -> ScopeResponse:
    if not await _member_exists(db, member_id):
        raise HTTPException(status_code=404, detail="member not found")

    await db.execute(
        """
        INSERT INTO scopes (member_id, patterns)
        VALUES (?, ?)
        ON CONFLICT(member_id) DO UPDATE SET patterns = excluded.patterns
        """,
        (member_id, json.dumps(payload.patterns)),
    )
    await db.commit()

    return ScopeResponse(member_id=member_id, patterns=payload.patterns)


@router.get("/scopes/{member_id}", response_model=ScopeResponse)
async def get_scope(
    member_id: int,
    db: aiosqlite.Connection = Depends(get_db),
) -> ScopeResponse:
    cursor = await db.execute(
        "SELECT member_id, patterns FROM scopes WHERE member_id = ?",
        (member_id,),
    )
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="scope not found")

    return ScopeResponse(member_id=row["member_id"], patterns=json.loads(row["patterns"]))


@router.delete("/scopes/{member_id}", response_model=MessageResponse)
async def delete_scope(
    member_id: int,
    db: aiosqlite.Connection = Depends(get_db),
) -> MessageResponse:
    cursor = await db.execute("DELETE FROM scopes WHERE member_id = ?", (member_id,))
    await db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="scope not found")

    return MessageResponse(message="scope deleted")


@router.post("/locked", response_model=LockedModule, status_code=201)
async def create_locked_module(
    payload: LockedModuleCreate,
    db: aiosqlite.Connection = Depends(get_db),
) -> LockedModule:
    try:
        await db.execute(
            """
            INSERT INTO locked_modules (pattern, reason)
            VALUES (?, ?)
            """,
            (payload.pattern, payload.reason),
        )
        await db.commit()
    except aiosqlite.IntegrityError as exc:
        raise HTTPException(status_code=400, detail="locked module already exists") from exc

    return LockedModule(pattern=payload.pattern, reason=payload.reason)


@router.get("/locked", response_model=list[LockedModule])
async def list_locked_modules(
    db: aiosqlite.Connection = Depends(get_db),
) -> list[LockedModule]:
    cursor = await db.execute(
        """
        SELECT pattern, reason
        FROM locked_modules
        ORDER BY pattern
        """
    )
    rows = await cursor.fetchall()
    return [LockedModule(**dict(row)) for row in rows]


@router.delete("/locked/{pattern:path}", response_model=MessageResponse)
async def delete_locked_module(
    pattern: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> MessageResponse:
    cursor = await db.execute("DELETE FROM locked_modules WHERE pattern = ?", (pattern,))
    await db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="locked module not found")

    return MessageResponse(message="locked module deleted")


@router.post("/standards", response_model=Standard, status_code=201)
async def create_standard(
    payload: StandardCreate,
    db: aiosqlite.Connection = Depends(get_db),
) -> Standard:
    scope = _validate_standard_scope(payload.scope)
    if scope != "global" and not await _member_exists(db, int(scope)):
        raise HTTPException(status_code=404, detail="member not found")

    try:
        await db.execute(
            """
            INSERT INTO standards (scope, category, content)
            VALUES (?, ?, ?)
            """,
            (scope, payload.category, payload.content),
        )
        await db.commit()
    except aiosqlite.IntegrityError as exc:
        raise HTTPException(status_code=400, detail="standard already exists") from exc

    standard = await _get_standard(db, scope, payload.category)
    if standard is None:
        raise HTTPException(status_code=500, detail="failed to create standard")

    return standard


@router.get("/standards/{scope}", response_model=list[Standard])
async def list_standards(
    scope: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> list[Standard]:
    normalized_scope = _validate_standard_scope(scope)
    cursor = await db.execute(
        """
        SELECT scope, category, content, updated_at
        FROM standards
        WHERE scope = ?
        ORDER BY category
        """,
        (normalized_scope,),
    )
    rows = await cursor.fetchall()
    return [Standard(**dict(row)) for row in rows]


@router.patch("/standards/{scope}/{category}", response_model=Standard)
async def update_standard(
    scope: str,
    category: str,
    payload: StandardUpdate,
    db: aiosqlite.Connection = Depends(get_db),
) -> Standard:
    normalized_scope = _validate_standard_scope(scope)
    cursor = await db.execute(
        """
        UPDATE standards
        SET content = ?, updated_at = CURRENT_TIMESTAMP
        WHERE scope = ? AND category = ?
        """,
        (payload.content, normalized_scope, category),
    )
    await db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="standard not found")

    standard = await _get_standard(db, normalized_scope, category)
    if standard is None:
        raise HTTPException(status_code=404, detail="standard not found")

    return standard


@router.delete("/standards/{scope}/{category}", response_model=MessageResponse)
async def delete_standard(
    scope: str,
    category: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> MessageResponse:
    normalized_scope = _validate_standard_scope(scope)
    cursor = await db.execute(
        "DELETE FROM standards WHERE scope = ? AND category = ?",
        (normalized_scope, category),
    )
    await db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="standard not found")

    return MessageResponse(message="standard deleted")
