from __future__ import annotations

from typing import Optional

from app.engine.models import GraphDefinition, WorkflowState, RunContext, EdgeDef
from app.engine.registry import node_registry, condition_registry, ToolRegistry

MAX_ITERATIONS = 20


def compute_next_node(edge: EdgeDef, state: WorkflowState, context: RunContext) -> Optional[str]:
    """Compute the next node based on branch conditions or default_next.

    Returns the target node name or None if workflow should complete.
    """
    # Evaluate branches in order; first truthy condition wins
    for branch in edge.branches:
        cond_fn = condition_registry.get(branch.condition)
        if cond_fn is None:
            # Beginner-level: silently skip missing conditions
            continue
        try:
            if cond_fn(state):
                return branch.target
        except Exception:
            # Beginner-level: silently skip on exceptions
            continue
    # Fallback to default_next
    return edge.default_next


async def run_graph(
    graph: GraphDefinition,
    initial_state: WorkflowState,
    tools: ToolRegistry,
    context: RunContext,
) -> RunContext:
    """Run a graph sequentially with branching, looping, and logging.

    Execution stops on completion, failure, or max iteration threshold.
    """
    state = initial_state
    current = graph.start_node
    context.current_node = current

    while True:
        context.iteration += 1

        # Fetch node function
        node_fn = node_registry.get(current)
        if node_fn is None:
            context.status = "failed"
            context.log.append(
                {
                    "node": current,
                    "iteration": context.iteration,
                    "event": "missing_node",
                    "message": f"Node function '{current}' not found",
                }
            )
            break

        # Execute node safely
        try:
            state = await node_fn(state, tools)
            # Log after successful execution
            context.log.append(
                {
                    "node": current,
                    "iteration": context.iteration,
                    "event": "executed",
                    # Restoring full state snapshot for detailed debugging.
                    "state": state.model_dump(),
                }
            )
        except Exception as exc:
            context.status = "failed"
            context.log.append(
                {
                    "node": current,
                    "iteration": context.iteration,
                    "event": "error",
                    "error": str(exc),
                }
            )
            break

        # Resolve next node
        edge = graph.edges.get(current)
        if edge is None:
            # No edge configured for current node => workflow completes
            context.status = "completed"
            break

        next_node = compute_next_node(edge, state, context)
        if next_node is None:
            context.status = "completed"
            break

        current = next_node
        context.current_node = current

        # Enforce max iterations
        if context.iteration >= MAX_ITERATIONS:
            context.status = "stopped_max_iterations"
            break

    # Finalize
    context.final_state = state
    return context
