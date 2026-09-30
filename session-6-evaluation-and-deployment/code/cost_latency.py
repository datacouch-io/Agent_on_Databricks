"""Lab 6B — token and latency comparison, read from the traces themselves."""
import os, sys, mlflow
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))
import lab_common as lc

profile = os.environ["DATABRICKS_PROFILE"]
mlflow.set_tracking_uri(f"databricks://{profile}")
os.environ["MLFLOW_TRACING_SQL_WAREHOUSE_ID"] = os.environ["LAB_WAREHOUSE_ID"]
user = lc.workspace().current_user.me().user_name

def stats(variant):
    exp = mlflow.get_experiment_by_name(f"/Users/{user}/agents-labs-6-{variant}")
    if exp is None: return None
    tr = mlflow.search_traces(locations=[exp.experiment_id], max_results=40)
    lat, tok, n = [], [], 0
    for i in range(len(tr)):
        t = mlflow.get_trace(tr.iloc[i]["trace_id"])
        root = [s for s in t.data.spans if s.parent_id is None]
        if not root: continue
        n += 1
        lat.append((root[0].end_time_ns - root[0].start_time_ns) / 1e9)
        u = (t.info.token_usage or {}) if hasattr(t.info, "token_usage") else {}
        total = u.get("total_tokens") if isinstance(u, dict) else None
        if total: tok.append(total)
    return {"traces": n,
            "p50_latency_s": sorted(lat)[len(lat)//2] if lat else None,
            "mean_latency_s": sum(lat)/len(lat) if lat else None,
            "mean_tokens": sum(tok)/len(tok) if tok else None}

print(f"\n  {'variant':12} {'traces':7} {'mean latency':14} {'p50 latency':13} {'mean tokens':12}")
print("  " + "-"*62)
for v in ("baseline", "tuned"):
    s = stats(v)
    if not s: continue
    ml = f"{s['mean_latency_s']:.1f}s" if s['mean_latency_s'] else "n/a"
    pl = f"{s['p50_latency_s']:.1f}s" if s['p50_latency_s'] else "n/a"
    mt = f"{s['mean_tokens']:.0f}" if s['mean_tokens'] else "n/a"
    print(f"  {v:12} {s['traces']:<7} {ml:14} {pl:13} {mt:12}")
