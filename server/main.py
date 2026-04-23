"""FastAPI entrypoint for the VibeRails server."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from server.database import init_db
from server.models import HealthResponse
from server.routes import contracts_router, members_router, sync_router


app = FastAPI(title="VibeRails Server", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="web"), name="static")

app.include_router(members_router)
app.include_router(contracts_router)
app.include_router(sync_router)


@app.on_event("startup")
async def on_startup() -> None:
    await init_db()


@app.get("/", response_model=HealthResponse)
async def read_root() -> HealthResponse:
    return HealthResponse()


@app.get("/ui")
async def serve_ui() -> FileResponse:
    return FileResponse("web/index.html")
