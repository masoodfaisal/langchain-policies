"""Agent Server graph compiled once with the configured policy middleware."""

from __future__ import annotations

import runpy
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from langchain.agents.middleware import AgentMiddleware

from agent import build_graph


SAMPLE_POLICY_PATH = Path(__file__).with_name("sample-policy.py")
POLICY_EXPORT = "POLICY_MIDDLEWARE"


class PolicyLoadError(RuntimeError):
    """Raised when a policy file does not satisfy the middleware contract."""


def load_policy_middleware(
    policy_path: Path = SAMPLE_POLICY_PATH,
) -> tuple[AgentMiddleware[Any, Any], ...]:
    """Execute ``policy_path`` and return its exported middleware.

    ``runpy`` deliberately loads the file by path because policy filenames can
    contain characters such as the hyphen in ``sample-policy.py``. The
    module-level graph below calls this function once when Agent Server imports
    this module for a worker process.
    """
    if not policy_path.is_file():
        raise PolicyLoadError(f"Policy file does not exist: {policy_path}")

    namespace = runpy.run_path(
        str(policy_path),
        run_name="policy._runtime_sample_policy",
    )
    exported = namespace.get(POLICY_EXPORT)
    if exported is None:
        raise PolicyLoadError(
            f"{policy_path} must export an iterable named {POLICY_EXPORT}"
        )
    if not isinstance(exported, Iterable) or isinstance(exported, (str, bytes)):
        raise PolicyLoadError(f"{POLICY_EXPORT} must be an iterable of middleware")

    middleware = tuple(exported)
    if not middleware:
        raise PolicyLoadError(f"{POLICY_EXPORT} must contain at least one middleware")
    if not all(isinstance(item, AgentMiddleware) for item in middleware):
        raise PolicyLoadError(
            f"Every item in {POLICY_EXPORT} must be an AgentMiddleware instance"
        )

    return middleware


# Agent Server imports this compiled graph once per worker process and reuses it
# for every run handled by that worker. Updating the policy requires a worker
# restart or a new deployment revision.
graph = build_graph(middleware=load_policy_middleware())
