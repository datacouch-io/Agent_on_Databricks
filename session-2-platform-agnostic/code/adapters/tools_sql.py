"""Tool adapter — live order facts from Unity Catalog via a SQL warehouse."""
from __future__ import annotations
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools"))
import lab_common as lc


class SqlOrderTools:
    def __init__(self):
        self._w = lc.workspace()
        self._wid = os.environ["LAB_WAREHOUSE_ID"]

    def _q(self, sql: str) -> list[dict]:
        from databricks.sdk.service.sql import StatementState
        r = self._w.statement_execution.execute_statement(
            statement=sql, warehouse_id=self._wid, wait_timeout="50s")
        while r.status.state in (StatementState.PENDING, StatementState.RUNNING):
            time.sleep(1); r = self._w.statement_execution.get_statement(r.statement_id)
        if r.status.state != StatementState.SUCCEEDED:
            return [{"error": r.status.error.message if r.status.error else "query failed"}]
        cols = [c.name for c in r.manifest.schema.columns]
        return [dict(zip(cols, row)) for row in (r.result.data_array or [])]

    def schemas(self):
        return [{
            "type": "function",
            "function": {
                "name": "get_order",
                "description": "Look up one order and the customer who placed it: status, "
                               "item, revenue, the customer's region and loyalty tier.",
                "parameters": {
                    "type": "object",
                    "properties": {"order_id": {"type": "string", "description": "e.g. ORD-1044"}},
                    "required": ["order_id"],
                },
            },
        }]

    def call(self, name: str, args: dict) -> dict:
        if name != "get_order":
            return {"error": f"unknown tool {name}"}
        oid = str(args.get("order_id", "")).replace("'", "")
        rows = self._q(
            "SELECT o.order_id, o.status, o.item, o.units, o.revenue, o.order_date, "
            "       c.name AS customer, c.region, c.tier "
            "FROM agents_labs.retail.orders o "
            "JOIN agents_labs.retail.customers c USING (customer_id) "
            f"WHERE o.order_id = '{oid}'")
        return rows[0] if rows else {"error": f"no such order: {oid}"}
