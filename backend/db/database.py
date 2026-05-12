from __future__ import annotations

from collections.abc import Generator
import re
from urllib.parse import parse_qsl
from urllib.parse import quote
from urllib.parse import urlencode
from urllib.parse import urlparse
from urllib.parse import urlunparse

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

try:
    from config import get_settings
except ModuleNotFoundError:  # pragma: no cover - supports package-style imports
    from backend.config import get_settings


Base = declarative_base()


def _normalize_database_url(database_url: str) -> str:
    if not database_url:
        return database_url

    if database_url.startswith("postgresql+psycopg://"):
        return database_url

    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)

    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    return database_url


def _encode_credentials(database_url: str) -> str:
    match = re.match(
        r"^(?P<scheme>postgresql(?:\+psycopg)?://)"
        r"(?P<username>[^:/?#]+):(?P<password>[^@]+)"
        r"@(?P<rest>.+)$",
        database_url,
    )
    if not match:
        return database_url

    username = quote(match.group("username"), safe="")
    password = quote(match.group("password"), safe="")
    return f"{match.group('scheme')}{username}:{password}@{match.group('rest')}"


def _ensure_sslmode(database_url: str) -> str:
    if not database_url.startswith("postgresql+psycopg://"):
        return database_url

    parsed = urlparse(database_url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.setdefault("sslmode", "require")
    query.setdefault("connect_timeout", "5")
    return urlunparse(parsed._replace(query=urlencode(query)))


DATABASE_URL = _ensure_sslmode(
    _encode_credentials(_normalize_database_url(get_settings().database_url))
)

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not configured. Set it in backend/.env.")


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


def get_engine():
    return engine


def get_session_factory():
    return SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
