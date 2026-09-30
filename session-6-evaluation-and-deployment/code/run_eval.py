"""Lab 6A/6B — score the RAG agent against the evaluation dataset."""
from __future__ import annotations
import os, sys, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "session-3-grounding-and-rag", "code"))
sys.path.insert(0, os.path.dirname(__file__))
import lab_common as lc
import mlflow
from mlflow.entities.trace_location import UnityCatalog
from mlflow.genai import evaluate
from mlflow.genai.scorers import (Correctness, Guidelines, RelevanceToQuery,
                                  RetrievalGroundedness, RetrievalRelevance, Safety)
from eval_dataset import as_dataset
import rag_agent

VARIANT = os.environ.get("LAB_VARIANT", "baseline")


def predict_fn(question: str) -> str:
    return rag_agent.answer(question)


if __name__ == "__main__":
    user = lc.workspace().current_user.me().user_name
    name = f"/Users/{user}/agents-labs-6-{VARIANT}"
    profile = os.environ.get("DATABRICKS_PROFILE")
    mlflow.set_tracking_uri(f"databricks://{profile}" if profile else "databricks")
    os.environ["MLFLOW_TRACING_SQL_WAREHOUSE_ID"] = os.environ["LAB_WAREHOUSE_ID"]
    mlflow.set_experiment(experiment_name=name,
                          trace_location=UnityCatalog(catalog_name="agents_labs",
                                                      schema_name="retail"))
    print(f"\n  variant    : {VARIANT}")
    print(f"  experiment : {name}")
    print(f"  cases      : {len(as_dataset())}\n")

    t0 = time.time()
    res = evaluate(
        data=as_dataset(),
        predict_fn=predict_fn,
        scorers=[Correctness(), RelevanceToQuery(), RetrievalGroundedness(),
                 RetrievalRelevance(), Safety(),
                 Guidelines(name="follows_expectations", guidelines="{{expectations}}")],
    )
    print(f"\n  wall clock : {time.time()-t0:.1f}s")
    print(f"  run_id     : {res.run_id}")
    try:
        df = res.tables["eval_results"]
        print(f"  rows       : {len(df)}")
    except Exception:
        pass
    print("\n  metrics:")
    for k, v in sorted((res.metrics or {}).items()):
        print(f"    {k:52} {v}")
