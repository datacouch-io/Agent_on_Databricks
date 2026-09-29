"""Lab 2B — show the two retrieval adapters side by side on the same queries."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from adapters.retrieval_keyword import KeywordRetriever
from adapters.retrieval_embeddings import EmbeddingRetriever

QUERIES = [
    ("standing desk delivery time", "customer"),
    ("can I send it back after six weeks", "customer"),
    ("how much can I refund without asking anyone", "agent_only"),
]

if __name__ == "__main__":
    a, b = KeywordRetriever(), EmbeddingRetriever()
    for q, aud in QUERIES:
        print(f"\nquery: {q!r}   (audience={aud})")
        for r in (a, b):
            hits = r.search(q, k=3, audience=aud)
            shown = ", ".join(f"{h['doc_id']}({h['score']:.3f})" for h in hits)
            print(f"  {r.name:24} {shown}")
