# Semantic Modeling Assistant API

## Running the API

**Working directory:** `semantic-modeling-assistant-agentic-backend` (this folder).

1. Start the API server (in one terminal):

   ```powershell
   cd semantic-modeling-assistant-agentic-backend
   .\start_api.ps1
   ```
   Or without the script:
   ```powershell
   python run_api.py
   ```

2. The API runs at `http://localhost:8000`. Health check: `http://localhost:8000/api/health`.

## Running the API example

**Working directory:** same — `semantic-modeling-assistant-agentic-backend`.

With the API server already running in another terminal:

```powershell
cd semantic-modeling-assistant-agentic-backend
python examples/api_example.py
```

This runs the example that demonstrates health check, create ontology, create project, domain areas, suggest iterations, and other API calls.

## Summarizing only part of a legal document

When adding a legal document, summarization can be limited to selected parts (e.g. Part 1 and Part 2) to speed up runs.

**Important:** Set the variable in the **same terminal where you start the API** (summarization runs in the API process, not in the client):

```powershell
# In the terminal where you run: python run_api.py
$env:SUMMARIZE_ONLY_ELEMENT_ID_CONTAINS = "cast_1"        # Only Part 1
# Or: "cast_1,cast_2" for Part 1 and Part 2
python run_api.py
```

Then in another terminal run `python examples/new_project_workflow_example.py`. Only root children whose id contains any of the given strings (and their descendants) will be summarized. Remove the variable or set it to empty for full document summarization.

## What’s next after you have a project

Once you have a project with domain areas (e.g. after `new_project_workflow_example.py`), the typical flow is:

1. **Suggest iterations** – Ask the API to propose modeling iterations for one domain area:
   - `POST /api/projects/{project_id}/iterations/suggest`
   - Body: `{ "focused_area_id": "<domain_area_id>", "count": 3, "user_instruction": "..." }`
   - Use a `domain_area_id` from your project (e.g. from `GET /api/projects/{project_id}` → `domain_areas[].id`).

2. **List iterations** – `GET /api/projects/{project_id}/iterations` to see planned iterations.

3. **Prepare an iteration** – Generate the task plan and ontology operations for one planned iteration:
   - `POST /api/projects/{project_id}/iterations/{iteration_id}/prepare`
   - The iteration becomes the “current” one and gets planned tasks and operations.

4. **Get prepared operations** (optional) – `GET /api/projects/{project_id}/iterations/current/operations` to inspect operations before applying.

5. **Apply operations** – Apply the ontology edits:
   - `POST /api/projects/{project_id}/iterations/current/apply` (optionally with a body to filter which operations to apply).

6. **Finish iteration** – Move the current iteration to finished (endpoint depends on your API; e.g. apply may auto-finish or there is a dedicated “finish” call).

You can drive these steps from a script (e.g. `requests` in Python) or from a frontend. OpenAPI docs: `http://localhost:8000/docs` when the API is running.

## Where to see the project ontology (working / “fake” ontology)

The ontology that the project is designing is stored in two ways:

1. **Via API** (when the API is running):
   - `GET /api/projects/{project_id}/ontology`  
   - Returns the current ontology (classes, attributes, relationships) in JSON.
   - Example: `http://localhost:8000/api/projects/9205edca-b5e8-4f92-961a-cf54dfcceecb/ontology`

2. **On disk** (same data, persisted by the ontology store):
   - Directory: `data/ontologies/<safe_uri>/`
   - File: `ontology.json`
   - The folder name is the ontology URI made filesystem-safe (e.g. `https://slovník.gov.cz/datový/turistické-cíle` → `slovník.gov.cz_datový_turistické-cíle`).
   - For project **9205edca** (Traffic Regulations) the ontology file is:
     - `data/ontologies/slovník.gov.cz_datový_turistické-cíle/ontology.json`

Initially the ontology is empty (`classes`, `attributes`, `relationships` are `{}`). After you **prepare** an iteration and **apply** operations, this file (and the API response) will contain the added classes, attributes, and relationships.

## Running tests

- **Unit tests:** from `semantic-modeling-assistant-agentic-backend`, run e.g. `python -m pytest tests/`.
- **API scenario tests:** `.\run_api_tests.ps1` (expects a `tests-api` folder and API server as needed by those tests).
