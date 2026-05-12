from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from auth.subscription import get_current_active_admin
from database import db_session_scope
from schemas.learning_schemas import LearningTopicResponse
from services.learning_service import LearningMediaService


router = APIRouter(tags=["learning"])


@router.get("/learning/topics/{topic_id}", response_model=LearningTopicResponse)
def get_learning_topic_media(
    topic_id: str,
    current_admin=Depends(get_current_active_admin),
) -> LearningTopicResponse:
    del current_admin
    try:
        with db_session_scope() as db:
            service = LearningMediaService(db)
            return LearningTopicResponse(**service.fetch_topic_media(topic_id))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
