"""
Lab 6B — register the tuned agent in Unity Catalog and deploy to Model Serving.

Uses MLflow's ResponsesAgent interface, which is what Databricks Model Serving
expects for an agent endpoint.
"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))
import lab_common as lc
import mlflow

UC_MODEL = "agents_labs.retail.support_agent"


def log_and_register():
    profile = os.environ.get("DATABRICKS_PROFILE")
    mlflow.set_tracking_uri(f"databricks://{profile}" if profile else "databricks")
    mlflow.set_registry_uri("databricks-uc")
    user = lc.workspace().current_user.me().user_name
    mlflow.set_experiment(f"/Users/{user}/agents-labs-6-deploy")

    here = os.path.dirname(os.path.abspath(__file__))
    agent_file = os.path.join(here, "serving_agent.py")

    from mlflow.models.resources import (DatabricksServingEndpoint,
                                         DatabricksVectorSearchIndex,
                                         DatabricksFunction)
    with mlflow.start_run():
        info = mlflow.pyfunc.log_model(
            name="agent",
            python_model=agent_file,
            registered_model_name=UC_MODEL,
            resources=[
                DatabricksServingEndpoint(endpoint_name=lc.DEFAULT_CHAT_MODEL),
                DatabricksServingEndpoint(endpoint_name=lc.DEFAULT_EMBED_MODEL),
                DatabricksVectorSearchIndex(index_name="agents_labs.retail.support_chunks_idx"),
                DatabricksFunction(function_name="agents_labs.retail.get_order_summary"),
            ],
            pip_requirements=["mlflow>=3.11", "databricks-sdk", "databricks-ai-search", "openai"],
        )
    print(f"  logged: {info.model_uri}")
    print(f"  registered: {UC_MODEL} version {info.registered_model_version}")
    return info.registered_model_version


if __name__ == "__main__":
    v = log_and_register()
    print(f"\n  next: databricks agents deploy {UC_MODEL} {v}")
