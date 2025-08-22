
from __future__ import annotations
from graphql import GraphQLError
from app.services.lifecycle_service import (
    element_material_usage,
    element_embodied_carbon,
)

class LifecycleQuery:

    @staticmethod
    def resolve_element_material_usage(_, info, filePath: str, elementId: str) -> float:

        try:
            return element_material_usage(filePath, elementId)
        except Exception as e:
            # Field-level GraphQL error (shows up in `errors` array)
            raise GraphQLError(f"elementMaterialUsage failed: {e}")

    @staticmethod
    def resolve_element_embodied_carbon(_, info, filePath: str, elementId: str) -> float:

        try:
            return element_embodied_carbon(filePath, elementId)
        except Exception as e:
            raise GraphQLError(f"elementEmbodiedCarbon failed: {e}")
