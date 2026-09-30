"""
Lab 3B — a RAG agent whose every step is auditable in MLflow.

Retrieval, the model call and the tool call are each their own span, so the
trace answers "which chunks produced this sentence" without reading any code.
"""
from __future__ import annotations
import json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))
import lab_common as lc
import mlflow
from mlflow.entities.trace_location import UnityCatalog
from databricks.ai_search.client import VectorSearchClient

INDEX    = "agents_labs.retail.support_chunks_idx"
ENDPOINT = "agents-labs-vs"
CATALOG, SCHEMA = "agents_labs", "retail"
MODEL = os.environ.get("LAB_CHAT_MODEL", lc.DEFAULT_CHAT_MODEL)

SYSTEM = """You are a support agent for an office furniture retailer.

Answer only from the policy excerpts you retrieve and the order facts you look
up. If the excerpts do not cover the question, say so rather than guessing.
Cite the document id of every excerpt you rely on, like [DOC-003]."""


def setup_tracing(experiment_name: str):
    """
    Traces go to Unity Catalog Delta tables, not the legacy workspace store.

    set_tracking_uri("databricks") alone is NOT enough: without a trace_location
    MLflow quietly uses legacy experiment storage, and you only find out when
    you go looking for the tables.
    """
    profile = os.environ.get("DATABRICKS_PROFILE")
    mlflow.set_tracking_uri(f"databricks://{profile}" if profile else "databricks")
    os.environ["MLFLOW_TRACING_SQL_WAREHOUSE_ID"] = os.environ["LAB_WAREHOUSE_ID"]
    mlflow.set_experiment(
        experiment_name=experiment_name,
        trace_location=UnityCatalog(catalog_name=CATALOG, schema_name=SCHEMA),
    )


_vsc = None
def _index():
    global _vsc
    if _vsc is None:
        w = lc.workspace()
        _vsc = VectorSearchClient(workspace_url=w.config.host,
                                  personal_access_token=lc.bearer_token(),
                                  disable_notice=True)
    return _vsc.get_index(endpoint_name=ENDPOINT, index_name=INDEX)


@mlflow.trace(span_type="RETRIEVER")
def search_policy(query: str, audience: str = "customer", k: int = 3) -> list[dict]:
    r = _index().similarity_search(
        query_text=query,
        columns=["chunk_id", "doc_id", "title", "audience", "chunk"],
        filters={"audience": audience}, num_results=k)
    rows = r.get("result", {}).get("data_array", []) or []
    return [{"chunk_id": x[0], "doc_id": x[1], "title": x[2],
             "text": x[4], "score": round(float(x[-1]), 4)} for x in rows]


@mlflow.trace(span_type="TOOL")
def get_order(order_id: str) -> dict:
    import time
    from databricks.sdk.service.sql import StatementState
    w = lc.workspace()
    oid = str(order_id).replace("'", "")
    r = w.statement_execution.execute_statement(
        statement=f"SELECT * FROM agents_labs.retail.get_order_summary('{oid}')",
        warehouse_id=os.environ["LAB_WAREHOUSE_ID"], wait_timeout="50s")
    while r.status.state in (StatementState.PENDING, StatementState.RUNNING):
        time.sleep(1); r = w.statement_execution.get_statement(r.statement_id)
    if r.status.state != StatementState.SUCCEEDED or not (r.result and r.result.data_array):
        return {"error": f"no such order: {oid}"}
    cols = [c.name for c in r.manifest.schema.columns]
    return dict(zip(cols, r.result.data_array[0]))


TOOLS = [
    {"type": "function", "function": {
        "name": "search_policy",
        "description": "Search company policy documents for delivery, returns, warranty or billing rules.",
        "parameters": {"type": "object",
                       "properties": {"query": {"type": "string"}},
                       "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "get_order",
        "description": "Look up one order: status, item, revenue, and the customer's region and tier.",
        "parameters": {"type": "object",
                       "properties": {"order_id": {"type": "string"}},
                       "required": ["order_id"]}}},
]


def _text(msg) -> str:
    c = msg.content
    if c is None: return ""
    if isinstance(c, str): return c
    return "\n".join(b.get("text","") for b in c
                     if isinstance(b, dict) and b.get("type") == "text").strip()


@mlflow.trace(span_type="AGENT")
def answer(question: str, max_steps: int = 5) -> str:
    client = lc.llm_client()
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": question}]
    for _ in range(max_steps):
        msg = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS, max_tokens=900
        ).choices[0].message
        messages.append(msg.model_dump(exclude_none=True))
        if not msg.tool_calls:
            return _text(msg)
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments or "{}")
            if tc.function.name == "search_policy":
                out = search_policy(**args)
            elif tc.function.name == "get_order":
                out = get_order(**args)
            else:
                out = {"error": "unknown tool"}
            messages.append({"role": "tool", "tool_call_id": tc.id,
                             "content": json.dumps(out, default=str)})
    return "(no answer within max_steps)"


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else \
        "My order ORD-1044 hasn't arrived. How long should it take, and what are my options?"
    user = lc.workspace().current_user.me().user_name
    setup_tracing(f"/Users/{user}/agents-labs-3b")
    print(f"\n  question: {q}\n")
    print(f"  answer:\n{answer(q)}\n")
    mlflow.flush_trace_async_logging()
    exp = mlflow.get_experiment_by_name(f"/Users/{user}/agents-labs-3b")
    print(f"  trace_location: {exp.trace_location}")
    traces = mlflow.search_traces(locations=[exp.experiment_id])
    print(f"  traces logged: {len(traces)}")
