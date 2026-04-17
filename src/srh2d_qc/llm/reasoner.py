from dataclasses import dataclass
from typing import List

from srh2d_qc.core.model_types import QCResults  # whatever you named it

@dataclass
class LLMRecommendation:
    summary: str
    prioritized_actions: List[str]
    notes: str | None = None


class LLMReasoner:
    def __init__(self, llm_client):
        self.llm = llm_client  # you wire this up however you like

    def analyze_qc(self, qc: QCResults, proposed_actions: List[str]) -> LLMRecommendation:
        """
        Use the LLM to:
        - explain the QC results
        - prioritize actions
        - add any modeling notes
        """
        prompt = self._build_prompt(qc, proposed_actions)
        response = self.llm(prompt)  # placeholder call
        return self._parse_response(response)

    def _build_prompt(self, qc: QCResults, proposed_actions: List[str]) -> str:
        # Minimal, structured, reviewer‑friendly
        return f"""
You are a senior hydraulic model reviewer.

Model QC summary:
- Mesh quality: {qc.mesh_quality.summary if qc.mesh_quality else "None"}
- Material coverage: {qc.material_coverage}
- Timestep stability: {qc.timestep_stability}
- Boundary conditions: {[ (b.bc_name, b.issues) for b in qc.bc_consistency ]}

Proposed actions:
{chr(10).join(f"- {a}" for a in proposed_actions)}

Tasks:
1. Briefly summarize the main issues in 3–5 bullet points.
2. Prioritize the proposed actions (most critical first).
3. Add any additional modeling notes or cautions.

Respond in JSON with keys: summary, prioritized_actions, notes.
"""

    def _parse_response(self, raw: str) -> LLMRecommendation:
        import json
        data = json.loads(raw)
        return LLMRecommendation(
            summary=data.get("summary", ""),
            prioritized_actions=data.get("prioritized_actions", []),
            notes=data.get("notes"),
        )
