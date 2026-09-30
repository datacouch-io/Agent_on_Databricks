"""
Lab 4B — an agent that calls a Genie space as one tool among several.

The point: Genie stops being a destination the user visits and becomes a
capability the agent invokes, mid-conversation, alongside document retrieval.
"""
from __future__ import annotations
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))
sys.path.insert(0, os.path.dirname(__file__))
import lab_common as lc
from ask_genie import ask as genie_ask

MODEL = os.environ.get("LAB_CHAT_MODEL", lc.DEFAULT_CHAT_MODEL)

SYSTEM = """You are an analyst assistant for an office furniture retailer.

Tools:
  * ask_genie      - natural-language questions over the governed orders and
                     customers tables. Use it for anything numeric: revenue,
                     counts, trends, comparisons, breakdowns.
  * search_policy  - the company's written policies.

Use ask_genie for numbers. Never invent a figure. When you quote a number,
say which question you asked Genie to get it."""


def search_policy(query: str, audience: str = "customer", k: int = 3) -> list[dict]:
    from databricks.ai_search.client import VectorSearchClient
    w = lc.workspace()
    vsc = VectorSearchClient(workspace_url=w.config.host,
                             personal_access_token=lc.bearer_token(), disable_notice=True)
    ix = vsc.get_index(endpoint_name="agents-labs-vs",
                       index_name="agents_labs.retail.support_chunks_idx")
    r = ix.similarity_search(query_text=query,
                            columns=["chunk_id", "doc_id", "title", "chunk"],
                            filters={"audience": audience}, num_results=k)
    return [{"doc_id": x[1], "title": x[2], "text": x[3]}
            for x in (r.get("result", {}).get("data_array", []) or [])]


TOOLS = [
    {"type": "function", "function": {
        "name": "ask_genie",
        "description": "Ask a natural-language analytics question over governed retail "
                       "orders and customers. Returns an answer plus the SQL Genie ran.",
        "parameters": {"type": "object",
                       "properties": {"question": {"type": "string"}},
                       "required": ["question"]}}},
    {"type": "function", "function": {
        "name": "search_policy",
        "description": "Search company policy documents.",
        "parameters": {"type": "object",
                       "properties": {"query": {"type": "string"}},
                       "required": ["query"]}}},
]


def _text(m):
    c = m.content
    if c is None: return ""
    if isinstance(c, str): return c
    return "\n".join(b.get("text","") for b in c
                     if isinstance(b, dict) and b.get("type") == "text").strip()


def run(question: str, max_steps: int = 5) -> str:
    client = lc.llm_client()
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": question}]
    print(f"\n  user: {question}\n")
    for step in range(1, max_steps + 1):
        msg = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS, max_tokens=1000
        ).choices[0].message
        messages.append(msg.model_dump(exclude_none=True))
        if not msg.tool_calls:
            print(f"  step {step}: answer")
            return _text(msg)
        for tc in msg.tool_calls:
            name = tc.function.name
            args = json.loads(tc.function.arguments or "{}")
            if name == "ask_genie":
                print(f"  step {step}: ask_genie({args['question']!r})")
                g = genie_ask(args["question"])
                out = {"answer": g.get("text"), "sql": g.get("sql"), "rows": g.get("rows")}
                n = len(g.get("rows") or [])
                print(f"           -> genie returned {n} row(s) and its SQL")
            else:
                print(f"  step {step}: search_policy({args.get('query')!r})")
                out = search_policy(**args)
            messages.append({"role": "tool", "tool_call_id": tc.id,
                             "content": json.dumps(out, default=str)[:12000]})
    return "(no answer within max_steps)"


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else (
        "Our Nordics numbers look bad this month. What happened, and is there any "
        "policy reason a big seating customer might have stopped ordering?")
    print(f"\n  answer:\n{run(q)}\n")
