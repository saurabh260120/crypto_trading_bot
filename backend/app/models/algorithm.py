"""
Algorithm version model.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class AlgorithmVersion(Base):
    """Algorithm code version model."""
    __tablename__ = "algorithm_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    code = Column(Text, nullable=False)  # Python algorithm code
    version = Column(Integer, default=1)  # Version number
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    note = Column(String(500), nullable=True)  # Change note
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    profile = relationship("Profile", foreign_keys=[profile_id], back_populates="algorithm_versions")
    author = relationship("User", foreign_keys=[author_id])

