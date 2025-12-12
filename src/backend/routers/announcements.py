from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from .. import database
from ..database import teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


def _parse_iso(dt: Optional[str]) -> Optional[datetime]:
    if not dt:
        return None
    try:
        # support trailing Z
        if dt.endswith("Z"):
            dt = dt[:-1] + "+00:00"
        return datetime.fromisoformat(dt)
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid datetime: {dt}")


@router.get("/")
def list_active():
    """List currently active announcements"""
    anns = database.get_active_announcements()
    return {"announcements": anns}


@router.get("/all")
def list_all(username: Optional[str] = None):
    """List all announcements; management view can show expired ones.
    If `username` provided, verify account exists (simple auth).
    """
    if username:
        user = teachers_collection.find_one({"_id": username})
        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized")
    anns = database.list_announcements(include_expired=bool(username))
    return {"announcements": anns}


@router.post("/")
def create_announcement(title: str, message: str, expires: str, username: str, start: Optional[str] = None) -> Dict[str, Any]:
    """Create an announcement. Requires `username` of a signed-in teacher."""
    user = teachers_collection.find_one({"_id": username})
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    expires_dt = _parse_iso(expires)
    start_dt = _parse_iso(start) if start else None

    ann_id = database.create_announcement(title=title, message=message, expires=expires_dt, start=start_dt)
    return {"id": ann_id}


@router.put("/{ann_id}")
def update_announcement(ann_id: str, username: str, title: Optional[str] = None, message: Optional[str] = None, expires: Optional[str] = None, start: Optional[str] = None):
    user = teachers_collection.find_one({"_id": username})
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    fields = {}
    if title is not None:
        fields["title"] = title
    if message is not None:
        fields["message"] = message
    if expires is not None:
        fields["expires"] = _parse_iso(expires)
    if start is not None:
        fields["start"] = _parse_iso(start)

    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    database.update_announcement(ann_id, fields)
    return {"id": ann_id}


@router.delete("/{ann_id}")
def delete_announcement(ann_id: str, username: str):
    user = teachers_collection.find_one({"_id": username})
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    database.delete_announcement(ann_id)
    return {"id": ann_id}
