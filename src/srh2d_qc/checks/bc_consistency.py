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

    mesh_node_ids = set(mesh.nodes.keys())

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

def _find_boundary_nodes(mesh) -> Set[int]:
    """
    Identify boundary nodes by finding edges used by only one element.
    """

    boundary_nodes = set()
    edge_count = {}

    # mesh.elements is a list of connectivity lists
    for conn in mesh.elements:
        # conn is already a list of node IDs
        for i in range(len(conn)):
            n1 = conn[i]
            n2 = conn[(i + 1) % len(conn)]
            edge = tuple(sorted((n1, n2)))
            edge_count[edge] = edge_count.get(edge, 0) + 1

    for (n1, n2), count in edge_count.items():
        if count == 1:  # boundary edge
            boundary_nodes.add(n1)
            boundary_nodes.add(n2)

    return boundary_nodes
