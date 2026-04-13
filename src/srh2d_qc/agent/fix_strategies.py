from __future__ import annotations
from pathlib import Path
from typing import List

from srh2d_qc.agent.agent_state import AgentState


# ---------------------------------------------------------
# Fix 1 — Assign all unassigned elements to material 1
# ---------------------------------------------------------
def fix_assign_unassigned_to_material_1(state: AgentState) -> str:
    """
    Assign all elements with material -1 to material 1.
    This is a safe default when the model has only one material.
    """

    mesh = state.model.mesh
    mat_ids = mesh.material_ids

    # Count before
    before = mat_ids.count(-1)

    if before == 0:
        return "No unassigned elements found. No changes made."

    # Assign material 1
    mesh.material_ids = [1 if mid == -1 else mid for mid in mat_ids]

    after = mesh.material_ids.count(-1)

    msg = (
        f"Assigned {before} previously unassigned elements to material 1. "
        f"Remaining unassigned: {after}."
    )

    state.log(msg)
    return msg


# ---------------------------------------------------------
# Fix 2 — Reduce dt to recommended geometric dt
# ---------------------------------------------------------
def fix_reduce_dt(state: AgentState) -> str:
    """
    Reduce dt in the .srhhydro file to the recommended geometric dt
    computed by the QC engine.
    """

    if state.qc_results is None:
        raise RuntimeError("QC must be run before applying dt fix.")

    ts = state.qc_results.timestep_stability
    recommended = ts.median_dt_geom

    hydro = state.model.run_config
    old_dt = hydro.dt

    # Apply fix
    hydro.dt = recommended

    msg = (
        f"Reduced dt from {old_dt:.4f} s to recommended geometric dt "
        f"{recommended:.4f} s."
    )

    state.log(msg)
    return msg


# ---------------------------------------------------------
# Fix dispatcher — maps action strings to functions
# ---------------------------------------------------------
ACTION_MAP = {
    "Assign all unassigned elements to material 1.": fix_assign_unassigned_to_material_1,
    "Reduce dt to recommended geometric dt.": fix_reduce_dt,
}


def apply_action(state: AgentState, action: str) -> str:
    """
    Apply a high-level action string using the ACTION_MAP.
    """

    if action not in ACTION_MAP:
        msg = f"No fix strategy implemented for action: {action}"
        state.log(msg)
        return msg

    fix_fn = ACTION_MAP[action]
    result = fix_fn(state)
    return result
