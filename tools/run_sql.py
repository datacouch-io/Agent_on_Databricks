"""Run SQL against a Databricks SQL warehouse. Usage: run_sql.py <file.sql|-> """
import os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

w = WorkspaceClient(profile=os.environ.get("DATABRICKS_PROFILE", "DEFAULT"))
wid = os.environ["LAB_WAREHOUSE_ID"]
src = sys.stdin.read() if sys.argv[1] == "-" else open(sys.argv[1]).read()

def _split_statements(text: str) -> list[str]:
    """
    Split on semicolons that are NOT inside a single-quoted string literal, and
    drop -- comment lines. A naive text.split(";") corrupts any statement whose
    data contains a semicolon, which policy prose very often does.
    """
    out, buf, in_str = [], [], False
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "'":
            # '' inside a literal is an escaped quote, not a terminator
            if in_str and i + 1 < len(text) and text[i + 1] == "'":
                buf.append("''"); i += 2; continue
            in_str = not in_str
            buf.append(ch)
        elif ch == ";" and not in_str:
            out.append("".join(buf)); buf = []
        else:
            buf.append(ch)
        i += 1
    out.append("".join(buf))

    cleaned = []
    for chunk in out:
        lines = [l for l in chunk.splitlines() if not l.strip().startswith("--")]
        c = "\n".join(lines).strip()
        if c:
            cleaned.append(c)
    return cleaned

stmts = _split_statements(src)
for i, s in enumerate(stmts, 1):
    r = w.statement_execution.execute_statement(statement=s, warehouse_id=wid, wait_timeout="50s")
    while r.status.state in (StatementState.PENDING, StatementState.RUNNING):
        time.sleep(2)
        r = w.statement_execution.get_statement(r.statement_id)
    head = " ".join(s.split())[:72]
    if r.status.state == StatementState.SUCCEEDED:
        n = (r.result.row_count if r.result else 0) or 0
        print(f"  [{i}/{len(stmts)}] ok   {head}" + (f"  ({n} rows)" if n else ""))
        if r.result and r.result.data_array:
            for row in r.result.data_array[:8]:
                print("        ", " | ".join("" if c is None else str(c) for c in row))
    else:
        print(f"  [{i}/{len(stmts)}] FAIL {head}")
        print("        ", (r.status.error.message if r.status.error else "unknown")[:400])
        sys.exit(1)
