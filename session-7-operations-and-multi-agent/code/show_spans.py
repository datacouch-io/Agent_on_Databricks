"""Print the span tree of the most recent supervisor trace.

The point of the exercise: a multi-agent run is only debuggable if you can see
which worker was asked what. The span tree is that record.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))
import lab_common as lc
import mlflow

profile = os.environ.get("DATABRICKS_PROFILE")
mlflow.set_tracking_uri(f"databricks://{profile}" if profile else "databricks")
os.environ["MLFLOW_TRACING_SQL_WAREHOUSE_ID"] = os.environ["LAB_WAREHOUSE_ID"]
user = lc.workspace().current_user.me().user_name
exp = mlflow.get_experiment_by_name(f"/Users/{user}/agents-labs-7a")
print(f"  experiment    {exp.experiment_id}")
print(f"  trace_location {exp.trace_location}\n")

df = mlflow.search_traces(locations=[exp.experiment_id], max_results=5)
print(f"  {len(df)} trace(s)\n")
for _, row in df.iterrows():
    tr = mlflow.get_trace(row.trace_id)
    spans = tr.data.spans
    print(f"  trace {row.trace_id[:24]}...  {len(spans)} spans  "
          f"{tr.info.execution_duration/1000:.1f}s")
    by_id = {s.span_id: s for s in spans}
    def depth(s):
        d = 0
        while s.parent_id and s.parent_id in by_id:
            s = by_id[s.parent_id]; d += 1
        return d
    for s in spans:
        pad = "    " + "  " * depth(s)
        extra = ""
        if s.name in ("analytics_worker", "policy_worker"):
            ins = s.inputs
            # span inputs come back as a dict, or as the JSON text of one
            if isinstance(ins, str):
                try: ins = json.loads(ins)
                except Exception: ins = {"task": ins}
            t = (ins or {}).get("task", "")
            extra = f"   task: {t[:60]}"
        print(f"{pad}{s.name:22} [{s.span_type}]{extra}")
    print()
    break
