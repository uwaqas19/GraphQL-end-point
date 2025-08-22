# Enhancing GraphQL Endpoints with Spatial/Geometrical Operators

 Automatically expose IFC building models over GraphQL, augmented with spatial and geometrical operators (exact 3D metrics, fast 2D plan checks, clashes, mesh/GLB export) with minimal manual work.

This complements IFC to GraphQL schema generation approaches by adding geometry-aware fields and resolvers, so BIM data becomes queryable on the web without shipping whole IFC files.

---

## Project Structure

* Schema Parser 

  &#x20;Generates a GraphQL schema from an IFC schema (entry-point queries, types).
* Resolver

  Auto-creates resolvers mapping GraphQL fields to IFC data access.
* GraphQL Server Ariadne plus FastAPI&#x20;

   Exposes POST /graphql and GET /graphql (playground).
* Spatial/Geometry Operators

  * Exact 3D metrics: elementVolume, elementSurfaceArea
  * Mesh plus GLB export: getElementGeometry and /viewer/{guid}
  * Exact 3D clash volumes: clashBetween, detectClashes
  * Fast 2D plan overlaps: detectPlanClashes, overlaps2DOnStorey
  * Optional lifecycle: elementMaterialUsage, elementEmbodiedCarbon
  * Optional exact CAD exports: exportElementBrep, exportElementStep, exportElementIges

---

## Dependencies

* IfcOpenShell
* pythonocc-core (OpenCASCADE)
* Shapely
* Ariadne
* FastAPI
* ifc2graphql-parser

See requirements.txt for exact versions.

---

## Installation (sketch)

```
# Clone your repo
git clone <YOUR_REPO_URL>
cd <YOUR_REPO_DIR>

# If you intend to regenerate the schema, include submodules
# git clone --recurse-submodules <YOUR_REPO_URL>
# or, if already cloned:
# git submodule update --init --recursive

# Create environment
python -m venv .venv
source .venv/bin/activate

# Or use conda
# conda env create -f environment.yml
# conda activate <env>

# Install deps
pip install -r requirements.txt
```

Optional environment:

```
export GEOM_DEBUG=1
```

---

## Usage (sketch)

Start the server (FastAPI):

```
uvicorn app.utils.main:app --reload
```

GraphQL API: [http://127.0.0.1:8000/graphql](http://127.0.0.1:8000/graphql) GLB Viewer: [http://127.0.0.1:8000/viewer](http://127.0.0.1:8000/viewer) and /viewer/{GUID}

Flask alternative (if you keep the original app):

```
export FLASK_APP=app.py
flask run
```

Example flow:

1. Discover elements (get GUIDs)

```
query { elementByType(filePath: "sample_ifc/arc.ifc", elementType: "IfcWall") { id name } }
```

2. Export mesh plus GLB

```
query { getElementGeometry(filePath: "sample_ifc/arc.ifc", elementId: "<GUID>") { id glbUrl } }
```

3. Open the viewer: /viewer/

Note: adjust the IFC path in your config or queries.

---

## Regenerating the GraphQL Schema (optional)

If you modify the generation logic:

```
git submodule update --init --recursive
python regenerate_graphql_schema.py
```

If you do not change schema generation, the pre-generated files are sufficient.

---

## Roadmap (sketch)

* Add mutations (write operations)
* More 2D overlap helpers and storey filters
* Caching and performance tuning
* Role-based field masking in middleware
* Export clash geometry diff as GLB

---

## Citation

If you use this in academic work, please cite the work above.

---

## License

MIT

---

## TODOs for you to fill in

* Replace placeholders like YOUR\_REPO\_URL and GUIDs
* Decide on FastAPI vs Flask and prune unused bits
* Confirm whether exact CAD exports are enabled; remove if not needed
* Add screenshots or GIFs (e.g., /viewer), and deployment notes (Docker, CI)

