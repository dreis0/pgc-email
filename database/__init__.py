import os

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def set_database_uri_from_env(app):
    user = os.getenv("DATABASE_USER")
    password = os.getenv("DATABASE_PASSWORD")
    host = os.getenv("DATABASE_HOST")
    port = int(os.getenv("DATABASE_PORT"))

    database = os.getenv("DATABASE_NAME")

    database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url


db = SQLAlchemy()
