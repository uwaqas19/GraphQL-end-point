from __future__ import annotations
from typing import Iterable, Mapping
from graphql import GraphQLError

def require_role(info, allowed: Iterable[str]) -> None:
    role = (info.context.get("role") or "anonymous").lower()
    if role not in {r.lower() for r in allowed}:
        raise GraphQLError("Forbidden", extensions={"code": "FORBIDDEN"})

def role_is(info, *roles: str) -> bool:
    role = (info.context.get("role") or "anonymous").lower()
    return role in {r.lower() for r in roles}

def mask_for_client(payload: Mapping):
    # Hide raw mesh for clients; keep viewer-friendly bits.
    keep = ("id", "name", "glbUrl", "matrix", "location", "hasGlbFile")
    return {k: payload.get(k) for k in keep if k in payload}
