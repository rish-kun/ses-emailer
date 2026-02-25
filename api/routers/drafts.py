"""
Drafts API router – CRUD operations for email drafts.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.auth import verify_token
from sending.db import Database

router = APIRouter()


class DraftCreate(BaseModel):
    name: str
    subject: str = ""
    body: str = ""
    sender: str = ""
    recipients: list[str] = []
    attachments: list[str] = []
    email_type: str = "html"


class DraftUpdate(BaseModel):
    name: str | None = None
    subject: str | None = None
    body: str | None = None
    sender: str | None = None
    recipients: list[str] | None = None
    attachments: list[str] | None = None
    email_type: str | None = None


@router.get("", dependencies=[Depends(verify_token)])
async def list_drafts():
    """List all drafts."""
    db = Database()
    drafts = db.get_all_drafts()
    db.close()
    return {"drafts": drafts, "total": len(drafts)}


@router.get("/{draft_id}", dependencies=[Depends(verify_token)])
async def get_draft(draft_id: int):
    """Get a draft by ID."""
    db = Database()
    draft = db.get_draft(draft_id)
    db.close()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft


@router.post("", dependencies=[Depends(verify_token)])
async def create_draft(body: DraftCreate):
    """Create a new draft."""
    db = Database()
    draft_id = db.add_draft(
        name=body.name,
        subject=body.subject,
        body=body.body,
        sender=body.sender,
        recipients=body.recipients,
        attachments=body.attachments,
        email_type=body.email_type,
    )
    db.close()
    return {"id": draft_id, "name": body.name}


@router.put("/{draft_id}", dependencies=[Depends(verify_token)])
async def update_draft(draft_id: int, body: DraftUpdate):
    """Update an existing draft."""
    db = Database()
    update_kwargs = body.model_dump(exclude_none=True)
    if not update_kwargs:
        raise HTTPException(status_code=400, detail="No fields to update")
    success = db.update_draft(draft_id, **update_kwargs)
    db.close()
    if not success:
        raise HTTPException(status_code=404, detail="Draft not found")
    return {"id": draft_id, "updated": True}


@router.delete("/{draft_id}", dependencies=[Depends(verify_token)])
async def delete_draft(draft_id: int):
    """Delete a draft."""
    db = Database()
    success = db.delete_draft(draft_id)
    db.close()
    if not success:
        raise HTTPException(status_code=404, detail="Draft not found")
    return {"id": draft_id, "deleted": True}
