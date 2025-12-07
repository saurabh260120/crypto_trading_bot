"""
Logs endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json
import asyncio
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.profile import Profile
from app.models.metric import LogEntry, LogLevel

router = APIRouter()


class LogResponse(BaseModel):
    """Log entry response model."""
    id: int
    profile_id: Optional[int]
    level: str
    message: str
    module: Optional[str]
    function: Optional[str]
    line_number: Optional[int]
    context: Optional[str]
    timestamp: str
    
    class Config:
        from_attributes = True


@router.get("/profile/{profile_id}", response_model=List[LogResponse])
async def get_profile_logs(
    profile_id: int,
    level: Optional[str] = None,
    limit: int = 1000,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get logs for a profile."""
    # Verify profile ownership
    profile = db.query(Profile).filter(
        Profile.id == profile_id,
        Profile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Profile not found"
        )
    
    query = db.query(LogEntry).filter(LogEntry.profile_id == profile_id)
    
    if level:
        try:
            log_level = LogLevel(level.upper())
            query = query.filter(LogEntry.level == log_level)
        except ValueError:
            pass
    
    logs = query.order_by(LogEntry.timestamp.desc()).limit(limit).all()
    return logs


@router.get("/profile/{profile_id}/stream")
async def stream_profile_logs(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stream logs for a profile using Server-Sent Events."""
    # Verify profile ownership
    profile = db.query(Profile).filter(
        Profile.id == profile_id,
        Profile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Profile not found"
        )
    
    async def event_generator():
        last_id = 0
        while True:
            # Query new logs
            logs = db.query(LogEntry).filter(
                LogEntry.profile_id == profile_id,
                LogEntry.id > last_id
            ).order_by(LogEntry.timestamp.asc()).all()
            
            for log in logs:
                data = {
                    "id": log.id,
                    "level": log.level.value,
                    "message": log.message,
                    "timestamp": log.timestamp.isoformat(),
                    "context": log.context
                }
                yield f"data: {json.dumps(data)}\n\n"
                last_id = log.id
            
            await asyncio.sleep(1)  # Poll every second
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

