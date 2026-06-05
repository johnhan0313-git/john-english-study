from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.schemas.common import AIConfigResponse, HealthResponse

router = APIRouter(tags=["common"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


@router.get("/health", response_model=HealthResponse)
def health():
    settings = get_settings()
    return HealthResponse(status="ok", app=settings.app_name)


@router.get("/config/ai", response_model=AIConfigResponse)
def get_ai_config():
    settings = get_settings()
    return AIConfigResponse(
        base_url=settings.ai_base_url,
        model=settings.ai_model,
        has_api_key=bool(settings.ai_api_key),
        use_edge_tts=settings.use_edge_tts,
    )


def create_access_token(username: str) -> str:
    settings = get_settings()
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


@router.post("/auth/register", response_model=TokenResponse, include_in_schema=True)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """JWT auth skeleton — optional for MVP."""
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    user = User(
        username=body.username,
        email=body.email,
        hashed_password=pwd_context.hash(body.password),
    )
    db.add(user)
    db.commit()
    return TokenResponse(access_token=create_access_token(body.username))


@router.post("/auth/login", response_model=TokenResponse, include_in_schema=True)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not pwd_context.verify(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenResponse(access_token=create_access_token(body.username))


def verify_token(token: str) -> str | None:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload.get("sub")
    except JWTError:
        return None
