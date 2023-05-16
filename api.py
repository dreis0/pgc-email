from flask import Flask

from config import app_config
from database import db
from database.configure import configure_database
from middlewares.admin_auth import AdminAuthMiddleware
from middlewares.auth import AuthMiddleware
from observability import metrics, tracing, logging

from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from flask_openapi3 import OpenAPI, Info

from routes.email import blueprint as email_routes
from routes.auth import blueprint as auth_routes
from routes.healthcheck import blueprint as healthcheck_route


def create_app():
    info = Info(title="UFABC Email Service", version="0.1.0")
    return OpenAPI(__name__, info=info)


def configure_env(app):
    if app_config.is_dev():
        app.logger.setLevel("DEBUG")
        app.logger.info("Running in development mode")


def configure_db(app):
    app.config["SQLALCHEMY_DATABASE_URI"] = app_config.database.get_url()
    db.init_app(app)
    configure_database(app, db)


def configure_auth(app):
    AuthMiddleware(app, app_config.auth.secret, white_listed_routes=[
        "/auth",
        "/openapi",
        "favicon.ico",
        "/healthcheck",
    ])

    AdminAuthMiddleware(app, app_config.auth.admin_key, protected_routes=["/auth/keys"])


def configure_middlewares(app):
    resource = Resource(attributes={
        SERVICE_NAME: "ufabc-email-service"
    })
    # add observability middlewares
    FlaskInstrumentor().instrument_app(app)
    with app.app_context():
        SQLAlchemyInstrumentor().instrument(engine=db.engine, enable_commenter=True)

    metrics.configure_metrics(app_config.observability.prometheus_port, resource)
    metrics.MetricsMiddleware(app)
    metrics.DatabaseMetrics()

    app.logger.info(f"Configuring tracing to {app_config.observability.collector_url}")
    tracing.configure_tracing(app_config.observability.collector_url, resource)
    logging.configure_logging(app, app_config.observability.collector_url, resource)


def configure_routes(app):
    # register routes
    app.register_api(auth_routes)
    app.register_api(email_routes)
    app.register_api(healthcheck_route)


def run():
    app = create_app()

    configure_env(app)
    configure_db(app)
    configure_auth(app)
    configure_middlewares(app)
    configure_routes(app)

    app.run(debug=app_config.is_dev(), port=app_config.port, host="0.0.0.0", use_reloader=False)


if __name__ == '__main__':
    run()
