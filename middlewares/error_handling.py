from http.client import HTTPException

from flask import Flask, current_app

from observability.tracing import tracer
from response import Response


def handle_error(error):
    with tracer.start_as_current_span("handle_error") as span:
        span.set_attribute("error", True)
        span.set_attribute("error.message", str(error))
        current_app.logger.error(f"Error: {error}")

        return Response(message=str(error.original_exception), status=500).as_return()
