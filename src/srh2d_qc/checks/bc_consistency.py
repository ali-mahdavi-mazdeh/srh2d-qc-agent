from srh2d_qc.core.model_types import SRH2DModel, BoundaryCondition, BCConsistencyResult
from typing import List, Set


def check_bc_consistency(mesh, bcs) -> List[BCConsistencyResult]:
    """
    QC checks for SRH-2D boundary conditions:
      - BC nodes exist in mesh
      - BC nodes lie on mesh boundary
      - No overlapping BC nodes
      - Time series monotonicity
    """

    results: List[BCConsistencyResult] = []

    # Get boundary nodes from mesh property
    boundary_nodes = mesh.boundary_nodes

    # Track node usage to detect overlaps
    node_usage = {}

    mesh_node_ids = set(mesh.node_ids)

    for bc in bcs:
        issues = []

        # -------------------------------------------------
        # 1. Node existence check
        # -------------------------------------------------
        if bc.nodes:
            missing = [n for n in bc.nodes if n not in mesh_node_ids]
            if missing:
                issues.append(f"Missing nodes: {missing}")

        # -------------------------------------------------
        # 2. Boundary location check
        # -------------------------------------------------
        if bc.nodes:
            non_boundary = [n for n in bc.nodes if n not in boundary_nodes]
            if non_boundary and bc.bc_type not in ("INTERNAL", "SOURCE"):
                issues.append(f"Nodes not on boundary: {non_boundary}")

        # -------------------------------------------------
        # 3. Overlap check
        # -------------------------------------------------
        if bc.nodes:
            for n in bc.nodes:
                if n in node_usage:
                    issues.append(
                        f"Node {n} overlaps with BC '{node_usage[n]}'"
                    )
                else:
                    node_usage[n] = bc.name

        # -------------------------------------------------
        # 4. Time series consistency
        # -------------------------------------------------
        if bc.timeseries:
            times = [t for t, _ in bc.timeseries]
            if any(times[i] >= times[i + 1] for i in range(len(times) - 1)):
                issues.append("Time series is not strictly increasing")

        results.append(BCConsistencyResult(bc_name=bc.name, issues=issues))

    return results
