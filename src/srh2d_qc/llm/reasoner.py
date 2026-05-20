from dataclasses import dataclass
from typing import List

from srh2d_qc.core.model_types import QCResults  # whatever you named it

@dataclass
class LLMRecommendation:
    summary: str
    prioritized_actions: List[str]
    notes: str | None = None


from openai import OpenAI
import os
import json

class LLMReasoner:
    def __init__(self):
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY not set in environment.")
        self.client = OpenAI(api_key=key)

    def analyze_qc(self, qc, proposed_actions):
        prompt = self._build_prompt(qc, proposed_actions)

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        raw = response.choices[0].message.content
        # print("RAW LLM OUTPUT:\n", raw)
        return self._parse_response(raw)

    def _build_prompt(self, qc, proposed_actions):
        return f"""
You are a senior hydraulic model reviewer.

QC Summary:
- Mesh quality: {qc.mesh_quality.summary if qc.mesh_quality else "None"}
- Material coverage: {qc.material_coverage}
- Timestep stability: {qc.timestep_stability}
- Boundary conditions: {[ (b.bc_name, b.issues) for b in qc.bc_consistency ]}

Proposed actions:
{chr(10).join(f"- {a}" for a in proposed_actions)}

Tasks:
1. Summarize the main issues in 3–5 bullet points.
2. Prioritize the proposed actions.
3. Add any modeling notes.

Respond in JSON with keys: summary, prioritized_actions, notes.
Do NOT use Markdown code fences.

"""

    def _parse_response(self, raw):
        # Remove Markdown code fences if present
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```", 1)[1]
            if "```" in raw:
                raw = raw.split("```", 1)[0]
            raw = raw.strip()

        # Try direct JSON
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Fallback: extract JSON object from text
            import re
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if not match:
                raise ValueError(f"LLM did not return valid JSON:\n{raw}")
            data = json.loads(match.group(0))

        # Convert dict → LLMRecommendation
        return LLMRecommendation(
            summary=data.get("summary"),
            prioritized_actions=data.get("prioritized_actions", []),
            notes=data.get("notes")
        )
