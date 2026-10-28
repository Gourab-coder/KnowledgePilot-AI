import uuid

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.models import User
from app.db.session import get_db

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized

    subject = decode_access_token(credentials.credentials, request.app.state.settings.jwt_secret_key)
    if subject is None:
        raise unauthorized
    try:
        user_id = uuid.UUID(subject)
    except ValueError:
        raise unauthorized from None

    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise unauthorized
    return user
