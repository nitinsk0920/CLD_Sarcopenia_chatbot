from __future__ import annotations

from pydantic import BaseModel


class LearningMediaItem(BaseModel):
    id: int
    topic: str
    media_type: str
    title: str
    media_url: str
    display_order: int


class LearningTopicResponse(BaseModel):
    topic: str
    items: list[LearningMediaItem]
