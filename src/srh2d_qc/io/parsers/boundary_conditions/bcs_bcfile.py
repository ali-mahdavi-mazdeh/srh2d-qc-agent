from pathlib import Path
from typing import List
from srh2d_qc.core.model_types import BoundaryCondition


def parse_bcs_from_bcfile(bc_path: Path) -> List[BoundaryCondition]:
    """
    Parse standalone .bc files (SMS or pyHMT2D).
    Format is identical to BC blocks in .srhhydro.
    """
    if not bc_path.exists():
        return []

    bcs = []
    current = None

    with bc_path.open() as f:
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
