"""
Metrics endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.profile import Profile
from app.models.metric import Metric
from app.models.order import OrderRecord, Trade
from sqlalchemy import func

router = APIRouter()


class MetricResponse(BaseModel):
    """Metric response model."""
    id: int
    profile_id: int
    total_pnl: float
    unrealized_pnl: float
    realized_pnl: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    max_drawdown: float
    max_drawdown_percent: float
    current_drawdown: float
    open_positions: int
    total_volume: float
    timestamp: str
    
    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    """Dashboard statistics model."""
    total_profiles: int
    active_profiles: int
    total_pnl: float
    total_trades: int
    win_rate: float


@router.get("/profile/{profile_id}", response_model=List[MetricResponse])
async def get_profile_metrics(
    profile_id: int,
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get metrics for a profile."""
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
    
    metrics = db.query(Metric).filter(
        Metric.profile_id == profile_id
    ).order_by(Metric.timestamp.desc()).offset(offset).limit(limit).all()
    
    return metrics


@router.get("/profile/{profile_id}/latest", response_model=MetricResponse)
async def get_latest_metrics(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get latest metrics for a profile."""
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
    
    metric = db.query(Metric).filter(
        Metric.profile_id == profile_id
    ).order_by(Metric.timestamp.desc()).first()
    
    if not metric:
        # Return default metrics
        return MetricResponse(
            id=0,
            profile_id=profile_id,
            total_pnl=0.0,
            unrealized_pnl=0.0,
            realized_pnl=0.0,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            max_drawdown=0.0,
            max_drawdown_percent=0.0,
            current_drawdown=0.0,
            open_positions=0,
            total_volume=0.0,
            timestamp=datetime.utcnow().isoformat()
        )
    
    return metric


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics for current user."""
    profiles = db.query(Profile).filter(Profile.user_id == current_user.id).all()
    active_profiles = [p for p in profiles if p.enabled and not p.paused]
    
    # Calculate aggregate stats
    total_pnl = 0.0
    total_trades = 0
    winning_trades = 0
    
    for profile in profiles:
        latest_metric = db.query(Metric).filter(
            Metric.profile_id == profile.id
        ).order_by(Metric.timestamp.desc()).first()
        
        if latest_metric:
            total_pnl += latest_metric.total_pnl
            total_trades += latest_metric.total_trades
            winning_trades += latest_metric.winning_trades
    
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
    
    return DashboardStats(
        total_profiles=len(profiles),
        active_profiles=len(active_profiles),
        total_pnl=total_pnl,
        total_trades=total_trades,
        win_rate=win_rate
    )

