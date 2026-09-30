"""The adjudicator packaged as a ResponsesAgent, so it can be registered in UC."""
import json, os, sys
import mlflow
from mlflow.pyfunc import ResponsesAgent
from mlflow.types.responses import ResponsesAgentRequest, ResponsesAgentResponse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class Adjudicator(ResponsesAgent):
    def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:
        from agent import adjudicate
        q = ""
        for m in request.input:
            m = m if isinstance(m, dict) else m.__dict__
            if m.get("role") == "user":
                q = m.get("content") or ""
        out = adjudicate(q)
        return ResponsesAgentResponse(output=[{
            "type": "message", "role": "assistant", "id": "adj-1",
            "content": [{"type": "output_text",
                         "text": json.dumps(out, default=str)}]}])


mlflow.models.set_model(Adjudicator())
