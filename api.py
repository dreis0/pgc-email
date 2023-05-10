from config import app_config
from database import  db
from database.configure import configure_database
from middlewares.auth import AuthMiddleware
from observability import metrics, tracing, logging

from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from flask_openapi3 import OpenAPI, Info
from dotenv import load_dotenv

from routes.email import blueprint as email_blueprint
from routes.auth import blueprint as auth_route


info = Info(title="UFABC Email Service", version="0.1.0")
app = OpenAPI(__name__, info=info)

resource = Resource(attributes={
    SERVICE_NAME: "ufabc-email-service"
})

if app_config.is_dev():
    app.logger.setLevel("DEBUG")
    app.logger.info("Running in development mode")

app.logger.info("Configuring app")

app.config["SQLALCHEMY_DATABASE_URI"] = app_config.database.get_url()
db.init_app(app)
configure_database(app, db)

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

# add custom middlewares
AuthMiddleware(app, app_config.auth.secret)

# register routes
app.register_api(auth_route)
app.register_api(email_blueprint)

app.logger.info("App configured")

if __name__ == '__main__':
    app.run(debug=app_config.is_dev(), port=app_config.port, host="0.0.0.0", use_reloader=False)
