"""
Order and trade models.
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class OrderStatus(str, enum.Enum):
    """Order status enumeration."""
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class OrderSide(str, enum.Enum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, enum.Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderRecord(Base):
    """Order record model."""
    __tablename__ = "order_records"
    
    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    
    # Exchange order ID
    exchange_order_id = Column(String(100), nullable=True, index=True)
    
    # Order details
    product_id = Column(Integer, nullable=False)
    product_symbol = Column(String(50), nullable=True)
    side = Column(SQLEnum(OrderSide), nullable=False)
    order_type = Column(SQLEnum(OrderType), nullable=False)
    size = Column(Float, nullable=False)
    price = Column(Float, nullable=True)  # For limit orders
    stop_price = Column(Float, nullable=True)  # For stop orders
    
    # Status
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING, index=True)
    filled_quantity = Column(Float, default=0.0)
    average_fill_price = Column(Float, nullable=True)
    
    # Flags
    reduce_only = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    filled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    profile = relationship("Profile", back_populates="orders")
    trades = relationship("Trade", back_populates="order", cascade="all, delete-orphan")


class Trade(Base):
    """Trade/fill record model."""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    order_record_id = Column(Integer, ForeignKey("order_records.id"), nullable=False)
    
    # Fill details
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    fee = Column(Float, default=0.0)
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    order = relationship("OrderRecord", back_populates="trades")

