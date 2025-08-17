import os
import ifcopenshell
import ifcopenshell.geom
from shapely import wkt as shapely_wkt
from OCC.Core.BRepGProp import brepgprop  # ✅ static methods
from OCC.Core.GProp import GProp_GProps


# ------------------ helpers ------------------

def _make_settings(world: bool = True, disable_openings: bool = False):
    """Build ifcopenshell geom settings compatible with your build."""
    s = ifcopenshell.geom.settings()
    if world:
        s.set(s.USE_WORLD_COORDS, True)
    # NOTE: do NOT set USE_BREP_DATA (not present in your build)
    if disable_openings:
        s.set(s.DISABLE_OPENING_SUBTRACTIONS, True)
    return s


def _shape_with_fallback(element):
    """
    Try base settings; on failure, retry with openings disabled.
    Returns a TopoDS_Shape (or raises the last exception).
    """
    s1 = _make_settings(world=True, disable_openings=False)
    try:
        return ifcopenshell.geom.create_shape(s1, element).geometry
    except Exception:
        s2 = _make_settings(world=True, disable_openings=True)
        return ifcopenshell.geom.create_shape(s2, element).geometry


def _open_model(path: str):
    """Open IFC with better error messages and normalized path."""
    norm = os.path.normpath(path)
    if not os.path.isabs(norm):
        # resolve relative to project root working dir
        norm = os.path.normpath(os.path.join(os.getcwd(), path))
    if not os.path.exists(norm):
        raise FileNotFoundError(f"IFC file not found: {norm}")
    return ifcopenshell.open(norm)


# ----------- 3D Geometry Operations (OpenCascade) -----------

def compute_element_volume(file_path: str, element_id: str) -> float:
    """
    Computes the volume of a 3D BIM element (m³).
    IMPORTANT: element_id must be the STEP id (integer).
    """
    model = _open_model(file_path)
    el = model.by_id(int(element_id))
    if not el:
        raise ValueError(f"Element with STEP id {element_id} not found")
    shape = _shape_with_fallback(el)

    props = GProp_GProps()
    brepgprop.VolumeProperties(shape, props)  # ✅ static call
    return round(props.Mass(), 4)


def compute_element_surface_area(file_path: str, element_id: str) -> float:
    """
    Computes the surface area of a 3D BIM element (m²).
    IMPORTANT: element_id must be the STEP id (integer).
    """
    model = _open_model(file_path)
    el = model.by_id(int(element_id))
    if not el:
        raise ValueError(f"Element with STEP id {element_id} not found")
    shape = _shape_with_fallback(el)

    props = GProp_GProps()
    brepgprop.SurfaceProperties(shape, props)  # ✅ static call
    return round(props.Mass(), 4)


# ----------- 2D Geometry Operations (Shapely / WKT) -----------

def compute_area_from_wkt(wkt_string: str) -> float:
    geom = shapely_wkt.loads(wkt_string)
    return round(geom.area, 4)


def compute_perimeter_from_wkt(wkt_string: str) -> float:
    geom = shapely_wkt.loads(wkt_string)
    return round(geom.length, 4)


def check_wkt_intersection(wkt1: str, wkt2: str) -> bool:
    geom1 = shapely_wkt.loads(wkt1)
    geom2 = shapely_wkt.loads(wkt2)
    return geom1.intersects(geom2)


# ----------- Geometry Exchange: GLB or Mesh Extraction -----------

def export_element_geometry(file_path: str, element_id: str) -> dict:
    """
    Returns minimal exchange geometry for a single element:
      - vertices, faces (if extraction succeeds)
      - a placeholder .glb URL (replace with real export later)
    NOTE: element_id must be the STEP id (integer).
    """
    model = _open_model(file_path)
    el = model.by_id(int(element_id))
    if not el:
        raise ValueError("Element not found.")

    vertices = None
    faces = None

    try:
        shape = _shape_with_fallback(el)
        raw_vertices = list(shape.verts)  # flat [x,y,z,...]
        raw_faces = list(shape.faces)     # flat triplets [i,j,k,...]
        vertices = [raw_vertices[i:i+3] for i in range(0, len(raw_vertices), 3)]
        faces    = [raw_faces[i:i+3]    for i in range(0, len(raw_faces),    3)]
    except Exception as ex:
        print(f"[WARN] Mesh extraction failed for {el.GlobalId} (#{el.id()}): {ex}")

    static_dir = os.path.join("app", "static", "geometry")
    os.makedirs(static_dir, exist_ok=True)
    glb_filename = f"{el.GlobalId}.glb"
    glb_path = os.path.join(static_dir, glb_filename)

    # placeholder file so the URL exists
    if not os.path.exists(glb_path):
        with open(glb_path, "wb") as f:
            f.write(b"Dummy GLB content")

    return {
        "id": el.GlobalId,
        "name": getattr(el, "Name", None),
        "glbUrl": f"/static/geometry/{glb_filename}",
        "vertices": vertices,  # may be None if OCC mesh failed
        "faces": faces,        # may be None if OCC mesh failed
    }
