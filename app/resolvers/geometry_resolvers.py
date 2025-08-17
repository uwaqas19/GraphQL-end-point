from app.services.geometry_service import (
    compute_element_volume,
    compute_element_surface_area,
    compute_area_from_wkt,
    compute_perimeter_from_wkt,
    check_wkt_intersection,
    export_element_geometry,  # 🔹 new function to implement
)

# ✅ Resolver class for 3D/2D geometric operations
class GeometryQuery:

    # --------- 3D Geometry Queries (OpenCascade) ---------

    @staticmethod
    def resolve_element_volume(_, info, filePath: str, elementId: str) -> float:
        """
        Returns volume (m³) of an element using BRep from OpenCascade.
        """
        return compute_element_volume(filePath, elementId)

    @staticmethod
    def resolve_element_surface_area(_, info, filePath: str, elementId: str) -> float:
        """
        Returns surface area (m²) of an element using BRep.
        """
        return compute_element_surface_area(filePath, elementId)

    @staticmethod
    def resolve_get_element_geometry(_, info, filePath: str, elementId: str) -> dict:
        """
        Returns either .glb URL or raw mesh data of an IFC element.
        """
        return export_element_geometry(filePath, elementId)

    # --------- 2D Geometry Queries (Shapely/WKT) ---------

    @staticmethod
    def resolve_area_from_wkt(_, info, wkt: str) -> float:
        """
        Computes area of 2D WKT polygon.
        """
        return compute_area_from_wkt(wkt)

    @staticmethod
    def resolve_perimeter_from_wkt(_, info, wkt: str) -> float:
        """
        Computes perimeter of WKT polygon or line.
        """
        return compute_perimeter_from_wkt(wkt)

    @staticmethod
    def resolve_intersection_from_wkt(_, info, wkt1: str, wkt2: str) -> bool:
        """
        Returns True if two WKT geometries intersect.
        """
        return check_wkt_intersection(wkt1, wkt2)
