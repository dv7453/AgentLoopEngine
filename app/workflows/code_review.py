from __future__ import annotations

from typing import List

from app.engine.models import WorkflowState, GraphDefinition, EdgeDef, BranchCondition
from app.engine.registry import register_node, register_condition, ToolRegistry


# ----------------------
# Node implementations
# ----------------------

async def extract_functions(state: WorkflowState, tools: ToolRegistry) -> WorkflowState:
    code: str = state.data.get("code", "")
    # Very naive mock: split by 'def ' and count
    functions: List[str] = []
    for chunk in code.split("def "):
        name = chunk.split("(")[0].strip()
        if name and "\n" not in name:
            functions.append(name)
    # Remove possible preamble part
    if functions and not code.startswith("def "):
        functions = functions[1:]
    state.data["functions"] = functions
    return state


async def check_complexity(state: WorkflowState, tools: ToolRegistry) -> WorkflowState:
    functions: List[str] = state.data.get("functions", [])
    code: str = state.data.get("code", "")
    # Simple heuristic: complexity grows with function count and code length
    score = min(100, len(functions) * 5 + len(code) // 500)
    state.data["complexity"] = {"score": score, "function_count": len(functions), "code_len": len(code)}
    return state


async def detect_issues(state: WorkflowState, tools: ToolRegistry) -> WorkflowState:
    complexity = state.data.get("complexity", {}).get("score", 0)
    issues: List[str] = []
    if complexity > 60:
        issues.append("High complexity may reduce readability")
    if complexity > 80:
        issues.append("Refactor large functions into smaller units")
    state.data["issues"] = {"count": len(issues), "items": issues}
    return state


async def suggest_improvements(state: WorkflowState, tools: ToolRegistry) -> WorkflowState:
    issues = state.data.get("issues", {})
    count = issues.get("count", 0)
    suggestions: List[str] = []
    if count == 0:
        suggestions.append("Add docstrings and type hints where missing")
    else:
        suggestions.extend(
            [
                "Introduce helper functions to reduce size",
                "Improve naming and add comments for clarity",
                "Add unit tests to cover complex paths",
            ]
        )
    state.data["suggestions"] = suggestions
    return state


async def evaluate_quality(state: WorkflowState, tools: ToolRegistry) -> WorkflowState:
    complexity = state.data.get("complexity", {}).get("score", 0)
    issue_count = state.data.get("issues", {}).get("count", 0)
    # Quality decreases with complexity and issues; bounded to [0, 100]
    quality_score = max(0, 100 - complexity - issue_count * 5)
    state.data["quality_score"] = quality_score
    return state


# ----------------------
# Registration
# ----------------------

register_node("extract_functions", extract_functions)
register_node("check_complexity", check_complexity)
register_node("detect_issues", detect_issues)
register_node("suggest_improvements", suggest_improvements)
register_node("evaluate_quality", evaluate_quality)


# Conditions

def _quality_below_threshold(state: WorkflowState) -> bool:
    quality_score = state.data.get("quality_score", 0)
    threshold = state.data.get("quality_threshold", 70)
    return quality_score < threshold


register_condition("quality_below_threshold", _quality_below_threshold)


# Optional: A helper to build the graph definition for this workflow.

def get_code_review_graph(graph_id: str = "code_review_graph") -> GraphDefinition:
    return GraphDefinition(
        graph_id=graph_id,
        start_node="extract_functions",
        nodes=[
            "extract_functions",
            "check_complexity",
            "detect_issues",
            "suggest_improvements",
            "evaluate_quality",
        ],
        edges={
            "extract_functions": EdgeDef(default_next="check_complexity"),
            "check_complexity": EdgeDef(default_next="detect_issues"),
            "detect_issues": EdgeDef(default_next="suggest_improvements"),
            "suggest_improvements": EdgeDef(default_next="evaluate_quality"),
            # Loop until quality meets threshold
            "evaluate_quality": EdgeDef(
                default_next=None,
                branches=[BranchCondition(condition="quality_below_threshold", target="detect_issues")],
            ),
        },
    )
