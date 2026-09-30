"""Register the adjudicator in Unity Catalog and alias it @champion (grader G8)."""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import lab_common as lc
import mlflow
from mlflow import MlflowClient

CATALOG = os.environ.get("LAB_CATALOG", "agents_labs")
SCHEMA = os.environ.get("LAB_SCHEMA", "retail")
UC_MODEL = f"{CATALOG}.{SCHEMA}.returns_adjudicator"
AGENT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "serving_adjudicator.py")

profile = os.environ.get("DATABRICKS_PROFILE")
mlflow.set_tracking_uri(f"databricks://{profile}" if profile else "databricks")
mlflow.set_registry_uri("databricks-uc")
user = lc.workspace().current_user.me().user_name
mlflow.set_experiment(f"/Users/{user}/agents-labs-capstone-models")

from mlflow.models.resources import (DatabricksServingEndpoint,
                                     DatabricksVectorSearchIndex, DatabricksFunction)
with mlflow.start_run(run_name="returns-adjudicator"):
    info = mlflow.pyfunc.log_model(
        name="agent", python_model=AGENT, registered_model_name=UC_MODEL,
        resources=[
            DatabricksServingEndpoint(endpoint_name=lc.DEFAULT_CHAT_MODEL),
            DatabricksServingEndpoint(endpoint_name=lc.DEFAULT_EMBED_MODEL),
            DatabricksVectorSearchIndex(index_name=f"{CATALOG}.{SCHEMA}.support_chunks_idx"),
            DatabricksFunction(function_name=f"{CATALOG}.{SCHEMA}.get_order_summary"),
        ],
        pip_requirements=["mlflow>=3.11", "databricks-sdk", "databricks-ai-search", "openai"],
    )
v = info.registered_model_version
MlflowClient().set_registered_model_alias(UC_MODEL, "champion", v)
print(f"  registered {UC_MODEL} v{v}")
print(f"  @champion -> v{v}")
