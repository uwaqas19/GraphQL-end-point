import pytest
from app.services.lifecycle_service import (
    calculate_element_material_usage,
    calculate_element_embodied_carbon
)

# 🧪 Unit tests for LCA logic using a mocked volume
# We'll simulate the geometry_service to isolate the logic

def mock_compute_element_volume(file_path, element_id):
    return 2.5  # 🔸 Pretend the element volume is 2.5 m³

# Inject the mock manually
import app.services.geometry_service
app.services.geometry_service.compute_element_volume = mock_compute_element_volume

def test_material_usage_default_density():
    # 2.5 m³ × 2400 kg/m³ = 6000 kg
    assert calculate_element_material_usage("dummy.ifc", "Wall123") == 6000.0

def test_material_usage_custom_density():
    # 2.5 m³ × 7850 (steel) = 19625 kg
    assert calculate_element_material_usage("dummy.ifc", "BeamX", density=7850) == 19625.0

def test_embodied_carbon_default_factor():
    # 6000 kg × 0.1 = 600 kg CO2
    assert calculate_element_embodied_carbon("dummy.ifc", "Wall123") == 600.0

def test_embodied_carbon_custom_factor():
    # 6000 kg × 0.25 = 1500 kg CO2
    assert calculate_element_embodied_carbon("dummy.ifc", "Wall123", carbon_factor=0.25) == 1500.0
