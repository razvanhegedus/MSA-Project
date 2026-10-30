import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.models.enums import UserRole


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=150)
    phone: str = Field(..., pattern=r"^\+?[0-9\s\-]{7,20}$")
    role: UserRole = Field(default=UserRole.PLAYER)


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # Default 15 minutes in seconds


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserPublicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    phone: str
    role: UserRole
    created_at: datetime


# Aliases for convenience across layers
UserRegister = UserRegisterRequest
UserLogin = UserLoginRequest
TokenRefreshRequest = RefreshTokenRequest
TokenRefresh = RefreshTokenRequest
