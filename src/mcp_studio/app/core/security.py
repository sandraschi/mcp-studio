"""
Security utilities for MCP Studio

This module provides security-related functionality including authentication,
authorization, and WebSocket security.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from ..core.config import settings
from ..models.user import User, UserInDB

logger = logging.getLogger(__name__)

# OAuth2 scheme for token authentication - only used where explicitly required
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# Note: This OAuth2 scheme is only used for routes that explicitly require authentication.
# Public routes (health checks, repo scanning, etc.) do not use this dependency.

# JWT configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Mock user database (replace with actual database in production)
fake_users_db = {
    "admin": {
        "username": "admin",
        "email": "admin@example.com",
        "full_name": "Admin User",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # secret
        "disabled": False,
        "roles": ["admin"],
    },
    "user": {
        "username": "user",
        "email": "user@example.com",
        "full_name": "Regular User",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # secret
        "disabled": False,
        "roles": ["user"],
    },
}


class Token(BaseModel):
    """Token model for authentication."""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data model."""

    username: str | None = None
    scopes: list[str] = []


def get_user(db: Any, username: str) -> Any:
    """Get user from database."""
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(fake_db: Any, username: str, password: str) -> Any:
    """Authenticate a user."""
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> Any:
    """Create a new access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> Any:
    """Get the current authenticated user from a token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = get_user(fake_users_db, username=username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get the current active user."""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_user_ws(token: str) -> User:
    """Get the current authenticated user from a WebSocket token."""
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")

        user = get_user(fake_users_db, username=username)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        return user

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    # In a real application, use a proper password hashing library
    # This is a simplified version for demonstration
    import binascii
    import hashlib

    # Simple hash verification (replace with proper password hashing in production)
    salt = hashed_password[:29]  # Extract the salt from the stored hash
    hashlib.pbkdf2_hmac(
        "sha256",
        plain_password.encode("utf-8"),
        salt.encode("utf-8"),
        100000,  # Number of iterations
    )

    # Compare the new hash with the stored hash
    return hashlib.pbkdf2_hmac(
        "sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100000
    ) == binascii.unhexlify(hashed_password[29:])


def get_password_hash(password: str) -> str:
    """Generate a password hash."""
    # In a real application, use a proper password hashing library
    # This is a simplified version for demonstration
    import binascii
    import hashlib
    import os

    # Generate a random salt
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode("ascii")

    # Hash the password with the salt
    pwdhash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100000,  # Number of iterations
    )

    # Combine the salt and hash
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode("ascii")


# Role-based access control (RBAC)
class RoleChecker:
    """Check if a user has the required roles."""

    def __init__(self, allowed_roles: list) -> None:
        """Initialize with allowed roles."""
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_user)) -> Any:
        """Check if the user has any of the allowed roles."""
        if not any(role in (user.roles or []) for role in self.allowed_roles):
            logger.warning(f"User {user.username} with roles {user.roles} not in {self.allowed_roles}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")
        return user


# Common role checkers
allow_admin = RoleChecker(["admin"])
allow_any_authenticated = RoleChecker(["user", "admin"])
