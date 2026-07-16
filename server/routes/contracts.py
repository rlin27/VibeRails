"""Contract endpoints."""

import json

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from server.database import get_db
from server.models import (
    Interface,
    InterfaceUpdate,
    InterfaceUploadRequest,
    InterfaceUploadResponse,
    LockedModule,
    LockedModuleCreate,
    MessageResponse,
    PaginatedInterfaces,
    PlannedInterfaceCreate,
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


async def _get_interface(
    db: aiosqlite.Connection,
    interface_id: int,
) -> Interface | None:
    cursor = await db.execute(
        """
        SELECT
            interfaces.id,
            interfaces.file_path,
            interfaces.signature,
            interfaces.description,
            interfaces.status,
            interfaces.owner_id,
            members.name AS owner_name,
            interfaces.updated_at
        FROM interfaces
        LEFT JOIN members ON members.member_id = interfaces.owner_id
        WHERE interfaces.id = ?
        """,
        (interface_id,),
    )
    row = await cursor.fetchone()
    return Interface(**dict(row)) if row is not None else None


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


@router.post("/interfaces/upload", response_model=InterfaceUploadResponse)
async def upload_interfaces(
    payload: InterfaceUploadRequest,
    db: aiosqlite.Connection = Depends(get_db),
) -> InterfaceUploadResponse:
    inserted = 0
    deprecated = 0
    skipped = 0

    scanned_by_file: dict[str, set[str]] = {}
    for item in payload.interfaces:
        scanned_by_file.setdefault(item.file_path, set()).add(item.signature)

        cursor = await db.execute(
            """
            SELECT id
            FROM interfaces
            WHERE file_path = ? AND signature = ?
            """,
            (item.file_path, item.signature),
        )
        if await cursor.fetchone() is not None:
            skipped += 1
            continue

        await db.execute(
            """
            INSERT INTO interfaces (file_path, signature, status)
            VALUES (?, ?, 'stable')
            """,
            (item.file_path, item.signature),
        )
        inserted += 1

    for file_path, current_signatures in scanned_by_file.items():
        existing_cursor = await db.execute(
            """
            SELECT signature, status
            FROM interfaces
            WHERE file_path = ?
            """,
            (file_path,),
        )
        existing_rows = await existing_cursor.fetchall()
        for row in existing_rows:
            if row["signature"] in current_signatures or row["status"] in {
                "deprecated",
                "planned",
            }:
                continue

            await db.execute(
                """
                UPDATE interfaces
                SET status = 'deprecated', updated_at = CURRENT_TIMESTAMP
                WHERE file_path = ? AND signature = ?
                """,
                (file_path, row["signature"]),
            )
            deprecated += 1

    await db.commit()
    return InterfaceUploadResponse(
        inserted=inserted,
        deprecated=deprecated,
        skipped=skipped,
    )


@router.get("/interfaces")
async def list_interfaces(
    limit: int = 0,
    offset: int = 0,
    search: str | None = None,
    status: str | None = None,
    owner_id: int | None = None,
    db: aiosqlite.Connection = Depends(get_db),
) -> list[Interface] | PaginatedInterfaces:
    conditions: list[str] = []
    params: list[str | int] = []

    if search:
        conditions.append("(interfaces.file_path LIKE ? OR interfaces.signature LIKE ?)")
        like = f"%{search}%"
        params.append(like)
        params.append(like)
    if status:
        conditions.append("interfaces.status = ?")
        params.append(status)
    if owner_id is not None:
        conditions.append("interfaces.owner_id = ?")
        params.append(owner_id)

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    base_query = f"""
        SELECT
            interfaces.id,
            interfaces.file_path,
            interfaces.signature,
            interfaces.description,
            interfaces.status,
            interfaces.owner_id,
            members.name AS owner_name,
            interfaces.updated_at
        FROM interfaces
        LEFT JOIN members ON members.member_id = interfaces.owner_id
        WHERE {where_clause}
    """

    count_cursor = await db.execute(
        f"SELECT COUNT(*) FROM ({base_query})",
        params,
    )
    count_row = await count_cursor.fetchone()
    total = count_row[0] if count_row else 0

    if limit > 0:
        query = f"{base_query} ORDER BY interfaces.file_path, interfaces.signature LIMIT ? OFFSET ?"
        data_params = params + [limit, offset]
    else:
        query = f"{base_query} ORDER BY interfaces.file_path, interfaces.signature"
        data_params = params

    cursor = await db.execute(query, data_params)
    rows = await cursor.fetchall()

    if limit > 0:
        return PaginatedInterfaces(
            items=[Interface(**dict(row)) for row in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    return [Interface(**dict(row)) for row in rows]


@router.patch("/interfaces/{interface_id}", response_model=Interface)
async def update_interface(
    interface_id: int,
    payload: InterfaceUpdate,
    db: aiosqlite.Connection = Depends(get_db),
) -> Interface:
    existing = await _get_interface(db, interface_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="interface not found")

    if payload.owner_id is not None and not await _member_exists(db, payload.owner_id):
        raise HTTPException(status_code=404, detail="owner not found")

    await db.execute(
        """
        UPDATE interfaces
        SET status = ?,
            owner_id = ?,
            description = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (payload.status, payload.owner_id, payload.description, interface_id),
    )
    await db.commit()

    updated = await _get_interface(db, interface_id)
    if updated is None:
        raise HTTPException(status_code=404, detail="interface not found")
    return updated


@router.post("/interfaces/planned", response_model=Interface, status_code=201)
async def create_planned_interface(
    payload: PlannedInterfaceCreate,
    db: aiosqlite.Connection = Depends(get_db),
) -> Interface:
    if payload.owner_id is not None and not await _member_exists(db, payload.owner_id):
        raise HTTPException(status_code=404, detail="owner not found")

    try:
        cursor = await db.execute(
            """
            INSERT INTO interfaces (
                file_path,
                signature,
                description,
                owner_id,
                status
            )
            VALUES (?, ?, ?, ?, 'planned')
            """,
            (
                payload.file_path,
                payload.signature,
                payload.description,
                payload.owner_id,
            ),
        )
        await db.commit()
    except aiosqlite.IntegrityError as exc:
        raise HTTPException(status_code=400, detail="interface already exists") from exc

    created = await _get_interface(db, cursor.lastrowid)
    if created is None:
        raise HTTPException(status_code=500, detail="failed to create interface")
    return created


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
