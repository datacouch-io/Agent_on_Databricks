"""Summarise the last evaluation run: metrics, then per-case scores."""
import os, sys, mlflow
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))
import lab_common as lc

VARIANT = os.environ.get("LAB_VARIANT", "baseline")
profile = os.environ["DATABRICKS_PROFILE"]
mlflow.set_tracking_uri(f"databricks://{profile}")
os.environ["MLFLOW_TRACING_SQL_WAREHOUSE_ID"] = os.environ["LAB_WAREHOUSE_ID"]
user = lc.workspace().current_user.me().user_name
exp = mlflow.get_experiment_by_name(f"/Users/{user}/agents-labs-6-{VARIANT}")
tr = mlflow.search_traces(locations=[exp.experiment_id], max_results=20)

print(f"  variant: {VARIANT}   traces: {len(tr)}\n")
print(f"  {'question':58} {'retr_rel':9} {'grounded':9} {'correct':8} {'guides':7}")
print("  " + "-"*95)
agg = {}
for i in range(len(tr)):
    t = mlflow.get_trace(tr.iloc[i]["trace_id"])
    q = (t.info.request_preview or "").replace('{"question": "', "").split('", "max_steps')[0]
    s = {}
    for a in (t.info.assessments or []):
        fb = getattr(a, "feedback", None)
        v = getattr(fb, "value", None) if fb else None
        s[a.name] = v if v is not None else "err"
    def g(k): return str(s.get(k, "-"))[:8]
    print(f"  {q[:58]:58} {g('retrieval_relevance'):9} {g('retrieval_groundedness'):9} "
          f"{g('correctness'):8} {g('follows_expectations'):7}")
    for k, v in s.items():
        if v in ("yes", "no"):
            agg.setdefault(k, []).append(1 if v == "yes" else 0)
print()
for k in sorted(agg):
    vals = agg[k]
    print(f"  {k:26} {sum(vals)}/{len(vals)} = {sum(vals)/len(vals):.2f}")
