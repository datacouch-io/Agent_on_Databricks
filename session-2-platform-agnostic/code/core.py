"""
Lab 2A/2B — the portable core.

This file knows nothing about Databricks, about which model it is talking to,
or about how documents are retrieved. It depends only on the three Protocols
below. That is what makes the Lab 2B adapter swap a one-line change.
"""
from __future__ import annotations
import json
from typing import Protocol, Any, Iterable


class Retriever(Protocol):
    def search(self, query: str, k: int = 3, **filters: Any) -> list[dict]:
        """Return [{'doc_id','title','text','score'}, ...] most relevant first."""
        ...
    @property
    def name(self) -> str: ...


class ToolBox(Protocol):
    def schemas(self) -> list[dict]:
        """OpenAI-style tool schemas."""
        ...
    def call(self, name: str, args: dict) -> dict: ...


class Chat(Protocol):
    def complete(self, messages: list[dict], tools: list[dict] | None) -> Any: ...
    @property
    def model(self) -> str: ...


SYSTEM = """You are a customer support agent for an office furniture retailer.

You have two sources and you usually need both:
  * search_policy  - the company's written policies (delivery times, returns, warranty)
  * the order tools - live facts about a specific order and the customer who placed it

Never state a policy you have not retrieved, and never state an order fact you
have not looked up. If answering needs both, use both before you answer.
Cite the policy document id you relied on, like [DOC-003]."""

MAX_STEPS = 6


def text_of(message) -> str:
    """Claude endpoints return content as a list of typed blocks, not a string."""
    c = getattr(message, "content", None)
    if c is None:
        return ""
    if isinstance(c, str):
        return c
    out = []
    for b in c:
        b = b if isinstance(b, dict) else getattr(b, "__dict__", {})
        if b.get("type") == "text" and b.get("text"):
            out.append(b["text"])
    return "\n".join(out).strip()


def run(question: str, *, chat: Chat, retriever: Retriever, tools: ToolBox,
        verbose: bool = True) -> dict:
    """One turn of the agent. Returns the answer plus which sources it touched."""
    schemas = [{
        "type": "function",
        "function": {
            "name": "search_policy",
            "description": "Search the company policy documents. Use for anything about "
                           "delivery times, returns, refunds, warranty or billing rules.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "audience": {"type": "string",
                                 "description": "customer or agent_only. Omit for customer-facing."},
                },
                "required": ["query"],
            },
        },
    }] + tools.schemas()

    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": question}]
    used = {"retrieval": [], "tools": []}

    for step in range(1, MAX_STEPS + 1):
        msg = chat.complete(messages, schemas)
        messages.append(msg.model_dump(exclude_none=True))

        if not msg.tool_calls:
            if verbose:
                print(f"  step {step}: answer")
            return {"answer": text_of(msg), "used": used,
                    "retriever": retriever.name, "model": chat.model}

        for tc in msg.tool_calls:
            name, args = tc.function.name, json.loads(tc.function.arguments or "{}")
            if name == "search_policy":
                hits = retriever.search(args["query"], k=3,
                                        audience=args.get("audience", "customer"))
                used["retrieval"] += [h["doc_id"] for h in hits]
                result = {"results": [{"doc_id": h["doc_id"], "title": h["title"],
                                       "text": h["text"], "score": round(h["score"], 4)}
                                      for h in hits]}
                if verbose:
                    print(f"  step {step}: search_policy({args['query']!r}) "
                          f"-> {[h['doc_id'] for h in hits]}")
            else:
                result = tools.call(name, args)
                used["tools"].append(name)
                if verbose:
                    print(f"  step {step}: {name}({json.dumps(args)}) -> "
                          f"{json.dumps(result)[:110]}")
            messages.append({"role": "tool", "tool_call_id": tc.id,
                             "content": json.dumps(result, default=str)})

    return {"answer": "(no answer within MAX_STEPS)", "used": used,
            "retriever": retriever.name, "model": chat.model}
