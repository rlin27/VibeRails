"""Sync endpoints."""

from fastapi import APIRouter

from server.models import SyncStatus


router = APIRouter(prefix="/sync", tags=["sync"])


@router.get("/status", response_model=SyncStatus)
async def get_sync_status() -> SyncStatus:
    return SyncStatus()
