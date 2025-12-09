# Minimal Async Workflow Engine (FastAPI)

## Overview

# A small, clean workflow/graph engine inspired by LangGraph.
# Nodes are async Python functions operating on a shared WorkflowState.
# A GraphDefinition defines how nodes connect, including branching and simple looping.

## 🚀 Features

# Async nodes with typed shared state
# Simple branching via named conditions
# Looping until a condition is met
# Per-node execution logs
# In-memory storage (no database required)
# FastAPI endpoints to create, run, and inspect workflows

## 🧩 Architecture Overview

### `engine/models.py`
# Pydantic models:
# WorkflowState, GraphDefinition, RunContext, EdgeDef, BranchCondition

### `engine/registry.py`
# Node registry
# Condition registry
# Simple ToolRegistry

### `engine/runner.py`
# Async workflow runner
# Sequential execution
# Branch evaluation
# Looping + max iteration safety
# Per-step logging

### `store/memory_store.py`
# In-memory dictionaries for graphs and run contexts

### `api/routes.py`
# /graph/create
# /graph/run
# /graph/state/{run_id}

### `workflows/code_review.py`
# Example Code Review Mini-Agent workflow

## ▶️ Running the Project

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install fastapi uvicorn pydantic requests

uvicorn app.main:app --reload
```

### Health check

```http
GET http://localhost:8000/
```

Expected response:

```json
{ "status": "ok" }
```

## 📌 API Usage

### 1) Create a graph

```http
POST /graph/create
Content-Type: application/json

{
  "graph_id": "code_review_graph",
  "start_node": "extract_functions",
  "nodes": [
    "extract_functions",
    "check_complexity",
    "detect_issues",
    "suggest_improvements",
    "evaluate_quality"
  ],
  "edges": {
    "extract_functions": { "default_next": "check_complexity", "branches": [] },
    "check_complexity":  { "default_next": "detect_issues", "branches": [] },
    "detect_issues":      { "default_next": "suggest_improvements", "branches": [] },
    "suggest_improvements": { "default_next": "evaluate_quality", "branches": [] },
    "evaluate_quality": {
      "default_next": null,
      "branches": [
        { "condition": "quality_below_threshold", "target": "detect_issues" }
      ]
    }
  }
}
```

Response:

```json
{ "graph_id": "<uuid>" }
```

### 2) Run a workflow

```http
POST /graph/run

{
  "graph_id": "<uuid-from-create>",
  "state": {
    "data": {
      "code": "def foo():\n    pass\n\ndef bar(x):\n    return x",
      "quality_threshold": 75
    },
    "metadata": {}
  }
}
```

Response includes:

# run_id
# final_state
# logs
# status (e.g., completed, failed, or stopped_max_iterations)

### 3) Inspect run state

```http
GET /graph/state/{run_id}
```

Example response:

```json
{
  "run_id": "...",
  "graph_id": "...",
  "current_node": "evaluate_quality",
  "iteration": 5,
  "logs": [ ... ],
  "status": "completed"
}
```

Note: `final_state` is only returned by `/graph/run`.

## 🧠 Example Workflow: Code Review Agent

# Nodes executed:
# extract_functions
# check_complexity
# detect_issues
# suggest_improvements
# evaluate_quality

# Looping:
# If quality_score < quality_threshold, evaluate_quality → detect_issues repeats.

# Condition:
# quality_below_threshold

This demonstrates branching + looping clearly.

## 📊 Log & Graph Visualization (Optional Helpers)

Two standalone scripts are included:

### `visualize_graph.py`
# Generates a Graphviz .dot file representing the workflow.

Render with:

```bash
dot -Tpng workflow_graph.dot -o workflow_graph.png
```

### `visualize_logs.py`
# Takes the output of `/graph/run`.

Shows a table:

```
Iteration | Node | Event | Keys Changed
```

# Computes differences between consecutive node states.

## 🔧 Possible Future Improvements

# Persist graph/runs in a database
# Structured logging
# WebSocket live log streaming
# Per-node timeouts / cancellation
# Node input/output schemas
# Minimal Async Workflow Engine (FastAPI)

A clean, minimal workflow/graph engine inspired by LangGraph. Nodes are async functions operating over a shared `WorkflowState` and routed via a declarative `GraphDefinition`.

## Features
- Async nodes with typed `WorkflowState`
- Branching via named conditions; looping supported
- Safe execution with per-node logging
- In-memory graph and run context storage
- Simple REST API: create graph, run, fetch state

## Architecture
- `engine/models.py`: Pydantic models (`WorkflowState`, `GraphDefinition`, `RunContext`, edges/branches)
- `engine/registry.py`: Node/Condition registries, `ToolRegistry`
- `engine/runner.py`: Sequential async runner with branching, loops, max iterations
- `store/memory_store.py`: In-memory stores for graphs and runs
- `api/routes.py`: FastAPI endpoints
- `workflows/code_review.py`: Example Code Review Mini-Agent

## Run locally

```bash
# Install deps
python3 -m venv .venv && source .venv/bin/activate
pip install fastapi uvicorn pydantic requests

