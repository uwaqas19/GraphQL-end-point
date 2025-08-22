
from __future__ import annotations
from typing import Dict, List, Tuple

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.shape
from shapely.geometry import Polygon
from shapely.ops import unary_union

from app.services.geometry_service import _open_ifc, _get_element  # reuse your helpers

# --- helpers -----------------------------------------------------

def _settings_mesh_world() -> ifcopenshell.geom.settings:
    s = ifcopenshell.geom.settings()
    s.set("use-world-coords", True)
    # OCC OFF -> we get mesh arrays
    # s.set("use-python-opencascade", False)  # default False
    return s

def _mesh_world(element) -> Tuple[List[List[float]], List[List[int]]]:
    """Return (verts, faces) in world coordinates."""
    shape = ifcopenshell.geom.create_shape(_settings_mesh_world(), element)
    geom = shape.geometry
    verts = ifcopenshell.util.shape.get_vertices(geom).tolist()  # [[x,y,z],...]
    faces = ifcopenshell.util.shape.get_faces(geom).tolist()     # [[i,j,k],...]
    return verts, faces

def _z_range(verts: List[List[float]]) -> Tuple[float, float]:
    zs = [v[2] for v in verts] or [0.0]
    return min(zs), max(zs)

def _project_triangle_xy(tri3d: List[List[float]]) -> Polygon:
    # drop Z -> [(x,y),...]; protect against degenerate facets
    ring = [(p[0], p[1]) for p in tri3d]
    if len(set(ring)) < 3:
        # degenerate; create zero-area triangle to keep unary_union robust
        return Polygon()
    return Polygon(ring)

def _footprint_polygon(verts: List[List[float]], faces: List[List[int]], buffer_eps: float = 1e-4) -> Polygon:
    """Union of triangle projections -> a single (possibly multi) polygon footprint."""
    tris = []
    for i, j, k in faces:
        tri = [verts[i], verts[j], verts[k]]
        poly = _project_triangle_xy(tri)
        if not poly.is_empty and poly.is_valid:
            tris.append(poly)
    if not tris:
        return Polygon()
    merged = unary_union(tris)
    # tiny buffer helps stitch sliver gaps from tessellation
    if buffer_eps > 0:
        try:
            merged = merged.buffer(buffer_eps).buffer(-buffer_eps)
        except Exception:
            pass
    # ensure Polygon (Shapely may return MultiPolygon; union is fine to intersect)
    return merged

# --- main API ----------------------------------------------------

def detect_plan_clashes(
    file_path: str,
    a_ifc_type: str,
    b_ifc_type: str,
    z_tolerance: float = 0.20,
    return_wkt: bool = False,
) -> List[Dict]:
    """
    Build XY footprints for all A and B type elements, cull by Z-overlap (+/- tol),
    then compute 2D intersection area in plan. Returns list of clashes with area>0.
    """
    model = _open_ifc(file_path)

    # collect all elements by type
    a_elems = list(model.by_type(a_ifc_type) or [])
    b_elems = list(model.by_type(b_ifc_type) or [])

    # precompute footprints + z ranges
    a_data: Dict[str, Dict] = {}
    b_data: Dict[str, Dict] = {}

    def _prep(elem):
        gid = getattr(elem, "GlobalId", None)
        if not gid:
            return None
        V, F = _mesh_world(elem)
        if not V or not F:
            return None
        zmin, zmax = _z_range(V)
        fp = _footprint_polygon(V, F)
        return {"id": gid, "zmin": zmin, "zmax": zmax, "fp": fp}

    for e in a_elems:
        d = _prep(e)
        if d and not d["fp"].is_empty:
            a_data[d["id"]] = d

    for e in b_elems:
        d = _prep(e)
        if d and not d["fp"].is_empty:
            b_data[d["id"]] = d

    clashes: List[Dict] = []
    if not a_data or not b_data:
        return clashes

    # pairwise scan with fast Z cull
    for aid, A in a_data.items():
        for bid, B in b_data.items():
            # z-overlap test (with tolerance)
            if (A["zmax"] + z_tolerance) < B["zmin"] or (B["zmax"] + z_tolerance) < A["zmin"]:
                continue

            inter = A["fp"].intersection(B["fp"])
            if not inter.is_empty:
                area = float(inter.area)
                if area > 0.0:
                    item = {"aId": aid, "bId": bid, "area": round(area, 6)}
                    if return_wkt:
                        try:
                            item["wkt"] = inter.wkt
                        except Exception:
                            item["wkt"] = None
                    clashes.append(item)

    return clashes
