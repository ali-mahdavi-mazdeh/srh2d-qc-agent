from __future__ import annotations
from pathlib import Path
import numpy as np

from srh2d_qc.core.model_types import Mesh


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

    return Mesh(
    nodes=nodes,
    node_ids=np.array(sorted_node_ids, dtype=int),
    elements=elements,
    element_ids=np.array(element_ids, dtype=int),
    material_ids=material_ids
)
