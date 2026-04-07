from __future__ import annotations
from pathlib import Path
from srh2d_qc.core.model_types import QCResults


def generate_markdown_report(results: QCResults) -> str:
    """
    Generate a human-readable Markdown QC report from QCResults.

    Parameters
    ----------
    results : QCResults
        Aggregated QC results from run_all_qc().

    Returns
    -------
    str
        Markdown-formatted QC report.
    """

    # ------------------------------------------------------------
    # Mesh Quality Summary
    # ------------------------------------------------------------
    mq = results.mesh_quality
    min_angles = [r.min_angle for r in mq]
    max_angles = [r.max_angle for r in mq]
    aspect_ratios = [r.aspect_ratio for r in mq]
    skewness = [r.skewness for r in mq]
    areas = [r.area for r in mq]

    mesh_section = f"""
# SRH‑2D QC Report

## Mesh Quality

**Elements:** {len(mq)}

- Min angle range: {min(min_angles):.2f}° – {max(min_angles):.2f}°
- Max angle range: {min(max_angles):.2f}° – {max(max_angles):.2f}°
- Aspect ratio range: {min(aspect_ratios):.2f} – {max(aspect_ratios):.2f}
- Skewness range: {min(skewness):.2f}° – {max(skewness):.2f}°
- Area range: {min(areas):.4f} – {max(areas):.4f}
"""

    # ------------------------------------------------------------
    # BC Consistency Summary
    # ------------------------------------------------------------
    bc_section = "## Boundary Condition Consistency\n\n"

    for bc in results.bc_consistency:
        if bc.issues:
            issues_text = "\n".join(f"- {issue}" for issue in bc.issues)
        else:
            issues_text = "_No issues detected_"

        bc_section += f"""
### {bc.bc_name}
{issues_text}

"""

    # ------------------------------------------------------------
    # Material Coverage Summary
    # ------------------------------------------------------------
    mc = results.material_coverage

    material_section = f"""
## Material Coverage

- Missing material IDs: {mc.missing_material_ids or "_None_"}
- Unused material IDs: {mc.unused_material_ids or "_None_"}

### Element counts per material
"""

    for mid, count in mc.element_counts.items():
        material_section += f"- Material {mid}: {count} elements\n"

    # ------------------------------------------------------------
    # Timestep Stability Summary
    # ------------------------------------------------------------
    ts = results.timestep_stability

    timestep_section = f"""
## Timestep Stability

- Model DT: {ts.dt:.4f} s
- Minimum geometric DT: {ts.min_geom_dt:.4f} s
- Median geometric DT: {ts.median_geom_dt:.4f} s
- Violating elements: {ts.num_violations}

"""

    if ts.violation_element_ids:
        timestep_section += "### Violating element IDs\n"
        timestep_section += ", ".join(str(e) for e in ts.violation_element_ids[:50])
        if ts.num_violations > 50:
            timestep_section += f"\n… and {ts.num_violations - 50} more"

    # ------------------------------------------------------------
    # Combine all sections
    # ------------------------------------------------------------
    return (
        mesh_section
        + "\n"
        + bc_section
        + "\n"
        + material_section
        + "\n"
        + timestep_section
    )
