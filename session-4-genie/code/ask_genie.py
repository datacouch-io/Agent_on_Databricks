"""
Lab 4A/4B — ask a Genie space a question and read the governed answer.

Genie returns an ANSWER plus the SQL it ran. Both matter: the SQL is the audit
trail, and it is the thing to check when an answer looks surprising.
"""
from __future__ import annotations
import os, sys, time, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))
import lab_common as lc

SPACE = os.environ.get("LAB_GENIE_SPACE", "")


def ask(question: str, space_id: str = "", timeout: int = 180) -> dict:
    """Start a conversation, poll to completion, return text + SQL + rows."""
    from databricks.sdk.service.dashboards import MessageStatus
    w = lc.workspace()
    sid = space_id or SPACE
    if not sid:
        raise SystemExit("set LAB_GENIE_SPACE to your Genie space id")

    conv = w.genie.start_conversation(space_id=sid, content=question)
    cid, mid = conv.conversation_id, conv.message_id

    for _ in range(timeout):
        m = w.genie.get_message(space_id=sid, conversation_id=cid, message_id=mid)
        if m.status in (MessageStatus.COMPLETED, MessageStatus.FAILED,
                        MessageStatus.QUERY_RESULT_EXPIRED):
            break
        time.sleep(1)

    out = {"question": question, "status": str(m.status), "text": None,
           "sql": None, "rows": None}

    for att in (m.attachments or []):
        if getattr(att, "text", None) and att.text.content:
            out["text"] = att.text.content
        q = getattr(att, "query", None)
        if q is not None:
            out["sql"] = q.query
            out["description"] = q.description
            try:
                res = w.genie.get_message_attachment_query_result(
                    space_id=sid, conversation_id=cid, message_id=mid,
                    attachment_id=att.attachment_id)
                sr = res.statement_response
                cols = [c.name for c in sr.manifest.schema.columns]
                out["rows"] = [dict(zip(cols, r)) for r in (sr.result.data_array or [])]
            except Exception as e:
                out["rows"] = [{"error": str(e)[:160]}]
    return out


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else \
        "Which region had the biggest drop in revenue from August to September 2026?"
    r = ask(q)
    print(f"\n  question: {r['question']}")
    print(f"  status  : {r['status']}\n")
    if r.get("sql"):
        print("  SQL Genie generated:")
        for line in r["sql"].strip().splitlines():
            print("    " + line)
        print()
    if r.get("rows"):
        print("  rows:")
        for row in r["rows"][:10]:
            print("    " + json.dumps(row, default=str))
        print()
    if r.get("text"):
        print(f"  answer:\n{r['text']}\n")
