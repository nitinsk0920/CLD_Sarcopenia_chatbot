from __future__ import annotations

from datetime import datetime
from datetime import timezone
from typing import Any

from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from auth.jwt_handler import security
from auth.jwt_handler import get_current_admin
from db.database import get_db
from models.report_models import HospitalAdmin


SUBSCRIPTION_EXPIRED_DETAIL = "Subscription expired"


def _normalize_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def get_subscription_status(admin_id: int, db: Session) -> dict[str, Any]:
    row = (
        db.execute(
            text(
                """
                SELECT status, active_from, active_until
                FROM hospital_subscription
                WHERE admin_id = :admin_id
                ORDER BY active_until DESC NULLS LAST
                LIMIT 1
                """
            ),
            {"admin_id": admin_id},
        )
        .mappings()
        .first()
    )

    if row is None:
        return {
            "status": "missing",
            "active_from": None,
            "active_until": None,
            "can_access": False,
        }

    status = str(row.get("status") or "").strip().lower()
    active_from = _normalize_datetime(row.get("active_from"))
    active_until = _normalize_datetime(row.get("active_until"))
    current_time = datetime.now(timezone.utc)
    can_access = status == "active" and active_until is not None and current_time <= active_until

    return {
        "status": row.get("status"),
        "active_from": active_from,
        "active_until": active_until,
        "can_access": can_access,
    }


def check_subscription(admin_id: int, db: Session) -> dict[str, Any]:
    subscription = get_subscription_status(admin_id, db)
    if not subscription["can_access"]:
        raise HTTPException(status_code=403, detail=SUBSCRIPTION_EXPIRED_DETAIL)
    return subscription


def require_active_subscription(
    current_admin: HospitalAdmin = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> HospitalAdmin:
    check_subscription(current_admin.id, db)
    return current_admin


def get_current_active_admin(
    credentials=Depends(security),
    db: Session = Depends(get_db),
) -> HospitalAdmin:
    try:
        current_admin = get_current_admin(credentials=credentials, db=db)
    except HTTPException as exc:
        raise HTTPException(status_code=403, detail="Admin access denied.") from exc

    try:
        check_subscription(current_admin.id, db)
    except HTTPException as exc:
        if exc.status_code == 403 and exc.detail == SUBSCRIPTION_EXPIRED_DETAIL:
            raise
        raise HTTPException(status_code=403, detail="Admin access denied.") from exc
    return current_admin
