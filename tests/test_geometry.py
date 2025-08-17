import pytest
from app.services.geometry_service import (
    compute_area_from_wkt,
    compute_perimeter_from_wkt,
    check_wkt_intersection,
)

# 🧪 Basic 2D Geometry Tests using Shapely

def test_area_from_wkt():
    square = "POLYGON((0 0, 0 10, 10 10, 10 0, 0 0))"
    assert compute_area_from_wkt(square) == 100.0  # 🔸 10x10 = 100 m²

def test_perimeter_from_wkt():
    square = "POLYGON((0 0, 0 10, 10 10, 10 0, 0 0))"
    assert compute_perimeter_from_wkt(square) == 40.0  # 🔸 4 × 10 = 40 m

def test_intersection_true():
    wkt1 = "POLYGON((0 0, 0 5, 5 5, 5 0, 0 0))"
    wkt2 = "POLYGON((3 3, 3 8, 8 8, 8 3, 3 3))"
    assert check_wkt_intersection(wkt1, wkt2) == True

def test_intersection_false():
    wkt1 = "POLYGON((0 0, 0 5, 5 5, 5 0, 0 0))"
    wkt2 = "POLYGON((10 10, 10 15, 15 15, 15 10, 10 10))"
    assert check_wkt_intersection(wkt1, wkt2) == False
