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
    nodes = {}
    elements = {}

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
                elements[eid] = node_ids

            elif tag == "NODE":
                # Format: NODE <nid> <x> <y> <z>
                nid = int(parts[1])
                x = float(parts[2])
                y = float(parts[3])
                # elevation exists but QC uses only x,y
                # we store it anyway for completeness
                z = float(parts[4])
                nodes[nid] = (x, y, z)

    if not nodes:
        raise ValueError(f"No NODE entries found in {path}")

    if not elements:
        raise ValueError(f"No ELEM entries found in {path}")

    # Convert dicts to sorted arrays
    element_ids = sorted(elements.keys())
    element_conn = [elements[eid] for eid in element_ids]

    # Placeholder material IDs (filled later)
    material_ids = [-1] * len(element_ids)

    return Mesh(
        nodes=nodes,
        elements=element_conn,
        element_ids=element_ids,
        material_ids=material_ids
    )
