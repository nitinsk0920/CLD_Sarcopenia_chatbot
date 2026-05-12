from __future__ import annotations

from datetime import datetime
from datetime import timezone

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from pydantic import BaseModel
from pydantic import Field
from sqlalchemy.orm import Session

from auth.jwt_handler import create_access_token
from auth.jwt_handler import verify_password
from db.database import get_db
from models.report_models import HospitalAdmin


router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    username = payload.username.strip()
    password = payload.password.strip()

    admin = db.query(HospitalAdmin).filter(HospitalAdmin.username == username).one_or_none()
    if admin is None or not verify_password(password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    if not admin.is_active:
        raise HTTPException(status_code=403, detail="Admin account is inactive.")

    admin.last_login_at = datetime.now(timezone.utc)
    db.commit()

    token = create_access_token(
        {
            "sub": admin.username,
            "admin_id": admin.id,
            "role": admin.role or "admin",
        }
    )
    return LoginResponse(access_token=token)
