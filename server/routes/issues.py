"""Issue tracking endpoints."""

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from server.database import get_db
from server.models import Issue, IssueComment, IssueCommentCreate, IssueCreate, IssueUpdate


router = APIRouter(prefix="/issues", tags=["issues"])


@router.get("/", response_model=list[Issue])
async def list_issues(
    status: str | None = None,
    assignee_id: int | None = None,
    feature_id: str | None = None,
    db: aiosqlite.Connection = Depends(get_db),
) -> list[Issue]:
    conditions: list[str] = ["1=1"]
    params: list[str | int] = []

    if status:
        conditions.append("issues.status = ?")
        params.append(status)
    if assignee_id is not None:
        conditions.append("issues.assignee_id = ?")
        params.append(assignee_id)
    if feature_id:
        conditions.append("issues.feature_id = ?")
        params.append(feature_id)

    where = " AND ".join(conditions)
    cursor = await db.execute(
        f"""
        SELECT issues.*, members.name AS assignee_name,
               (SELECT COUNT(*) FROM issue_comments WHERE issue_id = issues.id) AS comment_count
        FROM issues
        LEFT JOIN members ON members.member_id = issues.assignee_id
        WHERE {where}
        ORDER BY issues.created_at DESC
        """,
        params,
    )
    rows = await cursor.fetchall()
    return [Issue(**dict(row)) for row in rows]


@router.post("/", response_model=Issue, status_code=201)
async def create_issue(
    payload: IssueCreate,
    db: aiosqlite.Connection = Depends(get_db),
) -> Issue:
    if not payload.title.strip():
        raise HTTPException(status_code=400, detail="title cannot be empty")

    cursor = await db.execute(
        """
        INSERT INTO issues (title, description, status, assignee_id, feature_id, interface_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            payload.title.strip(),
            payload.description,
            payload.status,
            payload.assignee_id,
            payload.feature_id,
            payload.interface_id,
        ),
    )
    await db.commit()

    result_cursor = await db.execute(
        """
        SELECT issues.*, members.name AS assignee_name, 0 AS comment_count
        FROM issues
        LEFT JOIN members ON members.member_id = issues.assignee_id
        WHERE issues.id = ?
        """,
        (cursor.lastrowid,),
    )
    row = await result_cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=500, detail="failed to create issue")
    return Issue(**dict(row))


@router.get("/{issue_id}", response_model=Issue)
async def get_issue(
    issue_id: int,
    db: aiosqlite.Connection = Depends(get_db),
) -> Issue:
    cursor = await db.execute(
        """
        SELECT issues.*, members.name AS assignee_name,
               (SELECT COUNT(*) FROM issue_comments WHERE issue_id = issues.id) AS comment_count
        FROM issues
        LEFT JOIN members ON members.member_id = issues.assignee_id
        WHERE issues.id = ?
        """,
        (issue_id,),
    )
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="issue not found")
    return Issue(**dict(row))


@router.patch("/{issue_id}", response_model=Issue)
async def update_issue(
    issue_id: int,
    payload: IssueUpdate,
    db: aiosqlite.Connection = Depends(get_db),
) -> Issue:
    existing = await db.execute(
        "SELECT id FROM issues WHERE id = ?", (issue_id,)
    )
    if await existing.fetchone() is None:
        raise HTTPException(status_code=404, detail="issue not found")

    updates: list[str] = []
    params: list[str | int | None] = []

    if payload.title is not None:
        updates.append("title = ?")
        params.append(payload.title.strip())
    if payload.description is not None:
        updates.append("description = ?")
        params.append(payload.description)
    if payload.status is not None:
        updates.append("status = ?")
        params.append(payload.status)
    if payload.assignee_id is not None:
        updates.append("assignee_id = ?")
        params.append(payload.assignee_id)
    if payload.feature_id is not None:
        updates.append("feature_id = ?")
        params.append(payload.feature_id)
    if payload.interface_id is not None:
        updates.append("interface_id = ?")
        params.append(payload.interface_id)

    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(issue_id)
        await db.execute(
            f"UPDATE issues SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        await db.commit()

    result_cursor = await db.execute(
        """
        SELECT issues.*, members.name AS assignee_name,
               (SELECT COUNT(*) FROM issue_comments WHERE issue_id = issues.id) AS comment_count
        FROM issues
        LEFT JOIN members ON members.member_id = issues.assignee_id
        WHERE issues.id = ?
        """,
        (issue_id,),
    )
    row = await result_cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="issue not found")
    return Issue(**dict(row))


@router.delete("/{issue_id}")
async def delete_issue(
    issue_id: int,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict[str, str]:
    cursor = await db.execute("DELETE FROM issues WHERE id = ?", (issue_id,))
    await db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="issue not found")
    return {"message": "issue deleted"}


@router.get("/{issue_id}/comments", response_model=list[IssueComment])
async def list_issue_comments(
    issue_id: int,
    db: aiosqlite.Connection = Depends(get_db),
) -> list[IssueComment]:
    cursor = await db.execute(
        "SELECT id, issue_id, author_name, content, created_at FROM issue_comments WHERE issue_id = ? ORDER BY created_at ASC",
        (issue_id,),
    )
    rows = await cursor.fetchall()
    return [IssueComment(**dict(row)) for row in rows]


@router.post("/{issue_id}/comments", response_model=IssueComment, status_code=201)
async def create_issue_comment(
    issue_id: int,
    payload: IssueCommentCreate,
    db: aiosqlite.Connection = Depends(get_db),
) -> IssueComment:
    if not payload.content.strip():
        raise HTTPException(status_code=400, detail="comment cannot be empty")

    existing = await db.execute(
        "SELECT id FROM issues WHERE id = ?", (issue_id,)
    )
    if await existing.fetchone() is None:
        raise HTTPException(status_code=404, detail="issue not found")

    cursor = await db.execute(
        """
        INSERT INTO issue_comments (issue_id, author_name, content)
        VALUES (?, ?, ?)
        """,
        (issue_id, "User", payload.content),
    )
    await db.commit()

    result_cursor = await db.execute(
        "SELECT id, issue_id, author_name, content, created_at FROM issue_comments WHERE id = ?",
        (cursor.lastrowid,),
    )
    row = await result_cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=500, detail="failed to create comment")
    return IssueComment(**dict(row))
