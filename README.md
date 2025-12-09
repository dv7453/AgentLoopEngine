# Minimal Async Workflow Engine (FastAPI)

## Overview

A small, clean workflow/graph engine inspired by LangGraph. Nodes are async Python functions operating on a shared state. A `GraphDefinition` describes how nodes connect, including simple branching and looping. The project is intentionally minimal and student-friendly.

## Features

- Async nodes with typed shared state (Pydantic)
- Simple branching via named conditions
- Looping until a condition is met (with max-iteration safety)
- Per-node execution logs
- In-memory storage for graphs and runs
- FastAPI endpoints to create, run, and inspect workflows

## Architecture

- `app/engine/models.py`: Pydantic models (`WorkflowState`, `GraphDefinition`, `RunContext`, `EdgeDef`, `BranchCondition`)
- `app/engine/registry.py`: Node registry, condition registry, and a simple `ToolRegistry`
- `app/engine/runner.py`: Async sequential runner, branch evaluation, looping, per-step logging
- `app/store/memory_store.py`: In-memory dictionaries for graphs and run contexts
- `app/api/routes.py`: FastAPI endpoints (`/graph/create`, `/graph/run`, `/graph/state/{run_id}`)
- `app/workflows/code_review.py`: Example Code Review Mini-Agent workflow
- `visualize_graph.py`: Generates Graphviz DOT for the workflow (standalone helper)
- `visualize_logs.py`: Prints a table from run logs (standalone helper)

## Running the Project

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install fastapi uvicorn pydantic requests

uvicorn app.main:app --reload
```

Health check:

```http
GET http://localhost:8000/
```

Expected response:

```json
{ "status": "ok" }
```

## API Usage

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

Response includes:

```json
{
  "run_id": "...",
  "final_state": { ... },
  "logs": [ ... ],
  "status": "completed" | "failed" | "stopped_max_iterations"
}
```

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

## Example Workflow

Code Review Agent:

- Nodes: `extract_functions → check_complexity → detect_issues → suggest_improvements → evaluate_quality`
- Looping: If `quality_score < quality_threshold`, the flow returns to `detect_issues` and repeats.
- Condition: `quality_below_threshold`

## Visualization Helpers

- `visualize_graph.py`: Generates `workflow_graph.dot` for the Code Review workflow.

  Render with Graphviz:

  ```bash
  dot -Tpng workflow_graph.dot -o workflow_graph.png
  ```

- `visualize_logs.py`: Reads the POST `/graph/run` output and prints a table:

  ```
  Iteration | Node | Event | Keys Changed
  ```

  Keys Changed is computed by diffing consecutive `state.data` entries.

## Future Improvements

- Persist graphs/runs in a database
- Structured logging and tracing
- WebSocket live log streaming
- Per-node timeouts / cancellation
- Node input/output schemas
