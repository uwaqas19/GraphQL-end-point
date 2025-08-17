from app.services.geometry_service import compute_element_volume

# ----------- LCA: Material Usage & Embodied Carbon -----------

def calculate_element_material_usage(file_path: str, element_id: str, density: float = 2400) -> float:
    """
    Calculates total material mass used for a building element.
    Default density is 2400 kg/m³ (standard for concrete).
    """
    volume = compute_element_volume(file_path, element_id)  # 🔹 Volume in m³
    mass = volume * density  # 🔹 kg = m³ × kg/m³
    return round(mass, 2)


def calculate_element_embodied_carbon(file_path: str, element_id: str, carbon_factor: float = 0.1) -> float:
    """
    Estimates embodied carbon based on material usage.
    Default: 0.1 kg CO₂ per kg material.
    """
    mass = calculate_element_material_usage(file_path, element_id)
    carbon = mass * carbon_factor  # 🔹 kg CO₂ = kg × factor
    return round(carbon, 2)
