from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from app.application.identity.identity_command import (
    LoginOrRegisterByEmailInput,
    LoginOrRegisterByWechatInput,
    MergeDeviceInput,
)
from app.auth.dependencies import get_current_user
from app.auth.email_codes import can_send_code, create_email_code, rollback_email_code, verify_email_code
from app.auth.email_service import EmailDeliveryError, send_login_code
from app.auth.users import normalize_email
from app.auth.wechat import (
    WeChatNotConfiguredError,
    build_wechat_authorize_url,
    exchange_wechat_code,
    frontend_callback_url,
    wechat_configured,
)
from app.composition.shared_composition import AppContainer, get_container
from app.config import Settings, get_settings
from app.models.user import User
from app.schemas.auth import (
    EmailLoginRequest,
    MergeDeviceRequest,
    MergeDeviceResponse,
    SendEmailCodeRequest,
    SendEmailCodeResponse,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])

_oauth_states: dict[str, tuple[str, str]] = {}


def _user_response(user: User) -> UserResponse:
    display = user.display_name or user.username
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        display_name=display,
        avatar_url=user.avatar_url,
        oauth_provider=user.oauth_provider,
        created_at=user.created_at,
    )


def _token_response(access_token: str, user: User) -> TokenResponse:
    return TokenResponse(
        access_token=access_token,
        user=_user_response(user),
    )


def _should_expose_dev_secrets(settings: Settings) -> bool:
    return settings.testing or settings.debug or settings.auth_expose_codes


@router.post("/email/send-code", response_model=SendEmailCodeResponse)
def send_email_code(
    body: SendEmailCodeRequest,
    settings: Settings = Depends(get_settings),
):
    email = normalize_email(body.email)
    if not settings.testing:
        allowed, wait_seconds = can_send_code(email, cooldown_seconds=settings.email_code_cooldown_seconds)
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=f"请等待 {wait_seconds}s 后再试",
            )

    code = create_email_code(email, ttl_seconds=settings.email_code_expire_minutes * 60)
    try:
        send_login_code(settings, email, code)
    except EmailDeliveryError as exc:
        rollback_email_code(email)
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return SendEmailCodeResponse(
        cooldown_seconds=settings.email_code_cooldown_seconds,
        dev_code=code if _should_expose_dev_secrets(settings) else None,
    )


@router.post("/email/login", response_model=TokenResponse)
def email_login(
    body: EmailLoginRequest,
    container: AppContainer = Depends(get_container),
):
    email = normalize_email(body.email)
    if not verify_email_code(email, body.code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱验证码错误或已过期")

    result = container.identity.login_or_register_email.execute(
        LoginOrRegisterByEmailInput(email=email)
    )
    if not result.user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account inactive")
    return _token_response(result.access_token, result.user)


@router.get("/wechat/authorize")
def wechat_authorize(
    next: str = Query("/", max_length=256),
    platform: str = Query("web", pattern="^(web|app)$"),
    settings: Settings = Depends(get_settings),
):
    if not wechat_configured(settings):
        raise HTTPException(status_code=503, detail="WeChat login is not configured")
    state = secrets.token_urlsafe(16)
    _oauth_states[state] = (next if next.startswith("/") else "/", platform)
    return RedirectResponse(build_wechat_authorize_url(settings, state=state))


@router.get("/wechat/callback")
async def wechat_callback(
    code: str = Query(...),
    state: str = Query(""),
    settings: Settings = Depends(get_settings),
    container: AppContainer = Depends(get_container),
):
    if not wechat_configured(settings):
        raise HTTPException(status_code=503, detail="WeChat login is not configured")

    next_path, oauth_platform = _oauth_states.pop(state, ("/", "web"))
    try:
        profile = await exchange_wechat_code(settings, code)
    except WeChatNotConfiguredError:
        raise HTTPException(status_code=503, detail="WeChat login is not configured") from None
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    result = container.identity.login_or_register_wechat.execute(
        LoginOrRegisterByWechatInput(
            openid=profile["openid"],
            nickname=profile.get("nickname"),
            avatar_url=profile.get("avatar_url"),
        )
    )
    if not result.user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account inactive")

    return RedirectResponse(
        frontend_callback_url(
            settings,
            result.access_token,
            next_path=next_path,
            platform=oauth_platform,
        )
    )


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return _user_response(user)


@router.post("/merge-device", response_model=MergeDeviceResponse)
def merge_device(
    body: MergeDeviceRequest,
    user: User = Depends(get_current_user),
    container: AppContainer = Depends(get_container),
):
    result = container.identity.merge_device.execute(
        MergeDeviceInput(user_id=user.id, device_id=body.device_id)
    )
    return MergeDeviceResponse(**result)
