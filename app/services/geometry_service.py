from __future__ import annotations
import multiprocessing
import os
from typing import Any, Dict, List, Union, cast, Optional

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.shape
from shapely import wkt as shapely_wkt
from shapely.geometry import MultiPoint  # for 2D footprint hulls

# Enable extra logs with: GEOM_DEBUG=1
GEOM_DEBUG = os.getenv("GEOM_DEBUG", "0") in {"1", "true", "True"}

# ---- OpenCASCADE (pythonocc-core) ----
try:

    from OCC.Core.BRepTools import breptools_Write as _brep_write  # type: ignore[attr-defined]
except Exception:
    _brep_write = None  # type: ignore[assignment]

from OCC.Core.BRepGProp import brepgprop
from OCC.Core.GProp import GProp_GProps
from OCC.Core.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCC.Core.IGESControl import IGESControl_Writer
from OCC.Core.TopoDS import TopoDS_Shape

# Optional bbox acceleration for clash culling (guarded for stub/wheel differences)
from OCC.Core.Bnd import Bnd_Box
try:
    from OCC.Core.BRepBndLib import brepbndlib_Add as _bbox_add  # type: ignore[attr-defined]
except Exception:
    _bbox_add = None  # type: ignore[assignment]

# Boolean common (for pairwise clash volume)
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Common

# ====================== small constants & utilities ======================

_EPS = 1e-12         # clamp tiny numeric noise to 0.0
_DP = 4              # default rounding for areas/volumes
_CLASH_DP = 6        # finer rounding for tiny intersection volumes

def _round(x: float, dp: int = _DP) -> float:
    """Round with tiny-noise clamp."""
    x = float(x)
    if abs(x) < _EPS:
        return 0.0
    return round(x, dp)

def _norm(path: str) -> str:
    """Normalize file paths so we always open the same IFC file."""
    return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))

def _open_ifc(path: str) -> ifcopenshell.file:
    p = _norm(path)
    if GEOM_DEBUG:
        print(f"[geom] open IFC: {p}")
    return ifcopenshell.open(p)

# ====================== IfcOpenShell shape creation helpers ======================

def _make_settings(*, world: bool = True, disable_openings: bool = False, use_occ: bool = False) -> ifcopenshell.geom.settings:
    s = ifcopenshell.geom.settings()
    if world:
        s.set("use-world-coords", True)
    if disable_openings:
        s.set("disable-opening-subtractions", True)
    if use_occ:
        s.set("use-python-opencascade", True)  # exact BRep
    return s

def _get_element(model: ifcopenshell.file, element_ref: Union[int, str]):

    if isinstance(element_ref, int):
        return model.by_id(int(element_ref))

    ref = str(element_ref).strip()
    if ref.startswith("#") and ref[1:].isdigit():
        return model.by_id(int(ref[1:]))
    if ref.isdigit():
        return model.by_id(int(ref))

    try:
        return model.by_guid(ref)
    except Exception:
        pass
    try:
        for ent in model:
            if getattr(ent, "GlobalId", None) == ref:
                return ent
    except Exception:
        pass
    return None

def _create_shape_with_fallback(element, *, use_occ: bool, world: bool = True):
    """Try normal settings, then retry with opening subtractions disabled."""
    try:
        return ifcopenshell.geom.create_shape(_make_settings(world=world, use_occ=use_occ), element)
    except Exception as ex:
        if GEOM_DEBUG:
            print(f"[geom] primary create_shape failed: {ex}; retrying w/out openings")
        return ifcopenshell.geom.create_shape(
            _make_settings(world=world, use_occ=use_occ, disable_openings=True), element
        )

# ====================== 3D properties (exact BRep) ======================

def _topods_for_element(file_path: str, element_ref: Union[int, str]) -> TopoDS_Shape:
    model = _open_ifc(file_path)
    el = _get_element(model, element_ref)
    if not el:
        raise ValueError(f"Element '{element_ref}' not found")
    shape = _create_shape_with_fallback(el, use_occ=True, world=True)
    return cast(TopoDS_Shape, shape.geometry)

def compute_element_volume(file_path: str, element_id: Union[str, int]) -> float:
    """Exact volume in m³ (OpenCASCADE)."""
    topods = _topods_for_element(file_path, element_id)
    props = GProp_GProps()
    brepgprop.VolumeProperties(topods, props)
    return _round(props.Mass(), _DP)

def compute_element_surface_area(file_path: str, element_id: Union[str, int]) -> float:
    """Exact surface area in m² (OpenCASCADE)."""
    topods = _topods_for_element(file_path, element_id)
    props = GProp_GProps()
    brepgprop.SurfaceProperties(topods, props)
    return _round(props.Mass(), _DP)

# ====================== 2D geometry (WKT/Shapely) ======================

def compute_area_from_wkt(wkt_string: str) -> float:
    geom = shapely_wkt.loads(wkt_string)
    return _round(geom.area, _DP)

