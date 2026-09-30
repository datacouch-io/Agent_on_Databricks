"""
Lab 7A — a supervisor delegating to two specialist workers.

Each worker owns one capability and one system prompt. The supervisor decides
who to ask, passes explicit state between them, and combines the results.
Every delegation is its own MLflow span, so the hand-offs are visible.
"""
from __future__ import annotations
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "session-4-genie", "code"))
import lab_common as lc
import mlflow
from mlflow.entities.trace_location import UnityCatalog
from ask_genie import ask as genie_ask

MODEL = os.environ.get("LAB_CHAT_MODEL", lc.DEFAULT_CHAT_MODEL)


def _text(m):
    c = m.content
    if c is None: return ""
    if isinstance(c, str): return c
    return "\n".join(b.get("text", "") for b in c
                     if isinstance(b, dict) and b.get("type") == "text").strip()


# ---------------------------------------------------------------- workers ---
@mlflow.trace(span_type="AGENT")
def analytics_worker(task: str) -> dict:
    """Owns the numbers. Has Genie, has no policy access."""
    g = genie_ask(task)
    return {"worker": "analytics", "task": task,
            "finding": g.get("text"), "sql": g.get("sql"), "rows": g.get("rows")}


@mlflow.trace(span_type="AGENT")
def policy_worker(task: str) -> dict:
    """Owns the written rules. Has the policy index, has no data access."""
    from databricks.ai_search.client import VectorSearchClient
    w = lc.workspace()
    vsc = VectorSearchClient(workspace_url=w.config.host,
                             personal_access_token=lc.bearer_token(), disable_notice=True)
    ix = vsc.get_index(endpoint_name="agents-labs-vs",
                       index_name="agents_labs.retail.support_chunks_idx")
    r = ix.similarity_search(query_text=task,
                            columns=["doc_id", "title", "chunk"],
                            filters={"audience": "customer"}, num_results=3)
    hits = [{"doc_id": x[0], "title": x[1], "text": x[2]}
            for x in (r.get("result", {}).get("data_array", []) or [])]
    ctx = "\n\n".join(f"[{h['doc_id']}] {h['text']}" for h in hits)
    msg = lc.llm_client().chat.completions.create(
        model=MODEL, max_tokens=600,
        messages=[{"role": "system", "content":
                   "You summarise company policy. Answer only from the excerpts. "
                   "Cite document ids. If they do not cover it, say so."},
                  {"role": "user", "content": f"Excerpts:\n{ctx}\n\nTask: {task}"}],
    ).choices[0].message
    return {"worker": "policy", "task": task, "finding": _text(msg),
            "cited": [h["doc_id"] for h in hits]}


WORKERS = {"analytics": analytics_worker, "policy": policy_worker}

TOOLS = [{
    "type": "function",
    "function": {
        "name": "delegate",
        "description": "Delegate one self-contained sub-task to a specialist worker. "
                       "'analytics' can query governed order and customer data. "
                       "'policy' can search written company policy. Neither can do the other's job.",
        "parameters": {
            "type": "object",
            "properties": {
                "worker": {"type": "string", "enum": ["analytics", "policy"]},
                "task": {"type": "string",
                         "description": "A complete, standalone instruction. The worker "
                                        "cannot see the conversation or other workers' findings."},
            },
            "required": ["worker", "task"],
        },
    },
}]

SUPERVISOR = """You are a supervisor coordinating two specialist workers.

You cannot query data or read policy yourself. You must delegate.

Rules:
  * Each delegated task must stand alone. A worker sees only the task string,
    never the conversation and never another worker's findings.
  * If a task depends on something you do not know yet, delegate the first
    question, read the answer, then delegate the second with that fact included.
  * Finish with one combined answer that says which worker produced which part."""


@mlflow.trace(span_type="AGENT")
def run(request: str, max_steps: int = 6) -> str:
    client = lc.llm_client()
    messages = [{"role": "system", "content": SUPERVISOR},
                {"role": "user", "content": request}]
    state: list[dict] = []
    print(f"\n  request: {request}\n")
    for step in range(1, max_steps + 1):
        msg = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS, max_tokens=1100
        ).choices[0].message
        messages.append(msg.model_dump(exclude_none=True))
        if not msg.tool_calls:
            print(f"  step {step}: supervisor combines {len(state)} finding(s)")
            return _text(msg)
        for tc in msg.tool_calls:
            a = json.loads(tc.function.arguments or "{}")
            wk, task = a.get("worker"), a.get("task", "")
            print(f"  step {step}: delegate -> {wk}")
            print(f"           task: {task[:96]}")
            out = WORKERS[wk](task) if wk in WORKERS else {"error": f"no worker {wk}"}
            state.append({"worker": wk, "task": task})
            messages.append({"role": "tool", "tool_call_id": tc.id,
                             "content": json.dumps(out, default=str)[:9000]})
    return "(no answer within max_steps)"


if __name__ == "__main__":
    user = lc.workspace().current_user.me().user_name
    profile = os.environ.get("DATABRICKS_PROFILE")
    mlflow.set_tracking_uri(f"databricks://{profile}" if profile else "databricks")
    os.environ["MLFLOW_TRACING_SQL_WAREHOUSE_ID"] = os.environ["LAB_WAREHOUSE_ID"]
    mlflow.set_experiment(experiment_name=f"/Users/{user}/agents-labs-7a",
                          trace_location=UnityCatalog(catalog_name="agents_labs",
                                                      schema_name="retail"))
    q = sys.argv[1] if len(sys.argv) > 1 else (
        "Our worst-performing region last month — tell me which one, what caused it, "
        "and whether our returns policy could explain a big customer going quiet.")
    print(f"\n  answer:\n{run(q)}\n")
