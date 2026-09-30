"""
Lab 5B — MCP tool discovery, seen through two different identities.

Databricks exposes Unity Catalog functions as MCP tools at
  /api/2.0/mcp/functions/{catalog}/{schema}
The tool list is filtered by the caller's UC grants, so discovery itself is
governed: an identity cannot even SEE a tool it may not run.
"""
from __future__ import annotations
import json, os, sys, urllib.request

HOST = os.environ["LAB_HOST"].rstrip("/")
MCP = f"{HOST}/api/2.0/mcp/functions/agents_labs/retail"


def token_for(profile: str) -> str:
    from databricks.sdk import WorkspaceClient
    w = WorkspaceClient(profile=profile)
    return w.config.authenticate()["Authorization"].removeprefix("Bearer ")


def rpc(tok: str, method: str, params: dict) -> dict:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(MCP, data=body, method="POST", headers={
        "Authorization": f"Bearer {tok}", "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"http_error": e.code, "body": e.read().decode()[:200]}


def probe(profile: str, label: str):
    print(f"\n=== {label} ===")
    tok = token_for(profile)
    lst = rpc(tok, "tools/list", {})
    tools = [t["name"] for t in lst.get("result", {}).get("tools", [])]
    print(f"  tools discovered: {len(tools)}")
    for t in tools:
        print(f"    - {t}")

    for fn, args in [("agents_labs__retail__get_order_summary", {"order_ref": "ORD-1044"}),
                     ("agents_labs__retail__revenue_by_region", {"from_month": "2026-08"})]:
        r = rpc(tok, "tools/call", {"name": fn, "arguments": args})
        short = fn.split("__")[-1]
        if "http_error" in r:
            print(f"  CALL {short:20} -> HTTP {r['http_error']}")
        elif r.get("result", {}).get("isError"):
            msg = json.dumps(r["result"].get("content", ""))[:110]
            print(f"  CALL {short:20} -> DENIED  {msg}")
        elif "error" in r:
            print(f"  CALL {short:20} -> ERROR   {str(r['error'])[:110]}")
        else:
            c = r.get("result", {}).get("content", [{}])[0].get("text", "")
            print(f"  CALL {short:20} -> OK      {c[:100]}")


if __name__ == "__main__":
    probe(os.environ.get("DATABRICKS_PROFILE", "DEFAULT"), "as you — workspace admin")
    probe("agents-restricted", "as the agent's execution identity")
