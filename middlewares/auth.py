import os
from datetime import datetime

from flask import request, Flask
import jwt

from config import app_config
from response import Response


class AuthMiddleware:
    white_listed_routes = []

    secret = None
    app = None

    def __init__(self, app: Flask, secret, white_listed_routes=None):
        self.secret = secret
        self.app = app
        self.white_listed_routes = white_listed_routes if white_listed_routes is not None else []
        app.before_request(self.authenticate)

    def authenticate(self):
        self.app.logger.info("Authenticating request %s", request.path)

        if not any(element.lower() in request.path.lower() for element in self.white_listed_routes):
            token = request.headers.get("Authorization")
            if token is None:
                return Response(message=f"not authenticated: no token present", status=401).as_return()
            else:
                if token != app_config.auth.admin_key:
                    try:
                        payload = jwt.decode(token, self.secret, algorithms=["HS256"])

                        if payload["exp"] < datetime.now().timestamp():
                            return Response(message=f"not authenticated: expired", status=401).as_return()
                    except Exception as e:
                        return Response(message=f"not authenticated: {e}", status=500).as_return()
