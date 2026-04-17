from srh2d_qc.core.model_types import SRH2DModel, BoundaryCondition
from typing import List, Set
from dataclasses import dataclass


@dataclass
class BCConsistencyResult:
    bc_name: str
    issues: List[str]


def check_bc_consistency(mesh, bcs) -> List[BCConsistencyResult]:
    """
    QC checks for SRH-2D boundary conditions:
      - BC nodes exist in mesh
      - BC nodes lie on mesh boundary
      - No overlapping BC nodes
      - Time series monotonicity
    """

    results: List[BCConsistencyResult] = []

    # Precompute boundary node set
    boundary_nodes = _find_boundary_nodes(mesh)

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


# ------------------------------------------------------------
# Helper: find boundary nodes
# ------------------------------------------------------------
# todo it is not a good way to check the boundary nodes. becasue the the nodes at start and end of element does not mean boundary.
def _find_boundary_nodes(mesh) -> Set[int]:
    """
    Identify boundary nodes by finding edges used by only one element.
    Returns ORIGINAL SRH-2D node IDs.
    """

    edge_count = {}

    # mesh.elements contains node indices (0..N-1)
    for conn in mesh.elements:
        conn = [n for n in conn if n >= 0]
        for i in range(len(conn)):
            i1 = conn[i]
            i2 = conn[(i + 1) % len(conn)]
            edge = tuple(sorted((i1, i2)))
            edge_count[edge] = edge_count.get(edge, 0) + 1

    # boundary node indices
    boundary_indices = set()
    for (i1, i2), count in edge_count.items():
        if count == 1:
            boundary_indices.add(i1)
            boundary_indices.add(i2)

    # map indices → original SRH-2D node IDs
    boundary_node_ids = {int(mesh.node_ids[i]) for i in boundary_indices}

    return boundary_node_ids
