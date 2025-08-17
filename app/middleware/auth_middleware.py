from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import HTTPException
import jwt

SECRET_KEY = "your-secret-key"  # 🔐 Replace this with a strong, private key in production


class AuthMiddleware(BaseHTTPMiddleware):
    """
    JWT Authentication Middleware:
    - Extracts JWT from 'Authorization' header.
    - Decodes token and attaches user info to request scope.
    - Supports role-based access via `request.scope["user"]`.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        token = request.headers.get("Authorization")
        user = {}

        if token and token.startswith("Bearer "):
            try:
                payload = jwt.decode(token[7:], SECRET_KEY, algorithms=["HS256"])
                user = payload  # e.g., { "sub": "username", "role": "engineer" }
            except jwt.ExpiredSignatureError:
                raise HTTPException(status_code=401, detail="Token expired")
            except jwt.InvalidTokenError:
                raise HTTPException(status_code=401, detail="Invalid token")

        request.scope["user"] = user
        response = await call_next(request)
        return response
