import os

from dotenv import load_dotenv


class AuthConfig:
    expiration: int = 3600
    secret: str = "wn9AmoDNnqGSHi38poXA"
    admin_key: str = "wn9AmoDNnqGSHi38poXA"


class EmailConfig:
    host: str = "smtp.gmail.com"
    port: int = 587
    sender: str = "migueldreis01@gmail.com"
    password: str = ""


class DatabaseConfig:
    name = "dev"
    host = "postgres"
    port = 5432
    user = "postgres"
    password = "postgres"

    def get_url(self):
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class ObservabilityConfig:
    collector_url: str = "otel_collector:4317"
    prometheus_port: int = 8000


class ApiConfig:
    port: int = 5001
    env: str = "development"
    auth: AuthConfig = AuthConfig()
    email: EmailConfig = EmailConfig()
    database: DatabaseConfig = DatabaseConfig()
    observability: ObservabilityConfig = ObservabilityConfig()

    def is_dev(self):
        return self.env == "development"


def config_from_env() -> ApiConfig:
    c = ApiConfig()

    port = os.getenv("PORT")
    c.port = int(port) if port is not None else c.port

    env = os.getenv("ENV")
    c.env = env if env is not None else c.env

    if c.is_dev():
        load_dotenv()

    auth_secret = os.getenv("AUTH_SECRET")
    c.auth.secret = auth_secret if auth_secret is not None else c.auth.secret
    auth_expiration = os.getenv("AUTH_EXPIRATION")
    c.auth.expiration = int(auth_expiration) if auth_expiration is not None else c.auth.expiration
    auth_admin_key = os.getenv("AUTH_ADMIN_KEY")
    c.auth.admin_key = auth_admin_key if auth_admin_key is not None else c.auth.admin_key

    smtp_sender = os.getenv("SMTP_SENDER")
    c.email.sender = smtp_sender if smtp_sender is not None else c.email.sender
    smtp_host = os.getenv("SMTP_HOST")
    c.email.host = smtp_host if smtp_host is not None else c.email.host
    smtp_port = os.getenv("SMTP_PORT")
    c.email.port = int(smtp_port) if smtp_port is not None else c.email.port
    smtp_password = os.getenv("SMTP_PASSWORD")
    c.email.password = smtp_password if smtp_password is not None else c.email.password

    db_name = os.getenv("DATABASE_NAME")
    c.database.name = db_name if db_name is not None else c.database.name
    db_host = os.getenv("DATABASE_HOST")
    c.database.host = db_host if db_host is not None else c.database.host
    db_port = os.getenv("DATABASE_PORT")
    c.database.port = int(db_port) if db_port is not None else c.database.port
    db_user = os.getenv("DATABASE_USER")
    c.database.user = db_user if db_user is not None else c.database.user
    db_password = os.getenv("DATABASE_PASSWORD")
    c.database.password = db_password if db_password is not None else c.database.password

    collector_url = os.getenv("COLLECTOR_URL")
    c.observability.collector_url = collector_url if collector_url is not None else c.observability.collector_url
    prometheus_port = os.getenv("PROMETHEUS_PORT")
    c.observability.prometheus_port = int(
        prometheus_port) if prometheus_port is not None else c.observability.prometheus_port

    return c


app_config = config_from_env()
