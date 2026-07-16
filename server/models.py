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


class SyncLogEntry(BaseModel):
    id: int
    member_id: int
    status: str
    detail: str | None = None
    synced_at: str


class PaginatedInterfaces(BaseModel):
    items: list[Interface]
    total: int
    limit: int
    offset: int


class SyncStatus(BaseModel):
    state: str = "idle"
    detail: str = "sync logic not implemented yet"
    recent_syncs: list[SyncLogEntry] = []


# ===== Feature Models =====
class FeatureCreate(BaseModel):
    id: str | None = None
    name: str
    description: str | None = None
    status: Literal["planned", "in_progress", "stable", "deprecated"] = "planned"
    owner_id: int | None = None


class FeatureUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: Literal["planned", "in_progress", "stable", "deprecated"] | None = None
    owner_id: int | None = None


class Feature(BaseModel):
    id: str
    name: str
    description: str | None
    status: Literal["planned", "in_progress", "stable", "deprecated"]
    owner_id: int | None
    owner_name: str | None = None
    interface_ids: list[int] = []
    created_at: str
    updated_at: str


class FeatureInterfaceLink(BaseModel):
    interface_id: int


# ===== AI Provider Models =====
class AIProviderCreate(BaseModel):
    name: str
    api_base_url: str
    api_key: str
    model: str = "claude-sonnet-4-20250514"
    protocol: Literal["anthropic", "openai"] = "anthropic"
    is_active: bool = True


class AIProviderUpdate(BaseModel):
    name: str | None = None
    api_base_url: str | None = None
    api_key: str | None = None
    model: str | None = None
    protocol: Literal["anthropic", "openai"] | None = None
    is_active: bool | None = None


class AIProvider(BaseModel):
    id: int
    name: str
    api_base_url: str
    model: str
    protocol: Literal["anthropic", "openai"]
    is_active: bool
    created_at: str
    updated_at: str


class AIProviderTestResult(BaseModel):
    success: bool
    message: str


# ===== Chat Models =====
class ChatSendRequest(BaseModel):
    feature_id: str
    content: str
    provider_id: int | None = None


class ChatMessage(BaseModel):
    id: int
    feature_id: str
    author_name: str
    author_role: Literal["user", "assistant", "system"]
    content: str
    created_at: str


class ChatSendResponse(BaseModel):
    user_message: ChatMessage
    assistant_message: ChatMessage


# ===== Issue Models =====
class IssueCreate(BaseModel):
    title: str
    description: str | None = None
    status: Literal["open", "in_progress", "resolved", "closed"] = "open"
    assignee_id: int | None = None
    feature_id: str | None = None
    interface_id: int | None = None


class IssueUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: Literal["open", "in_progress", "resolved", "closed"] | None = None
    assignee_id: int | None = None
    feature_id: str | None = None
    interface_id: int | None = None


class Issue(BaseModel):
    id: int
    title: str
    description: str | None
    status: Literal["open", "in_progress", "resolved", "closed"]
    assignee_id: int | None
    assignee_name: str | None = None
    feature_id: str | None
    interface_id: int | None
    created_at: str
    updated_at: str
    comment_count: int = 0


class IssueCommentCreate(BaseModel):
    content: str


class IssueComment(BaseModel):
    id: int
    issue_id: int
    author_name: str
    content: str
    created_at: str
