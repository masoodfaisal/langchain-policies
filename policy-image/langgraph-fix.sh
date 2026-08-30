#!/usr/bin/env bash
set -euo pipefail

config_path="${LANGGRAPH_CONFIG_PATH:-./langgraph.json}"
graph_target="${POLICY_GRAPH_TARGET:-./policy/graph_factory.py:graph}"

if [[ ! -r "${config_path}" ]]; then
    printf 'langgraph-fix: cannot read LangGraph config: %s\n' "${config_path}" >&2
    exit 66
fi

# Production Agent Server images consume the graph mapping through
# LANGSERVE_GRAPHS. Load the project's config, preserve its other graphs, and
# replace only graphs.agent with the reusable policy-aware graph.
graphs_json="$(
    python3 - "${config_path}" "${graph_target}" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path


config_path = Path(sys.argv[1])
graph_target = sys.argv[2]

try:
    config = json.loads(config_path.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as exc:
    raise SystemExit(f"langgraph-fix: failed to load {config_path}: {exc}") from exc

if not isinstance(config, dict):
    raise SystemExit("langgraph-fix: LangGraph config must be a JSON object")

graphs = config.get("graphs")
if not isinstance(graphs, dict):
    raise SystemExit("langgraph-fix: LangGraph config must contain a graphs object")

graphs["agent"] = graph_target
sys.stdout.write(json.dumps(graphs, separators=(",", ":")))
PY
)"

export LANGSERVE_GRAPHS="${graphs_json}"

if (( $# == 0 )); then
    printf 'langgraph-fix: the base image must provide a CMD\n' >&2
    exit 64
fi

exec "$@"
