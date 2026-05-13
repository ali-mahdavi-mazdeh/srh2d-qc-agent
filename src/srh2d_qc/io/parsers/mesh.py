from __future__ import annotations
from pathlib import Path
import numpy as np
from typing import Set

from srh2d_qc.core.model_types import Mesh


def compute_boundary_nodes(elements, node_ids) -> Set[int]:
    """
    Identify boundary nodes by finding edges used by only one element.
    
    Args:
        elements: NumPy array of shape (M, 4) with node indices (0..N-1), -1 for unused
        node_ids: NumPy array of original SRH-2D node IDs
    
    Returns:
        Set of ORIGINAL SRH-2D node IDs that are on the mesh boundary
    """
    edge_count = {}

    # Count edge usage across all elements
    for conn in elements:
        conn = [n for n in conn if n >= 0]
        for i in range(len(conn)):
            i1 = conn[i]
            i2 = conn[(i + 1) % len(conn)]
            edge = tuple(sorted((i1, i2)))
            edge_count[edge] = edge_count.get(edge, 0) + 1

    # Boundary node indices
    boundary_indices = set()
    for (i1, i2), count in edge_count.items():
        if count == 1:
            boundary_indices.add(i1)
            boundary_indices.add(i2)

    # Map indices to original SRH-2D node IDs
    boundary_node_ids = {int(node_ids[i]) for i in boundary_indices}

    return boundary_node_ids


def parse_mesh(path: Path) -> Mesh:
    """
    Auto-detect mesh format:
      - classic SRH-2D .srhgeom (ELEM/NODE)
      - SMS .mesh (ND/E4T)
    """
    with path.open() as f:
        first_200 = [next(f).strip() for _ in range(200)]

    # Classic SRH-2D (Elem first, Node later)
    if any(line.startswith("Elem") for line in first_200) or \
       any(line.startswith("Node") for line in first_200):
        print(f"Detected classic SRH-2D .srhgeom format in {path}")
        return parse_srhgeom_mesh(path)

    # SMS .mesh
    if any(line.startswith("ND") for line in first_200):
        print(f"Detected SMS .mesh format in {path}")
        return parse_sms_mesh(path)

    raise ValueError(f"Unrecognized mesh format in {path}")

def parse_srhgeom_mesh(path: Path) -> Mesh:
    nodes_dict = {}
    elements_dict = {}

    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            tag = parts[0].upper()

            if tag == "ELEM":
                # Format: ELEM <eid> <n1> <n2> <n3> [n4]
                eid = int(parts[1])
                node_ids = [int(p) for p in parts[2:]]
                elements_dict[eid] = node_ids

            elif tag == "NODE":
                # Format: NODE <nid> <x> <y> <z>
                nid = int(parts[1])
                x = float(parts[2])
                y = float(parts[3])
                z = float(parts[4])
                nodes_dict[nid] = (x, y, z)

    if not nodes_dict:
        raise ValueError(f"No NODE entries found in {path}")

    if not elements_dict:
        raise ValueError(f"No ELEM entries found in {path}")

    # ---------------------------------------------------------
    # Convert nodes to NumPy array indexed by node ID
    # ---------------------------------------------------------
    sorted_node_ids = sorted(nodes_dict.keys())
    node_index_map = {nid: i for i, nid in enumerate(sorted_node_ids)}

    # nodes array shape: (N, 2) for QC (x, y only)
    nodes = np.array(
        [(nodes_dict[nid][0], nodes_dict[nid][1]) for nid in sorted_node_ids],
        dtype=float
    )

    # ---------------------------------------------------------
    # Convert elements to padded NumPy array
    # ---------------------------------------------------------
    element_ids = sorted(elements_dict.keys())
    element_conn_list = []

    for eid in element_ids:
        conn = elements_dict[eid]

        # Pad triangles to quads with -1
        if len(conn) == 3:
            conn = conn + [-1]

        element_conn_list.append([node_index_map[n] if n != -1 else -1 for n in conn])

    elements = np.array(element_conn_list, dtype=int)

    # ---------------------------------------------------------
    # Placeholder material IDs (filled later)
    # ---------------------------------------------------------
    material_ids = np.full(len(element_ids), -1, dtype=int)

    # ---------------------------------------------------------
    # Compute boundary nodes
    # ---------------------------------------------------------
    boundary_nodes = compute_boundary_nodes(elements, np.array(sorted_node_ids, dtype=int))

    return Mesh(
        nodes=nodes,
        node_ids=np.array(sorted_node_ids, dtype=int),
        elements=elements,
        element_ids=np.array(element_ids, dtype=int),
        material_ids=material_ids,
        boundary_nodes=boundary_nodes
    )


def parse_sms_mesh(path: Path) -> Mesh:
    """
    Parse SMS .mesh format (ND for nodes, E3T/E4T for elements).
    """
    nodes_dict = {}
    elements_dict = {}

    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            tag = parts[0].upper()

            if tag == "ND":
                # Format: ND <nid> <x> <y> [z]
                nid = int(parts[1])
                x = float(parts[2])
                y = float(parts[3])
                z = float(parts[4]) if len(parts) > 4 else 0.0
                nodes_dict[nid] = (x, y, z)

            elif tag in ("E3T", "E4T"):
                # Format: E3T/E4T <eid> <n1> <n2> <n3> [n4]
                eid = int(parts[1])
                node_ids = [int(p) for p in parts[2:]]
                elements_dict[eid] = node_ids

    if not nodes_dict:
        raise ValueError(f"No ND entries found in {path}")

    if not elements_dict:
        raise ValueError(f"No E3T/E4T entries found in {path}")

    # ---------------------------------------------------------
    # Convert nodes to NumPy array indexed by node ID
    # ---------------------------------------------------------
    sorted_node_ids = sorted(nodes_dict.keys())
    node_index_map = {nid: i for i, nid in enumerate(sorted_node_ids)}

    # nodes array shape: (N, 2) for QC (x, y only)
    nodes = np.array(
        [(nodes_dict[nid][0], nodes_dict[nid][1]) for nid in sorted_node_ids],
        dtype=float
    )

    # ---------------------------------------------------------
    # Convert elements to padded NumPy array
    # ---------------------------------------------------------
    element_ids = sorted(elements_dict.keys())
    element_conn_list = []

    for eid in element_ids:
        conn = elements_dict[eid]

        # Pad triangles to quads with -1
        if len(conn) == 3:
            conn = conn + [-1]

        element_conn_list.append([node_index_map[n] if n != -1 else -1 for n in conn])

    elements = np.array(element_conn_list, dtype=int)

    # ---------------------------------------------------------
    # Placeholder material IDs (filled later)
    # ---------------------------------------------------------
    material_ids = np.full(len(element_ids), -1, dtype=int)

    # ---------------------------------------------------------
    # Compute boundary nodes
    # ---------------------------------------------------------
    boundary_nodes = compute_boundary_nodes(elements, np.array(sorted_node_ids, dtype=int))

    return Mesh(
        nodes=nodes,
        node_ids=np.array(sorted_node_ids, dtype=int),
        elements=elements,
        element_ids=np.array(element_ids, dtype=int),
        material_ids=material_ids,
        boundary_nodes=boundary_nodes
    )
