from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import User
from app.db.session import get_db

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


def _token_response(user: User, request: Request) -> TokenResponse:
    settings = request.app.state.settings
    return TokenResponse(
        access_token=create_access_token(
            str(user.id),
            settings.jwt_secret_key,
            settings.access_token_expire_minutes,
        ),
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserResponse.model_validate(user),
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> User:
    if db.scalar(select(User.id).where(User.email == payload.email)) is not None:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="An account with this email already exists."
        ) from exc
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    email = payload.email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return _token_response(user, request)


@router.get("/me", response_model=UserResponse)
def current_user(user: User = Depends(get_current_user)) -> User:
    return user
