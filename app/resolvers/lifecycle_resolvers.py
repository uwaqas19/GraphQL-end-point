# app/resolvers/lifecycle_resolvers.py
from __future__ import annotations
from graphql import GraphQLError

# ⬇️ role checks
from app.utils.authz import require_role

from app.services.lifecycle_service import (
    element_material_usage,
    element_embodied_carbon,
)

class LifecycleQuery:
    @staticmethod
    def resolve_element_material_usage(_parent, info, filePath: str, elementId: str) -> float:
        """elementMaterialUsage(filePath: String!, elementId: ID!): Float"""
        # engineers & architects only
        require_role(info, {"engineer", "architect"})
        try:
            return element_material_usage(filePath, elementId)
        except Exception as e:
            raise GraphQLError(f"elementMaterialUsage failed: {e}")

    @staticmethod
    def resolve_element_embodied_carbon(_parent, info, filePath: str, elementId: str) -> float:
        """elementEmbodiedCarbon(filePath: String!, elementId: ID!): Float"""
        # engineers & architects only
        require_role(info, {"engineer", "architect"})
        try:
            return element_embodied_carbon(filePath, elementId)
        except Exception as e:
            raise GraphQLError(f"elementEmbodiedCarbon failed: {e}")