# Start API
uvicorn app.main:app --reload
```
### Save run_output.json for logs visualizer (optional)

Use a tiny Python snippet to create a graph, run it, and save the POST /graph/run output to `run_output.json`:

```bash
python3 - <<'PY'
import requests, json
BASE = "http://localhost:8000"
graph_def = {
  "graph_id": "code_review_graph",
  "start_node": "extract_functions",
  "nodes": ["extract_functions","check_complexity","detect_issues","suggest_improvements","evaluate_quality"],
  "edges": {
    "extract_functions": {"default_next": "check_complexity", "branches": []},
    "check_complexity": {"default_next": "detect_issues", "branches": []},
    "detect_issues": {"default_next": "suggest_improvements", "branches": []},
    "suggest_improvements": {"default_next": "evaluate_quality", "branches": []},
    "evaluate_quality": {"default_next": None, "branches": [{"condition": "quality_below_threshold", "target": "detect_issues"}]},
  },
}
# Create
create_out = requests.post(f"{BASE}/graph/create", json=graph_def).json()
graph_id = create_out["graph_id"]
# Run
initial_state = {"data": {"code": "def foo():\n    pass\n\ndef bar(x):\n    return x", "quality_threshold": 75}, "metadata": {}}
run_out = requests.post(f"{BASE}/graph/run", json={"graph_id": graph_id, "state": initial_state}).json()
# Save
with open("run_output.json", "w") as f:
  json.dump(run_out, f, indent=2)
print("Saved run_output.json")
PY
```

Then visualize:

```bash
python3 visualize_logs.py run_output.json
```

Health check: `GET http://localhost:8000/` → `{ "status": "ok" }`

## API usage

1) Create a graph
```http
POST /graph/create
Content-Type: application/json

{
  "graph_id": "code_review_graph",
  "start_node": "extract_functions",
  "nodes": ["extract_functions","check_complexity","detect_issues","suggest_improvements","evaluate_quality"],
  "edges": {
    "extract_functions": {"default_next": "check_complexity", "branches": []},
    "check_complexity": {"default_next": "detect_issues", "branches": []},
    "detect_issues": {"default_next": "suggest_improvements", "branches": []},
    "suggest_improvements": {"default_next": "evaluate_quality", "branches": []},
    "evaluate_quality": {
      "default_next": null,
      "branches": [{"condition": "quality_below_threshold", "target": "detect_issues"}]
    }
  }
}
```
Response: `{ "graph_id": "<uuid>" }`

2) Run a graph
```http
POST /graph/run
Content-Type: application/json

{
  "graph_id": "<uuid-from-create>",
  "state": {
    "data": {
      "code": "def foo():\n    pass\n\ndef bar(x):\n    return x",
      "quality_threshold": 75
    },
    "metadata": {}
  }
}
```
Response: `{ "run_id": "...", "final_state": { ... }, "logs": [ ... ], "status": "completed|failed|stopped_max_iterations" }`

3) Get run state
```http
GET /graph/state/{run_id}
```
Response: serialized core `RunContext` with fields:
`{"run_id","graph_id","current_node","iteration","logs","status"}`
Note: `final_state` is not included in GET; use POST /graph/run response for it.

## Example workflow: Code Review agent
- Nodes: `extract_functions → check_complexity → detect_issues → suggest_improvements → evaluate_quality`
- Loop: repeats `detect_issues → suggest_improvements → evaluate_quality` until `quality_score >= quality_threshold`
- Condition: `quality_below_threshold`

You can auto-generate the graph in code using `workflows/code_review.get_code_review_graph()`.

## Improvements
- Persistent storage (DB) and pagination for logs
- Rich tool ecosystem and resource limits per node
- Concurrency controls and cancellation tokens
- Structured logging and tracing (OpenTelemetry)
- Validation schemas for node I/O contracts

## Extended Improvements Implemented (Optional)

### Graph validation rules (minimal)
- `start_node` must be present in `nodes`.
- Each `edges` key must be a valid node.
- Fast-fail: first invalidity triggers `HTTP 400`.

### Logs field naming
- Both POST /graph/run and GET /graph/state return the logs under the key `logs`.

### Condition handling (minimal)
- Branch conditions that are missing or raise an error are skipped silently.

### Execution logs
- Logs record per-node execution snapshots. No extra optimization performed.

## Visualization helpers
Two standalone scripts (do not modify the FastAPI app):

1) `visualize_graph.py`
  - Generates `workflow_graph.dot` for the Code Review workflow.
  - Render with Graphviz:
    ```bash
    dot -Tpng workflow_graph.dot -o workflow_graph.png
    ```

2) `visualize_logs.py`
  - Reads a JSON file containing the POST /graph/run output (with `logs`).
  - Prints a table: `Iteration | Node | Event | Keys Changed` by diffing consecutive `state.data`.
