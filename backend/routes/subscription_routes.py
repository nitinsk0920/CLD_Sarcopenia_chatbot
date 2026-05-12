from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter
from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth.jwt_handler import get_current_admin
from auth.subscription import get_subscription_status
from db.database import get_db
from models.report_models import HospitalAdmin


router = APIRouter(prefix="/subscription", tags=["subscription"])


class SubscriptionStatusResponse(BaseModel):
    status: str | None = None
    active_from: datetime | None = None
    active_until: datetime | None = None
    can_access: bool


@router.get("/status", response_model=SubscriptionStatusResponse)
def subscription_status(
    current_admin: HospitalAdmin = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> SubscriptionStatusResponse:
    result = get_subscription_status(current_admin.id, db)
    return SubscriptionStatusResponse(**result)
