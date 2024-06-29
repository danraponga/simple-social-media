from typing import Generator

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from jose.exceptions import JWTError
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.core.security import (
    ACCESS_TOKEN_TYPE,
    REFRESH_TOKEN_TYPE,
    TOKEN_TYPE_FIELD,
    decode_token,
)
from app.models.user import User
from app.repositories.user_gateway import UserDbGateway
from app.schemas.auth import RefreshToken

bearer = HTTPBearer(auto_error=False)


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_user_gateway(db: Session = Depends(get_db)) -> UserDbGateway:
    return UserDbGateway(db)


def get_user_by_token(token: str, target_type: str, gateway: UserDbGateway) -> User:
    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(
            status_code=403,
            detail="Could not validate credentials",
        )
    if payload.get(TOKEN_TYPE_FIELD) != target_type:
        raise HTTPException(status_code=401, detail="Invalid token type")

    user = gateway.get_by_id(payload.get("sub"))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_current_auth_user(
    token: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_user_gateway),
) -> User:
    if not token:
        raise HTTPException(status_code=403, detail="Credentials not provided")
    return get_user_by_token(token.credentials, ACCESS_TOKEN_TYPE, db)


def get_current_auth_user_refresh(
    token: RefreshToken, gateway: Session = Depends(get_user_gateway)
) -> User:
    return get_user_by_token(token.refresh_token, REFRESH_TOKEN_TYPE, gateway)
