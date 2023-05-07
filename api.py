from database import set_database_uri_from_env, db
from database.configure import configure_database
from middlewares.auth import AuthMiddleware
from observability import metrics, tracing, logging
import os

from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from flask_sqlalchemy import SQLAlchemy
from flask_openapi3 import OpenAPI, Info
from dotenv import load_dotenv

from routes.email import blueprint as email_blueprint
from routes.auth import blueprint as auth_route, b

is_dev = os.environ['ENV'] == 'development'

info = Info(title="UFABC Email Service", version="0.1.0")
app = OpenAPI(__name__, info=info)

resource = Resource(attributes={
    SERVICE_NAME: "ufabc-email-service"
})

if is_dev:
    load_dotenv()
    app.logger.setLevel("DEBUG")
    app.logger.info("Running in development mode")

app.logger.info("Configuring app")

set_database_uri_from_env(app)
db.init_app(app)
configure_database(app, db)

# add observability middlewares
FlaskInstrumentor().instrument_app(app)
with app.app_context():
    SQLAlchemyInstrumentor().instrument(engine=db.engine, enable_commenter=True)

prometheus_port = int(os.getenv("PROMETHEUS_PORT"))
metrics.configure_metrics(prometheus_port, resource)
metrics.MetricsMiddleware(app)
metrics.DatabaseMetrics()

otel_collector_url = os.getenv("OTEL_COLLECTOR_URL")
app.logger.info(f"Configuring tracing to {otel_collector_url}")
tracing.configure_tracing(otel_collector_url, resource)
logging.configure_logging(app, otel_collector_url, resource)

# add custom middlewares
AuthMiddleware(app, "super-secret")

# register routes
app.register_api(auth_route)
app.register_blueprint(b)
app.register_api(email_blueprint)

app.logger.info("App configured")

if __name__ == '__main__':
    port = int(os.getenv("APP_PORT"))
    app.run(debug=is_dev, port=port, host="0.0.0.0", use_reloader=False)
