# app/resolvers/ifc_resolvers.py
from __future__ import annotations

import os
from itertools import combinations
from typing import Any, Dict, List

import ifcopenshell
from graphql import GraphQLError

# ⬇️ Auth helper for role checks
from app.utils.authz import require_role  # pip: see earlier step to add this helper

from app.services.ifc_service import elements_by_type
from app.services.geometry_service import clash_between, export_element_geometry


# -------- spatial hierarchy helpers --------

def _is_spatial(e) -> bool:
    """True if entity is a spatial structure element (Site/Building/Storey/Space)."""
    try:
        return e.is_a("IfcSpatialStructureElement")
    except Exception:
        return False


def _to_spatial_node(e) -> Dict[str, Any]:
    """Map IFC entity -> GraphQL SpatialNode dict, recursively."""
    kids: List[Any] = []
    try:
        for rel in (getattr(e, "IsDecomposedBy", None) or []):
            for obj in (getattr(rel, "RelatedObjects", None) or []):
                if _is_spatial(obj):
                    kids.append(obj)
    except Exception:
        pass

    return {
        "id": getattr(e, "GlobalId", None),
        "name": getattr(e, "Name", None),
        "type": e.is_a() if hasattr(e, "is_a") else None,
        "children": [_to_spatial_node(c) for c in kids],
    }


# ----------------- resolvers -------------------

class IFCQuery:
    # ---------- Discovery: elements by type (public) ----------
    @staticmethod
    def resolve_elements_by_type(_parent, _info, filePath: str, elementType: str):
        """
        elementByType(filePath: String!, elementType: String!): [IFCElement]
        """
        if not os.path.isfile(filePath):
            raise GraphQLError(f"File not found: {filePath}")
        try:
            return elements_by_type(filePath, elementType)
        except Exception as e:
            raise GraphQLError(f"elements_by_type failed for {elementType}: {e}")

    # ---------- Spatial hierarchy (public) ----------
    @staticmethod
    def resolve_ifc_spatial_hierarchy(_parent, _info, filePath: str) -> List[Dict[str, Any]]:
        """
        ifcSpatialHierarchy(filePath: String!): [SpatialNode]
        Builds a Project -> Site -> Building -> Storey tree (recursively).
        """
        if not os.path.isfile(filePath):
            raise GraphQLError(f"File not found: {filePath}")

        try:
            m = ifcopenshell.open(filePath)
            roots: List[Dict[str, Any]] = []

            projects = m.by_type("IfcProject")
            if projects:
                proj = projects[0]
                for rel in (getattr(proj, "IsDecomposedBy", None) or []):
                    for obj in (getattr(rel, "RelatedObjects", None) or []):
                        if _is_spatial(obj):  # typically IfcSite
                            roots.append(_to_spatial_node(obj))

            if not roots:
                for t in ("IfcSite", "IfcBuilding", "IfcBuildingStorey"):
                    for e in m.by_type(t):
                        roots.append(_to_spatial_node(e))

            return roots

        except Exception as e:
            raise GraphQLError(f"ifcSpatialHierarchy failed: {e}")

    # ---------- 3D clash detection (engineer/architect) ----------
    @staticmethod
    def resolve_detect_clashes(_parent, info, filePath: str) -> List[Dict[str, Any]]:
        """
        detectClashes(filePath: String!): [ClashResult]
        Returns rows { element1, element2, intersectionVolume } for pairs with volume > 0.
        """
        # role gate
        require_role(info, {"engineer", "architect"})

        if not os.path.isfile(filePath):
            raise GraphQLError(f"File not found: {filePath}")

        try:
            m = ifcopenshell.open(filePath)

            # Tune search space for performance
            types = ["IfcWall", "IfcSlab", "IfcBeam", "IfcColumn", "IfcFooting", "IfcStair"]

            guids: List[str] = []
            seen: set[str] = set()
            for t in types:
                for e in m.by_type(t):
                    gid = getattr(e, "GlobalId", None)
                    if gid and gid not in seen:
                        guids.append(gid)
                        seen.add(gid)

            results: List[Dict[str, Any]] = []
            for a, b in combinations(guids, 2):
                vol = clash_between(filePath, a, b)  # exact boolean intersection volume (m³)
                if vol > 0:
                    results.append({"element1": a, "element2": b, "intersectionVolume": vol})

            return results

        except Exception as e:
            raise GraphQLError(f"detectClashes failed: {e}")

    # ---------- Optional: single-pair helpers (engineer/architect) ----------
    @staticmethod
    def resolve_pairwise_clash(_parent, info, filePath: str, a: str, b: str) -> Dict[str, Any]:
        """
        pairwiseClash(filePath: String!, a: ID!, b: ID!): ClashResult
        (Bind this if you expose a separate field; otherwise your schema already has clashBetween.)
        """
        require_role(info, {"engineer", "architect"})

        if not os.path.isfile(filePath):
            raise GraphQLError(f"File not found: {filePath}")
        try:
            vol = clash_between(filePath, a, b)
            return {"element1": a, "element2": b, "intersectionVolume": vol}
        except Exception as e:
            raise GraphQLError(f"pairwiseClash failed: {e}")

    @staticmethod
    def resolve_pair_clash_with_geometry(_parent, info, filePath: str, a: str, b: str) -> Dict[str, Any]:
        """
        pairClashWithGeometry(filePath: String!, a: ID!, b: ID!): PairClashPayload
        Returns the clash volume plus minimal GLB info for A and B.
        """
        require_role(info, {"engineer", "architect"})

        if not os.path.isfile(filePath):
            raise GraphQLError(f"File not found: {filePath}")
        try:
            vol = clash_between(filePath, a, b)
            ga = export_element_geometry(filePath, a)
            gb = export_element_geometry(filePath, b)
            ga_small = {"id": ga.get("id"), "name": ga.get("name"), "glbUrl": ga.get("glbUrl")}
            gb_small = {"id": gb.get("id"), "name": gb.get("name"), "glbUrl": gb.get("glbUrl")}
            return {"intersectionVolume": vol, "a": ga_small, "b": gb_small}
        except Exception as e:
            raise GraphQLError(f"pairClashWithGeometry failed: {e}")
