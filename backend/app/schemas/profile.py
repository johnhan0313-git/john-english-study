from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ProfileResponse(BaseModel):
    id: int
    username: str
    email: str | None
    display_name: str | None
    avatar_url: str | None
    oauth_provider: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=32)

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Display name cannot be empty")
        return trimmed


class SendEmailChangeCodeRequest(BaseModel):
    new_email: str = Field(min_length=3, max_length=128)

    @field_validator("new_email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        normalized = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", normalized):
            raise ValueError("Invalid email address")
        return normalized


class SendEmailChangeCodeResponse(BaseModel):
    message: str = "Verification code sent"
    cooldown_seconds: int = 0
    dev_code: str | None = None


class ChangeEmailRequest(BaseModel):
    new_email: str = Field(min_length=3, max_length=128)
    code: str = Field(min_length=4, max_length=8)

    @field_validator("new_email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        normalized = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", normalized):
            raise ValueError("Invalid email address")
        return normalized
