from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qsl
from urllib.parse import urlencode
from urllib.parse import urlparse
from urllib.parse import urlunparse
from typing import Any

from config import Settings

PLACEHOLDER_POSTGRES_URL = "postgresql://username:password@localhost:5432/cld_chatbot"


@dataclass
class CheckpointerResources:
    saver: Any
    backend_name: str
    _context_manager: Any = None

    def close(self) -> None:
        if self._context_manager is not None:
            self._context_manager.__exit__(None, None, None)


def _is_placeholder_postgres_url(url: str) -> bool:
    normalized = (url or "").strip().lower().rstrip("/")
    return normalized == PLACEHOLDER_POSTGRES_URL.lower().rstrip("/")


def _with_connect_timeout(url: str, timeout_seconds: int = 2) -> str:
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.setdefault("connect_timeout", str(timeout_seconds))
    return urlunparse(parsed._replace(query=urlencode(query)))


def create_checkpointer(settings: Settings) -> CheckpointerResources:
    if settings.postgres_url:
        if _is_placeholder_postgres_url(settings.postgres_url):
            from langgraph.checkpoint.memory import InMemorySaver

            return CheckpointerResources(
                saver=InMemorySaver(),
                backend_name="memory",
            )

        try:
            from langgraph.checkpoint.postgres import PostgresSaver

            connection_string = _with_connect_timeout(settings.postgres_url, timeout_seconds=2)
            context_manager = PostgresSaver.from_conn_string(connection_string)
            saver = context_manager.__enter__()
            saver.setup()
            return CheckpointerResources(
                saver=saver,
                backend_name="postgres",
                _context_manager=context_manager,
            )
        except Exception:
            if not settings.allow_in_memory_fallback:
                raise

    from langgraph.checkpoint.memory import InMemorySaver

    return CheckpointerResources(
        saver=InMemorySaver(),
        backend_name="memory",
    )
