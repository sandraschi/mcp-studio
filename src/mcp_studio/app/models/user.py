"""User models for MCP Studio."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class User(BaseModel):
    """User model."""
    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: Optional[str] = Field(None, description="Email address")
    role: UserRole = Field(UserRole.USER, description="User role")
    active: bool = Field(True, description="Whether the user is active")


class UserInDB(User):
    """User model with database fields."""
    hashed_password: str = Field(..., description="Hashed password")
    full_name: Optional[str] = Field(None, description="Full name")
    disabled: bool = Field(False, description="Whether the user is disabled")
