from __future__ import annotations
from collections import Counter

from srh2d_qc.core.model_types import SRH2DModel, MaterialCoverageResult


def check_material_coverage(model: SRH2DModel) -> MaterialCoverageResult:
    """
    QC checks for SRH-2D material usage:
      - Elements referencing undefined materials
      - Materials defined but not used
      - Element counts per material
    """

    mesh = model.mesh
    materials = model.materials

    # ---------------------------------------------------------
    # 1. Material IDs defined in SRHMAT
    # ---------------------------------------------------------
    defined_ids = set(materials["names"].keys())

    # ---------------------------------------------------------
    # 2. Material IDs used by elements
    # ---------------------------------------------------------
    used_ids = set(int(mid) for mid in mesh.material_ids)

    # ---------------------------------------------------------
    # 3. Missing materials (elements reference undefined IDs)
    # ---------------------------------------------------------
    missing = sorted(list(used_ids - defined_ids))

    # ---------------------------------------------------------
    # 4. Unused materials (defined but not used)
    # ---------------------------------------------------------
    unused = sorted(list(defined_ids - used_ids))

    # ---------------------------------------------------------
    # 5. Element counts per material
    # ---------------------------------------------------------
    counts = Counter(int(mid) for mid in mesh.material_ids)

    return MaterialCoverageResult(
        missing_material_ids=missing,
        unused_material_ids=unused,
        element_counts=dict(counts),
    )
