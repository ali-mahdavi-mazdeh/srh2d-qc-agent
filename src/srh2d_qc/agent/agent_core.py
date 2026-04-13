from __future__ import annotations
from pathlib import Path
from typing import List

from srh2d_qc.agent.agent_state import AgentState
from srh2d_qc.core.model_types import SRH2DModel
from srh2d_qc.io.model_loader import load_model
from srh2d_qc.qc_engine.runner import run_all_qc


class SRH2D_QCAgent:
    """
    Core logic for the SRH-2D QC Agent.
    This class does NOT use LLMs yet — it is pure deterministic logic.

    Responsibilities:
      - load model into state
      - run QC
      - analyze QC results
      - propose high-level actions
      - maintain agent history
    """

    def __init__(self, model_dir: Path):
        self.state = AgentState(model_dir=model_dir)
        self.state.log(f"Agent initialized for model: {model_dir}")

    # ---------------------------------------------------------
    # 1. Load model
    # ---------------------------------------------------------
    def load(self):
        self.state.log("Loading SRH-2D model...")
        model = load_model(self.state.model_dir)
        self.state.model = model
        self.state.log("Model loaded successfully.")
        return model

    # ---------------------------------------------------------
    # 2. Run QC
    # ---------------------------------------------------------
    def run_qc(self):
        if self.state.model is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        self.state.log("Running QC checks...")
        qc_results = run_all_qc(self.state.model)
        self.state.qc_results = qc_results
        self.state.log("QC completed.")
        return qc_results

    # ---------------------------------------------------------
    # 3. Analyze QC results
    # ---------------------------------------------------------
    def analyze_qc(self) -> List[str]:
        """
        Convert QCResults into a list of human-readable issue summaries.
        These are NOT fixes — just problem descriptions.
        """
        if self.state.qc_results is None:
            raise RuntimeError("QC not run. Call run_qc() first.")

        r = self.state.qc_results
        issues = []

        # Mesh quality issues
        if r.mesh_quality.max_aspect_ratio > 10:
            issues.append("High aspect ratio elements detected.")

        if r.mesh_quality.min_angle < 20:
            issues.append("Very small angles detected in mesh.")

        # Material issues
        if r.material_coverage.missing_material_ids:
            issues.append(
                f"Missing material IDs: {r.material_coverage.missing_material_ids}"
            )

        # BC issues
        for bc in r.bc_consistency:
            if bc.issues:
                issues.append(f"Boundary condition '{bc.bc_name}' has issues.")

        # Timestep issues
        if r.timestep_stability.num_violations > 0:
            issues.append(
                f"Timestep too large: {r.timestep_stability.num_violations} violating elements."
            )

        # Save to state
        for issue in issues:
            self.state.add_issue(issue)

        self.state.log(f"Detected {len(issues)} issues.")
        return issues

    # ---------------------------------------------------------
    # 4. Propose high-level actions (not fixes yet)
    # ---------------------------------------------------------
    def propose_actions(self) -> List[str]:
        """
        Convert issues into high-level actions the agent *could* take.
        These are not applied yet — just proposed.
        """
        actions = []

        for issue in self.state.detected_issues:
            if "Missing material IDs" in issue:
                actions.append("Assign all unassigned elements to material 1.")

            if "Timestep too large" in issue:
                actions.append("Reduce dt to recommended geometric dt.")

            if "Boundary condition" in issue:
                actions.append("Inspect and correct BC node assignments.")

            if "aspect ratio" in issue:
                actions.append("Refine or smooth mesh in problematic regions.")

        for action in actions:
            self.state.add_action(action)

        self.state.log(f"Proposed {len(actions)} actions.")
        return actions
