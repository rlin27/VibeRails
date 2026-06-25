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


class InterfaceScanItem(BaseModel):
    file_path: str
    signature: str


class InterfaceUploadRequest(BaseModel):
    interfaces: list[InterfaceScanItem]


class InterfaceUploadResponse(BaseModel):
    inserted: int
    deprecated: int
    skipped: int


class InterfaceUpdate(BaseModel):
    status: Literal["stable", "in_progress", "planned", "deprecated"]
    owner_id: int | None = None
    description: str | None = None


class PlannedInterfaceCreate(BaseModel):
    file_path: str
    signature: str
    description: str | None = None
    owner_id: int | None = None


class Interface(BaseModel):
    id: int
    file_path: str
    signature: str
    description: str | None
    status: Literal["stable", "in_progress", "planned", "deprecated"]
    owner_id: int | None
    owner_name: str | None
    updated_at: str


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
