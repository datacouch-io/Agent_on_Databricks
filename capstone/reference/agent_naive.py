"""
A deliberately weak submission, kept so the rubric can be shown to discriminate.

It asks the model to adjudicate with no order lookup, no retrieval, and no
code-enforced threshold. It is fluent and completely ungrounded.
DO NOT use this as a starting point.
"""
from __future__ import annotations
import os, re, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import lab_common as lc
import mlflow

SYSTEM = ("You adjudicate product return requests for an office furniture retailer. "
          "Decide approve, refuse or escalate. Reply with ONLY JSON: "
          '{"decision": "...", "reason": "...", "citations": []}')


@mlflow.trace(span_type="AGENT")
def adjudicate(request: str) -> dict:
    msg = lc.llm_client().chat.completions.create(
        model=lc.DEFAULT_CHAT_MODEL, max_tokens=500,
        messages=[{"role": "system", "content": SYSTEM},
                  {"role": "user", "content": request}],
    ).choices[0].message
    c = msg.content
    raw = c if isinstance(c, str) else "\n".join(
        b.get("text", "") for b in (c or []) if isinstance(b, dict) and b.get("type") == "text")
    m = re.search(r"\{.*\}", raw or "", re.S)
    try:
        d = json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError:
        d = {}
    return {"decision": d.get("decision", "refuse"), "reason": d.get("reason", ""),
            "citations": d.get("citations") or [], "order": None}
