"""
Capstone reference solution — a returns adjudication agent.

Exposes the one function the grader calls:

    adjudicate(request: str) -> dict

This is a reference, not a model answer. It satisfies every graded requirement
in the brief and nothing more. Yours may look quite different.
"""
from __future__ import annotations
import json, os, re, sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "tools"))
import lab_common as lc
import mlflow

CATALOG = os.environ.get("LAB_CATALOG", "agents_labs")
SCHEMA = os.environ.get("LAB_SCHEMA", "retail")
INDEX = f"{CATALOG}.{SCHEMA}.support_chunks_idx"
VS_ENDPOINT = os.environ.get("LAB_VS_ENDPOINT", "agents-labs-vs")
MODEL = os.environ.get("LAB_CHAT_MODEL", lc.DEFAULT_CHAT_MODEL)

# Above this refund value a human signs off. The brief fixes this number so the
# grader can probe both sides of it.
ESCALATION_THRESHOLD = 5000.0

SYSTEM = f"""You adjudicate product return requests for an office furniture retailer.

Process, in order:
  1. If the request names an order reference, call lookup_order for it.
  2. Call search_policy to find the written rules that apply.
  3. Decide.

Decide exactly one of:
  approve   — the policy clearly permits the return
  refuse    — the policy clearly forbids it, OR the policy does not cover the
              question at all. Never guess a rule that is not in the excerpts.
  escalate  — the refund value is {ESCALATION_THRESHOLD:.0f} GBP or more. A human
              must sign off regardless of how clear the policy is.

Reply with ONLY a JSON object, no prose around it:
  {{"decision": "...", "reason": "...", "citations": ["DOC-001"]}}

`reason` is one or two sentences. `citations` lists the document ids you relied
on, and must be empty if you relied on none."""


@mlflow.trace(span_type="TOOL")
def lookup_order(order_ref: str) -> dict:
    """The governed UC function from Lab 5A is the tool."""
    from databricks.sdk.service.sql import StatementParameterListItem
    w = lc.workspace()
    r = w.statement_execution.execute_statement(
        warehouse_id=os.environ["LAB_WAREHOUSE_ID"],
        statement=f"SELECT * FROM {CATALOG}.{SCHEMA}.get_order_summary(:ref)",
        # a plain dict is rejected here: the SDK calls .as_dict() on each item
        parameters=[StatementParameterListItem(name="ref", value=order_ref)],
        wait_timeout="50s",
    )
    cols = [c.name for c in r.manifest.schema.columns]
    rows = (r.result.data_array or []) if r.result else []
    if not rows:
        return {"found": False, "order_ref": order_ref}
    rec = dict(zip(cols, rows[0]))
    rec["found"] = True
    rec["refund_value_gbp"] = float(rec.get("revenue") or 0)
    return rec


@mlflow.trace(span_type="RETRIEVER")
def search_policy(query: str, k: int = 3) -> list[dict]:
    from databricks.ai_search.client import VectorSearchClient
    w = lc.workspace()
    vsc = VectorSearchClient(workspace_url=w.config.host,
                             personal_access_token=lc.bearer_token(),
                             disable_notice=True)
    ix = vsc.get_index(endpoint_name=VS_ENDPOINT, index_name=INDEX)
    r = ix.similarity_search(query_text=query,
                             columns=["doc_id", "title", "chunk"],
                             filters={"audience": "customer"},
                             num_results=k)
    return [{"doc_id": x[0], "title": x[1], "text": x[2]}
            for x in (r.get("result", {}).get("data_array", []) or [])]


TOOLS = [
    {"type": "function", "function": {
        "name": "lookup_order",
        "description": "Look up one order by its reference: status, item, units, "
                       "refund value in GBP, region and the customer's loyalty tier.",
        "parameters": {"type": "object",
                       "properties": {"order_ref": {"type": "string",
                                      "description": "e.g. ORD-1007"}},
                       "required": ["order_ref"]}}},
    {"type": "function", "function": {
        "name": "search_policy",
        "description": "Search the customer-facing policy documents. Returns "
                       "excerpts with their document ids.",
        "parameters": {"type": "object",
                       "properties": {"query": {"type": "string"}},
                       "required": ["query"]}}},
]
IMPL = {"lookup_order": lambda a: lookup_order(a["order_ref"]),
        "search_policy": lambda a: search_policy(a["query"])}


def _text(m) -> str:
    c = m.content
    if c is None:
        return ""
    if isinstance(c, str):
        return c
    return "\n".join(b.get("text", "") for b in c
                     if isinstance(b, dict) and b.get("type") == "text").strip()


def _parse(raw: str) -> dict:
    """The model is asked for bare JSON. It sometimes fences it anyway."""
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return {"decision": "refuse", "reason": f"unparseable: {raw[:120]}",
                "citations": []}
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return {"decision": "refuse", "reason": f"unparseable: {raw[:120]}",
                "citations": []}
    d.setdefault("citations", [])
    d.setdefault("reason", "")
    return d


@mlflow.trace(span_type="AGENT")
def adjudicate(request: str, max_steps: int = 5) -> dict:
    """The entry point the grader calls."""
    client = lc.llm_client()
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": request}]
    order: dict | None = None

    for _ in range(max_steps):
        msg = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS, max_tokens=900
        ).choices[0].message
        messages.append(msg.model_dump(exclude_none=True))
        if not msg.tool_calls:
            out = _parse(_text(msg))
            out["order"] = order
            # The threshold is policy, not a suggestion to the model. Enforce it
            # in code so a prompt-injection or a sloppy completion cannot bypass
            # the human gate.
            if order and order.get("refund_value_gbp", 0) >= ESCALATION_THRESHOLD:
                if out.get("decision") != "escalate":
                    out["reason"] = (f"Refund value GBP {order['refund_value_gbp']:.2f} "
                                     f"is at or above the GBP {ESCALATION_THRESHOLD:.0f} "
                                     f"sign-off threshold. " + out.get("reason", ""))
                out["decision"] = "escalate"
            return out
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments or "{}")
            res = IMPL[tc.function.name](args)
            if tc.function.name == "lookup_order" and res.get("found"):
                order = res
            messages.append({"role": "tool", "tool_call_id": tc.id,
                             "content": json.dumps(res, default=str)[:6000]})

    return {"decision": "refuse", "reason": "no decision within step budget",
            "citations": [], "order": order}
