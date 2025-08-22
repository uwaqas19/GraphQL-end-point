
from __future__ import annotations
from typing import Union, Optional

from app.services.geometry_service import (
    compute_element_volume,
    _open_ifc,        # used to peek IFC type
    _get_element,     # used to peek IFC type
)

# --- very simple illustrative lookup tables ---
# Units:
# - density: kg/m³
# - carbon factor: kgCO2e per kg of material
DENSITY_BY_IFC = {
    "IfcSlab": 2300.0,    # concrete-ish
    "IfcWall": 2000.0,
    "IfcBeam": 7850.0,    # steel
    "IfcColumn": 7850.0,  # steel
    "default": 2400.0,    # keep your previous default
}

EC_FACTOR_BY_IFC = {
    "IfcSlab": 0.12,
    "IfcWall": 0.12,
    "IfcBeam": 1.90,
    "IfcColumn": 1.90,
    "default": 0.10,      # close to your previous 0.1
}

def _ifc_type(file_path: str, element_id: Union[str, int]) -> str:
    """Best-effort IFC type for the element (falls back to 'default')."""
    try:
        model = _open_ifc(file_path)
        el = _get_element(model, element_id)
        return el.is_a() if el else "default"
    except Exception:
        return "default"

# ----------- LCA: Material Usage & Embodied Carbon -----------

def calculate_element_material_usage(
    file_path: str,
    element_id: Union[str, int],
    density: Optional[float] = None,
) -> float:
    """
    Calculates total material mass used for a building element (kg).
    - volume is computed from OCC B-Rep (m³)
    - mass = volume * density  (kg)
    If density is not provided, a per-IFC-type default is used.
    """
    vol_m3 = float(compute_element_volume(file_path, element_id))  # m³
    etype = _ifc_type(file_path, element_id)
    rho = float(density) if density is not None else float(DENSITY_BY_IFC.get(etype, DENSITY_BY_IFC["default"]))
    mass_kg = max(0.0, vol_m3 * rho)
    return round(mass_kg, 3)

def calculate_element_embodied_carbon(
    file_path: str,
    element_id: Union[str, int],
    carbon_factor: Optional[float] = None,
    density: Optional[float] = None,
) -> float:
    """
    Estimates embodied carbon (kgCO2e) based on material usage.
    - mass computed with `calculate_element_material_usage`
    - kgCO2e = mass (kg) * emission factor (kgCO2e/kg)
    If carbon_factor is not provided, a per-IFC-type default is used.
    """
    etype = _ifc_type(file_path, element_id)
    factor = float(carbon_factor) if carbon_factor is not None else float(EC_FACTOR_BY_IFC.get(etype, EC_FACTOR_BY_IFC["default"]))
    mass_kg = calculate_element_material_usage(file_path, element_id, density=density)
    kgco2e = max(0.0, mass_kg * factor)
    return round(kgco2e, 3)

# --- aliases used by resolvers (keeps names consistent) ---

def element_material_usage(file_path: str, element_id: Union[str, int]) -> float:
    return calculate_element_material_usage(file_path, element_id)

def element_embodied_carbon(file_path: str, element_id: Union[str, int]) -> float:
    return calculate_element_embodied_carbon(file_path, element_id)
