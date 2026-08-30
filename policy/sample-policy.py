"""Example policy middleware loaded by :mod:`policy.graph_factory`.

Policy files use ``POLICY_MIDDLEWARE`` as their public contract. The graph
module executes this file once when each Agent Server worker starts, and the
exported middleware is attached to that worker's reusable compiled graph.

"""

from __future__ import annotations

from langchain.agents.middleware import AgentState, before_agent, before_model
from langgraph.runtime import Runtime


@before_agent(name="agent_policy")
async def agent_policy(
    _state: AgentState,
    _runtime: Runtime,
) -> None:
    """Run the sample policy before the agent starts processing a request."""
    print("I can change fate!!")


@before_model(name="model_policy")
async def model_policy(
    _state: AgentState,
    _runtime: Runtime,
) -> None:
    """Run the sample policy before the model starts processing a request."""
    print("I can intervene model calls!!")

POLICY_MIDDLEWARE = (agent_policy, model_policy,)
