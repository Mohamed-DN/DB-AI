"""
Authentication Router
Endpoints for user login, logout, and profile management.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta

from ..models.user import (
    Token, LoginRequest, UserCreate, UserResponse, 
    PasswordChange, UserRole, get_default_permissions
)
from ..services.auth_service import get_auth_service, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserResponse:
    """Dependency to get current authenticated user from JWT token"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    auth_service = get_auth_service()
    token_data = auth_service.decode_token(token)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await auth_service.get_user(token_data.username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive"
        )
    
    return UserResponse(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        databases_scope=user.databases_scope,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login,
        permissions=get_default_permissions(user.role)
    )


async def get_current_user_optional(token: str = Depends(oauth2_scheme)) -> UserResponse | None:
    """Dependency that returns None if not authenticated (for optional auth)"""
    if not token:
        return None
    try:
        return await get_current_user(token)
    except HTTPException:
        return None


def require_role(*roles: UserRole):
    """Dependency factory that requires specific roles"""
    async def check_role(current_user: UserResponse = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of these roles: {[r.value for r in roles]}"
            )
        return current_user
    return check_role


def require_permission(permission: str):
    """Dependency factory that requires a specific permission"""
    async def check_permission(current_user: UserResponse = Depends(get_current_user)):
        if not getattr(current_user.permissions, permission, False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission}"
            )
        return current_user
    return check_permission


# =============================================================================
# Public Endpoints (No Auth Required)
# =============================================================================

@router.post("/auth/login", response_model=Token, tags=["Authentication"])
async def login(login_request: LoginRequest):
    """
    Authenticate user and return JWT token.
    
    Use this token in the Authorization header: `Bearer <token>`
    """
    auth_service = get_auth_service()
    user = await auth_service.authenticate_user(login_request.username, login_request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_service.create_access_token(
        data={"sub": user.username, "role": user.role.value},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/auth/token", response_model=Token, tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token endpoint (for Swagger UI).
    """
    auth_service = get_auth_service()
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_service.create_access_token(
        data={"sub": user.username, "role": user.role.value},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


# =============================================================================
# Protected Endpoints
# =============================================================================

@router.get("/auth/me", response_model=UserResponse, tags=["Authentication"])
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    """Get current authenticated user's profile and permissions."""
    return current_user


@router.post("/auth/change-password", tags=["Authentication"])
async def change_password(
    password_change: PasswordChange,
    current_user: UserResponse = Depends(get_current_user)
):
    """Change current user's password."""
    auth_service = get_auth_service()
    
    # Verify current password
    user = await auth_service.authenticate_user(current_user.username, password_change.current_password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    success = await auth_service.update_password(current_user.username, password_change.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password"
        )
    
    return {"message": "Password changed successfully"}


# =============================================================================
# Admin Only Endpoints
# =============================================================================

@router.get("/auth/users", response_model=list[UserResponse], tags=["User Management"])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: UserResponse = Depends(require_role(UserRole.ADMIN))
):
    """List all users (Admin only)."""
    auth_service = get_auth_service()
    return await auth_service.list_users(skip=skip, limit=limit)


@router.post("/auth/users", response_model=UserResponse, tags=["User Management"])
async def create_user(
    user_create: UserCreate,
    current_user: UserResponse = Depends(require_role(UserRole.ADMIN))
):
    """Create a new user (Admin only)."""
    auth_service = get_auth_service()
    try:
        return await auth_service.create_user(user_create)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/auth/users/{username}", tags=["User Management"])
async def delete_user(
    username: str,
    current_user: UserResponse = Depends(require_role(UserRole.ADMIN))
):
    """Delete a user (Admin only)."""
    if username == current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    auth_service = get_auth_service()
    success = await auth_service.delete_user(username)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": f"User {username} deleted successfully"}
