from __future__ import annotations
import numpy as np

from srh2d_qc.core.model_types import SRH2DModel, TimestepStabilityResult


def check_timestep_stability(model: SRH2DModel) -> TimestepStabilityResult:
    """
    Compute geometric timestep stability limits for each element and
    compare them to the model DT.

    Geometry-only Courant proxy:
        dt_geom = L_min / sqrt(g * 1)
    """

    g = 9.81
    dt = model.run_config["dt"]   # new run_config structure

    mesh = model.mesh
    nodes = mesh.nodes            # dict: {node_id: (x,y)}
    elements = mesh.elements      # list of lists
    elem_ids = mesh.element_ids   # list of element IDs

    geom_dt_list = []
    violating_ids = []

    for eid, conn in zip(elem_ids, elements):

        # ---------------------------------------------------------
        # 1. Clean connectivity (remove -1 padding)
        # ---------------------------------------------------------
        conn = [n for n in conn if n >= 0]

        # ---------------------------------------------------------
        # 2. Convert node IDs → coordinate array
        # ---------------------------------------------------------
        try:
            pts = np.array([nodes[nid] for nid in conn], dtype=float)
        except KeyError:
            # Missing node → treat as degenerate
            geom_dt_list.append(0.0)
            violating_ids.append(int(eid))
            continue

        # ---------------------------------------------------------
        # 3. Compute edge lengths
        # ---------------------------------------------------------
        edges = np.linalg.norm(np.roll(pts, -1, axis=0) - pts, axis=1)
        L_min = edges.min()

        # ---------------------------------------------------------
        # 4. Geometric dt limit
        # ---------------------------------------------------------
        dt_geom = L_min / np.sqrt(g * 1.0)
        geom_dt_list.append(dt_geom)

        # ---------------------------------------------------------
        # 5. Check violation
        # ---------------------------------------------------------
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
