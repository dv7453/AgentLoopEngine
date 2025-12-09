# Minimal Async Workflow Engine (FastAPI)

## Overview

##### A small, clean workflow/graph engine inspired by LangGraph.
##### Nodes are async Python functions operating on a shared WorkflowState.
##### A GraphDefinition defines how nodes connect, including branching and simple looping.

## 🚀 Features

##### Async nodes with typed shared state
##### Simple branching via named conditions
##### Looping until a condition is met
##### Per-node execution logs
##### In-memory storage (no database required)
##### FastAPI endpoints to create, run, and inspect workflows

## 🧩 Architecture Overview

### `engine/models.py`
##### Pydantic models: WorkflowState, GraphDefinition, RunContext, EdgeDef, BranchCondition

### `engine/registry.py`
##### Node registry · Condition registry · Simple ToolRegistry

### `engine/runner.py`
##### Async workflow runner · Sequential execution · Branch evaluation · Looping + max iteration safety · Per-step logging

### `store/memory_store.py`
##### In-memory dictionaries for graphs and run contexts

### `api/routes.py`
##### /graph/create · /graph/run · /graph/state/{run_id}

### `workflows/code_review.py`
##### Example Code Review Mini-Agent workflow

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

##### run_id · final_state · logs · status (e.g., completed, failed, or stopped_max_iterations)

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

##### Nodes executed:
##### extract_functions · check_complexity · detect_issues · suggest_improvements · evaluate_quality

##### Looping:
##### If quality_score < quality_threshold, evaluate_quality → detect_issues repeats.

##### Condition:
##### quality_below_threshold

This demonstrates branching + looping clearly.

## 📊 Log & Graph Visualization (Optional Helpers)

Two standalone scripts are included:

### `visualize_graph.py`
##### Generates a Graphviz .dot file representing the workflow.

Render with:

```bash
dot -Tpng workflow_graph.dot -o workflow_graph.png
```

### `visualize_logs.py`
##### Takes the output of `/graph/run`.

Shows a table:

```
Iteration | Node | Event | Keys Changed
```

##### Computes differences between consecutive node states.

## 🔧 Possible Future Improvements

##### Persist graph/runs in a database
##### Structured logging
##### WebSocket live log streaming
##### Per-node timeouts / cancellation
##### Node input/output schemas
