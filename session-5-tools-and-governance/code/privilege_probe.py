"""
Lab 5A/5B — what can the agent's execution identity actually do?

Runs the same four statements twice: once as you (workspace admin), once as the
restricted service principal the agent would run as. The difference is the
governance boundary, demonstrated rather than described.
"""
from __future__ import annotations
import os, sys, time

PROBES = [
    ("call the granted function",
     "SELECT * FROM agents_labs.retail.get_order_summary('ORD-1044')"),
    ("read the table the function reads",
     "SELECT order_id, revenue FROM agents_labs.retail.orders LIMIT 2"),
    ("read the customers table",
     "SELECT customer_id, name FROM agents_labs.retail.customers LIMIT 2"),
    ("call a function that was NOT granted",
     "SELECT * FROM agents_labs.retail.revenue_by_region('2026-08') LIMIT 2"),
]


def run_as(profile: str, label: str):
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.service.sql import StatementState
    w = WorkspaceClient(profile=profile)
    wid = os.environ["LAB_WAREHOUSE_ID"]
    who = w.current_user.me()
    print(f"\n=== {label} ===")
    print(f"  identity: {who.display_name or who.user_name}\n")
    for desc, sql in PROBES:
        try:
            r = w.statement_execution.execute_statement(
                statement=sql, warehouse_id=wid, wait_timeout="50s")
            while r.status.state in (StatementState.PENDING, StatementState.RUNNING):
                time.sleep(1); r = w.statement_execution.get_statement(r.statement_id)
            if r.status.state == StatementState.SUCCEEDED:
                n = len(r.result.data_array or []) if r.result else 0
                print(f"  ALLOWED  {desc:42} ({n} row(s))")
            else:
                msg = (r.status.error.message if r.status.error else "failed")
                print(f"  DENIED   {desc:42} {msg.splitlines()[0][:88]}")
        except Exception as e:
            print(f"  DENIED   {desc:42} {str(e).splitlines()[0][:88]}")


if __name__ == "__main__":
    run_as(os.environ.get("DATABRICKS_PROFILE", "DEFAULT"), "as you — workspace admin")
    run_as("agents-restricted", "as the agent's execution identity")
