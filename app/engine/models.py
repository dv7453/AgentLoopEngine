from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BranchCondition(BaseModel):
    """A named condition directing flow to a target node."""
    condition: str
    target: str


class EdgeDef(BaseModel):
    """Edge definition with default next node and optional conditional branches."""
    default_next: Optional[str] = None
    branches: List[BranchCondition] = Field(default_factory=list)


class GraphDefinition(BaseModel):
    """Graph structure describing nodes and edges."""
    graph_id: str
    start_node: str
    nodes: List[str]
    edges: Dict[str, EdgeDef]


class WorkflowState(BaseModel):
    """Shared workflow state passed between nodes."""
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RunContext(BaseModel):
    """Run-time context tracking execution progress and logs."""
    run_id: str
    graph_id: str
    current_node: Optional[str] = None
    iteration: int = 0
    status: str = "running"
    log: List[Dict[str, Any]] = Field(default_factory=list)
    final_state: Optional[WorkflowState] = None

