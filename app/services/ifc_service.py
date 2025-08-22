
from __future__ import annotations
from typing import Dict, List
import ifcopenshell
import ifcopenshell.geom
from OCC.Core.BRepGProp import brepgprop
from OCC.Core.GProp import GProp_GProps


def _settings_occ(world: bool = True, disable_openings: bool = False) -> ifcopenshell.geom.settings:
    s = ifcopenshell.geom.settings()
    if world:
        s.set("use-world-coords", True)
    if disable_openings:
        s.set("disable-opening-subtractions", True)
    s.set("use-python-opencascade", True)  # request TopoDS_Shape
    return s


def _shape_with_fallback(el):
    """Return TopoDS_Shape for an element, retrying without openings if needed."""
    try:
        return ifcopenshell.geom.create_shape(_settings_occ(world=True), el).geometry
    except Exception:
        return ifcopenshell.geom.create_shape(_settings_occ(world=True, disable_openings=True), el).geometry


def _metrics_from_shape(topods) -> Dict[str, float | None]:
    """Exact volume (m³) and area (m²) from OCC."""
    vol = area = None
    try:
        gp = GProp_GProps()
        brepgprop.VolumeProperties(topods, gp)
        vol = round(gp.Mass(), 4)
    except Exception:
        vol = None
    try:
        gp = GProp_GProps()
        brepgprop.SurfaceProperties(topods, gp)
        area = round(gp.Mass(), 4)
    except Exception:
        area = None
    return {"volume": vol, "area": area}


def elements_by_type(file_path: str, element_type: str) -> List[Dict]:
    """
    Robust across IfcOpenShell builds: iterate IFC elements directly (no iterator),
    compute exact OCC metrics per element, and return [{id,name,type,area,volume}].
    """
    model = ifcopenshell.open(file_path)
    elements = model.by_type(element_type)

    results: List[Dict] = []
    for el in elements:
        try:
            topods = _shape_with_fallback(el)
            m = _metrics_from_shape(topods)
        except Exception:
            m = {"volume": None, "area": None}

        results.append(
            {
                "id": el.GlobalId,
                "name": getattr(el, "Name", None),
                "type": el.is_a(),
                "area": m["area"],
                "volume": m["volume"],
            }
        )
    return results
