"""Chat adapter: any OpenAI-compatible endpoint. Here, Databricks serving."""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools"))
import lab_common as lc


class DatabricksChat:
    def __init__(self, model: str | None = None):
        self._model = model or lc.DEFAULT_CHAT_MODEL
        self._client = lc.llm_client()

    @property
    def model(self) -> str:
        return self._model

    def complete(self, messages, tools):
        return self._client.chat.completions.create(
            model=self._model, messages=messages, tools=tools, max_tokens=900
        ).choices[0].message
