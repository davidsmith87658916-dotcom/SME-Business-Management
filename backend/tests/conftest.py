import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.dependencies import get_current_user, get_current_user_business, require_business_owner
from app.database import Base, get_db
from app.main import app
from app.models.business import Business
from app.models.business_member import BusinessMember, RoleEnum
from app.models.user import User, UserStatusEnum


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def current_test_user():
    return User(
        id=1,
        email="owner@example.com",
        name="Test Owner",
        password="not-used-in-authorized-api-tests",
        status=UserStatusEnum.ACTIVE,
    )


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = current_test_user
app.dependency_overrides[get_current_user_business] = current_test_user
app.dependency_overrides[require_business_owner] = current_test_user


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        db.add(
            User(
                id=1,
                email="owner@example.com",
                name="Test Owner",
                password="hashed",
                status=UserStatusEnum.ACTIVE,
            )
        )
        db.add(Business(id=1, name="Test Business", currency="USD", timezone="UTC"))
        db.flush()
        db.add(BusinessMember(business_id=1, user_id=1, role=RoleEnum.owner))
        db.commit()
    finally:
        db.close()
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
