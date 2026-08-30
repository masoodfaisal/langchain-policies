from __future__ import annotations

import importlib
import sys


def test_static_graph_is_reused_and_applies_sample_policy(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-placeholder")

    # Ensure agent configuration sees the test environment even if another
    # test imported these modules first.
    sys.modules.pop("policy.graph_factory", None)
    sys.modules.pop("agent", None)
    graph_factory = importlib.import_module("policy.graph_factory")

    default_graph = importlib.import_module("agent").graph
    policy_graph = graph_factory.graph
    default_nodes = default_graph.get_graph().nodes
    policy_nodes = policy_graph.get_graph().nodes

    assert importlib.import_module("agent").graph is default_graph
    assert importlib.import_module("policy.graph_factory").graph is policy_graph
    assert "agent_policy.before_agent" not in default_nodes
    assert "agent_policy.before_agent" in policy_nodes
    assert "model_policy.before_model" not in default_nodes
    assert "model_policy.before_model" in policy_nodes
    assert "model" in default_nodes
    assert "model" in policy_nodes
    assert "tools" in default_nodes
    assert "tools" in policy_nodes
