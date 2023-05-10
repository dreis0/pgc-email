import os
from functools import wraps
from flask import request, current_app

from config import app_config
from response import Response


def require_master_auth(f, *args, **kwargs):
    @wraps(f)
    def wrapper():
        auth = request.headers.get("Authorization")
        if auth is None:
            return Response(message=f"not authenticated: no token present", status=401).as_return()
        if auth != app_config.auth.admin_key:
            return Response(message=f"credentials do not grant permissions to execute this action",
                            status=403).as_return()

        return f(*args, **kwargs)

    return wrapper
