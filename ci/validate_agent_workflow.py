#!/usr/bin/env python3
"""Check the minimal agent.py contract required by the policy image."""

from __future__ import annotations

import ast
import sys
from pathlib import Path


def validate_agent_workflow(project_root: Path | None = None) -> None:
    """Require agent.py and ``def build_graph(*, middleware=())``."""
    root = (
        Path(__file__).resolve().parents[1]
        if project_root is None
        else project_root
    )
    agent_path = root / "agent.py"
    if not agent_path.is_file():
        raise FileNotFoundError(f"agent.py not found at {agent_path}")

    module = ast.parse(agent_path.read_bytes(), filename=str(agent_path))
    functions = [
        statement
        for statement in module.body
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
        and statement.name == "build_graph"
    ]

    match functions:
        case [
            ast.FunctionDef(
                args=ast.arguments(
                    posonlyargs=[],
                    args=[],
                    defaults=[],
                    vararg=None,
                    kwonlyargs=[ast.arg(arg="middleware")],
                    kw_defaults=[ast.Tuple(elts=[])],
                    kwarg=None,
                )
            )
        ]:
            pass
        case [_]:
            raise TypeError(
                "build_graph must use: def build_graph(*, middleware=())"
            )
        case _:
            raise ValueError(
                "agent.py must define exactly one top-level build_graph function"
            )

    graph_exports = [
        statement
        for statement in module.body
        if isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], ast.Name)
        and statement.targets[0].id == "graph"
    ]


    ## check if the build_graph exists in a policy free way. Good to make sure that local dev contract has been followed.
    match graph_exports:
        case [
            ast.Assign(
                value=ast.Call(
                    func=ast.Name(id="build_graph"),
                    args=[],
                    keywords=[],
                )
            )
        ]:
            pass
        case _:
            raise ValueError(
                "agent.py must define exactly: graph = build_graph()"
            )

def main() -> int:
    """Run the validator as a command-line check."""
    try:
        validate_agent_workflow()
    except (OSError, SyntaxError, TypeError, ValueError) as exc:
        print(f"Agent workflow validation failed: {exc}", file=sys.stderr)
        return 1
    print("Agent workflow validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
