import string
import random

import pytest
from flask_sqlalchemy.session import Session
from sqlalchemy import select

from api import create_app, configure_routes, configure_db, configure_auth
from config import app_config
from database import db
from database.auth_key import AuthKey
from routes.auth import create_account, CreateAccountBody


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


def test_create_key_should_succeed(client, app):
    name = ''.join(random.choices(string.ascii_lowercase, k=5))
    response = client.post(
        "/v1/auth/keys",
        json={
            "name": name,
            "key": "test",
        },
        headers={
            "Authorization": app_config.auth.admin_key
        }
    )

    assert response.status_code == 200

    with app.app_context():
        session = Session(db)

        query = select(AuthKey).where(AuthKey.name == name)
        key = session.execute(query).first()

        assert key is not None


def test_create_key_no_admin_auth_should_fail(client):
    response = client.post(
        "/v1/auth/keys",
        json={
            "name": "test",
            "key": "test",
            "description": "test"
        })

    assert response.status_code == 401


def test_create_key_wrong_key_should_fail(client):
    response = client.post(
        "/v1/auth/keys",
        json={
            "name": "test",
            "key": "test",
            "description": "test"
        },
        headers={
            "Authorization": "wrong_key"
        })

    assert response.status_code == 403


def test_create_key_no_body_should_fail(client):
    response = client.post(
        "/v1/auth/keys",
        json={},
        headers={
            "Authorization": app_config.auth.admin_key
        }
    )

    assert response.status_code == 400


def test_get_token_should_succeed(client):
    name = ''.join(random.choices(string.ascii_lowercase, k=5))
    response = client.post(
        "/v1/auth/keys",
        json={
            "name": name,
            "key": "test"
        },
        headers={
            "Authorization": app_config.auth.admin_key
        }
    )

    assert response.status_code == 200

    response = client.post(
        "/v1/auth",
        json={
            "name": name,
            "key": "test"
        }
    )

    assert response.status_code == 200
    assert response.json["content"]["token"] is not None


def test_get_token_key_not_found_should_fail(client):
    response = client.post(
        "/v1/auth",
        json={
            "name": ''.join(random.choices(string.ascii_lowercase, k=5)),
            "key": "test"
        }
    )

    assert response.status_code == 401


def test_get_token_wrong_key_should_fail(client):
    name = ''.join(random.choices(string.ascii_lowercase, k=5))
    response = client.post(
        "/v1/auth/keys",
        json={
            "name": name,
            "key": "test"
        },
        headers={
            "Authorization": app_config.auth.admin_key
        }
    )

    assert response.status_code == 200

    response = client.post(
        "/v1/auth",
        json={
            "name": name,
            "key": "not_the_key"
        }
    )

    assert response.status_code == 401
