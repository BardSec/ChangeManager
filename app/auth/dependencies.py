from fastapi import Depends, HTTPException, status, Request
from typing import Optional
from app.config import get_role_config


def get_current_user(request: Request) -> dict:
    """
    Get current authenticated user from session.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User dictionary with email, name, role, etc.
        
    Raises:
        HTTPException: If user is not authenticated
    """
    user = request.session.get('user')
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return user


def get_current_user_optional(request: Request) -> Optional[dict]:
    """
    Get current authenticated user from session, or None if not authenticated.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User dictionary or None
    """
    return request.session.get('user')


def require_role(required_role: str):
    """
    Dependency factory to require specific role.
    
    Args:
        required_role: Required role name (admin, auditor, user)
        
    Returns:
        Dependency function
    """
    def check_role(user: dict = Depends(get_current_user)) -> dict:
        """Check if user has required role."""
        user_role = user.get('role', 'user')
        
        # Role hierarchy: admin > auditor > user
        role_hierarchy = {'admin': 3, 'auditor': 2, 'user': 1}
        
        if role_hierarchy.get(user_role, 0) < role_hierarchy.get(required_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {required_role} role"
            )
        
        return user
    
    return check_role


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Require admin role."""
    if user.get('role') != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    return user


def require_write_access(user: dict = Depends(get_current_user)) -> dict:
    """Require write access (admin or user role, not auditor)."""
    if user.get('role') == 'auditor':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Auditors have read-only access"
        )
    return user
