"""Contract endpoints."""

from fastapi import APIRouter

from server.models import Contract


router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.get("/", response_model=list[Contract])
async def list_contracts() -> list[Contract]:
    return []
