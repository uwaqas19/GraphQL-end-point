from __future__ import annotations
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from ariadne import QueryType, make_executable_schema, gql
from ariadne.asgi import GraphQL
from app.middleware.auth_middleware import AuthMiddleware

# Resolver imports
from app.resolvers.geometry_resolvers import GeometryQuery           # geometry + 2D WKT helpers
from app.resolvers.auth_resolvers import AuthQuery                   # (if we start to work on exposing login)
from app.resolvers.ifc_resolvers import IFCQuery                     # IFC discovery, spatial tree, 3D clashes
from app.resolvers.lifecycle_resolvers import LifecycleQuery         #  lifecycle here
from app.resolvers.wkt_clash_resolvers import WKTClashQuery          #  WKT plan clashes here

#  Load GraphQL schema
schema_path = os.path.join(os.path.dirname(__file__), "schema.graphql")
type_defs = gql(open(schema_path, encoding="utf-8").read())

# Helper to bind only if resolver exists (keeps boot robust)
def _bind(query_obj: QueryType, field: str, resolver_cls: object, method: str) -> None:
    fn = getattr(resolver_cls, method, None)
    if callable(fn):
        query_obj.set_field(field, fn)

#  Initialize query bindings
query = QueryType()

# ---------- Geometry (OpenCASCADE + tessellated) ----------
_bind(query, "elementVolume", GeometryQuery, "resolve_element_volume")
_bind(query, "elementSurfaceArea", GeometryQuery, "resolve_element_surface_area")
_bind(query, "getElementGeometry", GeometryQuery, "resolve_get_element_geometry")

# ---------- Exact-geometry exports (BREP/STEP/IGES) ----------
_bind(query, "exportElementBrep", GeometryQuery, "resolve_export_element_brep")
_bind(query, "exportElementStep", GeometryQuery, "resolve_export_element_step")
_bind(query, "exportElementIges", GeometryQuery, "resolve_export_element_iges")

# ---------- 2D Geometry (basic WKT helpers) ----------
_bind(query, "areaFromWKT", GeometryQuery, "resolve_area_from_wkt")
_bind(query, "perimeterFromWKT", GeometryQuery, "resolve_perimeter_from_wkt")
_bind(query, "intersectionFromWKT", GeometryQuery, "resolve_intersection_from_wkt")

# ---------- IFC queries ----------
_bind(query, "elementByType", IFCQuery, "resolve_elements_by_type")
_bind(query, "elementProperties", IFCQuery, "resolve_element_properties")   # keep if implemented
_bind(query, "ifcPropertySets", IFCQuery, "resolve_ifc_property_sets")      # keep if implemented
_bind(query, "ifcSpatialHierarchy", IFCQuery, "resolve_ifc_spatial_hierarchy")

# ---------- Lifecycle / Analytics (now in LifecycleQuery) ----------
_bind(query, "elementMaterialUsage", LifecycleQuery, "resolve_element_material_usage")
_bind(query, "elementEmbodiedCarbon", LifecycleQuery, "resolve_element_embodied_carbon")

# ---------- Clash detection ----------
_bind(query, "detectClashes", IFCQuery, "resolve_detect_clashes")            # exact 3D batch
_bind(query, "detectPlanClashes", WKTClashQuery, "resolve_detect_plan_clashes")
_bind(query, "overlaps2DOnStorey", WKTClashQuery, "resolve_overlaps_2d_on_storey")

# (Optional: if you expose these fields in schema)
# _bind(query, "clashBetween", IFCQuery, "resolve_pairwise_clash")
# _bind(query, "pairClashWithGeometry", IFCQuery, "resolve_pair_clash_with_geometry")
# _bind(query, "login", AuthQuery, "resolve_login")

# ✅ Build app and apply middleware
schema = make_executable_schema(type_defs, query)
app = FastAPI()
app.add_middleware(AuthMiddleware)

# ✅ Static files for GLB/exports
os.makedirs("app/static/geometry", exist_ok=True)
os.makedirs("exports", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/exports", StaticFiles(directory="exports"), name="exports")

# ✅ GraphQL endpoint
app.mount("/graphql", GraphQL(schema, debug=True))

# ---------- Convenience routes ----------
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/graphql")

# Simple health check
@app.get("/health")
def health():
    return {"status": "ok"}

# Minimal dynamic GLB viewer (no files needed)
DEFAULT_GUID = "1hOSvn6df7F8_7GcBWlRrM"

_VIEWER_HTML = """<!doctype html>
<html>
  <head>
    <meta charset="utf-8"/>
    <title>Viewer {guid}</title>
    <script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>
    <style>
      html, body {{ margin: 0; height: 100%; }}
      #bar {{ position: absolute; top: 8px; left: 8px; background: #fff8; padding: 8px; border-radius: 8px; z-index: 10; }}
    </style>
  </head>
  <body>
    <div id="bar">
      <span>GUID: <code>{guid}</code></span>
      <span style="margin-left:8px">src: <code>/static/geometry/{guid}.glb</code></span>
    </div>
    <model-viewer src="/static/geometry/{guid}.glb"
                  camera-controls auto-rotate
                  style="width:100vw;height:100vh;background:#f2f2f2"></model-viewer>
  </body>
</html>"""

@app.get("/viewer", response_class=HTMLResponse)
def viewer_default():
    return HTMLResponse(_VIEWER_HTML.format(guid=DEFAULT_GUID))

@app.get("/viewer/{guid}", response_class=HTMLResponse)
def viewer_guid(guid: str):
    return HTMLResponse(_VIEWER_HTML.format(guid=guid))
