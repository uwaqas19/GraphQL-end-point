# app/resolvers/auth_resolvers.py
from __future__ import annotations
import os, time
from typing import Literal
from graphql import GraphQLError
import jwt  # pip install PyJWT

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
JWT_ALG = "HS256"
VALID_ROLES = {"architect", "engineer", "client"}

class AuthQuery:
    @staticmethod
    def resolve_login(_parent, _info, username: str, role: str) -> str:
        role = role.lower().strip()
        if role not in VALID_ROLES:
            raise GraphQLError(f"Invalid role '{role}'. Allowed: {sorted(VALID_ROLES)}")
        now = int(time.time())
        payload = {
            "sub": username,
            "role": role,
            "iat": now,
            "exp": now + 60 * 60 * 12,  # 12h
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)
