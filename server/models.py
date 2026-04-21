"""Shared response and domain models for the API skeleton."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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


class ScopeUpdate(BaseModel):
    patterns: list[str]


class ScopeResponse(BaseModel):
    member_id: int
    patterns: list[str]


class LockedModuleCreate(BaseModel):
    pattern: str
    reason: str


class LockedModule(BaseModel):
    pattern: str
    reason: str


class StandardCreate(BaseModel):
    scope: str
    category: str
    content: str


class StandardUpdate(BaseModel):
    content: str


class Standard(BaseModel):
    scope: str
    category: str
    content: str
    updated_at: str


class SyncMember(BaseModel):
    member_id: int
    name: str
    role: Literal["owner", "member"]


class SyncScope(BaseModel):
    patterns: list[str]


class SyncStandard(BaseModel):
    category: str
    content: str


class SyncStandards(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    global_: list[SyncStandard] = Field(default_factory=list, alias="global")
    personal: list[SyncStandard] = Field(default_factory=list)


class SyncContract(BaseModel):
    member: SyncMember
    scope: SyncScope
    locked_modules: list[LockedModule]
    standards: SyncStandards


class SyncStatus(BaseModel):
    state: str = "idle"
    detail: str = "sync logic not implemented yet"
