from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.db import Base
from app.db_views import PUBLIC_CHUNKS_VIEW_SQL
from app.deps import get_db, require_admin
from app.main import app

test_db_url = make_url(settings.get_database_url()).set(database="portfolio_test")
if not test_db_url.database or not test_db_url.database.endswith("_test"):
    raise RuntimeError(f"Test database name must end with '_test', got: {test_db_url.database}")

test_engine = create_engine(test_db_url)
test_sessionmaker = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database() -> None:
    # Ensure tables exist in Postgres
    with test_engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    with test_engine.begin() as connection:
        connection.execute(text(PUBLIC_CHUNKS_VIEW_SQL))


@pytest.fixture(autouse=True)
def clean_database() -> Generator[None, None, None]:
    with test_sessionmaker() as db:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(text(f'TRUNCATE TABLE "{table.name}" RESTART IDENTITY CASCADE;'))
        db.commit()
    yield
    with test_sessionmaker() as db:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(text(f'TRUNCATE TABLE "{table.name}" RESTART IDENTITY CASCADE;'))
        db.commit()


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    db = test_sessionmaker()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def admin_client(client: TestClient) -> Generator[TestClient, None, None]:
    app.dependency_overrides[require_admin] = lambda: None
    yield client
    app.dependency_overrides.pop(require_admin, None)
