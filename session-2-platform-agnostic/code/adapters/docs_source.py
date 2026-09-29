"""Loads the policy documents once, from Unity Catalog, for either retriever."""
from __future__ import annotations
import os, sys, functools
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools"))
import lab_common as lc


@functools.lru_cache(maxsize=1)
def load_docs() -> list[dict]:
    from databricks.sdk.service.sql import StatementState
    import time
    w = lc.workspace()
    wid = os.environ["LAB_WAREHOUSE_ID"]
    r = w.statement_execution.execute_statement(
        statement="SELECT doc_id, title, category, audience, body "
                  "FROM agents_labs.retail.support_docs ORDER BY doc_id",
        warehouse_id=wid, wait_timeout="50s")
    while r.status.state in (StatementState.PENDING, StatementState.RUNNING):
        time.sleep(2); r = w.statement_execution.get_statement(r.statement_id)
    if r.status.state != StatementState.SUCCEEDED:
        raise RuntimeError(r.status.error.message if r.status.error else "query failed")
    return [{"doc_id": a, "title": b, "category": c, "audience": d, "body": e}
            for a, b, c, d, e in (r.result.data_array or [])]
