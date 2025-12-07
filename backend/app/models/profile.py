"""
Profile model.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Profile(Base):
    """Trading profile model."""
    __tablename__ = "profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    
    # API credentials (encrypted)
    encrypted_api_key = Column(String(512), nullable=True)
    encrypted_api_secret = Column(String(512), nullable=True)
    
    # Environment
    environment = Column(String(20), default="sandbox")  # sandbox or live
    
    # Status
    enabled = Column(Boolean, default=False)
    paused = Column(Boolean, default=False)
    
    # Algorithm
    algorithm_version_id = Column(Integer, ForeignKey("algorithm_versions.id"), nullable=True)
    
    # Parameters (JSON)
    parameters = Column(JSON, default=dict)
    
    # Risk settings
    max_drawdown_percent = Column(Float, default=20.0)
    max_position_size = Column(Float, default=100000.0)
    max_trades_per_day = Column(Integer, default=10)
    
    # State
    state = Column(JSON, default=dict)  # Current trading state
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_execution_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="profiles")
    algorithm_version = relationship("AlgorithmVersion", foreign_keys=[algorithm_version_id], post_update=True)
    algorithm_versions = relationship("AlgorithmVersion", foreign_keys="AlgorithmVersion.profile_id", back_populates="profile")
    orders = relationship("OrderRecord", back_populates="profile", cascade="all, delete-orphan")
    metrics = relationship("Metric", back_populates="profile", cascade="all, delete-orphan")