def compute_perimeter_from_wkt(wkt_string: str) -> float:
    geom = shapely_wkt.loads(wkt_string)
    return _round(geom.length, _DP)

def check_wkt_intersection(wkt1: str, wkt2: str) -> bool:
    geom1 = shapely_wkt.loads(wkt1)
    geom2 = shapely_wkt.loads(wkt2)
    return geom1.intersects(geom2)

# ====================== Mesh + glTF for a single element ======================

def _mesh_for_element(model: ifcopenshell.file, element) -> Dict[str, Any]:
    """
    Tessellated mesh in world coords (verts/faces/edges + transform).
    OCC must be OFF here to receive mesh arrays.
    """
    shape = _create_shape_with_fallback(element, use_occ=False, world=True)
    geom = shape.geometry

    verts = ifcopenshell.util.shape.get_vertices(geom).tolist()
    faces = ifcopenshell.util.shape.get_faces(geom).tolist()
    edges = ifcopenshell.util.shape.get_edges(geom).tolist()
    matrix = ifcopenshell.util.shape.get_shape_matrix(shape).tolist()

    style_names: List[str] = []
    for s in getattr(geom, "materials", []):
        try:
            style_names.append(s.name or s.original_name())
        except Exception:
            style_names.append("Unnamed-Style")

    return {
        "matrix": matrix,
        "location": [matrix[0][3], matrix[1][3], matrix[2][3]],
        "vertices": verts,
        "faces": faces,
        "edges": edges,
        "styles": style_names,
        "materialIds": list(getattr(geom, "material_ids", [])),
        "itemIds": list(getattr(geom, "item_ids", [])),
    }

def _write_element_gltf(model: ifcopenshell.file, element, out_path: str) -> str:
    """
    glTF export via serializer + iterator, limited to a single element.
    Raises if the serializer isn't available.
    """
    if not hasattr(ifcopenshell.geom, "serializers") or not hasattr(
        ifcopenshell.geom.serializers, "gltf"
    ):
        raise RuntimeError("IfcOpenShell glTF serializer is not available in this build")

    settings = _make_settings(world=True, use_occ=False)
    settings.set("dimensionality", ifcopenshell.ifcopenshell_wrapper.CURVES_SURFACES_AND_SOLIDS)
    settings.set("apply-default-materials", True)

    ser_settings = ifcopenshell.geom.serializer_settings()
    ser_settings.set("use-element-guids", True)

    serialiser = ifcopenshell.geom.serializers.gltf(  # type: ignore[call-arg]
        out_path, settings, ser_settings
    )
    serialiser.setFile(model)
    serialiser.setUnitNameAndMagnitude("METER", 1.0)
    serialiser.writeHeader()

    it = ifcopenshell.geom.iterator(  # type: ignore[call-arg]
        settings, model, multiprocessing.cpu_count(), include=[element]
    )
    if it.initialize():
        while True:
            serialiser.write(it.get())
            if not it.next():
                break
    serialiser.finalize()
    return out_path

def export_element_geometry(file_path: str, element_id: Union[str, int]) -> Dict[str, Any]:
    """
    Return mesh (verts/faces/edges + transform) and always include a glbUrl.
    Writes a real .glb when possible; otherwise creates a small placeholder.
    """
    model = _open_ifc(file_path)
    el = _get_element(model, element_id)
    if not el:
        raise ValueError("Element not found.")

    payload = _mesh_for_element(model, el)

    static_dir = os.path.join("app", "static", "geometry")
    os.makedirs(static_dir, exist_ok=True)
    glb_filename = f"{el.GlobalId}.glb"
    glb_path = os.path.join(static_dir, glb_filename)
    glb_url = f"/static/geometry/{glb_filename}"

    wrote_file = False
    try:
        _write_element_gltf(model, el, glb_path)
        wrote_file = True
        if GEOM_DEBUG:
            print(f"[geom] wrote glTF: {glb_path}")
    except Exception as ex:
        if GEOM_DEBUG:
            print(f"[geom] glTF serializer failed: {ex}; writing placeholder {glb_path}")
        try:
            if not os.path.exists(glb_path):
                with open(glb_path, "wb") as f:
                    f.write(b"glTF placeholder")
            wrote_file = True
        except Exception as inner:
            if GEOM_DEBUG:
                print(f"[geom] could not create GLB placeholder: {inner}")

    payload.update({
        "id": el.GlobalId,
        "name": getattr(el, "Name", None),
        "glbUrl": glb_url,
        "hasGlbFile": wrote_file,
    })
    return payload

# ====================== Clash helpers (pairwise + 2D) ======================

def _bbox_disjoint(s1: TopoDS_Shape, s2: TopoDS_Shape) -> bool:
    """Fast AABB cull. If bbox helper isn't available, skip culling."""
    if _bbox_add is None:
        return False
    b1 = Bnd_Box(); _bbox_add(s1, b1)  # type: ignore[misc]
    b2 = Bnd_Box(); _bbox_add(s2, b2)  # type: ignore[misc]
    return b1.IsOut(b2)

