"""
Retrieval adapter A — keyword scoring (TF-IDF cosine), pure Python.

No embeddings, no index, no network. This is the adapter Lab 2A uses, chosen
precisely because it is the least "AI" thing that still works: it makes the
Lab 2B swap meaningful, because the replacement shares nothing but the
Retriever interface.
"""
from __future__ import annotations
import math, re
from collections import Counter
from .docs_source import load_docs

_WORD = re.compile(r"[a-z0-9]+")


def _tok(s: str) -> list[str]:
    return _WORD.findall(s.lower())


class KeywordRetriever:
    name = "keyword-tfidf"

    def __init__(self):
        self.docs = load_docs()
        self._tf = [Counter(_tok(f"{d['title']} {d['body']}")) for d in self.docs]
        df = Counter()
        for t in self._tf:
            df.update(set(t))
        n = len(self.docs)
        self._idf = {w: math.log((n + 1) / (c + 0.5)) for w, c in df.items()}

    def _score(self, q: list[str], tf: Counter) -> float:
        if not tf:
            return 0.0
        num = sum(tf[w] * self._idf.get(w, 0.0) for w in q)
        norm = math.sqrt(sum(v * v for v in tf.values())) or 1.0
        return num / norm

    def search(self, query: str, k: int = 3, **filters):
        aud = filters.get("audience")
        q = _tok(query)
        out = []
        for d, tf in zip(self.docs, self._tf):
            if aud and d["audience"] != aud:
                continue
            out.append({"doc_id": d["doc_id"], "title": d["title"],
                        "text": d["body"], "score": self._score(q, tf)})
        out.sort(key=lambda r: r["score"], reverse=True)
        return out[:k]
