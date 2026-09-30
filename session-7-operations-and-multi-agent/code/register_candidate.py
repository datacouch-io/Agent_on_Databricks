"""
Lab 7B step 1 — register a candidate version and give the versions names.

A version number is not a rollout. Aliases are: @champion is whatever serves
traffic, @challenger is whatever you are testing. Callers reference the alias,
never the number, so promotion and rollback are a pointer move.
"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))
import lab_common as lc
import mlflow
from mlflow import MlflowClient

UC_MODEL = "agents_labs.retail.support_agent"
AGENT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "serving_agent_v3.py")


def main():
    profile = os.environ.get("DATABRICKS_PROFILE")
    mlflow.set_tracking_uri(f"databricks://{profile}" if profile else "databricks")
    mlflow.set_registry_uri("databricks-uc")
    user = lc.workspace().current_user.me().user_name
    mlflow.set_experiment(f"/Users/{user}/agents-labs-7b")

    from mlflow.models.resources import (DatabricksServingEndpoint,
                                         DatabricksVectorSearchIndex,
                                         DatabricksFunction)
    with mlflow.start_run(run_name="candidate-loosened-prompt"):
        mlflow.log_param("variant", "loosened-prompt")
        mlflow.log_param("retrieval_k", 2)
        info = mlflow.pyfunc.log_model(
            name="agent", python_model=AGENT_FILE, registered_model_name=UC_MODEL,
            resources=[
                DatabricksServingEndpoint(endpoint_name=lc.DEFAULT_CHAT_MODEL),
                DatabricksServingEndpoint(endpoint_name=lc.DEFAULT_EMBED_MODEL),
                DatabricksVectorSearchIndex(index_name="agents_labs.retail.support_chunks_idx"),
                DatabricksFunction(function_name="agents_labs.retail.get_order_summary"),
            ],
            pip_requirements=["mlflow>=3.11", "databricks-sdk", "databricks-ai-search", "openai"],
        )
    new = info.registered_model_version
    print(f"  registered {UC_MODEL} version {new}")

    c = MlflowClient()
    ready = sorted((int(m.version) for m in c.search_model_versions(f"name='{UC_MODEL}'")
                    if m.status == "READY"), reverse=True)
    incumbent = next((v for v in ready if v != int(new)), None)
    print(f"  READY versions: {ready}   incumbent: v{incumbent}   candidate: v{new}")

    c.set_registered_model_alias(UC_MODEL, "champion", str(incumbent))
    c.set_registered_model_alias(UC_MODEL, "challenger", str(new))
    print(f"\n  @champion   -> v{incumbent}")
    print(f"  @challenger -> v{new}")
    print("\n  callers load 'models:/{}@champion' and never a version number".format(UC_MODEL))


if __name__ == "__main__":
    main()
