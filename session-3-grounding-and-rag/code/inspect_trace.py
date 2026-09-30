"""Lab 3B — read the last trace and show exactly what produced the answer."""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))
import lab_common as lc
import mlflow
from mlflow.entities.trace_location import UnityCatalog

user = lc.workspace().current_user.me().user_name
NAME = f"/Users/{user}/agents-labs-3b"

profile = os.environ.get("DATABRICKS_PROFILE")
mlflow.set_tracking_uri(f"databricks://{profile}" if profile else "databricks")
# Reading traces out of UC needs the warehouse too, not just writing them.
os.environ["MLFLOW_TRACING_SQL_WAREHOUSE_ID"] = os.environ["LAB_WAREHOUSE_ID"]

exp = mlflow.get_experiment_by_name(NAME)
print(f"  experiment    : {NAME}")
print(f"  trace_location: {exp.trace_location}")
assert isinstance(exp.trace_location, UnityCatalog), "NOT stored in Unity Catalog"

traces = mlflow.search_traces(locations=[exp.experiment_id], max_results=1)
print(f"  traces found  : {len(traces)}")
tid = traces.iloc[0]["trace_id"]
spans = mlflow.get_trace(tid).data.spans
print(f"\n  trace {tid} has {len(spans)} spans:")
for s in spans:
    print(f"    - {s.name:22} {str(s.span_type):12} {(s.end_time_ns - s.start_time_ns)/1e6:8.1f} ms")

print("\n  retrieval spans — the chunks behind the answer:")
for s in spans:
    if str(s.span_type) == "RETRIEVER":
        out = s.outputs if isinstance(s.outputs, list) else json.loads(s.outputs or "[]")
        q = (s.inputs or {}).get("query") if isinstance(s.inputs, dict) else s.inputs
        print(f"    query: {q}")
        for h in out:
            print(f"      {h['chunk_id']:12} {h['doc_id']}  score={h['score']}  {h['title'][:40]}")
