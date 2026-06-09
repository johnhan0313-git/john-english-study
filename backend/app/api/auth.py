from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth.captcha import create_captcha, verify_captcha
from app.auth.dependencies import get_current_user
from app.auth.email_codes import can_send_code, create_email_code, verify_email_code
from app.auth.email_service import EmailDeliveryError, send_login_code
from app.auth.jwt import create_access_token
from app.auth.merge import merge_device_to_user
from app.auth.users import get_or_create_user_by_email, get_or_create_user_by_wechat, normalize_email
from app.auth.wechat import (
    WeChatNotConfiguredError,
    build_wechat_authorize_url,
    exchange_wechat_code,
    frontend_callback_url,
    wechat_configured,
)
from app.config import Settings, get_settings
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    CaptchaResponse,
    EmailLoginRequest,
    MergeDeviceRequest,
    MergeDeviceResponse,
    SendEmailCodeRequest,
    SendEmailCodeResponse,
    TokenResponse,
    UserResponse,
)
from app.utils.time import utc_now

router = APIRouter(prefix="/auth", tags=["auth"])

_oauth_states: dict[str, str] = {}


def _user_response(user: User) -> UserResponse:
    display = user.display_name or user.username
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        display_name=display,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
    )


def _issue_token(user: User, db: Session) -> TokenResponse:
    user.last_login_at = utc_now()
    db.commit()
    db.refresh(user)
    return TokenResponse(
        access_token=create_access_token(user.id),
        user=_user_response(user),
    )


def _should_expose_dev_secrets(settings: Settings) -> bool:
    return settings.testing or settings.debug or settings.auth_expose_codes


@router.get("/captcha", response_model=CaptchaResponse)
def get_captcha(settings: Settings = Depends(get_settings)):
    payload = create_captcha()
    return CaptchaResponse(
        captcha_id=payload.captcha_id,
        width=payload.width,
        height=payload.height,
        puzzle_y=payload.puzzle_y,
        piece_width=payload.piece_width,
        background_svg=payload.background_svg,
        piece_svg=payload.piece_svg,
        dev_answer=str(payload.target_x) if _should_expose_dev_secrets(settings) else None,
    )


@router.post("/email/send-code", response_model=SendEmailCodeResponse)
def send_email_code(
    body: SendEmailCodeRequest,
    settings: Settings = Depends(get_settings),
):
    if not verify_captcha(body.captcha_id, body.captcha_x):
        raise HTTPException(status_code=400, detail="拼图验证失败，请重试")

    email = normalize_email(body.email)
    if not settings.testing:
        allowed, wait_seconds = can_send_code(email, cooldown_seconds=settings.email_code_cooldown_seconds)
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=f"Please wait {wait_seconds}s before requesting another code",
            )

    code = create_email_code(email, ttl_seconds=settings.email_code_expire_minutes * 60)
    try:
        send_login_code(settings, email, code)
    except EmailDeliveryError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return SendEmailCodeResponse(
        dev_code=code if _should_expose_dev_secrets(settings) else None,
    )


@router.post("/email/login", response_model=TokenResponse)
def email_login(body: EmailLoginRequest, db: Session = Depends(get_db)):
    email = normalize_email(body.email)
    if not verify_email_code(email, body.code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired code")

    user = get_or_create_user_by_email(db, email)
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account inactive")
    return _issue_token(user, db)


@router.get("/wechat/authorize")
def wechat_authorize(
    next: str = Query("/", max_length=256),
    settings: Settings = Depends(get_settings),
):
    if not wechat_configured(settings):
        raise HTTPException(status_code=503, detail="WeChat login is not configured")
    state = secrets.token_urlsafe(16)
    _oauth_states[state] = next if next.startswith("/") else "/"
    return RedirectResponse(build_wechat_authorize_url(settings, state=state))


@router.get("/wechat/callback")
async def wechat_callback(
    code: str = Query(...),
    state: str = Query(""),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if not wechat_configured(settings):
        raise HTTPException(status_code=503, detail="WeChat login is not configured")

    next_path = _oauth_states.pop(state, "/")
    try:
        profile = await exchange_wechat_code(settings, code)
    except WeChatNotConfiguredError:
        raise HTTPException(status_code=503, detail="WeChat login is not configured") from None
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    user = get_or_create_user_by_wechat(
        db,
        openid=profile["openid"],
        nickname=profile.get("nickname"),
        avatar_url=profile.get("avatar_url"),
    )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account inactive")

    token = _issue_token(user, db).access_token
    return RedirectResponse(frontend_callback_url(settings, token, next_path=next_path))


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return _user_response(user)


@router.post("/merge-device", response_model=MergeDeviceResponse)
def merge_device(
    body: MergeDeviceRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = merge_device_to_user(db, user, body.device_id)
    return MergeDeviceResponse(**result)
