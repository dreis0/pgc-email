from datetime import datetime, timedelta

import bcrypt as bcrypt
import jwt
from flask import request
from flask_openapi3 import APIBlueprint, Tag
from flask_sqlalchemy.session import Session
from pydantic import BaseModel, Field
from sqlalchemy import select, insert

from config import app_config
from database import db
from database.auth_key import AuthKey
from response import Response, ResponseWithContent


class CreateAccountBody(BaseModel):
    name: str = ""
    key: str = ""
    description: str = None

    class Config:
        # Customize the error message for missing fields
        missing_error = 'O campo "{field_name}" é obrigatório'


class LoginBody(BaseModel):
    name: str
    key: str


class KeyViewModel(BaseModel):
    name: str = Field("", description="Nome cadastrado para a chave")
    enabled: bool = Field(True, description="Status da chave")

    def __init__(self, name: str, enabled: bool, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.enabled = enabled


blueprint = APIBlueprint('auth', __name__, url_prefix='/v1/auth')
tag = Tag(name="Auth", description="Rotas de Autenticação")


@blueprint.post('/keys', summary="Cadastra uma nova chave",
                description="Cadastra uma nova chave de autenticação. Requer acesso de administrador.",
                responses={"200": ResponseWithContent, "400": Response},
                tags=[tag])
def create_account(body: CreateAccountBody):
    if body.name == "" or body.key == "":
        return Response(message="Name e key não podem ser vazios", status=400).as_return()

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
        return Response(message="Já existe uma chave com esse nome", status=400).as_return()


@blueprint.delete('/keys/<key_name>', summary="Revoga o acesso de uma chave",
                  description="Revoga o acesso de uma chave de autenticação. Requer acesso de administrador.",
                  responses={"200": Response, "400": Response},
                  tags=[tag])
def revoke_key():
    key_name = request.view_args["key_name"]
    session = Session(db)

    key = session.query(AuthKey) \
        .filter_by(name=key_name) \
        .filter_by(enabled=True) \
        .first()

    if key is None:
        return Response(message="Account does not exist", status=400).as_return()
    else:
        key.enabled = False
        session.commit()

        return Response(status=200).as_return()


@blueprint.get('/keys', summary="Lista todas as chaves",
               description="Lista todas as chaves de autenticação. Requer acesso de administrador.",
               responses={"200": ResponseWithContent, "400": Response},
               tags=[tag])
def list_keys():
    session = Session(db)

    query = select(AuthKey)
    keys = session.execute(query).scalars().all()

    return ResponseWithContent(status=200, content={
        "keys": [KeyViewModel(name=key.name, enabled=key.enabled).dict() for key in keys]}).as_return()


@blueprint.post('', summary="Gera um token de autenticação temporário ",
                description="Gera um token de autenticação temporário para uma chave de autenticação.",
                responses={"200": ResponseWithContent, "400": Response},
                tags=[tag])
def login(body: LoginBody):
    session = Session(db)

    user = session.query(AuthKey) \
        .filter_by(name=body.name) \
        .filter_by(enabled=True) \
        .first()

    if user is None:
        return Response(message="Nome ou chave incorretos", status=401).as_return()
    else:
        if bcrypt.checkpw(body.key.encode('utf-8'), user.key.encode('utf-8')):
            token = generate_token(body.name)

            return ResponseWithContent(content={"token": token}, status=200).as_return()
        else:
            return Response(message="Nome ou chave incorretos", status=401).as_return()


def generate_token(name):
    payload = {
        'exp': (datetime.utcnow() + timedelta(seconds=app_config.auth.expiration)),
        'iat': datetime.utcnow(),
        'sub': name
    }

    return jwt.encode(
        payload,
        app_config.auth.secret,
    )
