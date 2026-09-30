"""
Lab 6B — compare variants, segmented by case type.

An aggregate retrieval metric over a dataset containing negative cases is
close to meaningless: on a question the corpus cannot answer, NO retrieved
chunk can be relevant, so the agent is penalised for retrieving at all.
Segment before you conclude anything.
"""
import os, sys, mlflow
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))
sys.path.insert(0, os.path.dirname(__file__))
import lab_common as lc
from eval_dataset import CASES

NEGATIVE = {c["inputs"]["question"] for c in CASES
            if "expected_facts" not in c.get("expectations", {})}

profile = os.environ["DATABRICKS_PROFILE"]
mlflow.set_tracking_uri(f"databricks://{profile}")
os.environ["MLFLOW_TRACING_SQL_WAREHOUSE_ID"] = os.environ["LAB_WAREHOUSE_ID"]
user = lc.workspace().current_user.me().user_name

METRICS = ["retrieval_relevance", "retrieval_groundedness", "correctness",
           "follows_expectations", "safety"]

def collect(variant):
    exp = mlflow.get_experiment_by_name(f"/Users/{user}/agents-labs-6-{variant}")
    if exp is None: return {}
    tr = mlflow.search_traces(locations=[exp.experiment_id], max_results=40)
    seg = {"positive": {}, "negative": {}}
    for i in range(len(tr)):
        t = mlflow.get_trace(tr.iloc[i]["trace_id"])
        q = (t.info.request_preview or "").replace('{"question": "', "").split('", "max_steps')[0]
        if not q: continue
        kind = "negative" if any(q.startswith(n[:40]) for n in NEGATIVE) else "positive"
        for a in (t.info.assessments or []):
            fb = getattr(a, "feedback", None)
            v = getattr(fb, "value", None) if fb else None
            if v in ("yes", "no"):
                seg[kind].setdefault(a.name, []).append(1 if v == "yes" else 0)
    return seg

def fmt(vals):
    return f"{sum(vals)}/{len(vals)} = {sum(vals)/len(vals):.2f}" if vals else "   n/a"

base = collect("baseline")
tune = collect("tuned")
print(f"\n  {'metric':24} {'segment':9} {'baseline k=3':16} {'tuned k=2':16}")
print("  " + "-"*70)
for m in METRICS:
    for seg in ("positive", "negative"):
        b = base.get(seg, {}).get(m, [])
        t = tune.get(seg, {}).get(m, [])
        if not b and not t: continue
        print(f"  {m:24} {seg:9} {fmt(b):16} {fmt(t):16}")
