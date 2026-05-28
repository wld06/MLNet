import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.deps import get_db
from app.db.session import Base
from app.main import app

TEST_DATABASE_URL = "postgresql://user:password@localhost:5432/mlnest_test"


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_db(test_engine):
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSession()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
def client(test_db):
    def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
