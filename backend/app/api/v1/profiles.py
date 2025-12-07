"""
Profile management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.core.database import get_db
from app.core.security import encrypt_api_key, decrypt_api_key
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.profile import Profile
from app.models.algorithm import AlgorithmVersion

router = APIRouter()


class ProfileCreate(BaseModel):
    """Profile creation model."""
    name: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    environment: str = "sandbox"
    parameters: Dict[str, Any] = {}


class ProfileUpdate(BaseModel):
    """Profile update model."""
    name: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    environment: Optional[str] = None
    enabled: Optional[bool] = None
    paused: Optional[bool] = None
    parameters: Optional[Dict[str, Any]] = None
    max_drawdown_percent: Optional[float] = None
    max_position_size: Optional[float] = None
    max_trades_per_day: Optional[int] = None


class ProfileResponse(BaseModel):
    """Profile response model."""
    id: int
    user_id: int
    name: str
    environment: str
    enabled: bool
    paused: bool
    algorithm_version_id: Optional[int]
    parameters: Dict[str, Any]
    max_drawdown_percent: float
    max_position_size: float
    max_trades_per_day: int
    state: Dict[str, Any]
    created_at: str
    updated_at: Optional[str]
    last_execution_at: Optional[str]
    has_api_keys: bool
    
    class Config:
        from_attributes = True


@router.get("", response_model=List[ProfileResponse])
async def list_profiles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all profiles for current user."""
    profiles = db.query(Profile).filter(Profile.user_id == current_user.id).all()
    result = []
    for profile in profiles:
        profile_dict = {
            **profile.__dict__,
            "has_api_keys": bool(profile.encrypted_api_key and profile.encrypted_api_secret)
        }
        # Remove encrypted fields from response
        profile_dict.pop("encrypted_api_key", None)
        profile_dict.pop("encrypted_api_secret", None)
        result.append(ProfileResponse(**profile_dict))
    return result


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    profile_data: ProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new profile."""
    profile = Profile(
        user_id=current_user.id,
        name=profile_data.name,
        environment=profile_data.environment,
        parameters=profile_data.parameters or {}
    )
    
    if profile_data.api_key:
        profile.encrypted_api_key = encrypt_api_key(profile_data.api_key)
    if profile_data.api_secret:
        profile.encrypted_api_secret = encrypt_api_key(profile_data.api_secret)
    
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    return ProfileResponse(
        **{**profile.__dict__, "has_api_keys": bool(profile.encrypted_api_key and profile.encrypted_api_secret)}
    )


@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific profile."""
    profile = db.query(Profile).filter(
        Profile.id == profile_id,
        Profile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    profile_dict = {
        **profile.__dict__,
        "has_api_keys": bool(profile.encrypted_api_key and profile.encrypted_api_secret)
    }
    profile_dict.pop("encrypted_api_key", None)
    profile_dict.pop("encrypted_api_secret", None)
    return ProfileResponse(**profile_dict)


@router.put("/{profile_id}", response_model=ProfileResponse)
async def update_profile(
    profile_id: int,
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a profile."""
    profile = db.query(Profile).filter(
        Profile.id == profile_id,
        Profile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    # Update fields
    if profile_data.name is not None:
        profile.name = profile_data.name
    if profile_data.environment is not None:
        profile.environment = profile_data.environment
    if profile_data.enabled is not None:
        profile.enabled = profile_data.enabled
    if profile_data.paused is not None:
        profile.paused = profile_data.paused
    if profile_data.parameters is not None:
        profile.parameters = profile_data.parameters
    if profile_data.max_drawdown_percent is not None:
        profile.max_drawdown_percent = profile_data.max_drawdown_percent
    if profile_data.max_position_size is not None:
        profile.max_position_size = profile_data.max_position_size
    if profile_data.max_trades_per_day is not None:
        profile.max_trades_per_day = profile_data.max_trades_per_day
    
    # Update API keys if provided
    if profile_data.api_key:
        profile.encrypted_api_key = encrypt_api_key(profile_data.api_key)
    if profile_data.api_secret:
        profile.encrypted_api_secret = encrypt_api_key(profile_data.api_secret)
    
    db.commit()
    db.refresh(profile)
    
    profile_dict = {
        **profile.__dict__,
        "has_api_keys": bool(profile.encrypted_api_key and profile.encrypted_api_secret)
    }
    profile_dict.pop("encrypted_api_key", None)
    profile_dict.pop("encrypted_api_secret", None)
    return ProfileResponse(**profile_dict)


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a profile."""
    profile = db.query(Profile).filter(
        Profile.id == profile_id,
        Profile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    db.delete(profile)
    db.commit()
    return None


@router.post("/{profile_id}/start", response_model=ProfileResponse)
async def start_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start/enable a profile for trading."""
    profile = db.query(Profile).filter(
        Profile.id == profile_id,
        Profile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    if not profile.encrypted_api_key or not profile.encrypted_api_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API keys not configured"
        )
    
    if not profile.algorithm_version_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No algorithm configured"
        )
    
    profile.enabled = True
    profile.paused = False
    db.commit()
    db.refresh(profile)
    
    profile_dict = {
        **profile.__dict__,
        "has_api_keys": bool(profile.encrypted_api_key and profile.encrypted_api_secret)
    }
    profile_dict.pop("encrypted_api_key", None)
    profile_dict.pop("encrypted_api_secret", None)
    return ProfileResponse(**profile_dict)


@router.post("/{profile_id}/stop", response_model=ProfileResponse)
async def stop_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stop/disable a profile."""
    profile = db.query(Profile).filter(
        Profile.id == profile_id,
        Profile.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    profile.enabled = False
    db.commit()
    db.refresh(profile)
    
    profile_dict = {
        **profile.__dict__,
        "has_api_keys": bool(profile.encrypted_api_key and profile.encrypted_api_secret)
    }
    profile_dict.pop("encrypted_api_key", None)
    profile_dict.pop("encrypted_api_secret", None)
    return ProfileResponse(**profile_dict)

