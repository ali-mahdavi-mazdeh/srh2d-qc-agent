from __future__ import annotations
import numpy as np

from srh2d_qc.core.model_types import SRH2DModel, TimestepStabilityResult


def check_timestep_stability(model: SRH2DModel) -> TimestepStabilityResult:
    """
    Compute geometric timestep stability limits for each element and
    compare them to the model DT.

    This is a geometry-only Courant proxy:
        dt_geom = L_min / sqrt(g * 1)

    where:
        L_min = shortest edge length of the element
        g = 9.81 m/s^2

    Parameters
    ----------
    model : SRH2DModel
        Fully loaded model.

    Returns
    -------
    TimestepStabilityResult
        Summary of timestep stability issues.
    """

    g = 9.81
    dt = model.run_config.dt

    mesh = model.mesh
    nodes = mesh.nodes
    elements = mesh.elements
    elem_ids = mesh.element_ids

    geom_dt_list = []
    violating_ids = []

    for eid, conn in zip(elem_ids, elements):
        conn = conn[conn >= 0]
        pts = nodes[conn]

        # Compute edge lengths
        edges = np.linalg.norm(np.roll(pts, -1, axis=0) - pts, axis=1)
        L_min = edges.min()

        # Geometric dt limit
        dt_geom = L_min / np.sqrt(g * 1.0)
        geom_dt_list.append(dt_geom)

        # Check violation
        if dt > dt_geom:
            violating_ids.append(int(eid))

    geom_dt_arr = np.array(geom_dt_list)

    return TimestepStabilityResult(
        dt=float(dt),
        min_geom_dt=float(geom_dt_arr.min()),
        median_geom_dt=float(np.median(geom_dt_arr)),
        num_violations=len(violating_ids),
        violation_element_ids=violating_ids,
    )
