import ifcopenshell
import ifcopenshell.geom
from OCC.Core.BRepGProp import brepgprop
from OCC.Core.GProp import GProp_GProps

from app.services.geometry_service import (
    compute_element_volume,
    compute_element_surface_area,
)

def _settings(world=True, disable_openings=False):
    s = ifcopenshell.geom.settings()
    if world:
        s.set(s.USE_WORLD_COORDS, True)
    if disable_openings:
        s.set(s.DISABLE_OPENING_SUBTRACTIONS, True)
    return s

def elements_by_type(file_path: str, element_type: str):
    try:
        print(f"[DEBUG] Opening IFC file: {file_path}")
        model = ifcopenshell.open(file_path)
        elements = model.by_type(element_type)
        print(f"[DEBUG] Found {len(elements)} elements of type {element_type}")

        base_s = _settings(world=True, disable_openings=False)
        alt_s  = _settings(world=True, disable_openings=True)

        results = []
        for el in elements:
            step_id = el.id()

            volume = None
            surface_area = None

            # primary path: use geometry_service (casts step id)
            try:
                volume = compute_element_volume(file_path, step_id)
            except Exception as ex:
                print(f"[WARN] compute_element_volume failed for {el.GlobalId} (#{step_id}): {ex}")
            try:
                surface_area = compute_element_surface_area(file_path, step_id)
            except Exception as ex:
                print(f"[WARN] compute_element_surface_area failed for {el.GlobalId} (#{step_id}): {ex}")

            # local fallback: try building shape here
            if volume is None or surface_area is None:
                for s in (base_s, alt_s):
                    try:
                        shape = ifcopenshell.geom.create_shape(s, el).geometry
                        if volume is None:
                            gp = GProp_GProps()
                            brepgprop.VolumeProperties(shape, gp)
                            volume = round(gp.Mass(), 4)
                        if surface_area is None:
                            gp = GProp_GProps()
                            brepgprop.SurfaceProperties(shape, gp)
                            surface_area = round(gp.Mass(), 4)
                        if volume is not None and surface_area is not None:
                            break
                    except Exception as ex:
                        which = "ALT" if s is alt_s else "BASE"
                        print(f"[WARN] Local BRep compute failed for {el.GlobalId} (#{step_id}) with settings {which}: {ex}")

            results.append({
                "id": el.GlobalId,
                "name": getattr(el, "Name", None),
                "type": el.is_a(),
                "area": surface_area,   # total surface area (m²)
                "volume": volume,       # volume (m³)
            })

        return results

    except Exception as e:
        print(f"[ERROR] Could not process IFC file: {e}")
        return []
