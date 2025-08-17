from app.services.ifc_service import elements_by_type

class IFCQuery:
    @staticmethod
    def resolve_elements_by_type(_, info, filepath: str, elementType: str):
        return elements_by_type(filepath, elementType)
