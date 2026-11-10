from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import Base, SessionLocal, engine
from app.deps import get_db, require_admin
from app.main import app
from app.models import Block, BlockItem


@pytest.fixture(scope="session", autouse=True)
def setup_test_database() -> None:
    # Ensure tables exist in Postgres
    Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_database() -> Generator[None, None, None]:
    with SessionLocal() as db:
        db.query(BlockItem).delete()
        db.query(Block).delete()
        db.commit()
    yield
    with SessionLocal() as db:
        db.query(BlockItem).delete()
        db.query(Block).delete()
        db.commit()


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
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
