from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from srh2d_qc.core.model_types import SRH2DModel
from srh2d_qc.core.model_types import QCResults


@dataclass
class AgentState:
    """
    Persistent state for the SRH-2D QC agent.

    This is the single source of truth the agent reads/writes as it:
      - loads a model
      - runs QC
      - analyzes issues
      - proposes and applies fixes
      - re-runs QC
    """

    model_dir: Path
    model: Optional[SRH2DModel] = None
    qc_results: Optional[QCResults] = None

    # High-level issue summaries (human-readable)
    detected_issues: List[str] = field(default_factory=list)

    # Candidate actions the agent is considering (strings for now)
    pending_actions: List[str] = field(default_factory=list)

    # Simple text history of what the agent has done/decided
    history: List[str] = field(default_factory=list)

    def log(self, message: str) -> None:
        """Append a message to the agent's history."""
        self.history.append(message)

    def add_issue(self, issue: str) -> None:
        """Record a detected issue."""
        if issue not in self.detected_issues:
            self.detected_issues.append(issue)

    def add_action(self, action: str) -> None:
        """Record a proposed action."""
        self.pending_actions.append(action)

    def clear_actions(self) -> None:
        """Clear pending actions after they are executed or discarded."""
        self.pending_actions.clear()
