import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_login_page_unauthenticated():
    """Test login page is accessible."""
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Sign in with Microsoft" in response.content


def test_dashboard_requires_auth():
    """Test dashboard redirects to login when not authenticated."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["location"]


def test_secret_detection():
    """Test secret detection service."""
    from app.services.secret_detection import SecretDetector
    
    # Test private key detection
    text_with_secret = "Here is my key: -----BEGIN PRIVATE KEY-----"
    has_secrets, findings = SecretDetector.has_secrets({"what_changed": text_with_secret})
    assert has_secrets is True
    assert len(findings) > 0
    
    # Test clean text
    clean_text = "This is a normal change description"
    has_secrets, findings = SecretDetector.has_secrets({"what_changed": clean_text})
    assert has_secrets is False
    assert len(findings) == 0


def test_role_determination():
    """Test role configuration."""
    from app.config import RoleConfig
    
    config = RoleConfig()
    
    # Test default role
    role = config.get_user_role([])
    assert role == "user"
    
    # Test with unknown group
    role = config.get_user_role(["unknown-group-id"])
    assert role == "user"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
