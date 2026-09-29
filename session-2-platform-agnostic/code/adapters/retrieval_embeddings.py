"""
Retrieval adapter B — dense embeddings via a Databricks embeddings endpoint.

Same Retriever interface as the keyword adapter. Lab 2B swaps A for B and
changes nothing else, which is the whole point of the exercise.
"""
from __future__ import annotations
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools"))
import lab_common as lc
from .docs_source import load_docs


def _cos(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


class EmbeddingRetriever:
    name = "databricks-embeddings"

    def __init__(self, model: str | None = None):
        self.model = model or lc.DEFAULT_EMBED_MODEL
        self.docs = load_docs()
        self._client = lc.llm_client()
        texts = [f"{d['title']}. {d['body']}" for d in self.docs]
        self._vecs = self._embed(texts)

    def _embed(self, texts: list[str]) -> list[list[float]]:
        r = self._client.embeddings.create(model=self.model, input=texts)
        return [d.embedding for d in r.data]

    def search(self, query: str, k: int = 3, **filters):
        aud = filters.get("audience")
        qv = self._embed([query])[0]
        out = []
        for d, v in zip(self.docs, self._vecs):
            if aud and d["audience"] != aud:
                continue
            out.append({"doc_id": d["doc_id"], "title": d["title"],
                        "text": d["body"], "score": _cos(qv, v)})
        out.sort(key=lambda r: r["score"], reverse=True)
        return out[:k]
