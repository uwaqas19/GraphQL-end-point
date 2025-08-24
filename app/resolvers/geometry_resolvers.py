# app/resolvers/geometry_resolvers.py
from __future__ import annotations
import os
from graphql import GraphQLError

# ⬇️ Auth helpers (make sure you created app/utils/authz.py as shown earlier)
from app.utils.authz import require_role, role_is, mask_for_client

from app.services.geometry_service import (
    compute_element_volume,
    compute_element_surface_area,
    compute_area_from_wkt,
    compute_perimeter_from_wkt,
    check_wkt_intersection,
    export_element_geometry,       # GLB + mesh payload
    # Optional exact exchanges; bind only if exposed in schema:
    export_element_brep,
    export_element_step,
    export_element_iges,
)

class GeometryQuery:
    # --------- 3D Geometry (OpenCASCADE) ---------

    @staticmethod
    def resolve_element_volume(_parent, info, filePath: str, elementId: str) -> float:
        # Engineers & architects only (clients get forbidden)
        require_role(info, {"engineer", "architect"})
        try:
            return compute_element_volume(filePath, elementId)
        except Exception as e:
            raise GraphQLError(f"Volume computation failed: {e}")

    @staticmethod
    def resolve_element_surface_area(_parent, info, filePath: str, elementId: str) -> float:
        # Engineers & architects only
        require_role(info, {"engineer", "architect"})
        try:
            return compute_element_surface_area(filePath, elementId)
        except Exception as e:
            raise GraphQLError(f"Surface area computation failed: {e}")

    @staticmethod
    def resolve_get_element_geometry(_parent, info, filePath: str, elementId: str) -> dict:
        """
        getElementGeometry(filePath: String!, elementId: ID!): ElementGeometry
        Returns mesh data + a .glb URL written to /static/geometry/{GUID}.glb.
        Clients receive a masked payload (no raw vertices/faces/edges).
        """
        try:
            payload = export_element_geometry(filePath, elementId)
            # Clients can view, but only the safe subset (viewer-friendly)
            if role_is(info, "client"):
                return mask_for_client(payload)
            return payload
        except Exception as e:
            raise GraphQLError(f"getElementGeometry failed: {e}")

    # --------- Exact geometry exports (BREP/STEP/IGES) ---------
    # These are sensitive (exact CAD). Restrict to engineers/architects.

    @staticmethod
    def resolve_export_element_brep(_parent, info, filePath: str, elementId: str) -> dict:
        """exportElementBrep(filePath: String!, elementId: ID!): GeometryFile"""
        require_role(info, {"engineer", "architect"})
        try:
            path = export_element_brep(filePath, elementId)
            name = os.path.basename(path)
            return {"filename": name, "url": f"/exports/{name}", "contentType": "model/vnd.occt-brep"}
        except Exception as e:
            raise GraphQLError(f"exportElementBrep failed: {e}")

    @staticmethod
    def resolve_export_element_step(_parent, info, filePath: str, elementId: str) -> dict:
        """exportElementStep(filePath: String!, elementId: ID!): GeometryFile"""
        require_role(info, {"engineer", "architect"})
        try:
            path = export_element_step(filePath, elementId)
            name = os.path.basename(path)
            return {"filename": name, "url": f"/exports/{name}", "contentType": "application/step"}
        except Exception as e:
            raise GraphQLError(f"exportElementStep failed: {e}")

    @staticmethod
    def resolve_export_element_iges(_parent, info, filePath: str, elementId: str) -> dict:
        """exportElementIges(filePath: String!, elementId: ID!): GeometryFile"""
        require_role(info, {"engineer", "architect"})
        try:
            path = export_element_iges(filePath, elementId)
            name = os.path.basename(path)
            return {"filename": name, "url": f"/exports/{name}", "contentType": "model/iges"}
        except Exception as e:
            raise GraphQLError(f"exportElementIges failed: {e}")

    # --------- 2D Geometry (Shapely/WKT) ---------
    # Keep public for all roles (adjust if you want these restricted too).

    @staticmethod
    def resolve_area_from_wkt(_parent, _info, wkt: str) -> float:
        """areaFromWKT(wkt: String!): Float"""
        try:
            return compute_area_from_wkt(wkt)
        except Exception as e:
            raise GraphQLError(f"WKT area computation failed: {e}")

    @staticmethod
    def resolve_perimeter_from_wkt(_parent, _info, wkt: str) -> float:
        """perimeterFromWKT(wkt: String!): Float"""
        try:
            return compute_perimeter_from_wkt(wkt)
        except Exception as e:
            raise GraphQLError(f"WKT perimeter computation failed: {e}")

    @staticmethod
    def resolve_intersection_from_wkt(_parent, _info, wkt1: str, wkt2: str) -> bool:
        """intersectionFromWKT(wkt1: String!, wkt2: String!): Boolean"""
        try:
            return check_wkt_intersection(wkt1, wkt2)
        except Exception as e:
            raise GraphQLError(f"WKT intersection check failed: {e}")
