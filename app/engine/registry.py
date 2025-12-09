from __future__ import annotations

from typing import Awaitable, Callable, Dict, Optional

from app.engine.models import WorkflowState


class ToolRegistry:
    """Minimal registry for tools/utilities available to nodes."""

    def __init__(self) -> None:
        self._tools: Dict[str, Callable[..., object]] = {}

    def register(self, name: str, fn: Callable[..., object]) -> None:
        """Register a tool by name."""
        self._tools[name] = fn

    def get(self, name: str) -> Optional[Callable[..., object]]:
        """Retrieve a tool by name, if present."""
        return self._tools.get(name)


# Node registry maps node names to async callables operating on WorkflowState.
NodeFn = Callable[[WorkflowState, ToolRegistry], Awaitable[WorkflowState]]
node_registry: Dict[str, NodeFn] = {}


# Condition registry maps condition names to simple booleans on state.
ConditionFn = Callable[[WorkflowState], bool]
condition_registry: Dict[str, ConditionFn] = {}


def register_node(name: str, fn: NodeFn) -> None:
    """Register an async node function by name."""
    node_registry[name] = fn


def register_condition(name: str, fn: ConditionFn) -> None:
    """Register a condition function by name."""
    condition_registry[name] = fn
