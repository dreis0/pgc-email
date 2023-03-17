from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def set_db_url(app, user: str, password: str, host: str, port: int, database: str):
    database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
