# syntax=docker/dockerfile:1

# Build the reusable policy base consumed by `langgraph build --base-image`:
#   docker build --platform linux/amd64 -f policy-image/Dockerfile \
#     -t langchain-policies-base:3.14 .
# Override LANGSMITH_DEPLOYMENT_IMAGE to use a different Agent Server runtime.
ARG LANGSMITH_DEPLOYMENT_IMAGE=langchain/langgraph-api:3.14
FROM ${LANGSMITH_DEPLOYMENT_IMAGE}

# A LangGraph deployment image leaves WORKDIR set to the application project.
# Keep the policy path relative to that directory so it matches langgraph.json.
COPY --chmod=0444 \
    policy/__init__.py \
    policy/graph_factory.py \
    policy/sample-policy.py \
    ./policy/
COPY --chmod=0444 langgraph.json ./langgraph.json
COPY --chmod=0555 policy-image/langgraph-fix.sh /usr/local/bin/langgraph-fix

ENV LANGGRAPH_CONFIG_PATH="./langgraph.json" \
    POLICY_GRAPH_TARGET="./policy/graph_factory.py:graph" \
    FF_PROFILE_IMPORTS=true


# The base image's CMD is passed through to this wrapper unchanged.
ENTRYPOINT ["/usr/local/bin/langgraph-fix", "/storage/entrypoint.sh"]
