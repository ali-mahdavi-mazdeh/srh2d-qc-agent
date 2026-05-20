from __future__ import annotations
from pathlib import Path
import numpy as np

from srh2d_qc.core.model_types import Mesh, SRH2DModel
from srh2d_qc.core.model_types import Material
from srh2d_qc.core.model_types import BoundaryCondition
from srh2d_qc.core.model_types import RunConfig


from pathlib import Path
from typing import Dict, List


def parse_materials(path: Path, hydro_path: Path = None):
    """
    Parse SMS/XMS SRHMAT format with multi-line Material blocks.
    Returns Material objects keyed by material ID.
    
    Args:
        path: Path to .srhmat file
        hydro_path: Optional path to .srhhydro file to extract roughness values
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

    # Get roughness values from .srhhydro if provided
    roughness_dict: Dict[int, float] = {}
    if hydro_path:
        roughness_dict = parse_roughness_from_srhhydro(hydro_path)

    # Convert material_names to Material objects
    materials: Dict[int, Material] = {}
    for mat_id, name in material_names.items():
        roughness = roughness_dict.get(mat_id, 0.0)  # default to 0.0 if not found
        materials[mat_id] = Material(
            id=mat_id,
            name=name,
            roughness=roughness
        )

    return {
        "materials": materials,
        "assignments": elem_to_mat
    }


def parse_roughness_from_srhhydro(path: Path) -> Dict[int, float]:
    material_roughness = {}

    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split()

            if parts[0].lower() == "manningsn":
                mat_id = int(parts[1])
                value = float(parts[2])
                material_roughness[mat_id] = value

    return material_roughness
