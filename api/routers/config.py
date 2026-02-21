"""
Config API router – manage configuration profiles.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.auth import verify_token
from config.settings import get_config, reset_config

router = APIRouter()


class ProfileCreate(BaseModel):
    name: str
    copy_from: str | None = None


class ProfileRename(BaseModel):
    new_name: str


class ConfigUpdate(BaseModel):
    aws: dict | None = None
    sender: dict | None = None
    batch: dict | None = None
    files_directory: str | None = None
    data_directory: str | None = None
    last_excel_path: str | None = None
    last_excel_column: int | None = None
    theme: str | None = None
    test_recipients: list[str] | None = None


# ── Active config ─────────────────────────────────────────────────────


@router.get("", dependencies=[Depends(verify_token)])
async def get_active_config():
    """Get the active profile's configuration."""
    cm = get_config()
    return {
        "active_profile": cm.active_profile,
        "config": cm.get_config_dict(),
        "is_configured": cm.is_configured(),
    }


@router.put("", dependencies=[Depends(verify_token)])
async def update_active_config(body: ConfigUpdate):
    """Update the active profile's configuration."""
    cm = get_config()
    update_data = body.model_dump(exclude_none=True)
    cm.update_config(update_data)
    return {
        "active_profile": cm.active_profile,
        "config": cm.get_config_dict(),
        "is_configured": cm.is_configured(),
    }


# ── Profile management ───────────────────────────────────────────────


@router.get("/profiles", dependencies=[Depends(verify_token)])
async def list_profiles():
    """List all profile names and active profile."""
    cm = get_config()
    return {
        "active_profile": cm.active_profile,
        "profiles": cm.list_profiles(),
    }


@router.post("/profiles", dependencies=[Depends(verify_token)])
async def create_profile(body: ProfileCreate):
    """Create a new configuration profile."""
    cm = get_config()
    if not cm.create_profile(body.name, body.copy_from):
        raise HTTPException(
            status_code=409, detail=f"Profile '{body.name}' already exists"
        )
    return {"created": body.name, "profiles": cm.list_profiles()}


@router.delete("/profiles/{name}", dependencies=[Depends(verify_token)])
async def delete_profile(name: str):
    """Delete a configuration profile."""
    cm = get_config()
    if not cm.delete_profile(name):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete profile '{name}' (not found or last remaining)",
        )
    return {
        "deleted": name,
        "active_profile": cm.active_profile,
        "profiles": cm.list_profiles(),
    }


@router.post("/profiles/{name}/activate", dependencies=[Depends(verify_token)])
async def activate_profile(name: str):
    """Switch the active profile."""
    cm = get_config()
    if not cm.switch_profile(name):
        raise HTTPException(status_code=404, detail=f"Profile '{name}' not found")
    reset_config()  # Reload singleton
    cm = get_config()
    return {
        "active_profile": cm.active_profile,
        "config": cm.get_config_dict(),
        "is_configured": cm.is_configured(),
    }
