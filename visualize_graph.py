"""
Visualization Helper 1: Workflow Graph (Graphviz DOT)

This script manually defines the Code Review workflow graph and writes a Graphviz
DOT file to visualize the nodes and edges, including the loop when quality is
below threshold.

Nodes:
  extract_functions -> check_complexity -> detect_issues -> suggest_improvements -> evaluate_quality

Loop:
  evaluate_quality -> detect_issues [label="quality_below_threshold"]

Output:
  - workflow_graph.dot (Graphviz DOT file)

Render with Graphviz CLI (installed separately):
  dot -Tpng workflow_graph.dot -o workflow_graph.png

Explanation:
  - The diagram shows the linear progression through the workflow nodes.
  - The labeled edge represents the conditional branch: if the quality is below
    the threshold, the workflow loops back to re-run detection and suggestions.
"""

from pathlib import Path

def main() -> None:
    # Manually define the graph structure (matches the Code Review workflow)
    nodes = [
        "extract_functions",
        "check_complexity",
        "detect_issues",
        "suggest_improvements",
        "evaluate_quality",
    ]

    # Edges: default flow
    edges = [
        ("extract_functions", "check_complexity", None),
        ("check_complexity", "detect_issues", None),
        ("detect_issues", "suggest_improvements", None),
        ("suggest_improvements", "evaluate_quality", None),
    ]

    # Conditional loop edge when quality below threshold
    loop_edge = ("evaluate_quality", "detect_issues", "quality_below_threshold")

    dot_lines = [
        "digraph CodeReviewWorkflow {",
        "  rankdir=LR;",  # left-to-right layout
        "  node [shape=box, style=filled, fillcolor=lightgray];",
    ]

    # Declare nodes
    for n in nodes:
        dot_lines.append(f"  \"{n}\";")

    # Default edges
    for src, dst, label in edges:
        if label:
            dot_lines.append(f"  \"{src}\" -> \"{dst}\" [label=\"{label}\"];")
        else:
            dot_lines.append(f"  \"{src}\" -> \"{dst}\";")

    # Loop edge with label
    src, dst, label = loop_edge
    dot_lines.append(f"  \"{src}\" -> \"{dst}\" [label=\"{label}\", color=blue];")

    dot_lines.append("}")

    out_path = Path("workflow_graph.dot")
    out_path.write_text("\n".join(dot_lines), encoding="utf-8")
    print(f"Wrote Graphviz DOT to: {out_path.resolve()}")
    print("To render PNG (requires Graphviz 'dot' installed):")
    print("  dot -Tpng workflow_graph.dot -o workflow_graph.png")

if __name__ == "__main__":
    main()
