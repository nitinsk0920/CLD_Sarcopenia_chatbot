from __future__ import annotations

import re
from urllib.parse import quote

from sqlalchemy.orm import Session

from config import get_settings
from models.report_models import LearningMedia


TOPIC_ALIASES = {
    "introduction": {"introduction", "intro", "introduction video"},
    "cld": {"cld", "liver", "cld basics", "cld/liver"},
    "sarcopenia": {"sarcopenia", "muscle", "muscle loss", "sarcopenia basics"},
    "diet": {"diet", "protein", "diet/protein", "diet and protein", "diet and nutrition", "nutrition"},
    "exercise": {"exercise", "exercises", "safe exercise", "exercise and movement", "activity"},
    "safety": {"safety", "warning", "warning signs", "safety/warning signs", "safety and warnings", "safety and warning signs"},
}


def _normalize_topic(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", (value or "").strip().lower()).strip()
    for canonical, aliases in TOPIC_ALIASES.items():
        if normalized in aliases:
            return canonical
    return normalized.replace(" ", "-")


def _resolve_supabase_base_url() -> str:
    settings = get_settings()
    if settings.supabase_url:
        return settings.supabase_url.rstrip("/")

    database_url = settings.database_url
    username_match = re.search(r"postgres\.([a-z0-9]+)", database_url, flags=re.IGNORECASE)
    if username_match:
        return f"https://{username_match.group(1)}.supabase.co"

    host_match = re.search(r"db\.([a-z0-9]+)\.supabase\.co", database_url, flags=re.IGNORECASE)
    if host_match:
        return f"https://{host_match.group(1)}.supabase.co"

    raise RuntimeError(
        "Could not resolve the Supabase project URL. Set SUPABASE_URL in backend/.env."
    )


def _build_media_url(bucket_name: str, file_path: str) -> str:
    if file_path.startswith(("http://", "https://")):
        return file_path

    safe_path = quote(file_path.lstrip("/"), safe="/")
    return f"{_resolve_supabase_base_url()}/storage/v1/object/public/{bucket_name}/{safe_path}"


class LearningMediaService:
    def __init__(self, db: Session):
        self.db = db

    def fetch_topic_media(self, topic: str) -> dict[str, object]:
        normalized_topic = _normalize_topic(topic)
        rows = (
            self.db.query(LearningMedia)
            .filter(LearningMedia.is_active.is_(True))
            .order_by(LearningMedia.display_order.asc().nullslast(), LearningMedia.id.asc())
            .all()
        )
        topic_rows = [
            row for row in rows if _normalize_topic(row.topic) == normalized_topic
        ]

        return {
            "topic": normalized_topic,
            "items": [
                {
                    "id": row.id,
                    "topic": normalized_topic,
                    "media_type": (row.media_type or "").strip().lower(),
                    "title": (row.title or "").strip() or "Learning media",
                    "media_url": _build_media_url(row.bucket_name, row.file_path),
                    "display_order": row.display_order or 0,
                }
                for row in topic_rows
            ],
        }
