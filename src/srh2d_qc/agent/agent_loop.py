from __future__ import annotations
from pathlib import Path
from typing import Dict, Any

from .agent_core import SRH2D_QCAgent


def run_agent_once(model_dir: Path) -> Dict[str, Any]:
    """
    Run a single deterministic agent cycle:
      1. Load model
      2. Run QC
      3. Analyze QC results
      4. Propose high-level actions

    This is the "outer loop" that a future LLM agent will call.
    """

    agent = SRH2D_QCAgent(model_dir)

    # 1. Load model
    model = agent.load()

    # 2. Run QC
    qc_results = agent.run_qc()

    # 3. Analyze QC
    issues = agent.analyze_qc()

    # 4. Propose actions
    actions = agent.propose_actions()

    # Return a structured result
    return {
        "model": model,
        "qc_results": qc_results,
        "issues": issues,
        "proposed_actions": actions,
        "history": agent.state.history,
    }
