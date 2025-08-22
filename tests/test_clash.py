import pytest

#  This would normally be imported from your clash detection service
from app.services.geometry_service import check_wkt_intersection

#  Simulated Clash Detection Tests using 2D overlaps (proxy for 3D)

def test_clash_detected_between_elements():
    beam = "POLYGON((0 0, 0 3, 3 3, 3 0, 0 0))"
    slab = "POLYGON((2 2, 2 5, 5 5, 5 2, 2 2))"
    assert check_wkt_intersection(beam, slab) == True  # 🔸 Should clash (2D overlap)

def test_no_clash_between_separated_elements():
    column = "POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))"
    wall = "POLYGON((10 10, 10 12, 12 12, 12 10, 10 10))"
    assert check_wkt_intersection(column, wall) == False  # 🔹 No overlap
