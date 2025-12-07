"""
Tests for profile endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.profile import Profile
from app.core.security import get_password_hash, create_access_token

client = TestClient(app)


@pytest.fixture(scope="function")
def db():
    """Create test database."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db):
    """Create a test user."""
    user = User(
        email="test@example.com",
        password_hash=get_password_hash("testpassword"),
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user):
    """Get auth token for test user."""
    return create_access_token(data={"sub": test_user.id, "email": test_user.email})


def test_create_profile(auth_token):
    """Test profile creation."""
    response = client.post(
        "/api/v1/profiles",
        json={
            "name": "Test Profile",
            "environment": "sandbox",
            "api_key": "test_key",
            "api_secret": "test_secret"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Profile"
    assert data["environment"] == "sandbox"


def test_list_profiles(auth_token, test_user, db):
    """Test listing profiles."""
    # Create a profile
    profile = Profile(
        user_id=test_user.id,
        name="Test Profile",
        environment="sandbox"
    )
    db.add(profile)
    db.commit()
    
    response = client.get(
        "/api/v1/profiles",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Profile"

