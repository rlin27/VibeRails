"""Feature management endpoints (migrated from localStorage)."""

import json

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from server.database import get_db
from server.models import (
    Feature,
    FeatureCreate,
    FeatureInterfaceLink,
    FeatureUpdate,
)


router = APIRouter(prefix="/features", tags=["features"])


@router.get("/", response_model=list[Feature])
async def list_features(
    db: aiosqlite.Connection = Depends(get_db),
) -> list[Feature]:
    cursor = await db.execute(
        """
        SELECT features.*, members.name AS owner_name
        FROM features
        LEFT JOIN members ON members.member_id = features.owner_id
        ORDER BY features.created_at DESC
        """
    )
    rows = await cursor.fetchall()
    features: list[Feature] = []
    for row in rows:
        feature = Feature(**dict(row))
        # Load associated interface IDs
        iface_cursor = await db.execute(
            "SELECT interface_id FROM feature_interfaces WHERE feature_id = ?",
            (feature.id,),
        )
        iface_rows = await iface_cursor.fetchall()
        feature.interface_ids = [r["interface_id"] for r in iface_rows]
        features.append(feature)
    return features


@router.post("/", response_model=Feature, status_code=201)
async def create_feature(
    payload: FeatureCreate,
    db: aiosqlite.Connection = Depends(get_db),
) -> Feature:
    import uuid

    feature_id = payload.id or str(uuid.uuid4())

    await db.execute(
        """
        INSERT INTO features (id, name, description, status, owner_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        (feature_id, payload.name.strip(), payload.description, payload.status, payload.owner_id),
    )
    await db.commit()

    result_cursor = await db.execute(
        """
        SELECT features.*, members.name AS owner_name
        FROM features
        LEFT JOIN members ON members.member_id = features.owner_id
        WHERE features.id = ?
        """,
        (feature_id,),
    )
    row = await result_cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=500, detail="failed to create feature")
    return Feature(**dict(row), interface_ids=[])


@router.patch("/{feature_id}", response_model=Feature)
async def update_feature(
    feature_id: str,
    payload: FeatureUpdate,
    db: aiosqlite.Connection = Depends(get_db),
) -> Feature:
    existing = await db.execute(
        "SELECT id FROM features WHERE id = ?", (feature_id,)
    )
    if await existing.fetchone() is None:
        raise HTTPException(status_code=404, detail="feature not found")

    updates: list[str] = []
    params: list[str | int | None] = []

    if payload.name is not None:
        updates.append("name = ?")
        params.append(payload.name.strip())
    if payload.description is not None:
        updates.append("description = ?")
        params.append(payload.description)
    if payload.status is not None:
        updates.append("status = ?")
        params.append(payload.status)
    if payload.owner_id is not None:
        updates.append("owner_id = ?")
        params.append(payload.owner_id)

    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(feature_id)
        await db.execute(
            f"UPDATE features SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        await db.commit()

    result_cursor = await db.execute(
        """
        SELECT features.*, members.name AS owner_name
        FROM features
        LEFT JOIN members ON members.member_id = features.owner_id
        WHERE features.id = ?
        """,
        (feature_id,),
    )
    row = await result_cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="feature not found")

    iface_cursor = await db.execute(
        "SELECT interface_id FROM feature_interfaces WHERE feature_id = ?",
        (feature_id,),
    )
    iface_rows = await iface_cursor.fetchall()
    return Feature(
        **dict(row),
        interface_ids=[r["interface_id"] for r in iface_rows],
    )


@router.delete("/{feature_id}")
async def delete_feature(
    feature_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict[str, str]:
    cursor = await db.execute(
        "DELETE FROM features WHERE id = ?", (feature_id,)
    )
    await db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="feature not found")
    return {"message": "feature deleted"}


@router.post("/{feature_id}/interfaces", response_model=dict[str, str])
async def link_interface(
    feature_id: str,
    payload: FeatureInterfaceLink,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict[str, str]:
    feat = await db.execute(
        "SELECT id FROM features WHERE id = ?", (feature_id,)
    )
    if await feat.fetchone() is None:
        raise HTTPException(status_code=404, detail="feature not found")

    iface = await db.execute(
        "SELECT id FROM interfaces WHERE id = ?", (payload.interface_id,)
    )
    if await iface.fetchone() is None:
        raise HTTPException(status_code=404, detail="interface not found")

    try:
        await db.execute(
            "INSERT INTO feature_interfaces (feature_id, interface_id) VALUES (?, ?)",
            (feature_id, payload.interface_id),
        )
        await db.commit()
    except aiosqlite.IntegrityError:
        raise HTTPException(
            status_code=400, detail="interface already linked to this feature"
        ) from None

    return {"message": "interface linked"}


@router.delete("/{feature_id}/interfaces/{interface_id}")
async def unlink_interface(
    feature_id: str,
    interface_id: int,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict[str, str]:
    cursor = await db.execute(
        "DELETE FROM feature_interfaces WHERE feature_id = ? AND interface_id = ?",
        (feature_id, interface_id),
    )
    await db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="link not found")
    return {"message": "interface unlinked"}
