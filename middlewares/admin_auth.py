import os
from functools import wraps

import jwt
from flask import request, current_app, Flask

from config import app_config
from response import Response


class AdminAuthMiddleware:
    protected_routes = []

    secret = None
    app = None

    def __init__(self, app: Flask, secret, protected_routes=None):
        self.secret = secret
        self.app = app
        self.protected_routes = protected_routes if protected_routes is not None else []
        app.before_request(self.authenticate)

    def authenticate(self):
        self.app.logger.info("Authenticating request %s", request.path)

        if any(element.lower() in request.path.lower() for element in self.protected_routes):
            token = request.headers.get("Authorization")
            if token is None:
                return Response(message=f"not authenticated: no token present", status=401).as_return()
            elif token != app_config.auth.admin_key:
                return Response(message=f"credentials do not grant permissions to execute this action",
                                status=403).as_return()
