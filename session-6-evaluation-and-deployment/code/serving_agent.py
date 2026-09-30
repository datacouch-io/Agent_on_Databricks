"""The agent, packaged for Model Serving as an MLflow ResponsesAgent."""
import os, json
from typing import Any, Generator
import mlflow
from mlflow.pyfunc import ResponsesAgent
from mlflow.types.responses import ResponsesAgentRequest, ResponsesAgentResponse

INDEX = "agents_labs.retail.support_chunks_idx"
ENDPOINT = "agents-labs-vs"
CHAT = os.environ.get("LAB_CHAT_MODEL", "databricks-claude-sonnet-5")
RETRIEVAL_K = int(os.environ.get("LAB_RETRIEVAL_K", "2"))   # tuned in Lab 6B

SYSTEM = ("You are a support agent for an office furniture retailer. Answer only from "
          "the policy excerpts you retrieve. If they do not cover the question, say so. "
          "Cite the document id you relied on, like [DOC-003].")


class SupportAgent(ResponsesAgent):
    def _clients(self):
        from databricks.sdk import WorkspaceClient
        from openai import OpenAI
        from databricks.ai_search.client import VectorSearchClient
        w = WorkspaceClient()
        tok = w.config.authenticate()["Authorization"].removeprefix("Bearer ")
        oa = OpenAI(api_key=tok, base_url=f"{w.config.host}/serving-endpoints")
        vsc = VectorSearchClient(workspace_url=w.config.host,
                                 personal_access_token=tok, disable_notice=True)
        return oa, vsc.get_index(endpoint_name=ENDPOINT, index_name=INDEX)

    @mlflow.trace(span_type="RETRIEVER")
    def _search(self, ix, query: str):
        r = ix.similarity_search(query_text=query,
                                 columns=["chunk_id", "doc_id", "title", "chunk"],
                                 filters={"audience": "customer"},
                                 num_results=RETRIEVAL_K)
        return [{"doc_id": x[1], "title": x[2], "text": x[3]}
                for x in (r.get("result", {}).get("data_array", []) or [])]

    def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:
        oa, ix = self._clients()
        question = request.input[-1].content if request.input else ""
        if isinstance(question, list):
            question = " ".join(p.get("text", "") for p in question if isinstance(p, dict))
        hits = self._search(ix, question)
        ctx = "\n\n".join(f"[{h['doc_id']}] {h['title']}\n{h['text']}" for h in hits)
        msg = oa.chat.completions.create(
            model=CHAT, max_tokens=800,
            messages=[{"role": "system", "content": SYSTEM},
                      {"role": "user", "content": f"Policy excerpts:\n{ctx}\n\nQuestion: {question}"}],
        ).choices[0].message
        c = msg.content
        if isinstance(c, list):
            c = "\n".join(b.get("text", "") for b in c
                          if isinstance(b, dict) and b.get("type") == "text").strip()
        return ResponsesAgentResponse(
            output=[{"type": "message", "role": "assistant", "id": "1",
                     "content": [{"type": "output_text", "text": c or ""}]}])


from mlflow.models import set_model
set_model(SupportAgent())
