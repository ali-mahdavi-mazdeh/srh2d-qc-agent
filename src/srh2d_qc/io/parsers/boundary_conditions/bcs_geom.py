from pathlib import Path
from typing import List
from srh2d_qc.core.model_types import BoundaryCondition

def parse_bcs_from_geom(geom_path: Path) -> List[BoundaryCondition]:
    """
    Parse BC blocks from SMS-style .srhgeom files.
    SMS sometimes embeds BCs inside the geometry file.
    """
    if not geom_path.exists():
        return []

    bcs = []
    current = None

    with geom_path.open() as f:
        for line in f:
            line = line.strip()

            if line.upper().startswith("BEGIN BOUNDARY"):
                current = {"name": None, "type": None, "nodes": [], "timeseries": []}
                continue

            if line.upper().startswith("END BOUNDARY"):
                if current:
                    bcs.append(
                        BoundaryCondition(
                            name=current["name"],
                            bc_type=current["type"],
                            nodes=current["nodes"],
                            timeseries=current["timeseries"],
                        )
                    )
                current = None
                continue

            if current is None:
                continue

            if line.upper().startswith("BC_NAME"):
                current["name"] = line.split(maxsplit=1)[1]

            elif line.upper().startswith("BC_TYPE"):
                current["type"] = line.split(maxsplit=1)[1]

            elif line.upper().startswith("BC_NODES"):
                parts = line.split()[1:]
                current["nodes"].extend([int(p) for p in parts])

            elif line.upper().startswith("BC_TS"):
                _, t, v = line.split()
                current["timeseries"].append((float(t), float(v)))

    return bcs

from pathlib import Path
from typing import Dict, List


def parse_nodestrings_from_geom(path: Path) -> Dict[str, List[int]]:
    """
    Parse SMS/XMS SRHGEOM NodeString format:

        NodeString <id> <node1> <node2> ... <nodeN>

    Returns:
        { "1": [node ids], "2": [node ids], ... }
    """
    nodestrings: Dict[str, List[int]] = {}

    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split()

            if parts[0].upper() == "NODESTRING":
                ns_id = parts[1]  # keep as string to match BC.name
                node_ids = [int(x) for x in parts[2:]]
                nodestrings[ns_id] = node_ids

    return nodestrings

