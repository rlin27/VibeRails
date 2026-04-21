"""Member endpoints."""

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from server.database import get_db
from server.models import Member, MemberCreate, MessageResponse


router = APIRouter(prefix="/members", tags=["members"])


@router.get("/", response_model=list[Member])
async def list_members(
    db: aiosqlite.Connection = Depends(get_db),
) -> list[Member]:
    cursor = await db.execute(
        """
        SELECT member_id, name, role, created_at
        FROM members
        ORDER BY member_id
        """
    )
    rows = await cursor.fetchall()
    return [Member(**dict(row)) for row in rows]


@router.post("/", response_model=Member, status_code=201)
async def create_member(
    payload: MemberCreate,
    db: aiosqlite.Connection = Depends(get_db),
) -> Member:
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="name cannot be empty")

    cursor = await db.execute(
        """
        INSERT INTO members (name, role)
        VALUES (?, ?)
        """,
        (payload.name.strip(), payload.role),
    )
    await db.commit()

    member_cursor = await db.execute(
        """
        SELECT member_id, name, role, created_at
        FROM members
        WHERE member_id = ?
        """,
        (cursor.lastrowid,),
    )
    row = await member_cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=500, detail="failed to create member")

    return Member(**dict(row))


@router.get("/{member_id}", response_model=Member)
async def get_member(
    member_id: int,
    db: aiosqlite.Connection = Depends(get_db),
) -> Member:
    cursor = await db.execute(
        """
        SELECT member_id, name, role, created_at
        FROM members
        WHERE member_id = ?
        """,
        (member_id,),
    )
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="member not found")

    return Member(**dict(row))


@router.delete("/{member_id}", response_model=MessageResponse)
async def delete_member(
    member_id: int,
    db: aiosqlite.Connection = Depends(get_db),
) -> MessageResponse:
    cursor = await db.execute(
        "SELECT member_id FROM members WHERE member_id = ?",
        (member_id,),
    )
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="member not found")

    await db.execute("DELETE FROM scopes WHERE member_id = ?", (member_id,))
    await db.execute("DELETE FROM standards WHERE scope = ?", (str(member_id),))
    await db.execute("DELETE FROM members WHERE member_id = ?", (member_id,))
    await db.commit()

    return MessageResponse(message="member deleted")
