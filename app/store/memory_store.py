from __future__ import annotations

from typing import Dict, Optional

from app.engine.models import GraphDefinition, RunContext

# In-memory stores; minimal and clean.
graphs_store: Dict[str, GraphDefinition] = {}
runs_store: Dict[str, RunContext] = {}


def get_graph(graph_id: str) -> Optional[GraphDefinition]:
    return graphs_store.get(graph_id)


def save_graph(graph: GraphDefinition) -> None:
    graphs_store[graph.graph_id] = graph


def get_run(run_id: str) -> Optional[RunContext]:
    return runs_store.get(run_id)


def save_run(run: RunContext) -> None:
    runs_store[run.run_id] = run
