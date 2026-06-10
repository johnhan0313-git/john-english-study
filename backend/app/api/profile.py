from __future__ import annotations

import time

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.email_codes import can_send_code, create_email_code, verify_email_code
from app.auth.email_service import EmailDeliveryError, send_email_change_code
from app.auth.users import normalize_email
from app.config import Settings, get_settings
from app.database import get_db
from app.models.user import User
from app.schemas.profile import (
    ChangeEmailRequest,
    ProfileResponse,
    SendEmailChangeCodeRequest,
    SendEmailChangeCodeResponse,
    UpdateProfileRequest,
)
from app.services.media.avatar_paths import (
    ALLOWED_AVATAR_CONTENT_TYPES,
    avatar_api_url,
    avatar_path,
    find_avatar_path,
    remove_avatar_files,
)

router = APIRouter(prefix="/profile", tags=["profile"])


def _should_expose_dev_secrets(settings: Settings) -> bool:
    return settings.testing or settings.debug or settings.auth_expose_codes


def _profile_response(user: User) -> ProfileResponse:
    display = user.display_name or user.username
    return ProfileResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        display_name=display,
        avatar_url=user.avatar_url,
        oauth_provider=user.oauth_provider,
        created_at=user.created_at,
    )


@router.get("", response_model=ProfileResponse)
def get_profile(user: User = Depends(get_current_user)):
    return _profile_response(user)


@router.patch("", response_model=ProfileResponse)
def update_profile(
    body: UpdateProfileRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user.display_name = body.display_name
    db.commit()
    db.refresh(user)
    return _profile_response(user)


@router.post("/email/send-code", response_model=SendEmailChangeCodeResponse)
def send_email_change_code_endpoint(
    body: SendEmailChangeCodeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    new_email = normalize_email(body.new_email)
    current = normalize_email(user.email) if user.email else None
    if current and new_email == current:
        raise HTTPException(status_code=400, detail="新邮箱与当前邮箱相同")

    taken = db.query(User.id).filter(User.email == new_email, User.id != user.id).first()
    if taken:
        raise HTTPException(status_code=400, detail="该邮箱已被其他账号使用")

    if not settings.testing:
        allowed, wait_seconds = can_send_code(new_email, cooldown_seconds=settings.email_code_cooldown_seconds)
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=f"请等待 {wait_seconds}s 后再试",
            )

    code = create_email_code(new_email, ttl_seconds=settings.email_code_expire_minutes * 60)
    try:
        send_email_change_code(settings, new_email, code)
    except EmailDeliveryError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return SendEmailChangeCodeResponse(
        dev_code=code if _should_expose_dev_secrets(settings) else None,
    )


@router.patch("/email", response_model=ProfileResponse)
def change_email(
    body: ChangeEmailRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    new_email = normalize_email(body.new_email)
    current = normalize_email(user.email) if user.email else None
    if current and new_email == current:
        raise HTTPException(status_code=400, detail="新邮箱与当前邮箱相同")

    if not verify_email_code(new_email, body.code):
        raise HTTPException(status_code=400, detail="邮箱验证码错误或已过期")

    taken = db.query(User.id).filter(User.email == new_email, User.id != user.id).first()
    if taken:
        raise HTTPException(status_code=400, detail="该邮箱已被其他账号使用")

    user.email = new_email
    db.commit()
    db.refresh(user)
    return _profile_response(user)


@router.post("/avatar", response_model=ProfileResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    content_type = (file.content_type or "").split(";", 1)[0].strip().lower()
    ext = ALLOWED_AVATAR_CONTENT_TYPES.get(content_type)
    if not ext:
        raise HTTPException(status_code=400, detail="仅支持 JPG、PNG、WebP 格式")

    data = await file.read()
    if len(data) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片大小不能超过 2MB")
    if not data:
        raise HTTPException(status_code=400, detail="上传文件为空")

    remove_avatar_files(user.id, settings)
    path = avatar_path(user.id, ext, settings)
    path.write_bytes(data)

    user.avatar_url = avatar_api_url(user.id, version=int(time.time()))
    db.commit()
    db.refresh(user)
    return _profile_response(user)


@router.get("/avatar/{user_id}")
def get_avatar(user_id: int, settings: Settings = Depends(get_settings)):
    path = find_avatar_path(user_id, settings)
    if not path:
        raise HTTPException(status_code=404, detail="Avatar not found")

    media_type = {
        ".jpg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }.get(path.suffix.lower(), "application/octet-stream")
    return FileResponse(path, media_type=media_type)
