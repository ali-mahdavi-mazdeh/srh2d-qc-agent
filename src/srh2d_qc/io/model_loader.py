from __future__ import annotations
from pathlib import Path

from srh2d_qc.core.model_types import SRH2DModel
from srh2d_qc.io.parsers import (
    parse_mesh,
    parse_srhgeom_mesh,
    parse_materials,
    parse_bcs,
    parse_run_config,
)


def load_model(model_dir: Path) -> SRH2DModel:
    """
    Load an SRH-2D model from a directory.

    This function orchestrates all parsing steps:
      - Mesh:     .mesh or .srhgeom
      - Materials: .mat or .srhgeom
      - BCs:       .bc or .srhgeom
      - Run config: .srhhydro

    The function is intentionally minimal and QC-focused.
    It does not validate the model; it only loads it.

    Parameters
    ----------
    model_dir : Path
        Directory containing SRH-2D input files.

    Returns
    -------
    SRH2DModel
        Fully assembled model object.

    Raises
    ------
    FileNotFoundError
        If required files are missing.
    ValueError
        If parsing fails or required content is missing.
    """

    model_dir = Path(model_dir)

    # -------------------------
    # 1. Mesh: try .mesh first, then .srhgeom
    # -------------------------
    mesh_file = model_dir / "model.mesh"
    geom_file = model_dir / "model.srhgeom"

    if mesh_file.exists():
        mesh = parse_mesh(mesh_file)
    elif geom_file.exists():
        mesh = parse_srhgeom_mesh(geom_file)
    else:
        raise FileNotFoundError(
            f"No mesh found in {model_dir}. Expected model.mesh or model.srhgeom."
        )

    # -------------------------
    # 2. Materials: try .mat first, then .srhgeom
    # -------------------------
    mat_file = model_dir / "model.mat"

    if mat_file.exists():
        materials = parse_materials(mat_file)
    elif geom_file.exists():
        materials = parse_materials(geom_file)
    else:
        raise FileNotFoundError(
            f"No material definitions found in {model_dir}. "
            "Expected model.mat or MATERIAL block in model.srhgeom."
        )

    # -------------------------
    # 3. Boundary Conditions: try .bc first, then .srhgeom
    # -------------------------
    bc_file = model_dir / "model.bc"

    if bc_file.exists():
        bcs = parse_bcs(bc_file)
    elif geom_file.exists():
        bcs = parse_bcs(geom_file)
    else:
        raise FileNotFoundError(
            f"No boundary conditions found in {model_dir}. "
            "Expected model.bc or BOUNDARY blocks in model.srhgeom."
        )

    # -------------------------
    # 4. Run configuration: must have .srhhydro
    # -------------------------
    hydro_file = model_dir / "model.srhhydro"

    if not hydro_file.exists():
        raise FileNotFoundError(
            f"Run configuration file missing: {hydro_file}"
        )

    run_config = parse_run_config(hydro_file)

    # -------------------------
    # 5. Assemble the full model
    # -------------------------
    return SRH2DModel(
        mesh=mesh,
        materials=materials,
        bcs=bcs,
        run_config=run_config,
        model_dir=model_dir,
    )
