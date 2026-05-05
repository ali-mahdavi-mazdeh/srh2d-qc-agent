from __future__ import annotations
from pathlib import Path
from typing import List

from srh2d_qc.agent.agent_state import AgentState
from srh2d_qc.agent.agent_tools import ModelTools
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

    def __init__(self, model_dir: Path, llm_reasoner=None):
        self.state = AgentState(model_dir=model_dir)
        self.llm_reasoner = llm_reasoner
        self.state.log(f"Agent initialized for model: {model_dir}")

    # ---------------------------------------------------------
    # 1. Load model
    # ---------------------------------------------------------
    def load(self):
        self.state.log("Loading SRH-2D model...")
        model = load_model(self.state.model_dir)
        self.state.model = model
        self.model = model
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
        self.qc_results = qc_results
        self.tools = ModelTools(self.model, self.qc_results)
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
        mq = r.mesh_quality.summary

        if mq.max_aspect_ratio > 10:
            issues.append("High aspect ratio elements detected.")

        if mq.min_angle < 20:
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
        Convert QC results into high-level actions the agent *could* take.
        These are not applied yet — just proposed.
        """
        actions = []
        qc = self.state.qc_results

        # ------------------------------------------------------------
        # Material coverage
        # ------------------------------------------------------------
        if qc.material_coverage.missing_material_ids:
            actions.append("Assign default material to elements with missing material IDs.")

        # ------------------------------------------------------------
        # Timestep stability
        # ------------------------------------------------------------
        if qc.timestep_stability.num_violations > 0:
            actions.append("Reduce dt to recommended geometric dt.")

        # ------------------------------------------------------------
        # Boundary condition consistency
        # ------------------------------------------------------------
        for bc in qc.bc_consistency:
            if bc.issues:
                actions.append(f"Inspect and correct BC node assignments for BC '{bc.bc_name}'.")

        # ------------------------------------------------------------
        # Mesh quality
        # ------------------------------------------------------------
        mq = qc.mesh_quality
        if mq and mq.summary.max_aspect_ratio > 10:  # threshold can be tuned
            actions.append("Refine or smooth mesh in high aspect-ratio regions.")

        # ------------------------------------------------------------
        # Log and store actions
        # ------------------------------------------------------------
        for action in actions:
            self.state.add_action(action)

        self.state.log(f"Proposed {len(actions)} actions.")
        return actions

    def llm_analyze(self):
        """
        Run LLM reasoning on QC results + proposed actions.
        """
        if self.llm_reasoner is None:
            self.state.log("No LLM reasoner attached; skipping LLM analysis.")
            return None

        qc = self.state.qc_results
        actions = self.propose_actions()

        rec = self.llm_reasoner.analyze_qc(qc, actions)
        self.state.log("LLM analysis completed.")
        self.state.llm_summary = rec.summary
        self.state.llm_prioritized_actions = rec.prioritized_actions
        self.state.llm_notes = rec.notes
        return rec

    def apply_fixes(self):
        """
        Apply simple deterministic fixes:
        - Assign default material to elements with missing material IDs
        """
        from srh2d_qc.utils.material_utils import fix_missing_materials

        applied = False

        # Fix missing materials
        if self.state.qc_results.material_coverage.missing_material_ids:
            if fix_missing_materials(self.state.model):
                self.state.log("Assigned default material to missing elements.")
                applied = True

        return applied
