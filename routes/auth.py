import os
from datetime import datetime, timedelta

import bcrypt as bcrypt
import jwt
from flask_openapi3 import APIBlueprint, Tag
from flask_sqlalchemy.session import Session
from pydantic import BaseModel
from sqlalchemy import select, insert

from database import db
from database.auth_key import AuthKey
from middlewares.master_auth import require_master_auth
from response import Response, ResponseWithContent


class CreateAccountBody(BaseModel):
    name: str
    key: str
    description: str


class LoginBody(BaseModel):
    name: str
    key: str


secret = os.getenv("AUTH_SECRET")
blueprint = APIBlueprint('auth', __name__, url_prefix='/v1/auth')


@blueprint.post('/create', responses={"200": ResponseWithContent, "400": Response},
                tags=[Tag(name="Auth creation route", description="Registers a new key for authentication")])
@require_master_auth
def create_account(body: CreateAccountBody):
    session = Session(db)

    query = select(AuthKey).where(AuthKey.name == body.name)
    key = session.execute(query).first()

    if key is None:
        hashed_key = bcrypt.hashpw(body.key.encode('utf-8'), bcrypt.gensalt())
        registration = AuthKey(name=body.name, key=hashed_key.decode("utf-8"), description=body.description)

        session.execute(insert(AuthKey), [registration.to_dict()])
        session.commit()

        token = generate_token(body.name)

        return ResponseWithContent(status=200, content={"token": token}).as_return()
    else:
        return Response(message="Account already exists", status=400).as_return()


@blueprint.post('/login', responses={"200": ResponseWithContent, "400": Response}, tags=[Tag(
    name="Auth token generation route",
    description="Generates ephemeral token for authentication"
)])
def login(body: LoginBody):
    session = Session(db)

    query = select(AuthKey).where(AuthKey.name == body.name).where(AuthKey.enabled)
    user = session.execute(query).scalars().first()

    if user is None:
        return Response(message="Account does not exist", status=400).as_return()
    else:
        if bcrypt.checkpw(body.key.encode('utf-8'), user.key.encode('utf-8')):
            token = generate_token(body.name)

            return ResponseWithContent(content={"token": token}, status=200).as_return()
        else:
            return Response(message="Invalid auth data", status=400).as_return()


def generate_token(name):
    expiration = int(os.getenv("AUTH_EXPIRATION"))
    algorithm = os.getenv("AUTH_ALGORITHM")
    payload = {
        'exp': datetime.utcnow() + timedelta(seconds=expiration),
        'iat': datetime.utcnow(),
        'sub': name
    }

    return jwt.encode(
        payload,
        secret,
        algorithm=algorithm
    )
