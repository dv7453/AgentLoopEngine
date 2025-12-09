"""
Visualization Helper 2: Execution Log Summary Table

This script reads JSON output containing a `logs` list (as returned by /graph/run
or printed by test_api.py) and prints a clean summary table:

Iteration | Node | Event | Keys Changed

- Keys Changed is computed by diffing consecutive `state.data` dicts.
- Only standard Python is used; no third-party libraries.

Usage:
  python3 visualize_logs.py path/to/run_output.json

Where `run_output.json` contains a JSON object with a `logs` field like:
{
  "logs": [
    {
      "node": "extract_functions",
      "iteration": 1,
      "event": "executed",
      "state": {"data": {"functions": ["foo", "bar"]}, "metadata": {}}
    },
    ...
  ]
}

Notes:
- The diff is computed between consecutive entries in logs.
- For the first entry, Keys Changed lists keys present in its `state.data`.
- A key counts as changed if it is added or its value differs by !=.
- For nested structures, comparison uses Python's equality semantics, not deep difference.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set


def _dict_diff_keys(prev: Dict[str, Any], curr: Dict[str, Any]) -> Set[str]:
    """Return set of keys that were added or changed between prev and curr.

    - Added: key present in curr but not in prev.
    - Changed: key present in both but with different values according to !=.
    - Removed keys are ignored for this summary (focus on additions/changes).
    """
    changed: Set[str] = set()
    prev_keys = set(prev.keys()) if prev else set()
    curr_keys = set(curr.keys()) if curr else set()

    # Added keys
    for k in (curr_keys - prev_keys):
        changed.add(k)

    # Changed values for common keys
    for k in (curr_keys & prev_keys):
        if prev.get(k) != curr.get(k):
            changed.add(k)

    return changed


def _read_logs_from_file(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    # Handle cases where logs may be under 'logs' or 'log'
    logs = data.get("logs") or data.get("log") or []
    if not isinstance(logs, list):
        raise ValueError("Input JSON must contain a 'logs' list or 'log' list")
    return logs


def _format_row(iteration: Any, node: Any, event: Any, keys_changed: Set[str]) -> str:
    keys_str = ", ".join(sorted(keys_changed)) if keys_changed else "-"
    return f"{str(iteration):>9} | {str(node):<18} | {str(event):<9} | {keys_str}"


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 visualize_logs.py path/to/run_output.json")
        sys.exit(1)

    in_path = Path(sys.argv[1])
    if not in_path.exists():
        print(f"Input file not found: {in_path}")
        sys.exit(1)

    logs = _read_logs_from_file(in_path)

    print("Iteration | Node               | Event     | Keys Changed")
    print("-" * 70)

    prev_data: Dict[str, Any] = {}

    for entry in logs:
        iteration = entry.get("iteration", "-")
        node = entry.get("node", "-")
        event = entry.get("event", "-")
        state = entry.get("state") or {}
        curr_data = (state.get("data") or {}) if isinstance(state, dict) else {}

        keys_changed = _dict_diff_keys(prev_data, curr_data) if prev_data is not None else set(curr_data.keys())
        # For the first row, show all keys present
        if prev_data == {}:
            keys_changed = set(curr_data.keys())

        print(_format_row(iteration, node, event, keys_changed))
        prev_data = curr_data


if __name__ == "__main__":
    main()
