from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any

import bcrypt
import jwt
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from config import get_settings
from db.database import get_db
from models.report_models import HospitalAdmin


security = HTTPBearer(auto_error=False)


def _unauthorized(detail: str = "Could not validate admin credentials.") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except ValueError:
        return False


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    if not settings.jwt_secret_key:
        raise RuntimeError("JWT secret is not configured. Set JWT_SECRET_KEY or JWT_SECRET in backend/.env.")
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    payload = {
        **data,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    if not settings.jwt_secret_key:
        raise RuntimeError("JWT secret is not configured. Set JWT_SECRET_KEY or JWT_SECRET in backend/.env.")
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.InvalidTokenError as exc:
        raise _unauthorized("Invalid or expired admin token.") from exc


def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> HospitalAdmin:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized("Admin bearer token is required.")

    payload = decode_token(credentials.credentials)
    admin_id = payload.get("admin_id")
    username = str(payload.get("sub", "")).strip()

    if not admin_id or not username:
        raise _unauthorized("Admin token payload is invalid.")

    try:
        admin_id = int(admin_id)
    except (TypeError, ValueError) as exc:
        raise _unauthorized("Admin token payload is invalid.") from exc

    admin = (
        db.query(HospitalAdmin)
        .filter(HospitalAdmin.id == admin_id, HospitalAdmin.username == username)
        .one_or_none()
    )
    if admin is None or not admin.is_active:
        raise _unauthorized("Admin account is not available.")

    return admin
