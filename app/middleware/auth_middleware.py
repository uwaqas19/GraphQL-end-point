# app/middleware/auth_middleware.py
from __future__ import annotations
import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import jwt

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
JWT_ALG = "HS256"

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        user = {"role": "anonymous"}
        auth = request.headers.get("Authorization", "")
        if auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1].strip()
            try:
                decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
                user = {
                    "sub": decoded.get("sub"),
                    "role": (decoded.get("role") or "anonymous").lower(),
                }
            except Exception:
                # token invalid/expired ⇒ anonymous
                user = {"role": "anonymous"}
        request.state.user = user
        return await call_next(request)
