"""
Lab 2A / 2B runner.

  python run.py --retrieval keyword      # Lab 2A
  python run.py --retrieval embeddings   # Lab 2B — the only thing that changes
"""
from __future__ import annotations
import argparse, json, sys, os
sys.path.insert(0, os.path.dirname(__file__))

from core import run
from adapters.llm_databricks import DatabricksChat
from adapters.tools_sql import SqlOrderTools
from adapters.retrieval_keyword import KeywordRetriever
from adapters.retrieval_embeddings import EmbeddingRetriever

RETRIEVERS = {"keyword": KeywordRetriever, "embeddings": EmbeddingRetriever}

# Neither source answers this alone:
#   the ORDER says who placed it -> which region
#   the POLICY says the delivery window for that region
DEFAULT_Q = ("My order ORD-1044 hasn't arrived yet. How long should a standing desk "
             "take to reach me, and is that normal?")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--retrieval", choices=list(RETRIEVERS), default="keyword")
    ap.add_argument("--question", default=DEFAULT_Q)
    a = ap.parse_args()

    retriever = RETRIEVERS[a.retrieval]()
    chat = DatabricksChat()
    tools = SqlOrderTools()

    print(f"\n=== retrieval adapter: {retriever.name} | model: {chat.model} ===")
    print(f"  question: {a.question}\n")
    out = run(a.question, chat=chat, retriever=retriever, tools=tools)
    print(f"\n  sources used: retrieval={sorted(set(out['used']['retrieval']))} "
          f"tools={sorted(set(out['used']['tools']))}")
    print(f"\n  answer:\n{out['answer']}\n")
