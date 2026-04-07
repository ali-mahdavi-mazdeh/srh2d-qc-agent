from __future__ import annotations
from pathlib import Path

from srh2d_qc.core.model_types import QCResults, SRH2DModel
from srh2d_qc.io.model_loader import load_model
from srh2d_qc.checks.mesh_quality import compute_mesh_quality
from srh2d_qc.checks.bc_consistency import check_bc_consistency
from srh2d_qc.checks.materials import check_material_coverage
from srh2d_qc.checks.timestep_stability import check_timestep_stability


def run_all_qc(model_dir: Path) -> QCResults:
    """
    Load an SRH-2D model from a directory and run all QC checks.

    Parameters
    ----------
    model_dir : Path
        Directory containing SRH-2D input files.

    Returns
    -------
    QCResults
        Aggregated QC results for the model.
    """
    model: SRH2DModel = load_model(model_dir)

    mesh_quality = compute_mesh_quality(model.mesh)
    bc_consistency = check_bc_consistency(model)
    material_coverage = check_material_coverage(model)
    timestep_stability = check_timestep_stability(model)

    return QCResults(
        mesh_quality=mesh_quality,
        bc_consistency=bc_consistency,
        material_coverage=material_coverage,
        timestep_stability=timestep_stability,
    )
