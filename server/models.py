"""Shared response and domain models for the API skeleton."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "vibrails-server"


class Member(BaseModel):
    id: int
    name: str
    role: str = "member"


class Contract(BaseModel):
    id: int
    title: str
    body: str = ""


class SyncStatus(BaseModel):
    state: str = "idle"
    detail: str = "sync logic not implemented yet"
