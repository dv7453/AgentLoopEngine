from uuid import uuid4
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from app.engine.models import GraphDefinition, WorkflowState, RunContext
from app.engine.runner import run_graph
from app.engine.registry import ToolRegistry
from app.store.memory_store import graphs_store, runs_store

router = APIRouter()


def validate_graph_definition(definition: GraphDefinition) -> None:
    """Minimal validation for a GraphDefinition (student-level).

    Fast-fail checks:
    1. start_node must be in nodes.
    2. Every edge key must be an existing node.
    3. default_next and branch targets must be valid node names (when not None).
    """
    nodes = set(definition.nodes)

    # 1) start_node must exist
    if definition.start_node not in nodes:
        raise HTTPException(status_code=400, detail="Invalid graph: start_node not found in nodes")

    # 2) edge keys must be node names
    for edge_node in definition.edges.keys():
        if edge_node not in nodes:
            raise HTTPException(status_code=400, detail=f"Invalid graph: edge for unknown node '{edge_node}'")

    # 3) default_next and branch targets must be valid node names (when not None)
    for edge_node, edge_def in definition.edges.items():
        # default_next
        default_next = getattr(edge_def, "default_next", None)
        if default_next is not None and default_next not in nodes:
            raise HTTPException(status_code=400, detail=f"Invalid graph: default_next '{default_next}' for node '{edge_node}' not in nodes")
        # branches
        branches = getattr(edge_def, "branches", []) or []
        for br in branches:
            target = getattr(br, "target", None)
            if target is not None and target not in nodes:
                raise HTTPException(status_code=400, detail=f"Invalid graph: branch target '{target}' for node '{edge_node}' not in nodes")


@router.post("/create")
async def create_graph(definition: GraphDefinition) -> Dict[str, str]:
    """Create and store a graph; returns generated graph_id."""
    # Validate incoming definition first (fast-fail)
    validate_graph_definition(definition)
    graph_id = str(uuid4())
    # Minimal fix: overwrite graph_id inside stored GraphDefinition with server-generated id
    # Use Pydantic v2 model_copy to update graph_id safely
    clean_graph = definition.model_copy(update={"graph_id": graph_id})
    graphs_store[graph_id] = clean_graph
    return {"graph_id": graph_id}


@router.post("/run")
async def run_graph_endpoint(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Run a graph by id with an initial workflow state."""
    graph_id = payload.get("graph_id")
    initial_state_data = payload.get("state")

    if not graph_id:
        raise HTTPException(status_code=400, detail="graph_id is required")
    if initial_state_data is None:
        raise HTTPException(status_code=400, detail="state is required")

    graph = graphs_store.get(graph_id)
    if graph is None:
        raise HTTPException(status_code=404, detail="Graph not found")

    # Parse initial state
    try:
        initial_state = WorkflowState.model_validate(initial_state_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid state: {e}")

    run_id = str(uuid4())
    run_ctx = RunContext(run_id=run_id, graph_id=graph_id)
    tools = ToolRegistry()

    # Execute graph
    run_ctx = await run_graph(graph, initial_state, tools, run_ctx)

    # Persist run context
    runs_store[run_id] = run_ctx

    return {
        "run_id": run_id,
        "final_state": (run_ctx.final_state.model_dump() if run_ctx.final_state else {}),
        "logs": run_ctx.log,
        "status": run_ctx.status,
    }


@router.get("/state/{run_id}")
async def get_run_state(run_id: str) -> Dict[str, Any]:
    """Return serialized run context if exists."""
    run_ctx = runs_store.get(run_id)
    if run_ctx is None:
        raise HTTPException(status_code=404, detail="Run not found")
    # Minimal response: core run context only (no duplication of /graph/run output)
    return {
        "run_id": run_ctx.run_id,
        "graph_id": run_ctx.graph_id,
        "current_node": run_ctx.current_node,
        "iteration": run_ctx.iteration,
        "logs": run_ctx.log,
        "status": run_ctx.status,
    }
