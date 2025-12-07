"""
Algorithm management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.profile import Profile
from app.models.algorithm import AlgorithmVersion

router = APIRouter()


class AlgorithmCreate(BaseModel):
    """Algorithm creation model."""
    profile_id: int
    code: str
    note: Optional[str] = None


class AlgorithmResponse(BaseModel):
    """Algorithm response model."""
    id: int
    profile_id: int
    code: str
    version: int
    author_id: Optional[int]
    note: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True


@router.post("", response_model=AlgorithmResponse, status_code=status.HTTP_201_CREATED)
async def create_algorithm(
    algorithm_data: AlgorithmCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new algorithm version."""
    # Verify profile ownership
    profile = db.query(Profile).filter(
        Profile.id == algorithm_data.profile_id,
        Profile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    # Get next version number
    max_version = db.query(AlgorithmVersion).filter(
        AlgorithmVersion.profile_id == algorithm_data.profile_id
    ).order_by(AlgorithmVersion.version.desc()).first()
    
    next_version = (max_version.version + 1) if max_version else 1
    
    # Create algorithm version
    algorithm = AlgorithmVersion(
        profile_id=algorithm_data.profile_id,
        code=algorithm_data.code,
        version=next_version,
        author_id=current_user.id,
        note=algorithm_data.note
    )
    
    db.add(algorithm)
    db.commit()
    db.refresh(algorithm)
    
    # Update profile to use this version
    profile.algorithm_version_id = algorithm.id
    db.commit()
    
    return algorithm


@router.get("/profile/{profile_id}", response_model=List[AlgorithmResponse])
async def list_algorithm_versions(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all algorithm versions for a profile."""
    # Verify profile ownership
    profile = db.query(Profile).filter(
        Profile.id == profile_id,
        Profile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    algorithms = db.query(AlgorithmVersion).filter(
        AlgorithmVersion.profile_id == profile_id
    ).order_by(AlgorithmVersion.version.desc()).all()
    
    return algorithms


@router.get("/{algorithm_id}", response_model=AlgorithmResponse)
async def get_algorithm(
    algorithm_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific algorithm version."""
    algorithm = db.query(AlgorithmVersion).filter(
        AlgorithmVersion.id == algorithm_id
    ).first()
    
    if not algorithm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Algorithm not found"
        )
    
    # Verify profile ownership
    profile = db.query(Profile).filter(
        Profile.id == algorithm.profile_id,
        Profile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return algorithm


@router.post("/{algorithm_id}/activate")
async def activate_algorithm(
    algorithm_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Activate a specific algorithm version for a profile."""
    algorithm = db.query(AlgorithmVersion).filter(
        AlgorithmVersion.id == algorithm_id
    ).first()
    
    if not algorithm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Algorithm not found"
        )
    
    # Verify profile ownership
    profile = db.query(Profile).filter(
        Profile.id == algorithm.profile_id,
        Profile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    profile.algorithm_version_id = algorithm_id
    db.commit()
    
    return {"message": "Algorithm activated", "algorithm_id": algorithm_id}

