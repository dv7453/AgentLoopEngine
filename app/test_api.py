import requests

BASE = "http://localhost:8000"

graph_def = {
    "graph_id": "code_review_graph",
    "start_node": "extract_functions",
    "nodes": [
        "extract_functions",
        "check_complexity",
        "detect_issues",
        "suggest_improvements",
        "evaluate_quality",
    ],
    "edges": {
        "extract_functions": {"default_next": "check_complexity", "branches": []},
        "check_complexity": {"default_next": "detect_issues", "branches": []},
        "detect_issues": {"default_next": "suggest_improvements", "branches": []},
        "suggest_improvements": {"default_next": "evaluate_quality", "branches": []},
        "evaluate_quality": {
            "default_next": None,
            "branches": [
                {"condition": "quality_below_threshold", "target": "detect_issues"}
            ],
        },
    },
}


def main():
    # 1) Create graph
    r = requests.post(f"{BASE}/graph/create", json=graph_def)
    r.raise_for_status()
    create_out = r.json()
    graph_id = create_out["graph_id"]
    print("Created graph_id:", graph_id)

    # 2) Run workflow
    initial_state = {
        "data": {
            "code": "def foo():\n    pass\n\ndef bar(x):\n    return x",
            "quality_threshold": 75,
        },
        "metadata": {},
    }
    r2 = requests.post(
        f"{BASE}/graph/run", json={"graph_id": graph_id, "state": initial_state}
    )
    r2.raise_for_status()
    run_out = r2.json()
    run_id = run_out["run_id"]
    status = run_out.get("status")
    final_state = run_out.get("final_state")
    # Runner stores full snapshots under key 'log' (not 'logs'). Support both for compatibility.
    logs = run_out.get("log") or run_out.get("logs", [])
    print("Run status:", status)
    print("Run ID:", run_id)
    print("Final state exists:", isinstance(final_state, dict) and len(final_state) > 0)

    # Basic validations
    assert status in {"completed", "failed", "stopped_max_iterations"}, "Unexpected status"
    assert isinstance(final_state, dict), "final_state should be a dict"
    assert isinstance(logs, list), "logs should be a list"
    assert any(entry.get("event") == "executed" for entry in logs), "execution log missing"

    # 3) Fetch run state
    r3 = requests.get(f"{BASE}/graph/state/{run_id}")
    r3.raise_for_status()
    state_out = r3.json()
    print("Fetched run state:", state_out)

    # Validate final_state in GET response
    # GET /graph/state returns minimal fields and uses 'log' key
    fetched_log = state_out.get("log") or state_out.get("logs", [])
    assert isinstance(fetched_log, list), "log in GET should be a list"
    # Conditions are handled silently now; only 'executed' events are expected
    assert any(entry.get("event") == "executed" for entry in fetched_log), (
        "log should include at least one executed event"
    )


if __name__ == "__main__":
    main()
