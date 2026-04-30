from __future__ import annotations
from srh2d_qc.core.model_types import QCResults


def generate_markdown_report(results: QCResults, state=None) -> str:
    """
    Generate a human-readable Markdown QC report from QCResults.
    Optionally includes LLM review sections if `state` is provided.
    """

    # ------------------------------------------------------------
    # Mesh Quality Summary
    # ------------------------------------------------------------
    mq = results.mesh_quality

    if mq:
        s = mq.summary
        elems = mq.per_element

        mesh_section = f"""
# SRH‑2D QC Report

## Mesh Quality

**Elements:** {len(elems)}

- Min angle range: {s.min_angle:.2f}° – {s.max_angle:.2f}°
- Max angle range: {s.min_angle:.2f}° – {s.max_angle:.2f}°
- Aspect ratio range: {s.min_aspect_ratio:.2f} – {s.max_aspect_ratio:.2f}
- Skewness range: {s.min_skewness:.2f}° – {s.max_skewness:.2f}°
- Area range: {s.min_area:.4f} – {s.max_area:.4f}
"""
    else:
        mesh_section = """
# SRH‑2D QC Report

## Mesh Quality

_No mesh elements found_
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
### BC {bc.bc_name}
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
        timestep_section += "\n### Violating element IDs\n"
        timestep_section += ", ".join(str(e) for e in ts.violation_element_ids[:50])
        if ts.num_violations > 50:
            timestep_section += f"\n… and {ts.num_violations - 50} more"

    # ------------------------------------------------------------
    # LLM REVIEW SECTIONS (optional)
    # ------------------------------------------------------------
    llm_section = ""
    if state and (state.llm_summary or state.llm_prioritized_actions or state.llm_notes):
        llm_section += "\n---\n"
        llm_section += "## LLM Review Summary\n"

        # Summary
        if state.llm_summary:
            if isinstance(state.llm_summary, list):
                for item in state.llm_summary:
                    llm_section += f"- {item}\n"
            else:
                llm_section += f"{state.llm_summary}\n"
        else:
            llm_section += "_No LLM summary available._\n"

        # Prioritized actions
        llm_section += "\n## LLM Prioritized Actions\n"
        if state.llm_prioritized_actions:
            for action in state.llm_prioritized_actions:
                llm_section += f"- {action}\n"
        else:
            llm_section += "_No prioritized actions available._\n"

        # Notes
        llm_section += "\n## LLM Notes\n"
        if state.llm_notes:
            llm_section += f"{state.llm_notes}\n"
        else:
            llm_section += "_No LLM notes available._\n"

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
        + "\n"
        + llm_section
    )
