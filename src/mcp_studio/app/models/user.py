"""User models for MCP Studio."""

from enum import StrEnum

from pydantic import BaseModel, Field


class UserRole(StrEnum):
    """User role enumeration."""

    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class User(BaseModel):
    """User model."""

    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str | None = Field(None, description="Email address")
    role: UserRole = Field(UserRole.USER, description="User role")
    active: bool = Field(True, description="Whether the user is active")


class UserInDB(User):
    """User model with database fields."""

    hashed_password: str = Field(..., description="Hashed password")
    full_name: str | None = Field(None, description="Full name")
    disabled: bool = Field(False, description="Whether the user is disabled")
