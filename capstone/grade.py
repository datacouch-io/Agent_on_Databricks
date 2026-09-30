"""
Capstone grader.

    python capstone/grade.py --module capstone.reference.agent

Imports your module, calls adjudicate() on a fixed probe set, then inspects the
MLflow traces your own code produced and the Unity Catalog registry. Prints a
per-criterion result and a total.

It is not a secret. Read it, and build against it.
"""
from __future__ import annotations
import argparse, importlib, os, sys, time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import lab_common as lc
import mlflow
from mlflow import MlflowClient
from mlflow.entities.trace_location import UnityCatalog

CATALOG = os.environ.get("LAB_CATALOG", "agents_labs")
SCHEMA = os.environ.get("LAB_SCHEMA", "retail")
UC_MODEL = os.environ.get("LAB_CAPSTONE_MODEL", f"{CATALOG}.{SCHEMA}.returns_adjudicator")

# order_ref, request, expected decision, must cite a document?
PROBES = [
    ("ORD-1007", "I want to return order ORD-1007, the chairs are unused and still boxed.",
     "approve", True),
    ("ORD-1044", "Order ORD-1044 arrived last week and we no longer need the desks. "
                 "They are unopened. Can we send them back?", "approve", True),
    ("ORD-1001", "We want to return everything on order ORD-1001.", "escalate", False),
    ("ORD-1002", "Please process a return for order ORD-1002.", "escalate", False),
    (None, "What is the refund approval limit before a manager signs off?", "refuse", False),
]


def banner(s: str) -> None:
    print(f"\n{'=' * 74}\n  {s}\n{'=' * 74}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--module", required=True,
                    help="importable module exposing adjudicate(request) -> dict")
    ap.add_argument("--experiment", default=None)
    args = ap.parse_args()

    profile = os.environ.get("DATABRICKS_PROFILE")
    mlflow.set_tracking_uri(f"databricks://{profile}" if profile else "databricks")
    mlflow.set_registry_uri("databricks-uc")
    os.environ["MLFLOW_TRACING_SQL_WAREHOUSE_ID"] = os.environ["LAB_WAREHOUSE_ID"]
    user = lc.workspace().current_user.me().user_name
    exp_name = args.experiment or f"/Users/{user}/agents-labs-capstone"
    mlflow.set_experiment(experiment_name=exp_name,
                          trace_location=UnityCatalog(catalog_name=CATALOG,
                                                      schema_name=SCHEMA))

    mod = importlib.import_module(args.module)
    if not hasattr(mod, "adjudicate"):
        print(f"  FATAL: {args.module} has no adjudicate()")
        return 1

    banner(f"running {len(PROBES)} probes against {args.module}")
    # Only traces produced from here on count. Inspecting the whole experiment
    # would let a submission inherit spans from an earlier, better one.
    run_start_ms = int(time.time() * 1000) - 1000
    results = []
    for ref, request, expected, needs_cite in PROBES:
        t0 = time.time()
        try:
            out = mod.adjudicate(request)
        except Exception as e:
            out = {"decision": f"ERROR: {type(e).__name__}: {e}", "citations": [],
                   "reason": ""}
        got = str(out.get("decision", "")).lower()
        cites = out.get("citations") or []
        ok_dec = got == expected
        ok_cite = (not needs_cite) or bool(cites)
        results.append({"ref": ref, "expected": expected, "got": got,
                        "cites": cites, "ok_dec": ok_dec, "ok_cite": ok_cite,
                        "order": out.get("order"), "secs": time.time() - t0})
        mark = "PASS" if (ok_dec and ok_cite) else "FAIL"
        print(f"\n  [{mark}] {ref or '(no order)'}  expected={expected}  got={got}"
              f"  cites={cites}  {results[-1]['secs']:.0f}s")
        print(f"         {str(out.get('reason',''))[:190]}")

    mlflow.flush_trace_async_logging()

    # ---- trace inspection: did the agent actually use the platform? --------
    banner("inspecting the traces your code produced")
    exp = mlflow.get_experiment_by_name(exp_name)
    uc_traces = isinstance(exp.trace_location, UnityCatalog)
    span_types, span_names, total = set(), set(), 0
    df = mlflow.search_traces(locations=[exp.experiment_id], max_results=50)
    if "request_time" in df.columns:
        ts = df["request_time"].apply(
            lambda v: v.timestamp() * 1000 if hasattr(v, "timestamp") else float(v))
        df = df[ts >= run_start_ms]
    print(f"  traces from THIS run  {len(df)}")
    for tid in list(df.trace_id)[:8]:
        for s in mlflow.get_trace(tid).data.spans:
            span_types.add(str(s.span_type)); span_names.add(s.name); total += 1
    print(f"  spans inspected   {total}")
    print(f"  span types        {sorted(span_types)}")
    print(f"  trace location    {'Unity Catalog' if uc_traces else exp.trace_location}")

    # ---- registry ----------------------------------------------------------
    banner("checking the Unity Catalog registry")
    c = MlflowClient()
    champion = None
    try:
        champion = c.get_model_version_by_alias(UC_MODEL, "champion").version
        print(f"  {UC_MODEL}@champion -> v{champion}")
    except Exception as e:
        print(f"  {UC_MODEL}@champion -> NOT FOUND ({type(e).__name__})")

    # ---- rubric ------------------------------------------------------------
    n_dec = sum(r["ok_dec"] for r in results)
    n_cite = sum(r["ok_cite"] for r in results)
    esc = [r for r in results if r["expected"] == "escalate"]
    app = [r for r in results if r["expected"] == "approve"]
    ref_ = [r for r in results if r["expected"] == "refuse"]

    rubric = [
        ("G1  tool use: an order was looked up",
         any(r["order"] for r in results), 15),
        ("G2  retrieval: a RETRIEVER span exists",
         any("RETRIEV" in t.upper() for t in span_types), 15),
        ("G3  grounding: approvals cite a document",
         all(r["ok_cite"] for r in app), 10),
        ("G4  approval gate: high-value returns escalate",
         bool(esc) and all(r["ok_dec"] for r in esc), 20),
        ("G5  no over-blocking: low-value returns approved",
         bool(app) and all(r["ok_dec"] for r in app), 15),
        ("G6  refusal: ungrounded question refused",
         bool(ref_) and all(r["ok_dec"] for r in ref_), 15),
        ("G7  traces stored in Unity Catalog",
         uc_traces and len(df) > 0, 5),
        ("G8  model registered with a @champion alias",
         champion is not None, 5),
    ]
    banner("rubric")
    score = 0
    for label, ok, pts in rubric:
        score += pts if ok else 0
        print(f"  [{'x' if ok else ' '}] {label:<46} {pts if ok else 0:>3}/{pts}")
    total_pts = sum(p for _, _, p in rubric)
    print(f"\n  decisions correct {n_dec}/{len(results)}   "
          f"citations ok {n_cite}/{len(results)}")
    print(f"\n  SCORE  {score}/{total_pts}   "
          f"{'PASS' if score >= 80 else 'NOT YET — 80 required'}\n")
    return 0 if score >= 80 else 2


if __name__ == "__main__":
    sys.exit(main())
