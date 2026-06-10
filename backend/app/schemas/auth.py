from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class UserResponse(BaseModel):
    id: int
    username: str
    email: str | None
    display_name: str | None
    avatar_url: str | None
    oauth_provider: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class CaptchaResponse(BaseModel):
    captcha_id: str
    width: int
    height: int
    puzzle_y: int
    piece_width: int
    background_svg: str
    piece_svg: str
    dev_answer: str | None = None


class SendEmailCodeRequest(BaseModel):
    email: str = Field(min_length=3, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        normalized = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", normalized):
            raise ValueError("Invalid email address")
        return normalized


class SendEmailCodeResponse(BaseModel):
    message: str = "Verification code sent"
    cooldown_seconds: int = 0
    dev_code: str | None = None


class EmailLoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=128)
    code: str = Field(min_length=4, max_length=8)
    captcha_id: str
    captcha_x: int = Field(ge=0, le=500)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        normalized = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", normalized):
            raise ValueError("Invalid email address")
        return normalized


class WeChatAuthorizeResponse(BaseModel):
    authorize_url: str


class MergeDeviceRequest(BaseModel):
    device_id: str = Field(min_length=1, max_length=64)


class MergeDeviceResponse(BaseModel):
    word_progress: int
    scenarios: int
    attempts: int
    conversations: int
    streak: int
