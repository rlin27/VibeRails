"""FastAPI entrypoint for the VibeRails server."""

from fastapi import FastAPI

from server.database import init_db
from server.models import HealthResponse
from server.routes import contracts_router, members_router, sync_router


app = FastAPI(title="VibeRails Server", version="0.1.0")

app.include_router(members_router)
app.include_router(contracts_router)
app.include_router(sync_router)


@app.on_event("startup")
async def on_startup() -> None:
    await init_db()


@app.get("/", response_model=HealthResponse)
async def read_root() -> HealthResponse:
    return HealthResponse()
