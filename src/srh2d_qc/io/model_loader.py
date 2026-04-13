from pathlib import Path
from srh2d_qc.core.bc_utils import find_bc_elements
from srh2d_qc.io.parsers.mesh import parse_mesh
from srh2d_qc.io.parsers.materials import parse_materials
from srh2d_qc.io.parsers.run_config import parse_run_config
from srh2d_qc.io.parsers.boundary_conditions.bcs_unified import parse_bcs_from_files

from srh2d_qc.core.model_types import SRH2DModel
from typing import Union

def load_model(path: Union[str, Path]) -> SRH2DModel:
    """
    Load an SRH-2D model using the .srhhydro file as the primary entry point.

    Accepts either:
      - a path to a .srhhydro file, or
      - a directory containing exactly one .srhhydro file.
    """
    path = Path(path)

    # ---------------------------------------------------------
    # 1. Resolve entry .srhhydro file and model directory
    # ---------------------------------------------------------
    if path.is_file() and path.suffix.lower() == ".srhhydro":
        hydro_path = path
        model_dir = path.parent
    elif path.is_dir():
        hydro_files = list(path.glob("*.srhhydro"))
        if len(hydro_files) == 0:
            raise FileNotFoundError(
                f"No .srhhydro file found in {path}. "
                "Expected a native SRH-2D model (e.g., case01.srhhydro)."
            )
        if len(hydro_files) > 1:
            names = ", ".join(p.name for p in hydro_files)
            raise ValueError(
                f"Multiple .srhhydro files found in {path}: {names}. "
                "Please specify which case to load by passing the .srhhydro file path."
            )
        hydro_path = hydro_files[0]
        model_dir = path
    else:
        raise FileNotFoundError(
            f"{path} is neither a .srhhydro file nor a directory."
        )

    # ---------------------------------------------------------
    # 2. Extract case prefix from .srhhydro filename
    # ---------------------------------------------------------
    prefix = hydro_path.stem  # e.g., 'case01' from 'case01.srhhydro'

    geom_path = model_dir / f"{prefix}.srhgeom"
    mat_path = model_dir / f"{prefix}.srhmat"

    # ---------------------------------------------------------
    # 3. Validate required files
    # ---------------------------------------------------------
    missing = []
    if not geom_path.exists():
        missing.append(geom_path.name)
    if not mat_path.exists():
        missing.append(mat_path.name)
    if not hydro_path.exists():
        missing.append(hydro_path.name)

    if missing:
        missing_str = ", ".join(missing)
        raise FileNotFoundError(
            f"Missing required SRH-2D input files for case '{prefix}' in {model_dir}: {missing_str}"
        )

    # ---------------------------------------------------------
    # 4. Parse geometry, materials, run config, and BCs
    # ---------------------------------------------------------
    mesh = parse_mesh(geom_path)

    # Primary: native SRH-2D .srhmat
    # (You can add a fallback to parse from .srhgeom if .srhmat is missing in SMS workflows.)
    materials = parse_materials(mat_path)

    elem_to_mat = materials["assignments"]

    material_ids = [
        elem_to_mat.get(eid, -1)   # default -1 if not assigned
        for eid in mesh.element_ids
    ]

    mesh.material_ids = material_ids

    run_config = parse_run_config(hydro_path)

    # BCs: primary from .srhhydro, with optional fallbacks inside parse_bcs_from_files
    bcs = parse_bcs_from_files(
        geom_path=geom_path,
        hydro_path=hydro_path,
        model_dir=model_dir,
    )

    for bc in bcs:
        if bc.nodes:
            bc.elements = find_bc_elements(bc.nodes, mesh)

    # ---------------------------------------------------------
    # 5. Build SRH2DModel
    # ---------------------------------------------------------
    model = SRH2DModel(
        mesh=mesh,
        materials=materials,
        bcs=bcs,
        run_config=run_config,
        model_dir=model_dir,
    )

    return model
