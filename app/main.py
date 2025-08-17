from fastapi import FastAPI
from ariadne import QueryType, make_executable_schema, gql
from ariadne.asgi import GraphQL
import os

from starlette.middleware.base import BaseHTTPMiddleware
from app.middleware.auth_middleware import AuthMiddleware

# ✅ Resolver imports
from app.resolvers.geometry_resolvers import GeometryQuery
from app.resolvers.auth_resolvers import AuthQuery
from app.resolvers.ifc_resolvers import IFCQuery  # ✅ Check the filename

# ✅ Load GraphQL schema
schema_path = os.path.join(os.path.dirname(__file__), "schema.graphql")
type_defs = gql(open(schema_path, encoding="utf-8").read())

# ✅ Initialize query bindings
query = QueryType()

# Geometry
query.set_field("elementVolume", GeometryQuery.resolve_element_volume)
query.set_field("elementSurfaceArea", GeometryQuery.resolve_element_surface_area)
query.set_field("areaFromWKT", GeometryQuery.resolve_area_from_wkt)
query.set_field("perimeterFromWKT", GeometryQuery.resolve_perimeter_from_wkt)
query.set_field("intersectionFromWKT", GeometryQuery.resolve_intersection_from_wkt)
query.set_field("getElementGeometry", GeometryQuery.resolve_get_element_geometry)  # ✅ NEW

# IFC
query.set_field("elementByType", IFCQuery.resolve_elements_by_type)


# Auth
query.set_field("login", AuthQuery.resolve_login)

# ✅ Build app and apply middleware
schema = make_executable_schema(type_defs, query)
app = FastAPI()
app.add_middleware(AuthMiddleware)

# ✅ GraphQL endpoint
app.mount("/graphql", GraphQL(schema, debug=True))

