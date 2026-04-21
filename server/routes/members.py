"""Member endpoints."""

from fastapi import APIRouter

from server.models import Member


router = APIRouter(prefix="/members", tags=["members"])


@router.get("/", response_model=list[Member])
async def list_members() -> list[Member]:
    return []
