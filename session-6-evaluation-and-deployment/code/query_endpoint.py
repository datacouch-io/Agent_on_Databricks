"""
Lab 6B step 5 — query the deployed agent over HTTP.

This is the difference deployment makes: no vector-search client, no OpenAI
client, no Databricks SDK in the caller. One authenticated POST. The endpoint
holds the credentials for the model, the index and the UC function, which is
what the `resources` list at log time was for.
"""
from __future__ import annotations
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))
import lab_common as lc
import requests

ENDPOINT = os.environ.get("LAB_AGENT_ENDPOINT",
                          "agents_agents_labs-retail-support_agent")

QUESTIONS = [
    "How long do I have to return a task chair?",
    "What is the refund approval limit before a manager has to sign off?",
]


def ask(question: str) -> tuple[str, float]:
    w = lc.workspace()
    url = f"{w.config.host}/serving-endpoints/{ENDPOINT}/invocations"
    t0 = time.time()
    r = requests.post(
        url,
        headers={"Authorization": f"Bearer {lc.bearer_token()}",
                 "Content-Type": "application/json"},
        json={"input": [{"role": "user", "content": question}]},
        timeout=180,
    )
    r.raise_for_status()
    body = r.json()
    parts = []
    for item in body.get("output", []):
        for c in item.get("content", []) or []:
            if c.get("text"):
                parts.append(c["text"])
    return "\n".join(parts).strip(), time.time() - t0


if __name__ == "__main__":
    print(f"  endpoint  {ENDPOINT}")
    print(f"  host      {lc.workspace().config.host}\n")
    for q in QUESTIONS:
        ans, secs = ask(q)
        print(f"{'=' * 74}\n  Q: {q}\n{'-' * 74}")
        print(f"  ({secs:.1f}s)\n  {ans}\n")
