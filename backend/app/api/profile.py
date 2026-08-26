from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.application.profile.profile_command import (
    ChangeEmailInput,
    GetProfileInput,
    SendEmailChangeCodeInput,
    UpdateProfileInput,
    UploadAvatarInput,
)
from app.auth.dependencies import get_current_user
from app.auth.email_service import EmailDeliveryError
from app.composition.shared_composition import AppContainer, get_container
from app.config import Settings, get_settings
from app.models.user import User
from app.schemas.profile import (
    ChangeEmailRequest,
    ProfileResponse,
    SendEmailChangeCodeRequest,
    SendEmailChangeCodeResponse,
    UpdateProfileRequest,
)
from app.services.media.avatar_paths import find_avatar_key
from app.services.storage.responses import storage_stream_response

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
def get_profile(
    user: User = Depends(get_current_user),
    container: AppContainer = Depends(get_container),
):
    result = container.profile.get_profile.execute(GetProfileInput(user_id=user.id))
    return ProfileResponse(**asdict(result))


@router.patch("", response_model=ProfileResponse)
def update_profile(
    body: UpdateProfileRequest,
    user: User = Depends(get_current_user),
    container: AppContainer = Depends(get_container),
):
    result = container.profile.update_profile.execute(
        UpdateProfileInput(user_id=user.id, display_name=body.display_name)
    )
    return ProfileResponse(**asdict(result))


@router.post("/email/send-code", response_model=SendEmailChangeCodeResponse)
def send_email_change_code_endpoint(
    body: SendEmailChangeCodeRequest,
    user: User = Depends(get_current_user),
    container: AppContainer = Depends(get_container),
):
    try:
        result = container.profile.send_email_change_code.execute(
            SendEmailChangeCodeInput(user_id=user.id, new_email=body.new_email)
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except EmailDeliveryError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return SendEmailChangeCodeResponse(
        cooldown_seconds=result.cooldown_seconds,
        dev_code=result.dev_code,
    )


@router.patch("/email", response_model=ProfileResponse)
def change_email(
    body: ChangeEmailRequest,
    user: User = Depends(get_current_user),
    container: AppContainer = Depends(get_container),
):
    try:
        result = container.profile.change_email.execute(
            ChangeEmailInput(user_id=user.id, new_email=body.new_email, code=body.code)
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ProfileResponse(**asdict(result))


@router.post("/avatar", response_model=ProfileResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    container: AppContainer = Depends(get_container),
):
    data = await file.read()
    try:
        result = container.profile.upload_avatar.execute(
            UploadAvatarInput(
                user_id=user.id,
                content_type=file.content_type or "",
                data=data,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ProfileResponse(**asdict(result))


@router.get("/avatar/{user_id}")
def get_avatar(user_id: int, settings: Settings = Depends(get_settings)):
    found = find_avatar_key(user_id, settings)
    if not found:
        raise HTTPException(status_code=404, detail="Avatar not found")

    key, media_type = found
    return storage_stream_response(key, media_type=media_type, filename=f"avatar_{user_id}")
