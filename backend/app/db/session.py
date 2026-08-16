from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args = {"check_same_thread": False} if not settings.database_url else {}
        _engine = create_engine(settings.sqlalchemy_url, connect_args=connect_args)
        SQLModel.metadata.create_all(_engine)
    return _engine


def get_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session


def new_session() -> Session:
    return Session(get_engine())