def clash_between(file_path: str, a: Union[str, int], b: Union[str, int]) -> float:
    """
    Compute intersection volume (m³) between two elements.
    Returns 0.0 if no intersection, >0.0 if they clash.
    """
    sa = _topods_for_element(file_path, a)
    sb = _topods_for_element(file_path, b)

    # quick cull
    if _bbox_disjoint(sa, sb):
        return 0.0

    common = BRepAlgoAPI_Common(sa, sb).Shape()
    props = GProp_GProps()
    brepgprop.VolumeProperties(common, props)
    vol = max(0.0, props.Mass())
    return _round(vol, _CLASH_DP)

def intersection_volume_between(file_path: str, element_a: Union[str, int], element_b: Union[str, int]) -> float:
    """Alias so other modules can import a stable name."""
    return clash_between(file_path, element_a, element_b)

def _footprint_polygon_for_element(
    file_path: str,
    element_ref: Union[str, int],
    z_min: Optional[float] = None,
    z_max: Optional[float] = None,
):
    """
    Build a coarse XY footprint polygon (convex hull of XY verts) for an element.
    Optionally restrict to vertices within [z_min, z_max].
    Returns a Shapely geometry (Polygon/LineString/Point) or None.
    """
    model = _open_ifc(file_path)
    el = _get_element(model, element_ref)
    if not el:
        return None

    shape = _create_shape_with_fallback(el, use_occ=False, world=True)
    geom = shape.geometry
    verts = ifcopenshell.util.shape.get_vertices(geom).tolist()  # [[x,y,z], ...]

    pts_xy: List[tuple] = []
    for x, y, z in verts:
        if z_min is not None and z < z_min:
            continue
        if z_max is not None and z > z_max:
            continue
        pts_xy.append((float(x), float(y)))

    if len(pts_xy) < 3:
        return None  # not enough for an area

    return MultiPoint(pts_xy).convex_hull  # may be Polygon/LineString/Point

def overlaps_2d_on_storey(
    file_path: str,
    element_a: Union[str, int],
    element_b: Union[str, int],
    *,
    z_min: Optional[float] = None,
    z_max: Optional[float] = None,
    area_tol: float = 1e-6,
) -> bool:

    pa = _footprint_polygon_for_element(file_path, element_a, z_min=z_min, z_max=z_max)
    pb = _footprint_polygon_for_element(file_path, element_b, z_min=z_min, z_max=z_max)
    if pa is None or pb is None:
        return False

    inter = pa.intersection(pb)
    area = float(getattr(inter, "area", 0.0))
    return area > area_tol

# ====================== Exact BRep exchanges ======================

def _write_brep_file(shape: TopoDS_Shape, out_path: str) -> None:
    if not callable(_brep_write):  # type: ignore[arg-type]
        raise ImportError(
            "Your OCC build/stubs do not expose 'breptools_Write'. "
            "Consider updating pythonocc-core or use STEP/IGES export."
        )
    _brep_write(shape, out_path)  # type: ignore[misc]

def _ensure_occ_shape(file_path: str, element_id: Union[str, int]) -> TopoDS_Shape:
    return _topods_for_element(file_path, element_id)

def export_element_brep(file_path: str, element_id: Union[str, int], out_dir: str = "exports") -> str:
    os.makedirs(out_dir, exist_ok=True)
    model = _open_ifc(file_path)
    el = _get_element(model, element_id)
    if not el:
        raise ValueError("Element not found.")
    shape = _ensure_occ_shape(file_path, element_id)
    out = os.path.join(out_dir, f"{el.GlobalId}.brep")
    _write_brep_file(shape, out)
    return out

def export_element_step(file_path: str, element_id: Union[str, int], out_dir: str = "exports") -> str:
    os.makedirs(out_dir, exist_ok=True)
    model = _open_ifc(file_path)
    el = _get_element(model, element_id)
    if not el:
        raise ValueError("Element not found.")
    shape = _ensure_occ_shape(file_path, element_id)
    out = os.path.join(out_dir, f"{el.GlobalId}.stp")
    writer = STEPControl_Writer()
    writer.Transfer(shape, STEPControl_AsIs)
    writer.Write(out)
    return out

def export_element_iges(file_path: str, element_id: Union[str, int], out_dir: str = "exports") -> str:
    os.makedirs(out_dir, exist_ok=True)
    model = _open_ifc(file_path)
    el = _get_element(model, element_id)
    if not el:
        raise ValueError("Element not found.")
    shape = _ensure_occ_shape(file_path, element_id)
    out = os.path.join(out_dir, f"{el.GlobalId}.igs")
    writer = IGESControl_Writer()
    writer.AddShape(shape)
    writer.Write(out)
    return out
