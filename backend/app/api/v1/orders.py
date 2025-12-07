"""
Order management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.profile import Profile
from app.models.order import OrderRecord, Trade, OrderStatus

router = APIRouter()


class OrderResponse(BaseModel):
    """Order response model."""
    id: int
    profile_id: int
    exchange_order_id: Optional[str]
    product_id: int
    product_symbol: Optional[str]
    side: str
    order_type: str
    size: float
    price: Optional[float]
    stop_price: Optional[float]
    status: str
    filled_quantity: float
    average_fill_price: Optional[float]
    reduce_only: bool
    created_at: str
    updated_at: Optional[str]
    filled_at: Optional[str]
    
    class Config:
        from_attributes = True


class TradeResponse(BaseModel):
    """Trade response model."""
    id: int
    order_record_id: int
    price: float
    quantity: float
    fee: float
    timestamp: str
    
    class Config:
        from_attributes = True


@router.get("/profile/{profile_id}", response_model=List[OrderResponse])
async def list_orders(
    profile_id: int,
    status: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List orders for a profile."""
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
    
    query = db.query(OrderRecord).filter(OrderRecord.profile_id == profile_id)
    
    if status:
        try:
            order_status = OrderStatus(status)
            query = query.filter(OrderRecord.status == order_status)
        except ValueError:
            pass
    
    orders = query.order_by(OrderRecord.created_at.desc()).offset(offset).limit(limit).all()
    return orders


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific order."""
    order = db.query(OrderRecord).filter(OrderRecord.id == order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )
    
    # Verify profile ownership
    profile = db.query(Profile).filter(
        Profile.id == order.profile_id,
        Profile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )
    
    return order


@router.get("/{order_id}/trades", response_model=List[TradeResponse])
async def get_order_trades(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get trades for a specific order."""
    order = db.query(OrderRecord).filter(OrderRecord.id == order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )
    
    # Verify profile ownership
    profile = db.query(Profile).filter(
        Profile.id == order.profile_id,
        Profile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )
    
    trades = db.query(Trade).filter(Trade.order_record_id == order_id).all()
    return trades

