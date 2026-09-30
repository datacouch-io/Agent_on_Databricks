"""Lab 3A — prove the index retrieves the right chunks, before building on it."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))
import lab_common as lc
from databricks.ai_search.client import VectorSearchClient

INDEX = "agents_labs.retail.support_chunks_idx"
ENDPOINT = "agents-labs-vs"

CASES = [
    ("How long does delivery to the Nordics take?",        None,          "DOC-003"),
    ("Can I send it back after six weeks?",                 None,          "DOC-001"),
    ("How much can I refund without asking anyone?",        "agent_only",  "DOC-006"),
    ("What is covered if the chair frame breaks?",          None,          "DOC-004"),
]

def main():
    w = lc.workspace()
    vsc = VectorSearchClient(workspace_url=w.config.host,
                             personal_access_token=lc.bearer_token(), disable_notice=True)
    ix = vsc.get_index(endpoint_name=ENDPOINT, index_name=INDEX)

    passed = 0
    for q, audience, expect in CASES:
        flt = {"audience": audience} if audience else {"audience": "customer"}
        r = ix.similarity_search(
            query_text=q,
            columns=["chunk_id", "doc_id", "title", "audience", "chunk"],
            filters=flt, num_results=3)
        rows = r.get("result", {}).get("data_array", []) or []
        got = [row[1] for row in rows]
        ok = bool(got) and got[0] == expect
        passed += ok
        print(f"\n  q: {q}")
        print(f"     filter={flt}  expect top-1={expect}  {'PASS' if ok else 'FAIL'}")
        for row in rows:
            print(f"       {row[0]:12} {row[1]}  {row[3]:10} score={row[-1]:.4f}  {row[2][:44]}")
    print(f"\n  {passed}/{len(CASES)} retrieval checks passed")

if __name__ == "__main__":
    main()
