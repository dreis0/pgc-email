import pytest

from api import create_app, configure_routes, configure_db, configure_auth
from config import app_config


@pytest.fixture
def app():
    app = create_app()
    configure_routes(app)
    configure_db(app)
    configure_auth(app)

    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


def test_send_email_should_should_succeed(client):
    response = client.post(
        "/v1/email",
        json={
            "body": "test",
            "email": "test@email.com",
            "subject": "test"
        },
        headers={
            "Authorization": app_config.auth.admin_key,
        }
    )

    assert response.status_code == 200


def test_send_email_should_require_auth(client):
    response = client.post(
        "/v1/email",
        json={
            "body": "test",
            "email": "test@email.com",
            "subject": "test"
        },
    )

    assert response.status_code == 401


def test_empty_fields_should_fail(client):
    response = client.post(
        "/v1/email",
        json={
            "body": "",
            "email": "",
            "subject": ""
        },
        headers={
            "Authorization": app_config.auth.admin_key,
        }
    )

    assert response.status_code == 400


def test_invalid_email_address_should_fail(client):
    response = client.post(
        "/v1/email",
        json={
            "body": "test",
            "email": "test",
            "subject": "test"
        },
        headers={
            "Authorization": app_config.auth.admin_key,
        }
    )

    assert response.status_code == 400
