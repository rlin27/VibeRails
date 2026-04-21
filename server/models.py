"""Shared response and domain models for the API skeleton."""

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "vibrails-server"


class MemberCreate(BaseModel):
    name: str
    role: Literal["owner", "member"]


class Member(BaseModel):
    member_id: int
    name: str
    role: Literal["owner", "member"]
    created_at: str


class MessageResponse(BaseModel):
    message: str


class Contract(BaseModel):
    id: int
    title: str
    body: str = ""


class SyncStatus(BaseModel):
    state: str = "idle"
    detail: str = "sync logic not implemented yet"
