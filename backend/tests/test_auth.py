from app.models.user import User, UserStatusEnum


def test_register_openapi_example_is_valid(client):
    schema = client.get("/openapi.json").json()
    example = schema["components"]["schemas"]["UserCreate"]["example"]
    response = client.post("/api/v1/auth/register", json=example)
    assert response.status_code == 201, response.text


def test_register_normalizes_email_and_login_rejects_inactive_user(client, db_session):
    weak_password = client.post(
        "/api/v1/auth/register",
        json={"name": "New Owner", "email": "new.owner@example.com", "password": "short"},
    )
    assert weak_password.status_code == 422

    registered = client.post(
        "/api/v1/auth/register",
        json={"name": "New Owner", "email": "New.Owner@Example.COM", "password": "safe-password-123"},
    )
    assert registered.status_code == 201, registered.text
    assert registered.json()["email"] == "new.owner@example.com"

    login = client.post(
        "/api/v1/auth/login",
        data={"username": "NEW.OWNER@EXAMPLE.COM", "password": "safe-password-123"},
    )
    assert login.status_code == 200, login.text
    assert login.json()["token_type"] == "bearer"

    user = db_session.query(User).filter(User.email == "new.owner@example.com").one()
    user.status = UserStatusEnum.INACTIVE
    db_session.commit()
    inactive_login = client.post(
        "/api/v1/auth/login",
        data={"username": "new.owner@example.com", "password": "safe-password-123"},
    )
    assert inactive_login.status_code == 401
