"""
Metrics and logging models.
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class LogLevel(str, enum.Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Metric(Base):
    """Trading metrics snapshot model."""
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    
    # P&L metrics
    total_pnl = Column(Float, default=0.0)
    unrealized_pnl = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    
    # Trade statistics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    
    # Risk metrics
    max_drawdown = Column(Float, default=0.0)
    max_drawdown_percent = Column(Float, default=0.0)
    current_drawdown = Column(Float, default=0.0)
    
    # Position metrics
    open_positions = Column(Integer, default=0)
    total_volume = Column(Float, default=0.0)
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    profile = relationship("Profile", back_populates="metrics")


class LogEntry(Base):
    """Application log entry model."""
    __tablename__ = "log_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=True)
    
    # Log details
    level = Column(SQLEnum(LogLevel), nullable=False, index=True)
    message = Column(Text, nullable=False)
    module = Column(String(100), nullable=True)
    function = Column(String(100), nullable=True)
    line_number = Column(Integer, nullable=True)
    
    # Additional context (JSON)
    context = Column(Text, nullable=True)  # JSON string
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    profile = relationship("Profile", foreign_keys=[profile_id])

