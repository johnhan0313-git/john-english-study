from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.jwt import create_access_token
from app.auth.merge import merge_device_to_user
from app.auth.passwords import hash_password, verify_password
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    MergeDeviceRequest,
    MergeDeviceResponse,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.utils.time import utc_now

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        display_name=user.display_name or user.username,
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


@router.post("/register", response_model=TokenResponse)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    if body.email:
        email_taken = db.query(User).filter(User.email == body.email).first()
        if email_taken:
            raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
        display_name=body.username,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _issue_token(user, db)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account inactive")
    return _issue_token(user, db)


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


@router.get("/oauth/{provider}/authorize")
def oauth_authorize(provider: str):
    raise HTTPException(status_code=501, detail=f"OAuth provider '{provider}' is not configured yet")


@router.get("/oauth/{provider}/callback")
def oauth_callback(provider: str):
    raise HTTPException(status_code=501, detail=f"OAuth provider '{provider}' is not configured yet")
