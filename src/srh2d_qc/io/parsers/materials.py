from __future__ import annotations
from pathlib import Path
import numpy as np

from srh2d_qc.core.model_types import Mesh
from srh2d_qc.core.model_types import Material
from srh2d_qc.core.model_types import BoundaryCondition
from srh2d_qc.core.model_types import RunConfig


from pathlib import Path
from typing import Dict, List


def parse_materials(path: Path):
    """
    Parse SMS/XMS SRHMAT format with multi-line Material blocks.
    """

    material_names: Dict[int, str] = {}
    elem_to_mat: Dict[int, int] = {}

    current_mat_id = None

    with path.open() as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue

            parts = line.split()

            # Start of a new material name
            if parts[0] == "MatName":
                mat_id = int(parts[1])
                name = " ".join(parts[2:]).strip('"')
                material_names[mat_id] = name
                current_mat_id = None  # stop any ongoing block
                continue

            # Start of a new Material block
            if parts[0] == "Material":
                current_mat_id = int(parts[1])
                elem_ids = [int(x) for x in parts[2:]]
                for eid in elem_ids:
                    elem_to_mat[eid] = current_mat_id
                continue

            # Continuation of a Material block
            if current_mat_id is not None:
                # As long as the line does NOT start with a keyword,
                # treat it as continuation of element IDs
                if parts[0] not in ("MatName", "Material", "SRHMAT", "NMaterials"):
                    elem_ids = [int(x) for x in parts]
                    for eid in elem_ids:
                        elem_to_mat[eid] = current_mat_id
                    continue
                else:
                    # Hit a new keyword → stop continuation
                    current_mat_id = None

    return {
        "names": material_names,
        "assignments": elem_to_mat
    }
